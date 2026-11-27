"""
Training script for Character-Level CRNN on Doctor's Handwritten Prescription BD Dataset.
Computes CTCLoss and evaluates validation Character Error Rate (CER) and Word Error Rate (WER).
"""
import argparse
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import numpy as np
import pandas as pd
from PIL import Image

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from scripts.vocab import (
    VOCAB_SIZE,
    encode_text,
    decode_tokens,
    save_vocab,
)
from scripts.model_crnn import CRNN


def compute_levenshtein(s1: str, s2: str) -> int:
    """Computes Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return compute_levenshtein(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


class PrescriptionDataset(Dataset):
    def __init__(self, csv_path: str, img_dir: str, target_h: int = 32, target_w: int = 128):
        self.df = pd.read_csv(csv_path)
        self.img_dir = img_dir
        self.target_h = target_h
        self.target_w = target_w

        # Filter out rows whose images do not exist
        valid_rows = []
        for idx, row in self.df.iterrows():
            p = os.path.join(img_dir, str(row["IMAGE"]))
            if os.path.exists(p) and str(row["MEDICINE_NAME"]).strip():
                valid_rows.append(row)
        self.df = pd.DataFrame(valid_rows).reset_index(drop=True)

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_name = str(row["IMAGE"])
        text = str(row["MEDICINE_NAME"]).strip()
        img_path = os.path.join(self.img_dir, img_name)

        # 1. Load Grayscale Image
        img = Image.open(img_path).convert("L")
        w, h = img.size

        # 2. Resize maintaining aspect ratio to height 32, max width 128
        ratio = self.target_h / float(h)
        new_w = min(self.target_w, max(16, int(w * ratio)))
        img = img.resize((new_w, self.target_h), Image.Resampling.BILINEAR)

        # 3. Canvas padding with white background (255)
        canvas = Image.new("L", (self.target_w, self.target_h), color=255)
        canvas.paste(img, (0, 0))

        # 4. Convert to normalized tensor [-1.0, 1.0]
        arr = np.array(canvas, dtype=np.float32)
        arr = (arr / 127.5) - 1.0
        tensor = torch.from_numpy(arr).unsqueeze(0)  # (1, 32, 128)

        # 5. Target sequence tokenization
        encoded = encode_text(text)

        return tensor, encoded, text


def collate_fn(batch):
    images, encoded_list, texts = zip(*batch)
    images = torch.stack(images, 0)  # (B, 1, 32, 128)

    target_lengths = torch.tensor([len(enc) for enc in encoded_list], dtype=torch.long)
    flat_targets = []
    for enc in encoded_list:
        flat_targets.extend(enc)
    targets = torch.tensor(flat_targets, dtype=torch.long)

    return images, targets, target_lengths, texts


def evaluate(model, dataloader, device):
    model.eval()
    total_cer = 0.0
    total_wer = 0.0
    total_chars = 0
    total_words = 0

    with torch.no_grad():
        for images, targets, target_lengths, texts in dataloader:
            images = images.to(device)
            # Output: (32, B, nclass)
            logits = model(images)
            preds = logits.argmax(dim=2)  # (32, B)
            preds = preds.permute(1, 0).cpu().numpy()  # (B, 32)

            for i, pred_tokens in enumerate(preds):
                pred_text = decode_tokens(pred_tokens)
                gt_text = texts[i]

                # Edit distances
                dist = compute_levenshtein(pred_text.lower(), gt_text.lower())
                total_cer += dist
                total_chars += max(1, len(gt_text))

                if pred_text.lower() != gt_text.lower():
                    total_wer += 1.0
                total_words += 1

    cer = (total_cer / total_chars) * 100.0 if total_chars else 0.0
    wer = (total_wer / total_words) * 100.0 if total_words else 0.0
    return cer, wer


def train():
    parser = argparse.ArgumentParser(description="Train CRNN on Prescription Dataset")
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--data-root", type=str, default="data/Doctor’s Handwritten Prescription BD dataset")
    parser.add_argument("--output-model", type=str, default="models/crnn_prescription_ocr.pth")
    args = parser.parse_args()

    # Save canonical vocabulary
    save_vocab("models/crnn_vocab.json")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Executing training on compute device: {device}")

    # Datasets & DataLoaders
    train_csv = os.path.join(args.data_root, "Training", "training_labels.csv")
    train_dir = os.path.join(args.data_root, "Training", "training_words")
    val_csv = os.path.join(args.data_root, "Validation", "validation_labels.csv")
    val_dir = os.path.join(args.data_root, "Validation", "validation_words")

    train_ds = PrescriptionDataset(train_csv, train_dir)
    val_ds = PrescriptionDataset(val_csv, val_dir)

    print(f"Training samples: {len(train_ds)}, Validation samples: {len(val_ds)}, Classes: {VOCAB_SIZE}")

    train_loader = DataLoader(
        train_ds,
        batch_size=args.batch_size,
        shuffle=True,
        collate_fn=collate_fn,
        num_workers=0,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=args.batch_size,
        shuffle=False,
        collate_fn=collate_fn,
        num_workers=0,
    )

    # Initialize CRNN
    model = CRNN(nclass=VOCAB_SIZE).to(device)

    # CTC Loss: zero_infinity handles length edge-cases
    criterion = nn.CTCLoss(blank=0, zero_infinity=True)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=args.epochs, eta_min=1e-5)

    best_wer = float("inf")
    os.makedirs(os.path.dirname(args.output_model), exist_ok=True)

    print("\n--- Starting Character-Level CRNN Training ---")
    start_time = time.time()

    for epoch in range(1, args.epochs + 1):
        model.train()
        running_loss = 0.0
        batch_count = 0

        for images, targets, target_lengths, texts in train_loader:
            images = images.to(device)
            targets = targets.to(device)
            target_lengths = target_lengths.to(device)

            batch_size = images.size(0)
            input_lengths = torch.full(size=(batch_size,), fill_value=32, dtype=torch.long, device=device)

            optimizer.zero_grad()
            logits = model(images)  # (32, B, nclass)
            log_probs = logits.log_softmax(2)

            loss = criterion(log_probs, targets, input_lengths, target_lengths)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=5.0)
            optimizer.step()

            running_loss += loss.item()
            batch_count += 1

        scheduler.step()
        avg_loss = running_loss / max(1, batch_count)

        # Validation
        val_cer, val_wer = evaluate(model, val_loader, device)

        is_best = val_wer < best_wer
        if is_best:
            best_wer = val_wer
            torch.save(
                {
                    "epoch": epoch,
                    "state_dict": model.state_dict(),
                    "val_cer": val_cer,
                    "val_wer": val_wer,
                    "vocab_size": VOCAB_SIZE,
                },
                args.output_model,
            )
            saved_flag = "[BEST SAVED]"
        else:
            saved_flag = ""

        print(
            f"Epoch [{epoch:02d}/{args.epochs:02d}] "
            f"Loss: {avg_loss:.4f} | "
            f"Val CER: {val_cer:5.2f}% | "
            f"Val WER: {val_wer:5.2f}% {saved_flag}"
        )

    total_duration = time.time() - start_time
    print(f"\nTraining completed in {total_duration:.1f}s. Best Validation WER: {best_wer:.2f}%.")
    print(f"Checkpoint saved to {args.output_model}.")


if __name__ == "__main__":
    train()
