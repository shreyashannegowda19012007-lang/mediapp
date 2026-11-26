"""
Inference Engine for MediApp AI Clinical Ailment Assistant.
Provides high-speed probabilistic prediction of patient conditions from symptom text,
extracts targeted OTC active molecules, and links to live database inventory.
"""

import os
import json
from typing import Dict, Any, List, Optional
import joblib

class AilmentPredictor:
    _instance: Optional["AilmentPredictor"] = None
    
    def __init__(self):
        self.model = None
        self.metadata = {}
        self._load_artifacts()
        
    @classmethod
    def get_instance(cls) -> "AilmentPredictor":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
        
    def _load_artifacts(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "ailment_pipeline.joblib")
        meta_path = os.path.join(base_dir, "condition_metadata.json")
        
        if os.path.exists(model_path):
            try:
                self.model = joblib.load(model_path)
            except Exception as e:
                print(f"[AilmentPredictor] Warning: Failed to load model pipeline: {e}")
                self.model = None
                
        if os.path.exists(meta_path):
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
            except Exception as e:
                print(f"[AilmentPredictor] Warning: Failed to load metadata: {e}")
                self.metadata = {}

    def predict(self, query: str) -> Dict[str, Any]:
        """
        Predicts the clinical condition from patient symptom text.
        Returns top prediction, calibrated confidence, top 3 differentials, and active molecules.
        """
        if not query or not query.strip():
            return {
                "condition_id": "general_wellness",
                "condition_name": "General Health & Symptom Review",
                "confidence": 0.0,
                "category": "General",
                "otc_molecules": ["Multivitamins", "Hydration Fluids"],
                "catalog_keywords": ["Zincovit", "Electral", "Paracetamol"],
                "differentials": []
            }
            
        if not self.model:
            # Fallback if model not loaded
            return {
                "condition_id": "general_wellness",
                "condition_name": "General Health & Symptom Review",
                "confidence": 0.50,
                "category": "General",
                "otc_molecules": ["Paracetamol", "ORS"],
                "catalog_keywords": ["Paracetamol", "Electral"],
                "differentials": []
            }
            
        probs = self.model.predict_proba([query])[0]
        classes = self.model.classes_
        
        # Sort by highest probability
        sorted_indices = probs.argsort()[::-1]
        top_idx = sorted_indices[0]
        top_cid = classes[top_idx]
        top_prob = float(probs[top_idx])
        
        top_info = self.metadata.get(top_cid, {})
        
        differentials = []
        for idx in sorted_indices[1:4]:
            cid = classes[idx]
            info = self.metadata.get(cid, {})
            differentials.append({
                "condition_id": cid,
                "name": info.get("name", cid),
                "probability": round(float(probs[idx]), 3)
            })
            
        return {
            "condition_id": top_cid,
            "condition_name": top_info.get("name", top_cid),
            "category": top_info.get("category", "General"),
            "confidence": round(top_prob, 3),
            "otc_molecules": top_info.get("otc_molecules", []),
            "catalog_keywords": top_info.get("catalog_keywords", []),
            "differentials": differentials
        }
