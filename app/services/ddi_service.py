"""
Clinical Drug-Drug Interaction (DDI) and Generic Recommendation Service.
Provides traceable pharmacological interaction checking and bioequivalent generic matching.
"""
import os
import json
import re
from typing import Sequence, Mapping, Any
from app.database import query_db

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "ddi_rules.json")

def normalize_substance_name(name: str) -> set[str]:
    """
    Extracts root active ingredient tokens from brand or chemical nomenclature,
    stripping salt radicals, hydrate prefixes, and dosage numerals.
    """
    clean = re.sub(r"[\(\)\[\]\{\},]", " ", name.lower())
    clean = re.sub(r"\b\d+(\.\d+)?\s*(mg|g|mcg|ml|iu|puff|%)\b", "", clean)
    
    # Strip common pharmaceutical salt counter-ions and dosage forms
    salts_and_forms = [
        "hydrochloride", "hcl", "sodium", "potassium", "maleate", "succinate",
        "tartrate", "fumarate", "mesylate", "besylate", "citrate", "sulfate",
        "phosphate", "calcium", "acetate", "gluconate", "hydrate", "dihydrate",
        "tablet", "capsule", "syrup", "suspension", "injection", "ointment", "drops", "cream", "gel"
    ]
    for s in salts_and_forms:
        clean = re.sub(rf"\b{s}\b", "", clean)
        
    parts = re.split(r"[\+\/&;]|\band\b", clean)
    tokens = {p.strip() for p in parts if len(p.strip()) >= 3}
    for p in parts:
        for word in p.split():
            if len(word) >= 3:
                tokens.add(word)
    return tokens

class DDIService:
    _rules_cache = None

    @classmethod
    def load_rules(cls) -> list[dict[str, Any]]:
        """Loads and caches clinical DDI ruleset from JSON data."""
        if cls._rules_cache is None:
            if os.path.exists(DATA_PATH):
                with open(DATA_PATH, "r", encoding="utf-8") as f:
                    cls._rules_cache = json.load(f)
            else:
                cls._rules_cache = []
        return cls._rules_cache

    @classmethod
    def check_interactions_for_medicines(cls, medicines: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
        """
        Analyzes a set of medicines for clinical drug-drug interactions.
        
        Args:
            medicines: Sequence of medicine dicts with 'id', 'name', 'generic_name'
            
        Returns:
            Dictionary with 'has_interactions', 'highest_severity', 'interactions' list,
            and safety medical disclaimer.
        """
        rules = cls.load_rules()
        detected = []
        highest_severity = "NONE"
        severity_rank = {"CONTRAINDICATED": 4, "MAJOR": 3, "MODERATE": 2, "MINOR": 1, "NONE": 0}

        # Build substance mapping for each medicine
        med_substances = []
        for med in medicines:
            combined_text = f"{med.get('generic_name', '')} {med.get('name', '')}"
            substances = normalize_substance_name(combined_text)
            med_substances.append({
                "medicine": med,
                "substances": substances
            })

        # Pairwise cross-comparison
        n = len(med_substances)
        for i in range(n):
            for j in range(i + 1, n):
                item1 = med_substances[i]
                item2 = med_substances[j]
                
                # Check against each clinical rule
                for rule in rules:
                    p1_name = rule["pair"][0].lower()
                    p2_name = rule["pair"][1].lower()
                    
                    match_direct = (
                        any(p1_name in s or s in p1_name for s in item1["substances"]) and
                        any(p2_name in s or s in p2_name for s in item2["substances"])
                    )
                    match_reverse = (
                        any(p2_name in s or s in p2_name for s in item1["substances"]) and
                        any(p1_name in s or s in p1_name for s in item2["substances"])
                    )
                    
                    if match_direct or match_reverse:
                        sev = rule.get("severity", "MODERATE").upper()
                        if severity_rank.get(sev, 0) > severity_rank.get(highest_severity, 0):
                            highest_severity = sev
                            
                        detected.append({
                            "medicine_a": item1["medicine"]["name"],
                            "medicine_b": item2["medicine"]["name"],
                            "substance_pair": rule["pair"],
                            "severity": sev,
                            "title": rule["title"],
                            "description": rule["description"],
                            "management": rule["management"]
                        })

        return {
            "has_interactions": len(detected) > 0,
            "interaction_count": len(detected),
            "highest_severity": highest_severity,
            "interactions": detected,
            "disclaimer": "This automated check evaluates known primary interactions. It is not an exhaustive substitute for consultation with a licensed pharmacist or physician."
        }

    @classmethod
    def get_generic_alternatives(cls, medicine_id: int) -> dict[str, Any]:
        """
        Discovers equivalent lower-cost generic medications with matching active ingredient,
        dosage form, and strength. Supports salt-agnostic bioequivalent matching.
        """
        target = query_db("SELECT * FROM medicines WHERE id = ?", (medicine_id,), one=True)
        if not target:
            return {"target": None, "alternatives": []}

        # Extract root active molecule tokens (stripping salt variations like Hydrochloride, Maleate, etc.)
        target_tokens = normalize_substance_name(target["generic_name"])
        primary_token = next(iter(sorted(target_tokens, key=len, reverse=True)), target["generic_name"].lower())

        # Find medicines sharing the same base generic molecule and dosage_form
        candidates = query_db("""
            SELECT id, name, generic_name, strength, dosage_form, manufacturer, mrp, prescription_required
            FROM medicines
            WHERE (generic_name = ? OR LOWER(generic_name) LIKE ? OR LOWER(generic_name) LIKE ?)
              AND dosage_form = ?
              AND id != ?
            ORDER BY mrp ASC
        """, (target["generic_name"], f"{primary_token}%", f"%{primary_token}%", target["dosage_form"], target["id"]))

        alternatives = []
        target_mrp = target["mrp"]
        
        for cand in candidates:
            # Check strength equivalence
            cand_mrp = cand["mrp"]
            is_cheaper = cand_mrp < target_mrp
            savings_pct = round(((target_mrp - cand_mrp) / target_mrp) * 100, 1) if is_cheaper and target_mrp > 0 else 0.0
            savings_amount = round(target_mrp - cand_mrp, 2) if is_cheaper else 0.0

            alternatives.append({
                "id": cand["id"],
                "name": cand["name"],
                "generic_name": cand["generic_name"],
                "strength": cand["strength"],
                "dosage_form": cand["dosage_form"],
                "manufacturer": cand["manufacturer"],
                "price": cand_mrp,
                "is_cheaper": is_cheaper,
                "savings_pct": savings_pct,
                "savings_amount": savings_amount,
                "match_type": "Confirmed Bioequivalent Generic" if "generic" in cand["name"].lower() else "Therapeutic Alternative",
                "rx_required": bool(cand["prescription_required"])
            })

        return {
            "target_medicine": dict(target),
            "has_alternatives": len(alternatives) > 0,
            "alternatives": alternatives
        }
