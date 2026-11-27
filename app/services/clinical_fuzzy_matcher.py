"""
Clinical Fuzzy Matcher for MediApp Dispensary Catalogue.
Maps noisy OCR transcriptions (e.g. 'Dl 650', 'Augmntn', 'Pantoc 40')
to genuine 1,250+ SKU inventory with strength, generic molecule, and stock linkage.
"""
import re
from typing import Optional, Any
from app.database import get_connection


def levenshtein_distance(s1: str, s2: str) -> int:
    """Computes standard Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def similarity_ratio(s1: str, s2: str) -> float:
    """Computes normalized similarity ratio in [0.0, 1.0]."""
    if not s1 and not s2:
        return 1.0
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    dist = levenshtein_distance(s1, s2)
    return max(0.0, 1.0 - (dist / max_len))


def is_subsequence(sub: str, full: str) -> bool:
    """Checks if characters of sub appear in order in full (e.g. 'dl' in 'dolo', 'augmntn' in 'augmentin')."""
    if not sub:
        return True
    if len(sub) > len(full):
        return False
    it = iter(full)
    return all(c in it for c in sub)


def extract_dosage_strength(text: str) -> Optional[str]:
    """Extracts dosage strength numeric/unit token like '650mg', '500', '40mg'."""
    m = re.search(r"\b(\d{1,4})\s*(mg|ml|mcg|gm|g|iu|units?)?\b", text, re.IGNORECASE)
    if m:
        num = m.group(1)
        unit = (m.group(2) or "mg").lower()
        return f"{num}{unit}"
    return None


class ClinicalFuzzyMatcher:
    """High-performance clinical catalogue matcher with Levenshtein and dosage resolution."""

    _cached_catalogue: Optional[list[dict[str, Any]]] = None

    @classmethod
    def load_catalogue(cls, force_reload: bool = False) -> list[dict[str, Any]]:
        """Loads and pre-indexes all medicines from SQLite database."""
        if cls._cached_catalogue is not None and not force_reload:
            return cls._cached_catalogue

        conn = get_connection()
        try:
            cur = conn.cursor()
            rows = cur.execute("""
                SELECT
                    m.id,
                    m.name,
                    m.generic_name,
                    m.dosage_form,
                    m.strength,
                    m.category,
                    m.manufacturer,
                    m.mrp,
                    m.prescription_required,
                    m.requires_cold_chain,
                    COALESCE(SUM(pi.stock_quantity), 25) AS stock_units,
                    COALESCE(MIN(pi.unit_price), m.mrp) AS unit_price
                FROM medicines m
                LEFT JOIN pharmacy_inventory pi
                    ON m.id = pi.medicine_id AND pi.is_available = 1
                GROUP BY m.id
                ORDER BY m.name ASC
            """).fetchall()

            items = []
            for r in rows:
                d = dict(r)
                name = str(d["name"]).strip()
                # Clean brand base name (e.g. 'Dolo 650mg Tablet' -> 'dolo')
                brand_tokens = re.findall(r"[A-Za-z0-9]+", name)
                brand_base = brand_tokens[0].lower() if brand_tokens else ""

                generic_clean = (str(d.get("generic_name") or "").split("|")[0]).strip()
                gen_tokens = re.findall(r"[A-Za-z0-9]+", generic_clean)
                gen_base = gen_tokens[0].lower() if gen_tokens else ""

                strength_str = str(d.get("strength") or "").strip().lower()
                clean_strength = re.sub(r"\s+", "", strength_str)

                items.append({
                    "id": d["id"],
                    "name": name,
                    "generic_name": generic_clean,
                    "dosage_form": d.get("dosage_form") or "Tablet",
                    "strength": d.get("strength") or "",
                    "clean_strength": clean_strength,
                    "category": d.get("category") or "General",
                    "manufacturer": d.get("manufacturer") or "",
                    "mrp": float(d.get("mrp") or 0.0),
                    "unit_price": float(d.get("unit_price") or d.get("mrp") or 0.0),
                    "stock_units": int(d.get("stock_units") or 0),
                    "prescription_required": int(d.get("prescription_required") or 0),
                    "requires_cold_chain": int(d.get("requires_cold_chain") or 0),
                    "brand_base": brand_base,
                    "gen_base": gen_base,
                    "full_name_lower": name.lower(),
                })

            cls._cached_catalogue = items
            return items
        finally:
            conn.close()

    @classmethod
    def match_term(cls, term: str, threshold: float = 0.68) -> Optional[dict[str, Any]]:
        """
        Matches a single raw token / phrase (e.g. 'Dl 650', 'Augmntn')
        against the genuine catalogue using multi-tier fuzzy matching.
        """
        clean_term = term.strip()
        if len(clean_term) < 2:
            return None

        catalogue = cls.load_catalogue()
        term_lower = clean_term.lower()

        # Extract numeric dosage if present in query
        query_strength = extract_dosage_strength(term_lower)
        query_num = re.search(r"\b\d{2,4}\b", term_lower)
        query_num_str = query_num.group(0) if query_num else None

        # Clean query alphabetic core
        words = re.findall(r"[A-Za-z]+", term_lower)
        if not words:
            return None
        core_query = words[0]

        best_match = None
        best_score = 0.0

        for item in catalogue:
            score = 0.0

            # 1. Exact full name match
            if term_lower == item["full_name_lower"]:
                score = 1.0

            # 2. Exact brand base match (e.g. 'dolo' == item.brand_base)
            elif core_query == item["brand_base"]:
                score = 0.92

            # 3. Prefix match on brand base (e.g. 'pantoc' is prefix of 'pantocid')
            elif item["brand_base"].startswith(core_query) and len(core_query) >= 2:
                cov = len(core_query) / float(len(item["brand_base"]))
                score = 0.86 + 0.06 * cov

            # 4. Brand base prefix of query (e.g. query 'augmentin625' starts with 'augmentin', or 'pantoc' starts with 'pan')
            elif core_query.startswith(item["brand_base"]) and len(item["brand_base"]) >= 2:
                cov = len(item["brand_base"]) / float(len(core_query))
                score = 0.82 + 0.06 * cov

            # 5. Generic molecule core match (e.g. 'paracetamol')
            elif core_query == item["gen_base"] and len(core_query) >= 3:
                score = 0.85
            elif item["gen_base"].startswith(core_query) and len(core_query) >= 3:
                score = 0.82

            # 6. Subsequence ligature matching (e.g. 'dl' in 'dolo', 'augmntn' in 'augmentin')
            elif is_subsequence(core_query, item["brand_base"]) and len(core_query) >= 2:
                score = 0.78
            elif is_subsequence(core_query, item["gen_base"]) and len(core_query) >= 3:
                score = 0.75

            else:
                # 7. Levenshtein edit distance on brand base
                ratio_brand = similarity_ratio(core_query, item["brand_base"])
                # Also check Levenshtein against generic base
                ratio_gen = similarity_ratio(core_query, item["gen_base"]) if len(core_query) >= 3 else 0.0
                score = max(ratio_brand, ratio_gen)

            # Strength reinforcement bonus
            if query_num_str and query_num_str in item["clean_strength"]:
                score = min(1.0, score + 0.12)
            elif query_strength and query_strength in item["clean_strength"]:
                score = min(1.0, score + 0.15)

            if score > best_score:
                best_score = score
                best_match = item

        if best_match and best_score >= threshold:
            return {
                "matched": True,
                "medicine_id": best_match["id"],
                "name": best_match["name"],
                "generic_name": best_match["generic_name"],
                "dosage_form": best_match["dosage_form"],
                "strength": best_match["strength"],
                "category": best_match["category"],
                "mrp": best_match["mrp"],
                "unit_price": best_match["unit_price"],
                "stock_units": best_match["stock_units"],
                "prescription_required": best_match["prescription_required"],
                "requires_cold_chain": best_match["requires_cold_chain"],
                "confidence": round(best_score, 2),
                "original_query": clean_term,
            }

        return None

    @classmethod
    def match_prescription_lines(cls, text: str, threshold: float = 0.68) -> list[dict[str, Any]]:
        """
        Parses OCR multiline text, extracts candidate medical tokens,
        and matches against catalogue without duplicates.
        """
        if not text:
            return []

        results = []
        seen_ids = set()

        # Split text into lines, then filter clinical lines
        lines = [line.strip() for line in re.split(r"[\r\n;,]+", text) if line.strip()]

        for line in lines:
            # Skip lines that are purely doctor/patient headers or dates
            if re.search(r"^(Dr\.|Doctor|Patient|Name|Date|Age|Sex|Hospital|Clinic)\b", line, re.IGNORECASE):
                continue

            match = cls.match_term(line, threshold=threshold)
            if match and match["medicine_id"] not in seen_ids:
                seen_ids.add(match["medicine_id"])
                results.append(match)
                continue

            # If entire line didn't match, attempt per-word matching for lines with multiple words
            words = line.split()
            if len(words) > 1:
                for w in words:
                    if len(w) >= 3 and not re.match(r"^\d+$", w):
                        sub_match = cls.match_term(w, threshold=threshold)
                        if sub_match and sub_match["medicine_id"] not in seen_ids:
                            seen_ids.add(sub_match["medicine_id"])
                            results.append(sub_match)

        return results
