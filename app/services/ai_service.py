"""
AI Ailment Assistant Service for MediApp.
Provides triage guidance, OTC symptom assistance, emergency red-flag screening,
and medical disclaimers via Gemini API with a deterministic clinical demo fallback.
"""
import re
import requests
from typing import Mapping, Any
from app.config import Config

SYSTEM_PROMPT = """
You are the MediApp AI Clinical Ailment Assistant, a helpful and medically responsible healthcare information guide.
Your clinical principles:
1. EMERGENCY TRIAGE FIRST: If the user describes any red-flag symptoms such as severe crushing chest pain, radiating left arm/jaw pain, acute shortness of breath, sudden weakness/facial drooping/speech slurring (stroke signs), massive bleeding, suicidal ideation, or severe anaphylaxis:
   IMMEDIATELY and PROMINENTLY advise the user to call emergency medical services (112 / 911 / local emergency) or proceed to the nearest emergency room immediately.
2. OTC ONLY: You may suggest well-known, safe Over-The-Counter (OTC) symptomatic relief measures (e.g., Paracetamol for mild fever, ORS for mild dehydration, antacids for minor heartburn, throat lozenges), but you must NEVER prescribe or recommend prescription-only medications (antibiotics, steroids, opioids, psychotropics, cardiac drugs).
3. NON-DIAGNOSTIC: Never present information as a definitive diagnosis. Frame suggestions as possibilities to discuss with a healthcare provider.
4. LIFESTYLE & HYDRATION: Emphasize rest, fluid intake, and general non-pharmacological care.
5. CONCISE & STRUCTURED: Keep your answers clear, empathetic, easy to read for patients, using bullet points for symptoms, home care, OTC options, and when to see a doctor immediately.
"""

# Curated deterministic clinical guidelines for demo mode
CURATED_DEMO_KNOWLEDGE = {
    "headache": {
        "title": "Tension Headache / Mild Headache Guidance",
        "red_flags": "Sudden onset 'thunderclap' headache, stiff neck with high fever, neurological deficits, or visual changes require emergency evaluation.",
        "otc_options": ["Paracetamol 500mg (Crocin/Calpol) after food (do not exceed 4g daily)", "Oral rehydration and rest in a quiet, dark room"],
        "care_tips": "Ensure adequate hydration, limit screen exposure, and practice gentle neck stretching.",
        "when_to_see_doctor": "If the headache worsens progressively, recurs frequently, or does not respond to standard OTC analgesics."
    },
    "fever": {
        "title": "Mild Acute Fever Guidance",
        "red_flags": "Fever exceeding 103°F (39.4°C), difficulty breathing, persistent vomiting, confusion, or neck stiffness require urgent hospital care.",
        "otc_options": ["Paracetamol 500mg or 650mg (Dolo/Crocin) every 6 to 8 hours as needed", "Cold sponging with room-temperature water"],
        "care_tips": "Rest extensively, drink plenty of electrolyte fluids (ORS, coconut water, warm broths), and wear light clothing.",
        "when_to_see_doctor": "If fever persists beyond 72 hours, or if accompanied by chills, rash, or intense body aches."
    },
    "acidity": {
        "title": "Acid Reflux / Heartburn / Indigestion",
        "red_flags": "Chest pressure radiating to arm or jaw, difficulty swallowing, vomiting blood, or black tarry stools require immediate ER attention.",
        "otc_options": ["Antacid gel or chewable tablets (Gelusil / Digene)", "Pantoprazole 40mg (Pan 40) or Omeprazole 20mg once daily 30 minutes before breakfast"],
        "care_tips": "Avoid spicy, greasy, or deep-fried foods. Avoid lying down for at least 2 hours after meals. Elevate head end of bed.",
        "when_to_see_doctor": "If symptoms occur more than twice weekly or interfere with swallowing."
    },
    "cold": {
        "title": "Common Cold & Nasal Congestion",
        "red_flags": "Shortness of breath, wheezing, chest pain, or coughing up yellowish-green blood require clinical diagnosis.",
        "otc_options": ["Saline nasal spray/drops (Otrivin S)", "Steam inhalation 2-3 times daily", "Antihistamine (Cetirizine 10mg or Fexofenadine 120mg) for sneezing and runny nose"],
        "care_tips": "Drink warm liquids (ginger tea, warm water, soups), rest your vocal cords, and get at least 8 hours of sleep.",
        "when_to_see_doctor": "If symptoms fail to improve after 7 to 10 days, or high fever develops."
    },
    "cough": {
        "title": "Acute Cough Guidance",
        "red_flags": "Coughing up blood (hemoptysis), high fever, severe chest tightness, or rapid breathing warrant immediate physician review.",
        "otc_options": ["Warm honey with lemon (for adults and children over 1 year)", "OTC cough lozenges", "Dextromethorphan syrup for dry non-productive cough"],
        "care_tips": "Avoid cold beverages, tobacco smoke, and dusty environments. Keep the room humidified.",
        "when_to_see_doctor": "If cough lasts more than 3 weeks or is accompanied by unexplained weight loss or night sweats."
    }
}

