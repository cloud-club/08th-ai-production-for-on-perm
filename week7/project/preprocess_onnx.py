# preprocess_onnx.py
import argparse
from pathlib import Path
from typing import Iterable, List, Tuple, Optional

import numpy as np
from PIL import Image
from tqdm import tqdm
import onnxruntime as ort

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}

def iter_images(p: Path) -> Iterable[Path]:
    if p.is_file():
        yield p
        return
    for f in p.rglob("*"):
        if f.is_file() and f.suffix.lower() in IMG_EXT:
            yield f

def letterbox(im: np.ndarray, new_shape: Tuple[int,int], color=(114,114,114)) -> Tuple[np.ndarray, float, Tuple[int,int]]:
    """Ultralytics ONNXRuntime 예제의 letterbox 개념(비율 유지 + 패딩) 기반. :contentReference[oaicite:6]{index=6}"""
    shape = im.shape[:2]  # (h,w)
    h0, w0 = shape
    h1, w1 = new_shape

    r = min(h1 / h0, w1 / w0)
    new_unpad = (int(round(w0 * r)), int(round(h0 * r)))  # (w,h)

    im_resized = np.array(Image.fromarray(im).resize(new_unpad, Image.BILINEAR))
    dw = w1 - new_unpad[0]
    dh = h1 - new_unpad[1]
    dw //= 2
    dh //= 2

    out = np.full((h1, w1, 3), color, dtype=np.uint8)
    out[dh:dh + new_unpad[1], dw:dw + new_unpad[0], :] = im_resized
    return out, r, (dw, dh)

def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1 / (1 + np.exp(-x))

def nms_xyxy(boxes: np.ndarray, scores: np.ndarray, iou_thres: float) -> List[int]:
    """간단 NMS(ORT-only)."""
    x1, y1, x2, y2 = boxes[:,0], boxes[:,1], boxes[:,2], boxes[:,3]
    areas = (x2 - x1 + 1e-6) * (y2 - y1 + 1e-6)
    order = scores.argsort()[::-1]
    keep = []
    while order.size > 0:
        i = order[0]
        keep.append(int(i))
        if order.size == 1:
            break
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])
        w = np.maximum(0.0, xx2 - xx1)
        h = np.maximum(0.0, yy2 - yy1)
        inter = w * h
        iou = inter / (areas[i] + areas[order[1:]] - inter + 1e-6)
        inds = np.where(iou <= iou_thres)[0]
        order = order[inds + 1]
    return keep

