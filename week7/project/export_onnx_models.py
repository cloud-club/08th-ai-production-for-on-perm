# export_onnx_models.py  (옵션: ONNX 생성용, 여기서는 torch/facenet_pytorch 필요)
import argparse
from pathlib import Path
import torch
from facenet_pytorch import InceptionResnetV1

class FaceEmbed(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.backbone = InceptionResnetV1(pretrained="vggface2").eval()

    def forward(self, x):
        return self.backbone(x)  # (B, 512)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--embed_onnx", type=str, default="facenet_embed.onnx")
    ap.add_argument("--opset", type=int, default=13)
    args = ap.parse_args()

    m = FaceEmbed().eval()
    dummy = torch.randn(1, 3, 160, 160)

    out = Path(args.embed_onnx)
    out.parent.mkdir(parents=True, exist_ok=True)

    torch.onnx.export(
        m,
        dummy,
        str(out),
        opset_version=args.opset,
        input_names=["face"],
        output_names=["emb"],
        dynamic_axes={"face": {0: "batch"}, "emb": {0: "batch"}},
    )
    print("Saved embed onnx:", out.resolve())

if __name__ == "__main__":
    main()