EMERGENCY_KEYWORDS = [
    r"\bchest\s+pain\b", r"\bheart\s+attack\b", r"\bshortness\s+of\s+breath\b",
    r"\bcannot\s+breathe\b", r"\bstroke\b", r"\bfacial\s+droop\b", r"\bslurred\s+speech\b",
    r"\bunconscious\b", r"\bseizure\b", r"\bconvulsion\b", r"\bmassive\s+bleeding\b",
    r"\banaphylaxis\b", r"\bsevere\s+allergic\s+reaction\b", r"\bpoison\b", r"\bsuicid\b"
]

class AIService:
    @classmethod
    def check_emergency_red_flags(cls, query: str) -> str | None:
        """Inspects query for life-threatening acute red flags."""
        for pattern in EMERGENCY_KEYWORDS:
            if re.search(pattern, query, re.IGNORECASE):
                return (
                    "CRITICAL ALERT: Your query mentions potential life-threatening emergency symptoms. "
                    "Please do not wait for online information. Immediately call your national emergency services "
                    "(112 / 911 / 108) or go to the nearest Hospital Emergency Room right away!"
                )
        return None

    @classmethod
    def query_assistant(cls, user_query: str) -> dict[str, Any]:
        """
        Processes an ailment consultation query.
        Dispatches to real Gemini API when configured, or reliable clinical demo fallback.
        """
        if not user_query or not user_query.strip():
            raise ValueError("Query text cannot be empty.")

        # 1. Screen for medical emergency flags
        emergency_warning = cls.check_emergency_red_flags(user_query)
        if emergency_warning:
            return {
                "source": "emergency_triage_engine",
                "is_emergency": True,
                "response": emergency_warning,
                "emergency_message": emergency_warning,
                "disclaimer": "Automated emergency red-flag alert. Immediate medical intervention required."
            }

        api_key = Config.GEMINI_API_KEY
        # 2. Real Gemini Integration
        if not Config.is_demo():
            if not api_key:
                raise ValueError("APP_MODE is set to 'real' but GEMINI_API_KEY is not configured on the server.")
            try:
                endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": f"{SYSTEM_PROMPT}\n\nPatient Query: {user_query}"}
                        ]
                    }],
                    "generationConfig": {
                        "temperature": 0.2,
                        "maxOutputTokens": 800
                    }
                }
                res = requests.post(endpoint, json=payload, timeout=12.0)
                if res.status_code == 200:
                    data = res.json()
                    candidates = data.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        text = candidates[0]["content"]["parts"][0]["text"]
                        return {
                            "source": "gemini_api",
                            "is_demo": False,
                            "is_emergency": False,
                            "response": text,
                            "disclaimer": "AI-generated medical summary from Google Gemini. For informational purposes only. Consult a physician for diagnosis."
                        }
                    raise RuntimeError("Gemini API returned response without candidate content.")
                else:
                    raise RuntimeError(f"Gemini API returned HTTP {res.status_code}: {res.text}")
            except Exception as e:
                # In real mode, do not silently fallback to demo mode
                raise RuntimeError(f"External AI Provider failure: {str(e)}")

        # 3. Labelled Demo Fallback
        matched_topic = None
        q_lower = user_query.lower()
        for key in CURATED_DEMO_KNOWLEDGE:
            if key in q_lower:
                matched_topic = key
                break

        if matched_topic:
            info = CURATED_DEMO_KNOWLEDGE[matched_topic]
            formatted_response = (
                f"### [DEMO MODE: Clinical Guidance] {info['title']}\n\n"
                f"**Self-Care & Non-Pharmacological Measures:**\n{info['care_tips']}\n\n"
                f"**Over-The-Counter (OTC) Symptom Relief Options:**\n" +
                "\n".join([f"- {opt}" for opt in info["otc_options"]]) +
                f"\n\n**Red Flags & Urgent Warnings:**\n{info['red_flags']}\n\n"
                f"**When to Consult a Physician:**\n{info['when_to_see_doctor']}"
            )
        else:
            formatted_response = (
                "### [DEMO MODE: General Health Assistant]\n\n"
                "Thank you for reaching out to the MediApp Health Assistant. For mild everyday symptoms:\n"
                "- Stay well hydrated with clean water and oral electrolyte fluids.\n"
                "- Get adequate physical rest.\n"
                "- Monitor your temperature and symptoms closely.\n"
                "- For specific OTC medicines, browse our catalogue by therapeutic category.\n\n"
                "**Important:** If you experience severe pain, difficulty breathing, persistent vomiting, or symptoms lasting more than 48-72 hours, please visit a licensed medical practitioner for proper clinical evaluation."
            )

        return {
            "source": "demo_clinical_knowledgebase",
            "is_demo": True,
            "is_emergency": False,
            "response": formatted_response,
            "disclaimer": "[DEMO MODE] This is a demonstrative medical response. In real mode with GEMINI_API_KEY configured, live Gemini models provide real-time responses."
        }
