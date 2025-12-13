import argparse
from pathlib import Path
from typing import List, Tuple, Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import onnxruntime as ort  

# -----------------------------
# Utils (no torch)
# -----------------------------
def fixed_image_standardization(img_255_hwc: np.ndarray) -> np.ndarray:
    # facenet-pytorch fixed_image_standardization: (x - 127.5) / 128.0 
    return (img_255_hwc.astype(np.float32) - 127.5) / 128.0


def l2norm(x: np.ndarray, axis: int = -1, eps: float = 1e-12) -> np.ndarray:
    return x / (np.linalg.norm(x, axis=axis, keepdims=True) + eps)


def sigmoid(x: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + np.exp(-x))


def letterbox(im: np.ndarray, new_shape: Tuple[int, int], color=(114, 114, 114)):
    """
    Ultralytics 계열 ONNX 추론에서 흔히 쓰는 letterbox(비율 유지 + 패딩) 전처리.
    (YOLO ONNX 출력 후처리는 모델/옵션에 따라 달라서, 아래 decode에서 몇 가지 케이스를 처리함)
    """
    h0, w0 = im.shape[:2]
    h1, w1 = new_shape

    r = min(h1 / h0, w1 / w0)
    new_unpad = (int(round(w0 * r)), int(round(h0 * r)))  # (w, h)

    im_resized = np.array(Image.fromarray(im).resize(new_unpad, Image.BILINEAR))
    dw = w1 - new_unpad[0]
    dh = h1 - new_unpad[1]
    dw //= 2
    dh //= 2

    out = np.full((h1, w1, 3), color, dtype=np.uint8)
    out[dh:dh + new_unpad[1], dw:dw + new_unpad[0], :] = im_resized
    return out, r, (dw, dh)


def nms_xyxy(boxes: np.ndarray, scores: np.ndarray, iou_thres: float) -> List[int]:
    """간단 NMS."""
    if boxes.size == 0:
        return []
    x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
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


def decode_yolo_output(raw: np.ndarray, conf_thres: float, iou_thres: float) -> np.ndarray:
    """
    YOLO-face ONNX 출력은 export 옵션(nms 포함 여부)과 버전에 따라 달라질 수 있음.
    여기서는 실무에서 자주 만나는 케이스를 처리:

    A) NMS 포함 export: (1, N, 6) = [x1, y1, x2, y2, score, cls]
    B) NMS 미포함 export: (1, C, N) 또는 (1, N, C) 형태에서
       첫 4개 = xywh, 나머지 = class score(들). face-only면 nc=1인 경우가 흔함.

    반환: det (M, 6) with xyxy in model-input scale (letterboxed), score, cls
    """
    out = np.asarray(raw)

    # Case A
    if out.ndim == 3 and out.shape[-1] == 6:
        det = out[0]
        det = det[det[:, 4] >= conf_thres]
        return det.astype(np.float32)

    # Case B (fallback)
    x = out[0]
    if x.ndim != 2:
        return np.zeros((0, 6), dtype=np.float32)

    # (C, N) -> (N, C)
    if x.shape[0] < x.shape[1]:
        x = x.T

    if x.shape[1] < 5:
        return np.zeros((0, 6), dtype=np.float32)

    xywh = x[:, :4]
    cls_scores = x[:, 4:]  # (N, nc)
    scores = cls_scores.max(axis=1)
    cls = cls_scores.argmax(axis=1).astype(np.float32)

    mask = scores >= conf_thres
    xywh = xywh[mask]
    scores = scores[mask]
    cls = cls[mask]
    if xywh.shape[0] == 0:
        return np.zeros((0, 6), dtype=np.float32)

    cx, cy, w, h = xywh[:, 0], xywh[:, 1], xywh[:, 2], xywh[:, 3]
    x1 = cx - w / 2
    y1 = cy - h / 2
    x2 = cx + w / 2
    y2 = cy + h / 2
    boxes = np.stack([x1, y1, x2, y2], axis=1).astype(np.float32)

    keep = nms_xyxy(boxes, scores.astype(np.float32), iou_thres)
    boxes = boxes[keep]
    scores = scores[keep]
    cls = cls[keep]

    det = np.concatenate(
        [boxes, scores[:, None].astype(np.float32), cls[:, None].astype(np.float32)],
        axis=1
    )
    return det.astype(np.float32)


def to_original_coords(det_xyxy: np.ndarray, r: float, dw: int, dh: int) -> np.ndarray:
    """
    letterbox 좌표계 -> 원본 좌표계 복원
    """
    boxes = det_xyxy.copy().astype(np.float32)
    boxes[:, [0, 2]] -= float(dw)
    boxes[:, [1, 3]] -= float(dh)
    boxes /= max(r, 1e-6)
    return boxes


def crop_with_margin(img: Image.Image, xyxy: np.ndarray, margin_ratio: float) -> Image.Image:
    """
    xyxy in original image coords
    """
    x1, y1, x2, y2 = xyxy.tolist()
    w = x2 - x1
    h = y2 - y1
    mx = w * margin_ratio
    my = h * margin_ratio

    W, H = img.size
    x1m = int(max(0, x1 - mx))
    y1m = int(max(0, y1 - my))
    x2m = int(min(W - 1, x2 + mx))
    y2m = int(min(H - 1, y2 + my))
    return img.crop((x1m, y1m, x2m, y2m)).resize((160, 160))


