"""
Export trained PyTorch CRNN checkpoint to ONNX format.
Enables lightweight, zero-PyTorch inference in production via onnxruntime.
"""
import argparse
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import torch
import torch.nn as nn

from scripts.vocab import VOCAB_SIZE, save_vocab
from scripts.model_crnn import CRNN


class CRNNInferenceWrapper(nn.Module):
    """Wraps CRNN to output batch-first logits (Batch, Seq_Len, Classes)."""
    def __init__(self, crnn: CRNN):
        super().__init__()
        self.crnn = crnn

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, 1, 32, 128)
        logits = self.crnn(x)           # (32, B, nclass)
        return logits.permute(1, 0, 2)  # (B, 32, nclass)


def export(checkpoint_path: str, onnx_path: str, vocab_path: str = "models/crnn_vocab.json"):
    # Ensure vocab is saved
    save_vocab(vocab_path)

    print(f"Loading checkpoint from: {checkpoint_path}")
    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint not found at {checkpoint_path}")

    device = torch.device("cpu")
    crnn = CRNN(nclass=VOCAB_SIZE)
    checkpoint = torch.load(checkpoint_path, map_location=device)
    if "state_dict" in checkpoint:
        crnn.load_state_dict(checkpoint["state_dict"])
        print(f"Loaded weights from Epoch {checkpoint.get('epoch', '?')}, Val WER: {checkpoint.get('val_wer', '?'):.2f}%")
    else:
        crnn.load_state_dict(checkpoint)

    model = CRNNInferenceWrapper(crnn)
    model.eval()

    dummy_input = torch.randn(1, 1, 32, 128, dtype=torch.float32)

    os.makedirs(os.path.dirname(onnx_path), exist_ok=True)
    print(f"Exporting ONNX model to: {onnx_path}")

    torch.onnx.export(
        model,
        dummy_input,
        onnx_path,
        export_params=True,
        opset_version=14,
        do_constant_folding=True,
        input_names=["image"],
        output_names=["logits"],
        dynamic_axes={
            "image": {0: "batch_size"},
            "logits": {0: "batch_size"},
        },
        dynamo=False,
    )

    print("ONNX export succeeded. Validating with onnxruntime...")
    import onnxruntime as ort

    sess = ort.InferenceSession(onnx_path, providers=["CPUExecutionProvider"])
    inp_name = sess.get_inputs()[0].name
    out_name = sess.get_outputs()[0].name
    test_inp = np.random.randn(1, 1, 32, 128).astype(np.float32)
    res = sess.run([out_name], {inp_name: test_inp})[0]

    print(f"Inference validation passed! Output shape: {res.shape} (Batch, Seq_Len, Classes)")
    print(f"Model saved: {onnx_path} ({os.path.getsize(onnx_path) / (1024 * 1024):.2f} MB)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Export CRNN model to ONNX")
    parser.add_argument("--checkpoint", type=str, default="models/crnn_prescription_ocr.pth")
    parser.add_argument("--output", type=str, default="models/crnn_prescription_ocr.onnx")
    parser.add_argument("--vocab", type=str, default="models/crnn_vocab.json")
    args = parser.parse_args()

    export(args.checkpoint, args.output, args.vocab)
