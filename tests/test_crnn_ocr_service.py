"""
Unit and Integration Tests for MediApp CRNN OCR and Clinical Fuzzy Matcher.
Verifies vocabulary tokenization, ONNX preprocessing, fuzzy catalogue linkage (1250+ SKUs),
and end-to-end OCRService entity extraction.
"""
import os
import pytest
import numpy as np
from PIL import Image

from scripts.vocab import CHARACTERS, VOCAB_SIZE, encode_text, decode_tokens
from app.services.clinical_fuzzy_matcher import (
    ClinicalFuzzyMatcher,
    levenshtein_distance,
    similarity_ratio,
    extract_dosage_strength,
)
from app.services.crnn_onnx_predictor import CRNNOnnxPredictor
from app.services.ocr_service import OCRService


def test_vocab_encoding_and_decoding():
    """Verifies alphanumeric vocabulary maps correctly and CTC greedy decoding strips duplicates/blank."""
    text = "Dolo-650"
    encoded = encode_text(text)
    assert len(encoded) == len(text)
    for token in encoded:
        assert 1 <= token < VOCAB_SIZE

    # Decode without duplicates
    decoded = decode_tokens(encoded)
    assert decoded == text

    # Decode with CTC duplicates and blank (0)
    # [blank, D, D, o, blank, l, o, blank] -> "Dolo"
    d_idx = encoded[0]
    o_idx = encoded[1]
    l_idx = encoded[2]
    ctc_stream = [0, d_idx, d_idx, o_idx, 0, l_idx, o_idx, 0]
    assert decode_tokens(ctc_stream) == "Dolo"


def test_levenshtein_and_similarity():
    """Verifies Levenshtein distance and normalized similarity ratio."""
    assert levenshtein_distance("Dolo", "Dolo") == 0
    assert levenshtein_distance("Dolo", "Dlo") == 1
    assert levenshtein_distance("Augmentin", "Augmntn") == 2

    assert similarity_ratio("Dolo", "Dolo") == 1.0
    assert similarity_ratio("Dolo", "Dlo") == 0.75
    assert similarity_ratio("", "") == 1.0


def test_extract_dosage_strength():
    """Verifies dosage token regex."""
    assert extract_dosage_strength("Dolo 650mg") == "650mg"
    assert extract_dosage_strength("Augmentin 625") == "625mg"
    assert extract_dosage_strength("Pantocid 40 mg") == "40mg"
    assert extract_dosage_strength("No Dosage Here") is None


def test_clinical_fuzzy_matcher_exact():
    """Verifies exact matches against the 1,250+ SKU database."""
    res = ClinicalFuzzyMatcher.match_term("Dolo 650mg Tablet")
    assert res is not None
    assert "Dolo" in res["name"]
    assert res["confidence"] >= 0.90
    assert res["stock_units"] >= 0
    assert res["unit_price"] > 0


def test_clinical_fuzzy_matcher_noisy_ligatures():
    """
    Verifies noisy handwritten OCR strings snap cleanly to genuine MediApp SKUs:
    - 'Dl 650' -> Dolo 650mg
    - 'Augmntn' -> Augmentin 625 Duo
    - 'Pantoc 40' -> Pantocid 40mg
    - 'Amlong 5' -> Amlong 5mg
    """
    # 1. 'Dl 650'
    res_dolo = ClinicalFuzzyMatcher.match_term("Dl 650")
    assert res_dolo is not None
    assert "Dolo" in res_dolo["name"]
    assert res_dolo["confidence"] >= 0.70

    # 2. 'Augmntn'
    res_aug = ClinicalFuzzyMatcher.match_term("Augmntn")
    assert res_aug is not None
    assert "Augmentin" in res_aug["name"]

    # 3. 'Pantoc 40'
    res_panto = ClinicalFuzzyMatcher.match_term("Pantoc 40")
    assert res_panto is not None
    assert "Pantocid" in res_panto["name"]

    # 4. 'Amlong 5'
    res_amlong = ClinicalFuzzyMatcher.match_term("Amlong 5")
    assert res_amlong is not None
    assert "Amlong" in res_amlong["name"]


def test_clinical_fuzzy_matcher_multiline():
    """Verifies multiline prescription parsing and deduplication."""
    rx_text = """
    Dr. Sharma Clinic
    Rx:
    Dl 650 1 tab TDS
    Augmntn 625 1 tab BD
    Pantoc 40 1 tab OD
    """
    matches = ClinicalFuzzyMatcher.match_prescription_lines(rx_text)
    assert len(matches) >= 2
    matched_names = [m["name"] for m in matches]
    assert any("Dolo" in n for n in matched_names)
    assert any("Augmentin" in n for n in matched_names)


def test_crnn_onnx_preprocessing():
    """Verifies ONNX image preprocessing dimensions and normalization."""
    predictor = CRNNOnnxPredictor()
    dummy_img = Image.new("RGB", (200, 50), color=(255, 255, 255))
    tensor = predictor.preprocess_image(dummy_img)

    assert tensor.shape == (1, 1, 32, 128)
    assert tensor.dtype == np.float32
    assert -1.01 <= tensor.min() <= 1.01
    assert -1.01 <= tensor.max() <= 1.01


def test_crnn_onnx_real_image_inference():
    """Verifies that the standalone ONNX model executes on real prescription images without PyTorch."""
    predictor = CRNNOnnxPredictor()
    assert predictor.is_available, "CRNN ONNX model should be initialized and ready."

    test_img_path = "data/Doctor’s Handwritten Prescription BD dataset/Testing/testing_words/0.png"
    if os.path.exists(test_img_path):
        text, conf = predictor.predict(test_img_path)
        assert isinstance(text, str)
        assert 0.0 <= conf <= 1.0



def test_ocr_service_parse_prescription_entities():
    """Verifies end-to-end OCR entity extraction with fuzzy catalogue linkage."""
    raw_ocr = """
    Dr. Rajesh Sharma, MBBS, MD
    Patient: Amit Verma
    Date: 27/11/2026
    
    Rx:
    Dolo 650mg - 1 tablet three times daily
    Augmentin 625 - 1 tablet twice daily
    """
    entities = OCRService.parse_prescription_entities(raw_ocr)

    assert entities["doctor_name"] == "Dr. Rajesh Sharma"
    assert entities["patient_name"] == "Amit Verma"
    assert entities["prescription_date"] == "27/11/2026"
    assert len(entities["extracted_medicines"]) >= 2
    assert any("Dolo" in m for m in entities["extracted_medicines"])
    assert any("Augmentin" in m for m in entities["extracted_medicines"])
    assert len(entities["matched_formulations"]) >= 2
    assert entities["confidence"] >= 0.80