# -----------------------------
# Main
# -----------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--img", type=str, required=True, help="단체 사진 경로")
    ap.add_argument("--yolo_onnx", type=str, required=True, help="yolo_face.onnx")
    ap.add_argument("--embed_onnx", type=str, required=True, help="facenet_embed.onnx")
    ap.add_argument("--verifier_npz", type=str, required=True, help="verifier.npz (centroid/threshold)")
    ap.add_argument("--out_img", type=str, default="group_result.jpg", help="bbox 그려서 저장할 이미지")
    ap.add_argument("--conf", type=float, default=0.35)
    ap.add_argument("--iou", type=float, default=0.5)
    ap.add_argument("--margin_ratio", type=float, default=0.25)
    ap.add_argument("--topk", type=int, default=5, help="점수 상위 K개만 표시")
    ap.add_argument("--min_prob", type=float, default=0.3, help="내 얼굴로 표시할 최소 prob(me)")
    ap.add_argument("--providers", type=str, default="CPUExecutionProvider", help="예: CPUExecutionProvider 또는 CUDAExecutionProvider")
    args = ap.parse_args()

    providers = [p.strip() for p in args.providers.split(",") if p.strip()]

    # Load verifier (centroid/threshold/temperature)
    v = np.load(args.verifier_npz, allow_pickle=True)
    centroid = v["centroid"].astype(np.float32)          # (512,)
    score_th = float(v["threshold"].reshape(-1)[0])      # cosine threshold
    temp = float(v["temperature"].reshape(-1)[0])

    # ORT sessions
    yolo_sess = ort.InferenceSession(args.yolo_onnx, providers=providers)   
    emb_sess  = ort.InferenceSession(args.embed_onnx, providers=providers)

    yolo_in = yolo_sess.get_inputs()[0]
    yolo_in_name = yolo_in.name

    # YOLO input size (대부분 1x3xHxW)
    shape = yolo_in.shape
    H = int(shape[2]) if isinstance(shape[2], (int, np.integer)) else 640
    W = int(shape[3]) if isinstance(shape[3], (int, np.integer)) else 640

    img = Image.open(Path(args.img)).convert("RGB")
    im0 = np.asarray(img)

    # preprocess for YOLO
    lb, r, (dw, dh) = letterbox(im0, (H, W))
    x = (lb.astype(np.float32) / 255.0)  # YOLO 계열에서 흔한 입력 스케일 
    x = np.transpose(x, (2, 0, 1))[None, ...].astype(np.float32)

    # run YOLO
    yolo_out = yolo_sess.run(None, {yolo_in_name: x})[0]
    det = decode_yolo_output(yolo_out, conf_thres=args.conf, iou_thres=args.iou)
    if det.shape[0] == 0:
        raise SystemExit("얼굴을 찾지 못했습니다(검출 결과 0). conf를 낮춰보세요.")

    # map boxes to original image coords
    boxes_orig = to_original_coords(det[:, :4], r=r, dw=dw, dh=dh)

    # embed each face
    emb_in_name = emb_sess.get_inputs()[0].name
    results = []
    for i in range(det.shape[0]):
        face = crop_with_margin(img, boxes_orig[i], margin_ratio=args.margin_ratio)
        arr = np.asarray(face).astype(np.float32)              # HWC [0,255]
        arr = fixed_image_standardization(arr)                 
        inp = np.transpose(arr, (2, 0, 1))[None, ...].astype(np.float32)  # 1,3,160,160

        emb = emb_sess.run(None, {emb_in_name: inp})[0]        # 1,512
        emb = l2norm(emb, axis=1)[0].astype(np.float32)

        score = float(emb @ centroid)                          # cosine similarity
        prob = float(sigmoid((score - score_th) * temp))       # 0~1

        results.append({
            "idx": i,
            "box": boxes_orig[i].astype(float),  # x1,y1,x2,y2
            "det_score": float(det[i, 4]),
            "score": score,
            "prob": prob
        })

    # sort by "prob" desc
    results.sort(key=lambda d: d["prob"], reverse=True)
    show = results[: max(1, args.topk)]

    # draw
    out_img = img.copy()
    draw = ImageDraw.Draw(out_img)
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    found_any = False
    for d in show:
        x1, y1, x2, y2 = d["box"]
        label = f"p={d['prob']:.2f} s={d['score']:.2f}"
        is_me = d["prob"] >= args.min_prob

        # bbox
        draw.rectangle([x1, y1, x2, y2], outline=(0, 255, 0) if is_me else (255, 255, 0), width=3)
        # text background
        tx1, ty1 = x1, max(0, y1 - 12)
        draw.text((tx1, ty1), ("ME " if is_me else "?? ") + label, fill=(0, 0, 0), font=font)
        if is_me:
            found_any = True

    Path(args.out_img).parent.mkdir(parents=True, exist_ok=True)
    out_img.save(args.out_img)

    print(f"[Saved] {args.out_img}")
    print(f"[Verifier] score_th={score_th:.4f}, temp={temp:.2f}, min_prob={args.min_prob:.2f}")
    print(f"[Detections] total={len(results)} shown={len(show)} providers={providers}")

    # print "ME candidates"
    me_cands = [d for d in results if d["prob"] >= args.min_prob]
    if not me_cands:
        print("내 얼굴 후보를 찾지 못했습니다. (min_prob 낮추거나, verifier/모델/전처리를 확인하세요.)")
    else:
        print("내 얼굴 후보(상위):")
        for d in me_cands[:10]:
            x1, y1, x2, y2 = d["box"]
            print(f" - prob={d['prob']:.3f} score={d['score']:.3f} box=[{x1:.1f},{y1:.1f},{x2:.1f},{y2:.1f}]")


if __name__ == "__main__":
    main()