def decode_ultralytics_output(out: np.ndarray, conf_thres: float, iou_thres: float) -> np.ndarray:
    """
    1) NMS 포함 export(nms=True)인 경우: (1,N,6) 형태(x1,y1,x2,y2,score,cls)로 나오는 경우가 많음.
    2) NMS 없는 경우: (1,84,8400) 또는 (1,8400,84) 같이 나올 수 있어 최소한의 디코딩 제공.
    """
    out = np.array(out)
    if out.ndim == 3 and out.shape[-1] == 6:
        det = out[0]
        det = det[det[:,4] >= conf_thres]
        return det

    # fallback: (1, C, N) or (1, N, C)
    x = out[0]
    if x.shape[0] < x.shape[1]:
        # (C,N) -> (N,C)
        x = x.T

    # x: (N, 4+nc) or (N, 5+nc)
    # Ultralytics ONNX는 모델/버전에 따라 다르므로, 여기선 "가장 흔한 케이스"만 처리:
    # - 첫 4개: xywh (center-x,center-y,width,height) in input scale
    # - 나머지: class scores (nc>=1)
    xywh = x[:, :4]
    cls_scores = x[:, 4:]  # (N,nc)
    if cls_scores.shape[1] == 0:
        return np.zeros((0,6), dtype=np.float32)

    scores = cls_scores.max(axis=1)
    cls = cls_scores.argmax(axis=1).astype(np.float32)

    mask = scores >= conf_thres
    xywh, scores, cls = xywh[mask], scores[mask], cls[mask]
    if xywh.shape[0] == 0:
        return np.zeros((0,6), dtype=np.float32)

    # xywh -> xyxy
    cx, cy, w, h = xywh[:,0], xywh[:,1], xywh[:,2], xywh[:,3]
    x1 = cx - w/2
    y1 = cy - h/2
    x2 = cx + w/2
    y2 = cy + h/2
    boxes = np.stack([x1,y1,x2,y2], axis=1).astype(np.float32)

    keep = nms_xyxy(boxes, scores.astype(np.float32), iou_thres)
    boxes = boxes[keep]
    scores = scores[keep]
    cls = cls[keep]
    det = np.concatenate([boxes, scores[:,None].astype(np.float32), cls[:,None].astype(np.float32)], axis=1)
    return det

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", type=str, required=True)
    ap.add_argument("--output", type=str, default="faces_out")
    ap.add_argument("--yolo_onnx", type=str, required=True)
    ap.add_argument("--conf", type=float, default=0.5)
    ap.add_argument("--iou", type=float, default=0.5)
    ap.add_argument("--margin_ratio", type=float, default=0.25)
    ap.add_argument("--keep_all", action="store_true")
    ap.add_argument("--pick", choices=["best","largest"], default="best")
    ap.add_argument("--face_size", type=int, default=160)
    ap.add_argument("--providers", type=str, default="CPUExecutionProvider")
    args = ap.parse_args()

    inp = Path(args.input)
    outdir = Path(args.output)
    outdir.mkdir(parents=True, exist_ok=True)

    providers = [p.strip() for p in args.providers.split(",") if p.strip()]
    sess = ort.InferenceSession(args.yolo_onnx, providers=providers) 
    in0 = sess.get_inputs()[0]
    in_name = in0.name
    # 입력 shape에서 H,W 추론(대부분 [1,3,H,W])
    _, _, H, W = [int(x) if isinstance(x, (int, np.integer)) else 640 for x in in0.shape]

    paths = list(iter_images(inp))
    if not paths:
        raise SystemExit("입력에서 이미지 파일을 찾지 못했습니다.")

    saved, failed = 0, 0

    for src in tqdm(paths, desc="preprocess_onnx"):
        rel = src.name if inp.is_file() else src.relative_to(inp)
        rel = Path(rel)

        try:
            img = Image.open(src).convert("RGB")
        except Exception:
            failed += 1
            continue

        im0 = np.array(img)  # HWC RGB uint8
        lb, r, (dw, dh) = letterbox(im0, (H, W))
        x = lb.astype(np.float32) / 255.0  # Ultralytics ORT 예제에서 /255 정규화
        x = np.transpose(x, (2,0,1))[None, ...]  # 1,3,H,W

        outputs = sess.run(None, {in_name: x})
        det = decode_ultralytics_output(outputs[0], args.conf, args.iou)

        if det.shape[0] == 0:
            failed += 1
            continue

        # bbox를 letterbox 좌표계 -> 원본 좌표계로 복원
        boxes = det[:, :4].copy()
        boxes[:, [0,2]] -= dw
        boxes[:, [1,3]] -= dh
        boxes /= max(r, 1e-6)

        # margin 적용
        h0, w0 = im0.shape[0], im0.shape[1]
        out_faces = []
        for i in range(boxes.shape[0]):
            x1,y1,x2,y2 = boxes[i]
            bw = x2 - x1
            bh = y2 - y1
            mx = bw * args.margin_ratio
            my = bh * args.margin_ratio
            x1m = int(max(0, x1 - mx))
            y1m = int(max(0, y1 - my))
            x2m = int(min(w0-1, x2 + mx))
            y2m = int(min(h0-1, y2 + my))
            face = img.crop((x1m,y1m,x2m,y2m)).resize((args.face_size, args.face_size))
            out_faces.append((face, float(det[i,4])))

        if not args.keep_all:
            # 1개만 저장(best/ largest)
            if args.pick == "best":
                face = max(out_faces, key=lambda t: t[1])[0]
            else:
                # largest
                areas = []
                for i in range(boxes.shape[0]):
                    x1,y1,x2,y2 = boxes[i]
                    areas.append((i, max(0.0,(x2-x1))*max(0.0,(y2-y1))))
                idx = max(areas, key=lambda t: t[1])[0]
                face = out_faces[idx][0]

            dst = outdir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            face.save(dst)
            saved += 1
        else:
            for i,(face,_) in enumerate(out_faces):
                dst = outdir / rel.parent / f"{rel.stem}_{i}{rel.suffix.lower()}"
                dst.parent.mkdir(parents=True, exist_ok=True)
                face.save(dst)
                saved += 1

    print(f"done: saved={saved}, failed={failed}, out_dir={outdir.resolve()}, providers={providers}")

if __name__ == "__main__":
    main()
