"""
Convolutional Recurrent Neural Network (CRNN) Architecture for Medical Handwriting OCR.
Combines CNN spatial feature extraction, Bidirectional GRU sequence modeling,
and Connectionist Temporal Classification (CTC) character projection.
"""
import torch
import torch.nn as nn
from scripts.vocab import VOCAB_SIZE


class CRNN(nn.Module):
    def __init__(self, img_height: int = 32, nc: int = 1, nclass: int = VOCAB_SIZE, nh: int = 256):
        super().__init__()
        assert img_height == 32, "CRNN architecture expects input height of 32 pixels."

        # 1. Convolutional Backbone (VGG-style)
        # Input: (B, 1, 32, 128)
        self.cnn = nn.Sequential(
            # Block 1
            nn.Conv2d(nc, 64, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # -> (64, 16, 64)
            # Block 2
            nn.Conv2d(64, 128, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=2, stride=2),  # -> (128, 8, 32)
            # Block 3
            nn.Conv2d(128, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1)),  # -> (256, 4, 32)
            # Block 4
            nn.Conv2d(256, 512, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(2, 1), stride=(2, 1)),  # -> (512, 2, 32)
            # Block 5 (Final height collapse)
            nn.Conv2d(512, 512, kernel_size=(2, 1), stride=(1, 1), padding=0),  # -> (512, 1, 32)
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
        )

        # 2. Sequence Modeling (Bidirectional GRU)
        self.rnn = nn.GRU(
            input_size=512,
            hidden_size=nh,
            num_layers=2,
            bidirectional=True,
            batch_first=False,
            dropout=0.2,
        )

        # 3. CTC Projection Head
        self.fc = nn.Linear(nh * 2, nclass)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: (B, 1, 32, 128)
        conv = self.cnn(x)  # (B, 512, 1, 32)
        b, c, h, w = conv.size()
        assert h == 1, f"Height must be 1 after CNN, got {h}"

        conv = conv.squeeze(2)          # (B, 512, 32)
        conv = conv.permute(2, 0, 1)    # (32, B, 512) -> (T, B, C) for RNN

        recurrent, _ = self.rnn(conv)   # (32, B, 2 * nh) = (32, B, 512)
        T, b, f = recurrent.size()
        logits = self.fc(recurrent.view(T * b, f))  # (T * b, nclass)
        logits = logits.view(T, b, -1)              # (32, B, nclass)

        return logits
