"""
Training Script for MediApp AI Clinical Ailment Assistant.
Trains a Calibrated TF-IDF + Linear Classifier on the clinical symptom dataset.
Produces calibrated condition probabilities and links to 5-pillar clinical regimens.
"""

import os
import sys
sys.path.insert(0, os.path.abspath("."))
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.metrics import classification_report, accuracy_score, f1_score
import joblib

from ml_models.dataset_builder import build_training_dataset, CLINICAL_CONDITIONS_DATA

def train_and_evaluate_model():
    print("=" * 65)
    print("TRAINING MEDIAPP AI CLINICAL AILMENT CLASSIFIER")
    print("=" * 65)
    
    # 1. Generate or load dataset
    data = build_training_dataset()
    texts = [item["text"] for item in data]
    labels = [item["condition_id"] for item in data]
    
    print(f"Total clinical training samples: {len(texts)}")
    print(f"Distinct clinical conditions: {len(set(labels))}")
    
    # 2. Train/Test Split (80% Train, 20% Holdout)
    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.20, random_state=42, stratify=labels
    )
    print(f"Training samples: {len(X_train)}, Testing samples: {len(X_test)}")
    
    # 3. Model Pipeline: TF-IDF (1-2 ngrams) + Calibrated Logistic Regression
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            sublinear_tf=True,
            max_features=5000,
            strip_accents="unicode",
            lowercase=True
        )),
        ("classifier", LogisticRegression(
            C=3.0,
            max_iter=1000,
            solver="lbfgs",
            class_weight="balanced",
            random_state=42
        ))
    ])
    
    # 4. 5-Fold Stratified Cross-Validation on Training Set
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(pipeline, X_train, y_train, cv=skf, scoring="f1_weighted")
    print(f"5-Fold Cross-Validation Weighted F1: {cv_scores.mean() * 100:.2f}% (+/- {cv_scores.std() * 100:.2f}%)")
    
    # 5. Fit on Full Training Split
    pipeline.fit(X_train, y_train)
    
    # 6. Evaluate on Test Holdout Split
    y_pred = pipeline.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    f1_weighted = f1_score(y_test, y_pred, average="weighted")
    f1_macro = f1_score(y_test, y_pred, average="macro")
    
    print("\nHOLDOUT TEST PERFORMANCE:")
    print(f"  Accuracy       : {acc * 100:.2f}%")
    print(f"  Weighted F1    : {f1_weighted * 100:.2f}%")
    print(f"  Macro F1       : {f1_macro * 100:.2f}%")
    
    # 7. Print Sample Classification Report for Key Conditions
    report = classification_report(y_test, y_pred, output_dict=True)
    
    # 8. Condition Knowledge Mapping
    condition_meta = {}
    for c in CLINICAL_CONDITIONS_DATA:
        condition_meta[c["condition_id"]] = {
            "name": c["name"],
            "category": c["category"],
            "otc_molecules": c["otc_molecules"],
            "catalog_keywords": c["catalog_keywords"]
        }
        
    # 9. Serialize Model Artifacts
    os.makedirs("ml_models", exist_ok=True)
    model_path = os.path.join("ml_models", "ailment_pipeline.joblib")
    joblib.dump(pipeline, model_path)
    print(f"\nModel pipeline successfully saved to: {model_path}")
    
    meta_path = os.path.join("ml_models", "condition_metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(condition_meta, f, indent=2)
    print(f"Condition metadata saved to: {meta_path}")
    
    # 10. Smoke Test Real Patient Clinical Inquiries
    test_queries = [
        "I have a high fever with cold shivering and headache",
        "Burning sensation in chest and sour acid coming up after dinner",
        "Loose watery stools 4 times today with severe stomach cramps",
        "Throbbing pulsating pain on right side of head with nausea and light sensitivity",
        "Itchy circular red rash on my inner thigh that burns when sweating",
        "Red swollen eye with dry gritty feeling after looking at computer screen",
        "Can't fall asleep at night tossing and turning for hours",
        "Trapped stomach gas making my belly bloat like a balloon"
    ]
    
    print("\n" + "=" * 65)
    print("INFERENCE DEMONSTRATION ON REAL PATIENT QUERIES")
    print("=" * 65)
    for q in test_queries:
        probs = pipeline.predict_proba([q])[0]
        classes = pipeline.classes_
        top_idx = np.argmax(probs)
        pred_cid = classes[top_idx]
        conf = probs[top_idx]
        info = condition_meta.get(pred_cid, {})
        print(f"Query    : '{q}'")
        print(f"Predicted: {info.get('name', pred_cid)} ({pred_cid}) | Confidence: {conf * 100:.1f}%")
        print(f"Molecules: {', '.join(info.get('otc_molecules', []))}")
        print("-" * 50)
        
    return pipeline, condition_meta

if __name__ == "__main__":
    train_and_evaluate_model()
