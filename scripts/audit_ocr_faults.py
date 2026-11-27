"""
Comprehensive Forensic Audit Script for MediApp CRNN OCR and Clinical Fuzzy Matcher.
Benchmarks test accuracy, evaluates error rates, and stresses edge cases to discover faults.
"""
import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import numpy as np
import pandas as pd
from PIL import Image

from scripts.vocab import decode_tokens
from app.services.crnn_onnx_predictor import CRNNOnnxPredictor
from app.services.clinical_fuzzy_matcher import (
    ClinicalFuzzyMatcher,
    levenshtein_distance,
    similarity_ratio,
)
from app.services.ocr_service import OCRService


def run_benchmark():
    print("=================================================================")
    print("PHASE 1: BENCHMARKING CRNN ON TESTING SPLIT (780 IMAGES)")
    print("=================================================================")

    predictor = CRNNOnnxPredictor()
    if not predictor.is_available:
        print("ERROR: CRNN ONNX predictor is not available.")
        return

    test_csv = "data/Doctor’s Handwritten Prescription BD dataset/Testing/testing_labels.csv"
    test_dir = "data/Doctor’s Handwritten Prescription BD dataset/Testing/testing_words"

    if os.path.exists(test_csv) and os.path.exists(test_dir):
        df = pd.read_csv(test_csv)
        total_samples = min(200, len(df))
        print(f"Evaluating {total_samples} test word images...")

        exact_matches = 0
        total_cer_dist = 0
        total_chars = 0
        confidences = []
        failure_examples = []
        short_words_wer = 0
        long_words_wer = 0
        short_words_count = 0
        long_words_count = 0

        for idx in range(total_samples):
            row = df.iloc[idx]
            img_file = str(row["IMAGE"])
            gt_text = str(row["MEDICINE_NAME"]).strip()
            img_path = os.path.join(test_dir, img_file)

            if not os.path.exists(img_path):
                continue

            pred_text, conf = predictor.predict(img_path)
            confidences.append(conf)

            dist = levenshtein_distance(pred_text.lower(), gt_text.lower())
            total_cer_dist += dist
            total_chars += max(1, len(gt_text))

            is_exact = pred_text.lower() == gt_text.lower()
            if is_exact:
                exact_matches += 1
            else:
                if len(failure_examples) < 10:
                    failure_examples.append({
                        "image": img_file,
                        "ground_truth": gt_text,
                        "predicted": pred_text,
                        "confidence": conf,
                        "dist": dist
                    })

            if len(gt_text) <= 5:
                short_words_count += 1
                if not is_exact:
                    short_words_wer += 1
            else:
                long_words_count += 1
                if not is_exact:
                    long_words_wer += 1

        cer = (total_cer_dist / total_chars) * 100.0 if total_chars else 0.0
        wer = ((total_samples - exact_matches) / total_samples) * 100.0 if total_samples else 0.0
        exact_acc = (exact_matches / total_samples) * 100.0 if total_samples else 0.0
        avg_conf = np.mean(confidences) if confidences else 0.0

        print(f"\n--- TESTING SPLIT METRICS ({total_samples} samples) ---")
        print(f"Exact Word Match Accuracy: {exact_acc:.2f}% ({exact_matches}/{total_samples})")
        print(f"Word Error Rate (WER):      {wer:.2f}%")
        print(f"Character Error Rate (CER): {cer:.2f}%")
        print(f"Average Confidence:        {avg_conf:.3f}")
        print(f"Short Words (<= 5 chars) WER: {(short_words_wer/short_words_count)*100 if short_words_count else 0:.1f}%")
        print(f"Long Words (> 5 chars) WER:  {(long_words_wer/long_words_count)*100 if long_words_count else 0:.1f}%")

        print("\nTop Sample Failure Modes:")
        for ex in failure_examples[:8]:
            print(f"  Image: {ex['image']} | GT: '{ex['ground_truth']}' -> Pred: '{ex['predicted']}' (Conf: {ex['confidence']}, Dist: {ex['dist']})")
    else:
        print("Testing directory not found, skipping split evaluation.")

    print("\n=================================================================")
    print("PHASE 2: STRESS-TESTING CRNN ON EXTREME INPUTS & RESOLUTIONS")
    print("=================================================================")

    # 1. Pure Blank Image
    blank_img = Image.new("L", (128, 32), color=255)
    pred_blank, conf_blank = predictor.predict(blank_img)
    print(f"[TEST 1] Pure White Canvas: Pred='{pred_blank}', Conf={conf_blank}")

    # 2. Pure Black Image
    black_img = Image.new("L", (128, 32), color=0)
    pred_black, conf_black = predictor.predict(black_img)
    print(f"[TEST 2] Pure Black Canvas: Pred='{pred_black}', Conf={conf_black}")

    # 3. High Resolution Full Prescription Page (2000x3000)
    full_page = Image.new("L", (2000, 3000), color=255)
    pred_page, conf_page = predictor.predict(full_page)
    print(f"[TEST 3] Full Uncropped Page (2000x3000): Pred='{pred_page}', Conf={conf_page}")

    # 4. Extreme Aspect Ratio: Ultra-wide (1000x32)
    ultra_wide = Image.new("L", (1000, 32), color=255)
    pred_wide, conf_wide = predictor.predict(ultra_wide)
    print(f"[TEST 4] Ultra-wide Aspect Ratio (1000x32): Pred='{pred_wide}', Conf={conf_wide}")

    # 5. Extreme Aspect Ratio: Ultra-tall (32x1000)
    ultra_tall = Image.new("L", (32, 1000), color=255)
    pred_tall, conf_tall = predictor.predict(ultra_tall)
    print(f"[TEST 5] Ultra-tall Aspect Ratio (32x1000): Pred='{pred_tall}', Conf={conf_tall}")

    # 6. Low Contrast Image
    low_contrast = Image.new("L", (128, 32), color=120)
    pred_lc, conf_lc = predictor.predict(low_contrast)
    print(f"[TEST 6] Low Contrast Gray Canvas: Pred='{pred_lc}', Conf={conf_lc}")

    print("\n=================================================================")
    print("PHASE 3: STRESS-TESTING CLINICAL FUZZY MATCHER & CATALOGUE LINKAGE")
    print("=================================================================")

    matcher_queries = [
        # (Query, Expected target, Description)
        ("Par", None, "Overly short ambiguous prefix (Paracetamol, Pantoprazole, Paroxetine)"),
        ("Tab", None, "Pure dosage form word should not match medicine"),
        ("500mg", None, "Pure strength token without medicine name"),
        ("1-0-1", None, "Pure dosing frequency schedule"),
        ("Take after meals", None, "General clinical instruction text"),
        ("Dloo 650", "Dolo", "Transposition in brand name with strength"),
        ("Augemntin", "Augmentin", "Transposition in antibiotic name"),
        ("Azithral 500", "Azee", "Brand synonym / alternative generic equivalent"),
        ("Xyzzynonexistent 100mg", None, "Completely non-existent fictitious drug"),
        ("paracetamol", "Dolo", "Active molecule query (should map to paracetamol brand)"),
        ("amoxicillin clavulanate", "Augmentin", "Multi-word generic molecule query"),
        ("Insulin Glargine", "Lantus", "Cold-chain biologic query"),
    ]

    for q, exp_sub, desc in matcher_queries:
        res = ClinicalFuzzyMatcher.match_term(q)
        matched_name = res["name"] if res else "NO_MATCH"
        conf = res["confidence"] if res else 0.0
        success = False
        if exp_sub is None and res is None:
            success = True
        elif exp_sub is not None and res is not None and exp_sub.lower() in matched_name.lower():
            success = True

        status = "PASS" if success else "FLAGGED"
        print(f"[{status}] Query: '{q}' -> Matched: '{matched_name}' (Conf: {conf}) | Note: {desc}")

    print("\n=================================================================")
    print("PHASE 4: OCRSERVICE FULL DOCUMENT PARSING AUDIT")
    print("=================================================================")

    test_docs = [
        ("Empty Document", ""),
        ("Only Header", "Dr. A. K. Sen, MD\nPatient: John\nDate: 01/01/2026"),
        ("Noisy Transcription", "Rx\nDl 650 1-0-1\nPantoc 40 1-0-0\nAugmntn 625 1-0-1"),
        ("Contradictory Dosage", "Dolo 40mg\nAugmentin 10mg"),  # Dolo is 500/650, Augmentin is 625/375
        ("Unreadable Garbage", "#$%^&*()_+ 12345 !@#$"),
    ]

    for label, doc_text in test_docs:
        parsed = OCRService.parse_prescription_entities(doc_text)
        meds = parsed["extracted_medicines"]
        formulations = parsed.get("matched_formulations", [])
        conf = parsed["confidence"]
        print(f"\nDocument: '{label}'")
        print(f"  Extracted Medicines: {meds}")
        print(f"  Matched Formulations: {len(formulations)}")
        print(f"  Confidence: {conf}")


if __name__ == "__main__":
    run_benchmark()
