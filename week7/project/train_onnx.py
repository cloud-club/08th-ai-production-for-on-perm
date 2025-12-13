# train_onnx.py
import argparse
from pathlib import Path
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image
from tqdm import tqdm
import onnxruntime as ort 

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

def list_images(d: Path) -> List[Path]:
    return sorted([p for p in d.rglob("*") if p.is_file() and p.suffix.lower() in IMG_EXT])

def fixed_image_standardization(img_255: np.ndarray) -> np.ndarray:
    # facenet-pytorch fixed_image_standardization: (x - 127.5) / 128.0 
    return (img_255.astype(np.float32) - 127.5) / 128.0

def l2norm(x: np.ndarray, axis: int = -1, eps: float = 1e-12) -> np.ndarray:
    return x / (np.linalg.norm(x, axis=axis, keepdims=True) + eps)

def embed_one(sess: ort.InferenceSession, in_name: str, img_path: Path) -> Optional[np.ndarray]:
    try:
        img = Image.open(img_path).convert("RGB").resize((160,160))
    except Exception:
        return None
    arr = np.asarray(img).astype(np.float32)  # HWC [0,255]
    arr = fixed_image_standardization(arr)    # HWC
    x = np.transpose(arr, (2,0,1))[None, ...].astype(np.float32)  # 1,3,160,160
    out = sess.run(None, {in_name: x})[0]     # 1,512
    e = l2norm(out, axis=1)[0]                # (512,)
    return e.astype(np.float32)

def choose_threshold(me_scores: np.ndarray, other_scores: np.ndarray, target_far: Optional[float]) -> Tuple[float, dict]:
    all_scores = np.concatenate([me_scores, other_scores])
    lo, hi = float(all_scores.min()), float(all_scores.max())
    thresholds = np.linspace(lo, hi, 400)

    best_key = None
    best = None

    for th in thresholds:
        tp = (me_scores >= th).sum()
        fn = (me_scores < th).sum()
        fp = (other_scores >= th).sum()
        tn = (other_scores < th).sum()

        tpr = tp / max(1, tp + fn)
        fpr = fp / max(1, fp + tn)
        prec = tp / max(1, tp + fp)
        rec = tpr
        f1 = (2 * prec * rec) / max(1e-12, prec + rec)

        if target_far is not None:
            if fpr <= target_far:
                key = (tpr, -fpr)
            else:
                continue
        else:
            key = (f1, -fpr)

        if best_key is None or key > best_key:
            best_key = key
            best = (th, tpr, fpr, prec, rec, f1)

    if best is None:
        th = float(np.max(thresholds))
        return th, {"warning": "target_far를 만족하는 threshold를 찾지 못해 가장 보수적으로 설정"}

    th, tpr, fpr, prec, rec, f1 = best
    return float(th), {"tpr": float(tpr), "fpr": float(fpr), "precision": float(prec), "recall": float(rec), "f1": float(f1)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--me_dir", type=str, required=True, help="내 얼굴 크롭 폴더(preprocess_onnx 결과)")
    ap.add_argument("--others_dir", type=str, default="", help="타인 얼굴 크롭 폴더(선택)")
    ap.add_argument("--embed_onnx", type=str, required=True, help="facenet_embed.onnx")
    ap.add_argument("--out", type=str, default="verifier.npz")
    ap.add_argument("--reject_rate", type=float, default=0.05, help="others 없을 때: me 점수 하위 분위수")
    ap.add_argument("--target_far", type=float, default=None, help="others 있을 때: FAR 목표(예 0.001)")
    ap.add_argument("--temperature", type=float, default=12.0)
    ap.add_argument("--providers", type=str, default="CPUExecutionProvider")
    args = ap.parse_args()

    me_paths = list_images(Path(args.me_dir))
    if not me_paths:
        raise SystemExit("me_dir에 이미지가 없습니다.")

    others_paths = list_images(Path(args.others_dir)) if args.others_dir else []

    providers = [p.strip() for p in args.providers.split(",") if p.strip()]
    sess = ort.InferenceSession(args.embed_onnx, providers=providers)  
    in_name = sess.get_inputs()[0].name

    me_embs = []
    for p in tqdm(me_paths, desc="embed me"):
        e = embed_one(sess, in_name, p)
        if e is not None:
            me_embs.append(e)
    if len(me_embs) == 0:
        raise SystemExit("me 임베딩 생성 실패(이미지/모델 확인).")
    me_embs = np.stack(me_embs, axis=0)  # (Nm,512)

    centroid = l2norm(me_embs.mean(axis=0, keepdims=False), axis=0).astype(np.float32)  # (512,)
    me_scores = (me_embs @ centroid).astype(np.float32)

    info = {"mode": "", "detail": {}}
    if len(others_paths) > 0:
        other_embs = []
        for p in tqdm(others_paths, desc="embed others"):
            e = embed_one(sess, in_name, p)
            if e is not None:
                other_embs.append(e)
        if len(other_embs) == 0:
            print("[WARN] others_dir가 있었지만 임베딩이 0개라 me-only로 진행합니다.")
        else:
            other_embs = np.stack(other_embs, axis=0)
            other_scores = (other_embs @ centroid).astype(np.float32)
            th, detail = choose_threshold(me_scores, other_scores, args.target_far)
            threshold = th
            info["mode"] = "calibrated_with_others"
            info["detail"] = detail
    if info["mode"] == "":
        threshold = float(np.quantile(me_scores, args.reject_rate))
        info["mode"] = "me_only_quantile"
        info["detail"] = {"reject_rate": args.reject_rate}

    np.savez(
        args.out,
        centroid=centroid,
        threshold=np.array([threshold], dtype=np.float32),
        temperature=np.array([args.temperature], dtype=np.float32),
        info=np.array([str(info)], dtype=object),
    )
    print(f"Saved: {args.out}")
    print(f"threshold={threshold:.4f} mode={info['mode']} providers={providers}")

if __name__ == "__main__":
    main()
