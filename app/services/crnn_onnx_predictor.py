"""
CRNN ONNX Predictor for Prescription Handwriting Recognition.
Provides lightweight, zero-PyTorch inference in production using onnxruntime.
Preprocesses medical handwriting images, runs bidirectional CTC inference,
and decodes character sequences.
"""
import io
import json
import os
from pathlib import Path
from typing import Union, Optional
import numpy as np
from PIL import Image


class CRNNOnnxPredictor:
    """Inference engine for CRNN ONNX handwriting recognition model."""

    def __init__(
        self,
        model_path: Optional[str] = None,
        vocab_path: Optional[str] = None,
    ):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.model_path = model_path or os.path.join(base_dir, "models", "crnn_prescription_ocr.onnx")
        self.vocab_path = vocab_path or os.path.join(base_dir, "models", "crnn_vocab.json")

        self.session = None
        self.idx_to_char = {}
        self.char_to_idx = {}
        self.input_name = "image"
        self.output_name = "logits"

        self._load_vocab()
        self._init_session()

    def _load_vocab(self):
        """Loads canonical CTC vocabulary from json."""
        if os.path.exists(self.vocab_path):
            try:
                with open(self.vocab_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.idx_to_char = {int(k): v for k, v in data.get("idx_to_char", {}).items()}
                self.char_to_idx = data.get("char_to_idx", {})
            except Exception:
                pass

        if not self.idx_to_char:
            # Fallback canonical medical OCR alphabet
            chars = list("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-/.% ")
            self.idx_to_char = {0: "<blank>"}
            for i, c in enumerate(chars, start=1):
                self.idx_to_char[i] = c

    def _init_session(self):
        """Initializes ONNX Runtime session if model file exists."""
        if os.path.exists(self.model_path):
            try:
                import onnxruntime as ort
                # Suppress verbose ONNX logs
                opts = ort.SessionOptions()
                opts.log_severity_level = 3
                self.session = ort.InferenceSession(
                    self.model_path,
                    sess_options=opts,
                    providers=["CPUExecutionProvider"],
                )
                self.input_name = self.session.get_inputs()[0].name
                self.output_name = self.session.get_outputs()[0].name
            except Exception:
                self.session = None

    @property
    def is_available(self) -> bool:
        """Returns True if the ONNX session is ready for inference."""
        return self.session is not None

    def preprocess_image(
        self,
        image_input: Union[str, Path, bytes, Image.Image],
        target_h: int = 32,
        target_w: int = 128,
    ) -> np.ndarray:
        """
        Converts image to grayscale, resizes preserving aspect ratio,
        pads canvas to target_w, and normalizes pixels to [-1.0, 1.0].
        Returns shape (1, 1, target_h, target_w) in float32.
        """
        if isinstance(image_input, (str, Path)):
            img = Image.open(str(image_input)).convert("L")
        elif isinstance(image_input, bytes):
            img = Image.open(io.BytesIO(image_input)).convert("L")
        elif isinstance(image_input, Image.Image):
            img = image_input.convert("L")
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")

        w, h = img.size
        ratio = target_h / float(max(1, h))
        new_w = min(target_w, max(16, int(w * ratio)))
        img_resized = img.resize((new_w, target_h), Image.Resampling.BILINEAR)

        # Pad on white background (255)
        canvas = Image.new("L", (target_w, target_h), color=255)
        canvas.paste(img_resized, (0, 0))

        arr = np.array(canvas, dtype=np.float32)

        arr = (arr / 127.5) - 1.0
        # Add channel and batch dimensions -> (1, 1, 32, 128)
        tensor = np.expand_dims(np.expand_dims(arr, axis=0), axis=0)
        return tensor

    def decode_greedy_ctc(self, logits: np.ndarray) -> tuple[str, float]:
        """
        Greedy CTC decoding over logits of shape (Seq_Len=32, Classes) or (1, 32, Classes).
        Collapses consecutive duplicates, strips blank (0), and averages confidence.
        """
        if logits.ndim == 3:
            logits = logits[0]  # (32, Classes)

        # Softmax for probabilities
        exp_logits = np.exp(logits - np.max(logits, axis=-1, keepdims=True))
        probs = exp_logits / np.sum(exp_logits, axis=-1, keepdims=True)

        token_indices = np.argmax(probs, axis=-1)  # (32,)
        token_probs = np.max(probs, axis=-1)      # (32,)

        chars = []
        confidences = []
        prev_idx = -1

        for idx, p in zip(token_indices, token_probs):
            if idx != prev_idx:
                if idx != 0:  # 0 is blank
                    c = self.idx_to_char.get(int(idx), "")
                    if c and c != "<blank>":
                        chars.append(c)
                        confidences.append(float(p))
            prev_idx = idx

        transcription = "".join(chars).strip()
        avg_conf = float(np.mean(confidences)) if confidences else 0.0
        return transcription, round(avg_conf, 3)

    def predict(
        self,
        image_input: Union[str, Path, bytes, Image.Image],
    ) -> tuple[str, float]:
        """
        Executes end-to-end CRNN inference on an image input.
        Returns (predicted_text, confidence_score).
        """
        if not self.is_available:
            self._init_session()
            if not self.is_available:
                return "", 0.0

        tensor = self.preprocess_image(image_input)
        if tensor is None:
            return "", 0.0
        # Contrast guard: if image has virtually zero variance (blank white or solid black), reject early
        if float(np.std(tensor)) < 0.05:
            return "", 0.0
        res = self.session.run([self.output_name], {self.input_name: tensor})[0]
        # res shape: (1, 32, Classes)
        return self.decode_greedy_ctc(res[0])

    def segment_text_lines(
        self,
        image_input: Union[str, Path, bytes, Image.Image]
    ) -> list[Image.Image]:
        """
        Segments a multi-line document into individual horizontal text-line crops
        using morphological dilation and contour detection.
        """
        if isinstance(image_input, (str, Path)):
            img = Image.open(str(image_input)).convert("L")
        elif isinstance(image_input, bytes):
            img = Image.open(io.BytesIO(image_input)).convert("L")
        elif isinstance(image_input, Image.Image):
            img = image_input.convert("L")
        else:
            return []

        w, h = img.size
        # If image is already a single cropped word or line (short height or wide aspect), don't segment
        if h <= 48 or (w / max(1, h) >= 3.0 and h <= 80):
            return [img]

        try:
            import cv2
            arr = np.array(img, dtype=np.uint8)
            # Otsu threshold on inverted image (text white, bg black)
            _, thresh = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            # Horizontal rectangular kernel to bridge characters in each line
            kernel_w = max(15, int(w * 0.05))
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_w, 3))
            dilated = cv2.dilate(thresh, kernel, iterations=2)
            contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            boxes = [cv2.boundingRect(c) for c in contours]
            # Filter noise contours: require width > 30px, height > 10px, and height < 70% of page
            valid_boxes = [b for b in boxes if b[2] > 30 and 10 < b[3] < int(h * 0.70)]
            valid_boxes.sort(key=lambda b: b[1])  # Top to bottom

            crops = []
            for x, y, bw, bh in valid_boxes:
                pad_y = int(bh * 0.15)
                pad_x = int(bw * 0.04)
                crop = img.crop((
                    max(0, x - pad_x),
                    max(0, y - pad_y),
                    min(w, x + bw + pad_x),
                    min(h, y + bh + pad_y)
                ))
                crops.append(crop)
            return crops if crops else [img]
        except Exception:
            return [img]

    def predict_document(
        self,
        image_input: Union[str, Path, bytes, Image.Image],
    ) -> tuple[str, float]:
        """
        Predicts multi-line documents by segmenting text lines, predicting each line crop
        with CRNN ONNX, and concatenating results with line breaks.
        Returns (full_transcription, average_confidence).
        """
        line_crops = self.segment_text_lines(image_input)
        if not line_crops:
            return self.predict(image_input)

        lines = []
        confidences = []

        for crop in line_crops:
            text, conf = self.predict(crop)
            if text and len(text) >= 2 and conf > 0.20:
                lines.append(text)
                confidences.append(conf)

        if not lines:
            # Fallback to direct prediction
            return self.predict(image_input)

        full_text = "\n".join(lines)
        avg_conf = float(np.mean(confidences)) if confidences else 0.0
        return full_text, round(avg_conf, 3)
