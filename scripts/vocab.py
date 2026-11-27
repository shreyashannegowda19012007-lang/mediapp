"""
Character vocabulary definition for Prescription CRNN OCR.
Provides bidirectional mapping between characters and indices with CTC blank token at index 0.
"""
import json
import os
import string

# CTC blank token is index 0
BLANK_TOKEN = "[blank]"

# Full clinical alphanumeric character set
CHARACTERS = (
    [" "]
    + list(string.digits)
    + list(string.ascii_uppercase)
    + list(string.ascii_lowercase)
    + ["-", ".", "+", "/", "%", "(", ")", ","]
)

# Build mappings
CHAR_TO_IDX = {BLANK_TOKEN: 0}
for idx, ch in enumerate(CHARACTERS, start=1):
    CHAR_TO_IDX[ch] = idx

IDX_TO_CHAR = {idx: ch for ch, idx in CHAR_TO_IDX.items()}
VOCAB_SIZE = len(CHAR_TO_IDX)


def encode_text(text: str) -> list[int]:
    """Encodes a string into list of token indices."""
    return [CHAR_TO_IDX[c] for c in text if c in CHAR_TO_IDX]


def decode_tokens(tokens: list[int]) -> str:
    """Decodes a list of token indices using standard CTC greedy collapse."""
    chars = []
    prev = 0
    for t in tokens:
        if t != 0 and t != prev:
            chars.append(IDX_TO_CHAR.get(t, ""))
        prev = t
    return "".join(chars).strip()


def save_vocab(path: str = "models/crnn_vocab.json"):
    """Saves vocabulary to JSON for standalone inference runtime."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "blank_token": BLANK_TOKEN,
                "vocab_size": VOCAB_SIZE,
                "char_to_idx": CHAR_TO_IDX,
                "idx_to_char": {str(k): v for k, v in IDX_TO_CHAR.items()},
            },
            f,
            indent=2,
        )


if __name__ == "__main__":
    save_vocab()
    print(f"Vocabulary saved. Total classes (including CTC blank): {VOCAB_SIZE}")
