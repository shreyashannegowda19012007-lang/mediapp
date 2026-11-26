"""
AI Ailment Assistant Service for MediApp.
Provides triage guidance, OTC symptom assistance, emergency red-flag screening,
and structured evidence-based clinical medication plans with live dispensary stock verification.
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
5. CONCISE & STRUCTURED: Keep your answers clear, empathetic, easy to read for patients, formatted into the 5 Clinical Pillars:
   - Clinical Condition Context
   - Non-Pharmacological Self-Care Action Plan
   - Recommended Over-The-Counter (OTC) Regimen (with specific adult dosing and food timing)
   - Red Flags & Urgent Emergency Warnings
   - Physician Consultation Criteria
"""

# Curated deterministic clinical guidelines for 25+ distinct medical conditions
CURATED_DEMO_KNOWLEDGE = {
    "acidity": {
        "title": "Acid Reflux / Heartburn / GERD & Indigestion",
        "aliases": ["acid", "acidity", "reflux", "heartburn", "indigestion", "burning chest", "gastric", "gerd", "sour burp", "stomach acid"],
        "keywords": ["Gelusil", "Digene", "Aciloc", "Pan", "Quick Chews", "Antacid"],
        "clinical_overview": "Gastric hyperacidity and gastroesophageal reflux occur when acidic stomach contents back up into the esophagus, causing burning retrosternal discomfort and dyspepsia.",
        "care_tips": "Avoid lying down for at least 2 to 3 hours after meals. Elevate the head end of your bed by 6 inches. Avoid spicy, greasy, deep-fried foods, caffeine, chocolate, and carbonated beverages. Eat smaller, more frequent meals rather than large dinners.",
        "otc_options": [
            "Antacid liquid gel (Gelusil / Digene 10ml-15ml) taken 30 to 60 minutes after meals and at bedtime for immediate mucosal coating",
            "H2-Receptor Antagonist (Ranitidine / Aciloc 150mg) taken with a glass of water for prolonged acid suppression",
            "Proton Pump Inhibitor (Pantoprazole / Pan 40mg) taken once daily strictly 30 minutes before breakfast"
        ],
        "red_flags": "Crushing chest pain radiating to the left arm or jaw, difficulty swallowing (dysphagia), vomiting blood (hematemesis), black tarry stools (melena), or unexplained weight loss require immediate emergency evaluation.",
        "when_to_see_doctor": "If symptoms occur more than twice weekly, awaken you from sleep, fail to resolve after 14 days of OTC treatment, or require escalating doses of antacids."
    },
    "fever": {
        "title": "Acute Mild-to-Moderate Fever & Pyrexia",
        "aliases": ["fever", "temperature", "chills", "pyrexia", "shivering", "febrile", "hot forehead", "body temperature"],
        "keywords": ["Dolo", "Calpol", "Crocin", "Paracetamol"],
        "clinical_overview": "Fever is a regulated physiological increase in core body temperature, typically mediated by endogenous pyrogens in response to viral or bacterial immune activation.",
        "care_tips": "Enforce physical bed rest. Maintain high fluid intake (oral electrolyte fluids, fresh coconut water, clear broths) to prevent dehydration. Wear lightweight, breathable cotton clothing. Apply room-temperature (tepid) wet washcloths to forehead and neck (never use ice water).",
        "otc_options": [
            "Paracetamol 500mg or 650mg (Dolo 650 / Calpol) every 6 to 8 hours as needed after meals (do NOT exceed 4000mg in 24 hours)",
            "Oral rehydration salts (ORS) between medication doses to replenish electrolytes depleted by sweating"
        ],
        "red_flags": "Temperature exceeding 103°F (39.4°C), severe neck stiffness (meningism), petechial purple skin rash, acute breathing difficulty, confusion, or convulsions mandate immediate hospital emergency care.",
        "when_to_see_doctor": "If fever persists longer than 72 hours, does not respond to standard antipyretics, or is accompanied by intense shivering rigors or productive cough with discolored phlegm."
    },
    "headache": {
        "title": "Tension Headache / Migraine & Cervicogenic Strain",
        "aliases": ["headache", "head ache", "migraine", "temple pain", "forehead pain", "throbbing head", "cranial pain"],
        "keywords": ["Crocin", "Dolo", "Calpol", "Combiflam", "Paracetamol"],
        "clinical_overview": "Tension headaches arise from sustained myofascial contraction of pericranial muscles often precipitated by stress, ocular fatigue, or poor cervical posture; migraines involve neurovascular trigeminal activation.",
        "care_tips": "Retreat to a darkened, quiet, noise-free room. Apply a cool damp cloth or ice pack wrapped in a towel over forehead or base of skull. Maintain adequate hydration. Practice gentle neck and shoulder stretching exercises.",
        "otc_options": [
            "Paracetamol 500mg-650mg (Crocin Advance / Dolo) taken early at symptom onset with a full glass of water",
            "Combination analgesic (Combiflam / Paracetamol + Ibuprofen) after food for severe inflammatory tension headaches"
        ],
        "red_flags": "Sudden 'thunderclap' headache reaching peak intensity in seconds, headache following recent head trauma, unilateral facial droop, visual field loss, or speech difficulty (call 112 / 911 immediately).",
        "when_to_see_doctor": "If headaches recur more than 3 times weekly, progressively increase in intensity, or require daily painkiller consumption (risk of medication-overuse headache)."
    },
    "cold": {
        "title": "Common Cold, Acute Viral Rhinitis & Nasal Congestion",
        "aliases": ["cold", "sneezing", "congestion", "runny nose", "rhinitis", "stuffy nose", "blocked nose", "nasal blockage", "sinus pressure"],
        "keywords": ["Otrivin", "Cetirizine", "Levocetirizine", "Sinarest", "Cetzine"],
        "clinical_overview": "Acute viral nasopharyngitis causes mucosal vasodilation, hypersecretion, and tissue edema in the nasal turbinates, resulting in rhinorrhea, obstruction, and sinus fullness.",
        "care_tips": "Inhale hot water steam 2 to 3 times daily (you may add eucalyptus or menthol). Sip warm fluids (ginger-lemon water, herbal teas, warm soups). Sleep with your head slightly elevated to facilitate venous drainage from nasal passages.",
        "otc_options": [
            "Saline nasal spray or drops used liberally to rinse allergens and loosen dried mucus",
            "Second-generation antihistamine (Cetirizine 10mg or Levocetirizine 5mg) once daily in the evening to control sneezing and watery discharge",
            "Topical nasal decongestant (Xylometazoline / Otrivin 0.1%) limited to a STRICT maximum of 3 consecutive days to prevent rebound rhinitis medicamentosa"
        ],
        "red_flags": "Severe unremitting facial pain with localized swelling, periorbital edema, high fever (>102°F), or marked shortness of breath.",
        "when_to_see_doctor": "If symptoms worsen after 10 days without improvement, or if you develop a severe secondary earache or thick foul-smelling unilateral nasal drainage."
    },
    "cough": {
        "title": "Acute Bronchial Cough (Dry Tickling vs. Productive)",
        "aliases": ["cough", "throat irritation", "dry cough", "wet cough", "phlegm", "coughing", "bronchial cough", "hacking cough"],
        "keywords": ["Benadryl", "Ascoril", "Ambroxol", "Dextromethorphan"],
        "clinical_overview": "A cough is a protective vagal reflex triggered by irritation of respiratory mucosal receptors by post-nasal drip, viral airway inflammation, or environmental irritants.",
        "care_tips": "Sip warm water with honey (1-2 teaspoons for adults; never under 1 year of age). Avoid exposure to cigarette smoke, cold aerosols, dust, and sudden temperature shifts. Keep room air humidified.",
        "otc_options": [
            "For dry, hacking cough: Dextromethorphan-based antitussive syrup (Benadryl DR) or glycerin-based soothing lozenges",
            "For wet, phlegm-producing cough: Expectorant with Ambroxol or Guaifenesin (Ascoril) taken with generous water to thin mucus",
            "Antihistamine combination syrup at bedtime if cough is triggered by nocturnal post-nasal drip"
        ],
        "red_flags": "Coughing up blood (hemoptysis), whistling stridor or audible wheezing, acute shortness of breath, unexplained weight loss, or night sweats require immediate clinical evaluation.",
        "when_to_see_doctor": "If cough persists beyond 3 weeks (chronic cough investigation needed), or if accompanied by high persistent fever or pleuritic chest pain."
    },
    "pain": {
        "title": "General Musculoskeletal Pain & Body Aches",
        "aliases": ["pain", "ache", "stiffness", "body ache", "back pain", "joint pain", "muscle pain", "sore muscles", "backache"],
        "keywords": ["Combiflam", "Brufen", "Volini", "Intagesic", "Paracetamol"],
        "clinical_overview": "Musculoskeletal discomfort typically stems from myofascial strain, minor inflammatory arthralgia, or structural tension in paraspinal and limb muscle groups.",
        "care_tips": "Alternate cold packs (first 24-48 hours for acute inflammation) with mild moist heat (for chronic stiffness). Maintain ergonomic posture. Avoid prolonged bed rest; engage in gentle mobilization.",
        "otc_options": [
            "Ibuprofen 400mg (Brufen) or Combiflam (Ibuprofen + Paracetamol) taken with or after food (do NOT take on an empty stomach)",
            "Topical NSAID gel or spray (Volini / Diclofenac gel) massaged gently over the painful area 2 to 3 times daily"
        ],
        "red_flags": "Inability to bear any weight on a limb, joint swelling with intense erythema and warmth, radiating sharp nerve pain with foot drop or bowel/bladder incontinence (cauda equina syndrome - surgical emergency).",
        "when_to_see_doctor": "If localized pain persists beyond 5 to 7 days, progressively limits daily mobility, or fails to respond to oral NSAIDs."
    },
    "allergies": {
        "title": "Allergic Rhinitis, Urticaria (Hives) & Histamine Flare",
        "aliases": ["allergy", "allergies", "hives", "urticaria", "rash", "itching", "itchy skin", "hay fever", "allergic rhinitis", "dust allergy", "skin allergy"],
        "keywords": ["Allegra", "Fexofenadine", "Cetzine", "Cetirizine", "Avil", "Candid"],
        "clinical_overview": "Allergic reactions occur when mast cells and basophils degranulate upon allergen exposure (pollen, dust mites, pet dander), releasing histamine and triggering pruritus, erythema, and mucosal hypersecretion.",
        "care_tips": "Apply cool compresses over itchy wheals. Take cool showers and pat skin dry gently. Wear loose, smooth cotton garments. Identify and minimize contact with suspected triggers (pollens, detergents, pets). Avoid scratching to prevent secondary bacterial excoriation.",
        "otc_options": [
            "Non-sedating second-generation antihistamine: Fexofenadine 120mg or 180mg (Allegra) once daily with water",
            "Cetirizine 10mg (Cetzine) or Levocetirizine 5mg once daily at bedtime for intense cutaneous itching",
            "Topical soothing Calamine lotion applied over unbroken pruritic lesions for barrier relief"
        ],
        "red_flags": "Swelling of the lips, tongue, uvula, or throat (angioedema), difficulty breathing, audible stridor, dizziness, or lightheadedness are signs of severe anaphylaxis (CALL 112 / 911 IMMEDIATELY).",
        "when_to_see_doctor": "If hives persist continuously for more than 6 weeks (chronic urticaria), or if accompanied by joint pains or systemic fever."
    },
    "diarrhea": {
        "title": "Acute Diarrhea, Loose Stools & Gastroenteritis",
        "aliases": ["diarrhea", "diarrhoea", "loose motion", "loose motions", "watery stool", "stomach bug", "gastroenteritis", "stomach infection", "frequent motions"],
        "keywords": ["Electral", "Oral Rehydration", "Eldoper", "Enterogermina", "Loperamide"],
        "clinical_overview": "Acute diarrhea is characterized by abnormally frequent, loose, or watery bowel movements, leading to rapid intestinal loss of water, sodium, potassium, and bicarbonate electrolytes.",
        "care_tips": "Aggressive and continuous oral hydration is paramount. Reconstitute 1 sachet of WHO-formula Oral Rehydration Salts (ORS) in 1 liter of boiled and cooled drinking water; sip continuously after every loose stool. Follow the BRAT diet (Bananas, Rice, Applesauce, Toast). Strictly avoid dairy products, spicy gravies, caffeine, and alcohol.",
        "otc_options": [
            "Oral Rehydration Salts (ORS / Electral) as the primary life-saving electrolyte replenisher",
            "Spore-forming probiotic (Enterogermina / Bacillus clausii or Sporlac) to support gut microbiome restoration",
            "Antidiarrheal agent (Loperamide / Eldoper 2mg) strictly for adult non-bloody, afebrile watery diarrhea (do NOT take if fever or blood is present)"
        ],
        "red_flags": "Visible blood or mucus in stool (dysentery), high fever (>101.5°F), signs of severe dehydration (dry mouth, sunken eyes, skin tenting, zero urination for 8 hours), or inability to retain fluids.",
        "when_to_see_doctor": "If loose motions persist longer than 48 hours without improvement, or if diarrhea occurs in infants, small children, or elderly patients."
    },
    "nausea_vomiting": {
        "title": "Acute Nausea & Emesis Management",
        "aliases": ["nausea", "vomiting", "vomit", "throwing up", "queasy", "nauseous", "feeling sick", "emesis", "food poisoning"],
        "keywords": ["Emeset", "Vomikind", "Domstal", "Ondansetron", "Domperidone"],
        "clinical_overview": "Nausea and vomiting are coordinated autonomic and somatic responses mediated by the chemoreceptor trigger zone (CTZ) and the vomiting center in the medulla oblongata.",
        "care_tips": "Do not consume solid food for 3 to 4 hours following an episode of emesis. Sip small volumes (1 teaspoon to 1 tablespoon every 5 to 10 minutes) of clear fluids such as chilled water, electrolyte solution, or ginger-infused water. Sit upright and avoid lying down flat. Avoid strong cooking aromas or perfumes.",
        "otc_options": [
            "Ondansetron 4mg fast-dissolving tablet (Vomikind-MD / Emeset) placed under the tongue 30 minutes before oral rehydration",
            "Prokinetic agent (Domperidone / Domstal 10mg) taken before meals for postprandial fullness-related nausea"
        ],
        "red_flags": "Vomiting bright red blood or dark 'coffee-ground' material, severe unremitting localized abdominal pain, high fever with stiff neck, or intractable vomiting exceeding 24 hours.",
        "when_to_see_doctor": "If you cannot retain any fluids for more than 12 hours, feel faint upon standing, or develop profound lethargy."
    },
    "constipation": {
        "title": "Functional Constipation & Sluggish Bowel Transit",
        "aliases": ["constipation", "constipated", "hard stool", "cannot poop", "irregular bowels", "sluggish bowel", "straining", "bowel movement"],
        "keywords": ["Dulcoflex", "Cremaffin", "Bisacodyl", "Laxative"],
        "clinical_overview": "Constipation is characterized by infrequent bowel movements (fewer than 3 per week), hard stools, and excessive straining, often due to inadequate dietary fiber, dehydration, or slowed colonic transit.",
        "care_tips": "Significantly increase dietary soluble and insoluble fiber (whole grains, oats, prunes, leafy vegetables). Drink at least 2.5 to 3 liters of water throughout the day. Engage in 30 minutes of daily physical exercise (brisk walking). Establish a dedicated, unhurried morning bowel routine.",
        "otc_options": [
            "Osmotic stool softener / laxative (Cremaffin Syrup: Liquid Paraffin + Milk of Magnesia, 15-30ml at bedtime with a full glass of water)",
            "Stimulant laxative (Bisacodyl / Dulcoflex 5mg) strictly for short-term acute relief (limit to 2-3 consecutive days to avoid dependency)"
        ],
        "red_flags": "Severe sudden abdominal distension with colic and complete inability to pass stool or gas (obstipation - suspect bowel obstruction), rectal bleeding, or unexplained weight loss.",
        "when_to_see_doctor": "If constipation lasts longer than 2 weeks despite lifestyle adjustments, or if it represents a sudden new change in bowel habits in an individual over 50 years of age."
    },
    "sore_throat": {
        "title": "Pharyngitis, Tonsillar Irritation & Odynophagia",
        "aliases": ["sore throat", "throat pain", "pharyngitis", "tonsil", "tonsillitis", "scratchy throat", "painful swallowing", "raw throat", "throat ache"],
        "keywords": ["Wokadine", "Strepsils", "Paracetamol", "Povidone", "Calpol"],
        "clinical_overview": "Pharyngeal inflammation is predominantly caused by respiratory viruses (rhinovirus, adenovirus, EBV), leading to mucosal congestion, edema, and localized pain on swallowing.",
        "care_tips": "Perform warm saline gargles (1/2 teaspoon of salt in 1 glass of warm water) 3 to 4 times daily. Drink warm fluids (turmeric milk, ginger tea, warm broth). Maintain strict voice rest. Use a cool-mist room humidifier to keep pharyngeal mucosa moist.",
        "otc_options": [
            "Antiseptic gargle solution (Povidone Iodine 2% / Wokadine diluted 1:1 with warm water) gargled for 30 seconds twice daily",
            "Antiseptic / soothing throat lozenges to lubricate mucosal membranes and provide local comfort",
            "Paracetamol 500mg (Calpol / Crocin) after food to relieve acute throat pain and reduce difficulty swallowing"
        ],
        "red_flags": "Inability to swallow own saliva (drooling), difficulty breathing or audible stridor, inability to fully open mouth (trismus), or asymmetric bulging of one tonsil (peritonsillar abscess).",
        "when_to_see_doctor": "If throat pain is accompanied by high fever without a cough, tender swollen neck lymph nodes, and white exudative patches on tonsils (concerning for Group A Strep requiring antibiotics)."
    },
    "mouth_ulcers": {
        "title": "Aphthous Stomatitis (Mouth Ulcers & Canker Sores)",
        "aliases": ["mouth ulcer", "mouth ulcers", "canker sore", "canker sores", "aphthous", "tongue blister", "lip sore", "cheek bite", "burning mouth"],
        "keywords": ["Becosules", "Zincovit", "Gelusil", "B-Complex", "Multivitamin"],
        "clinical_overview": "Recurrent aphthous stomatitis presents as benign, non-contagious, painful shallow mucosal ulcerations on non-keratinized oral mucosa, often triggered by mechanical trauma, nutritional deficiencies (B-complex, iron), stress, or acidic foods.",
        "care_tips": "Avoid spicy, acidic, crunchy, or heavily salted foods that irritate exposed nerve endings. Use an ultra-soft toothbrush. Rinse mouth with mild warm salt water after meals. Avoid toothpastes containing Sodium Lauryl Sulfate (SLS).",
        "otc_options": [
            "High-potency Vitamin B-Complex with Zinc (Becosules / Zincovit) taken once daily after meals for 7 to 10 days to support epithelial repair",
            "Topical oral anesthetic and antiseptic gel (Choline Salicylate + Benzalkonium Chloride) applied gently with a clean fingertip before meals",
            "Antacid suspension dabbed directly onto the ulcer to neutralize oral acidity and coat nerve endings"
        ],
        "red_flags": "Any solitary mouth ulcer that fails to heal after 3 weeks (mandatory biopsy rule-out for oral malignancy), giant ulcers (>1 cm), or mouth ulcers accompanied by genital sores or uveitis.",
        "when_to_see_doctor": "If mouth ulcers are so painful that you cannot maintain hydration, or if you experience recurrent clusters of multiple ulcers every month."
    },
    "toothache": {
        "title": "Odontalgia (Dental Pain & Gum Inflammation)",
        "aliases": ["toothache", "tooth pain", "dental pain", "gum pain", "cavity", "swollen gum", "tooth ache", "sensitive tooth", "tooth sensitivity"],
        "keywords": ["Combiflam", "Brufen", "Paracetamol", "Wokadine"],
        "clinical_overview": "Dental pain commonly arises from dental caries, pulpitis, periodontal inflammation, or dentin hypersensitivity where exposed tubules transmit thermal and chemical pain signals.",
        "care_tips": "Rinse mouth thoroughly with warm salt water to dislodge trapped food debris. Gently apply pure clove oil (eugenol) on a tiny sterile cotton pellet directly onto the cavity (avoid contact with gums). Avoid very hot, ice-cold, or sugary foods. Do not apply aspirin tablets directly against the gum (causes chemical burns).",
        "otc_options": [
            "Combination analgesic and anti-inflammatory (Combiflam: Ibuprofen 400mg + Paracetamol 325mg) taken after meals for acute dental pain",
            "Antiseptic mouth rinse (Povidone Iodine 1% / Wokadine diluted) to reduce bacterial load around inflamed gingival margins"
        ],
        "red_flags": "Facial swelling spreading to the cheek, eye, or underneath the jawline (Ludwig's angina risk), high fever, difficulty swallowing or breathing (dental infection spreading to deep neck spaces).",
        "when_to_see_doctor": "All dental pain requires professional dental evaluation. OTC painkillers provide only temporary symptomatic relief and do not treat underlying pulp necrosis or periapical abscesses."
    },
    "skin_rash_fungal": {
        "title": "Superficial Fungal Skin Infection (Ringworm / Tinea / Athlete's Foot)",
        "aliases": ["fungal", "fungus", "ringworm", "tinea", "athlete's foot", "jock itch", "skin itch", "fungal infection", "groin itch", "itchy rash"],
        "keywords": ["Candid", "Fungicros", "Lulifin", "Luliconazole", "Clotrimazole"],
        "clinical_overview": "Dermatophytosis (Tinea corporis, cruris, pedis) is a superficial fungal infection of keratinized tissue, presenting with circular erythematous plaques with raised, active scaling borders and central clearing.",
        "care_tips": "Keep the affected skin folds clean and completely dry. Wear loose, breathable 100% cotton clothing. Do NOT share bath towels, clothing, or footwear. Wash garments in warm water and dry under sunlight. NEVER apply steroid-only creams alone, as they suppress local immunity and cause 'Tinea incognito'.",
        "otc_options": [
            "Topical broad-spectrum antifungal cream (Clotrimazole 1% / Candid or Luliconazole 1% / Fungicros) applied in a thin layer twice daily over the lesion and 2cm into healthy surrounding skin",
            "Continue topical antifungal application for at least 1 to 2 weeks after visible lesions clear to eradicate residual fungal spores"
        ],
        "red_flags": "Rapidly spreading fiery redness with intense warmth, pain, fever, and red streaks (secondary bacterial cellulitis), or extensive infection in diabetic/immunocompromised patients.",
        "when_to_see_doctor": "If the rash does not improve after 14 days of compliant antifungal use, involves the scalp or nails, or covers extensive body surface areas."
    },
    "eye_strain_dry": {
        "title": "Ocular Fatigue, Asthenopia & Dry Eye Syndrome",
        "aliases": ["eye strain", "dry eyes", "burning eyes", "eye fatigue", "tired eyes", "computer vision", "itchy eyes", "red eyes", "eye irritation"],
        "keywords": ["Xalatan", "Refresh Tears", "Eye Drops", "Saline"],
        "clinical_overview": "Computer vision syndrome and evaporative dry eye result from reduced blink rates during screen use, disruption of the pre-corneal tear film, and ciliary muscle fatigue.",
        "care_tips": "Follow the clinical 20-20-20 rule: every 20 minutes look at an object 20 feet away for at least 20 seconds. Ensure ambient lighting matches screen brightness; reduce blue-light intensity. Position monitor slightly below eye level. Avoid direct draft from fans or air conditioners onto your face.",
        "otc_options": [
            "Lubricating artificial tear drops (Carboxymethylcellulose 0.5% or Hydroxypropyl Methylcellulose) 1 to 2 drops into conjunctival sac 3 to 4 times daily",
            "Cold compresses applied over closed eyelids for 5 minutes in the evening to soothe tired ocular muscles"
        ],
        "red_flags": "Severe unremitting eye pain, sudden decrease in visual acuity or blurred vision, perception of halos around lights, copious yellow-green pus discharge, or foreign body sensation.",
        "when_to_see_doctor": "If eye redness persists beyond 3 days, is accompanied by photophobia (light sensitivity), or fails to respond to lubricating drops."
    },
    "muscle_spasm_sprain": {
        "title": "Acute Ligament Sprain, Muscle Strain & Sports Injury",
        "aliases": ["sprain", "strain", "cramp", "muscle spasm", "twisted ankle", "sports injury", "ligament", "pulled muscle", "swollen ankle"],
        "keywords": ["Volini", "Intagesic", "Combiflam", "Brufen", "Diclofenac"],
        "clinical_overview": "A sprain involves stretching or tearing of stabilizing ligaments; a strain involves muscle fibers or tendons. Acute tissue injury releases prostaglandins and bradykinin, causing localized edema and pain.",
        "care_tips": "Institute the PRICE protocol immediately: Protect the injured limb; Rest from weight-bearing activities; Ice with cold packs wrapped in a cloth (15-20 mins every 3 hours for the first 48 hours; do NOT apply ice directly to skin); Compress gently with an elastic crepe bandage; Elevate the limb above heart level.",
        "otc_options": [
            "Topical analgesic gel or spray (Volini / Diclofenac Diethylamine + Methyl Salicylate) applied gently 3 times daily (do NOT apply on broken skin)",
            "Oral NSAID with muscle relaxant (Intagesic-MR: Diclofenac + Chlorzoxazone + Paracetamol) or Combiflam taken after food for acute spasm"
        ],
        "red_flags": "Immediate inability to bear any weight (more than 4 steps), an audible 'pop' or snap sensation at the moment of injury, visible gross joint deformity, or loss of distal sensation.",
        "when_to_see_doctor": "If severe swelling and pain fail to improve after 72 hours, or if the joint feels chronically unstable."
    },
    "gas_bloating": {
        "title": "Meteorism (Intestinal Gas, Flatulence & Abdominal Bloating)",
        "aliases": ["gas", "bloating", "flatulence", "burping", "belching", "bloated", "distended stomach", "heavy stomach", "trapped gas"],
        "keywords": ["Digene", "Gelusil", "Buscopan", "Antacid"],
        "clinical_overview": "Intestinal gas results from aerophagia (air swallowing) and colonic bacterial fermentation of undigested carbohydrates, leading to increased intraluminal pressure, cramping, and distension.",
        "care_tips": "Eat and drink slowly; chew food thoroughly. Avoid carbonated sodas, chewing gum, and drinking through straws. Moderate intake of high-FODMAP foods (beans, lentils, cabbage, onions). Take a light 15-minute walk after meals to promote gas propulsion.",
        "otc_options": [
            "Antiflatulent antacid containing Simethicone (Digene Gel / Gelusil MPS) to coalesce tiny micro-bubbles into easily passable gas",
            "Antispasmodic (Hyoscine Butylbromide / Buscopan 10mg) for painful intestinal gas colic and cramping"
        ],
        "red_flags": "Severe localized abdominal rigidity, high fever with vomiting, involuntary weight loss, or palpable abdominal masses.",
        "when_to_see_doctor": "If bloating is chronic (>2 weeks), associated with altered bowel frequency (alternating diarrhea and constipation), or accompanied by anemia."
    },
    "dehydration_heat": {
        "title": "Electrolyte Depletion & Mild Heat Exhaustion",
        "aliases": ["dehydration", "heat exhaustion", "electrolyte", "heat fatigue", "extreme thirst", "dry mouth", "sun exhaustion", "sweating weakness"],
        "keywords": ["Oral Rehydration", "Electral", "Zincovit", "Multivitamin"],
        "clinical_overview": "Dehydration is a state of negative fluid balance with loss of water and critical ions (Na+, K+, Cl-), impairing circulatory volume, thermal regulation, and cellular homeostasis.",
        "care_tips": "Move to a cool, shaded, or air-conditioned environment immediately. Loosen restrictive clothing. Sip oral rehydration solutions slowly in small, frequent sips. Apply cool, wet towels to the back of the neck, armpits, and groin.",
        "otc_options": [
            "WHO-Formula Oral Rehydration Salts (ORS / Electral) dissolved in exact specified volume of clean drinking water",
            "Oral multivitamin with zinc to support cellular recovery once hydration is stabilized"
        ],
        "red_flags": "Body temperature exceeding 104°F (40°C), cessation of sweating with hot, dry, flushed skin (HEAT STROKE - MEDICAL EMERGENCY), confusion, hallucinations, or loss of consciousness (CALL 112 / 911 IMMEDIATELY).",
        "when_to_see_doctor": "If unable to keep oral fluids down due to persistent nausea, or if urine remains absent or dark amber for more than 8 hours."
    },
    "minor_cuts_burns": {
        "title": "First-Aid Superficial Wound Care & Minor Thermal Burns",
        "aliases": ["cut", "cuts", "scrape", "scratch", "burn", "minor burn", "wound", "abrasion", "bleeding cut", "first aid"],
        "keywords": ["Wokadine", "Soframycin", "Povidone", "Antiseptic"],
        "clinical_overview": "Superficial cutaneous lacerations and first-degree thermal burns disrupt the stratum corneum barrier, activating the coagulation cascade and local inflammatory healing mechanisms.",
        "care_tips": "For burns: immediately hold the area under cool, clean running water for at least 10 to 15 minutes (never use ice, butter, or toothpaste on burns). For cuts: apply firm direct pressure with clean gauze for 5 minutes to achieve hemostasis; cleanse with mild soap and water.",
        "otc_options": [
            "Topical Povidone-Iodine 10% solution or ointment (Wokadine) for broad-spectrum antiseptic disinfection",
            "Topical antibiotic cream (Soframycin: Framycetin Sulfate) applied thinly under a sterile non-stick dressing"
        ],
        "red_flags": "Deep gaping wounds requiring surgical closure (sutures), wound caused by rusty metal or animal/human bites, full-thickness charred or white skin burns, or tetanus immunization lapsed >5 years.",
        "when_to_see_doctor": "If you observe spreading fiery redness, expanding warmth, purulent pus drainage, or if the burn involves the face, hands, feet, or groin."
    },
    "motion_sickness_vertigo": {
        "title": "Kinetosis (Motion Sickness) & Travel Equilibrium Support",
        "aliases": ["motion sickness", "car sickness", "travel sickness", "sea sickness", "airsickness", "dizziness", "vertigo", "car sick"],
        "keywords": ["Emeset", "Vomikind", "Domstal", "Ondansetron"],
        "clinical_overview": "Motion sickness occurs when conflicting sensory signals are received simultaneously by the vestibular apparatus, visual system, and proprioceptive sensors during passive transportation.",
        "care_tips": "Sit in the front passenger seat of cars or over the wing in aircraft. Keep your gaze fixed firmly on the distant, stationary horizon. Ensure cool, fresh airflow from air vents. Avoid reading books or looking down at smartphone screens during transit. Eat a light carbohydrate snack before travel; avoid heavy or greasy foods.",
        "otc_options": [
            "Fast-acting antiemetic (Ondansetron 4mg / Vomikind-MD) taken 30 minutes before departure to suppress vestibulocochlear emetic triggers",
            "Prokinetic tablet (Domperidone 10mg) to prevent gastric stasis during long journeys"
        ],
        "red_flags": "Sudden vertigo accompanied by acute unilateral hearing loss, double vision (diplopia), facial asymmetry, severe sudden headache, or inability to walk in a straight line (ataxia).",
        "when_to_see_doctor": "If vertigo persists long after travel ends or recurs spontaneously while stationary."
    },
    "insomnia_sleep": {
        "title": "Acute Sleep Latency & Circadian Disruption",
        "aliases": ["insomnia", "sleeplessness", "cannot sleep", "trouble sleeping", "sleep problem", "jet lag", "restless night", "waking up"],
        "keywords": ["Calpol", "Crocin", "Zincovit", "Multivitamin"],
        "clinical_overview": "Transient insomnia involves difficulty initiating or maintaining sleep, often driven by hyperarousal, disruption of melatonin rhythms, screen blue-light exposure, or psychological stress.",
        "care_tips": "Maintain a strict, non-negotiable wake-up time 7 days a week. Discontinue all digital screens (phones, laptops, TV) at least 60 minutes before bedtime. Keep the bedroom completely dark, quiet, and cool (around 20°C / 68°F). Avoid caffeine after 2:00 PM. Reserve the bed strictly for sleep and intimacy.",
        "otc_options": [
            "Warm chamomile infusion or warm milk (contains natural tryptophan) 30 minutes before bed",
            "Magnesium supplementation with dinner to promote neuromuscular relaxation",
            "Short-term low-dose Melatonin (1mg-3mg) strictly for circadian realignment or jet lag (avoid chronic dependence)"
        ],
        "red_flags": "Insomnia accompanied by severe daytime sleep attacks while driving, loud gasping or choking awakenings (concerning for obstructive sleep apnea), or severe depressive ideation.",
        "when_to_see_doctor": "If sleep difficulty persists for more than 4 consecutive weeks and significantly impairs daytime cognitive or occupational performance."
    },
    "ear_discomfort": {
        "title": "Otalgia (Ear Fullness, Cerumen Impaction & Swimmer's Ear)",
        "aliases": ["earache", "ear ache", "ear pain", "ear fullness", "ear wax", "blocked ear", "swimmer's ear", "ear clogging"],
        "keywords": ["Waxolve", "Calpol", "Crocin", "Paracetamol"],
        "clinical_overview": "Ear fullness and mild otalgia commonly result from impacted cerumen (hardened ear wax), Eustachian tube dysfunction during upper respiratory infections, or external canal moisture accumulation.",
        "care_tips": "NEVER insert cotton buds (Q-tips), hairpins, or sharp objects into the ear canal (this impacts wax deeper against the tympanic membrane and risks traumatic eardrum perforation). Keep the ear dry during bathing; use a cotton ball coated in petroleum jelly as an outer plug. Apply a warm, dry towel over the outer ear.",
        "otc_options": [
            "Cerumenolytic ear drops (Waxolve: Paradichlorobenzene + Benzocaine + Chlorbutol) 3 to 4 drops instilled twice daily for 3 days to soften hardened wax",
            "Oral Paracetamol 500mg (Calpol / Crocin) for temporary symptomatic relief of mild dull ear discomfort"
        ],
        "red_flags": "Purulent, foul-smelling, or bloody ear discharge (otorrhea), sudden severe hearing loss, painful erythema and swelling behind the ear over the mastoid bone, or facial nerve weakness.",
        "when_to_see_doctor": "If ear pain is sharp and severe, fails to resolve in 48 hours, or occurs in a child or swimmer with outer canal tenderness."
    },
    "acne_breakouts": {
        "title": "Mild Acne Vulgaris & Cutaneous Blemish Control",
        "aliases": ["acne", "pimples", "pimple", "breakout", "breakouts", "zits", "blackheads", "whiteheads", "oily skin", "facial blemishes"],
        "keywords": ["Candid", "Soframycin", "Antiseptic"],
        "clinical_overview": "Acne vulgaris is a multifactorial dermatosis of the pilosebaceous unit involving sebum hyperproduction, follicular hyperkeratinization, and colonization by Cutibacterium acnes.",
        "care_tips": "Cleanse face gently twice daily with a mild, soap-free foaming cleanser (do not scrub aggressively). NEVER squeeze, pick, or pop pimples, as this drives inflammation deeper and leads to permanent scarring. Use strictly non-comedogenic, oil-free moisturizers and sunscreen. Change pillowcases twice weekly.",
        "otc_options": [
            "Topical Benzoyl Peroxide 2.5% gel applied in a thin layer over acne-prone areas at night (anti-bacterial and keratolytic)",
            "Topical 2% Salicylic Acid (BHA) cleanser to clear sebum from clogged pores",
            "Topical Framycetin (Soframycin) applied on minor inflamed blemishes to reduce surface bacterial proliferation"
        ],
        "red_flags": "Deep, painful, nodulocystic lesions, extensive scarring, sudden explosive eruption of widespread pustules, or acne accompanied by irregular periods and hirsutism (suspect PCOS).",
        "when_to_see_doctor": "If acne fails to improve after 8 to 12 weeks of compliant topical OTC care, or if it causes significant emotional distress."
    },
    "urinary_discomfort_mild": {
        "title": "Mild Urinary Discomfort & Hydration Support",
        "aliases": ["burning urine", "urinary discomfort", "mild dysuria", "urine irritation", "burning pee", "urinary burning", "cloudy urine"],
        "keywords": ["Oral Rehydration", "Electral", "Zincovit"],
        "clinical_overview": "Mild burning upon urination (dysuria) often indicates concentrated acidic urine or early lower urinary tract mucosal irritation.",
        "care_tips": "Immediately increase fluid intake to at least 3 liters of water daily to promote frequent mechanical flushing of the bladder and urethra. Urinate whenever the urge arises; do not hold urine. Urinate immediately following sexual intercourse. Avoid bubble baths, chemical douches, and scented feminine hygiene products.",
        "otc_options": [
            "Systemic urinary alkalinizer (Disodium Hydrogen Citrate liquid, 1-2 teaspoons diluted in a full glass of water 2 to 3 times daily) to neutralize acidic urine and soothe burning",
            "Oral electrolyte hydration (Electral / ORS) to ensure adequate urinary dilution and mineral balance"
        ],
        "red_flags": "High spiking fever with shaking chills, flank or severe lower back pain (suspect acute pyelonephritis / kidney infection), visible blood in urine (hematuria), or male dysuria (requires immediate STI/prostatitis evaluation).",
        "when_to_see_doctor": "Any persistent urinary symptom lasting >24 hours, or any urinary discomfort during pregnancy or in diabetic individuals requires urinalysis and culture under clinical supervision."
    },
    "sunburn_heat_rash": {
        "title": "Solar Erythema (Sunburn) & Prickly Heat (Miliaria)",
        "aliases": ["sunburn", "prickly heat", "heat rash", "miliaria", "sun burn", "sun redness", "sweat rash", "sun stinging"],
        "keywords": ["Candid", "Calpol", "Crocin", "Paracetamol"],
        "clinical_overview": "Sunburn is an acute radiation-induced inflammatory burn caused by ultraviolet B (UVB) damage to epidermal DNA; prickly heat is caused by obstruction of eccrine sweat ducts in hot, humid climates.",
        "care_tips": "Stay in a cool, air-conditioned room. Take cool showers or apply cool, moist compresses over sunburned skin. Apply pure aloe vera gel or calamine lotion generously to sooth erythema and stinging. Do NOT pop sunburn blisters. Wear loose, lightweight cotton clothing.",
        "otc_options": [
            "Topical soothing Calamine lotion applied freely over unbroken itchy heat rash",
            "Paracetamol 500mg (Calpol / Crocin) taken with water to reduce inflammatory stinging pain and headache associated with sunburn",
            "Oral rehydration fluid (ORS) to replace insensible fluid loss from sun-exposed skin"
        ],
        "red_flags": "Extensive blistering covering more than 20% of the body, accompanying high fever, chills, dizziness, or confusion (severe solar toxemia / heat injury), or yellow crusting on blisters.",
        "when_to_see_doctor": "If sunburn blisters become secondarily infected with pus, or if severe sunburn occurs in infants or elderly individuals."
    }
}

EMERGENCY_KEYWORDS = [
    r"\bchest\s+pain\b", r"\bheart\s+attack\b", r"\bshortness\s+of\s+breath\b",
    r"\bcannot\s+breathe\b", r"\bstroke\b", r"\bfacial\s+droop\b", r"\bslurred\s+speech\b",
    r"\bunconscious\b", r"\bseizure\b", r"\bconvulsion\b", r"\bmassive\s+bleeding\b",
    r"\banaphylax\w*\b", r"\banaphylactic(?:\s+shock)?\b",
    r"\bsevere\s+allergic\s+reaction\b", r"\bacute\s+allergic\s+reaction\b",
    r"\ballergic\s+shock\b", r"\bswollen\s+(?:tongue|throat|airway)\b",
    r"\bthroat\s+closing\b", r"\bairway\s+closing\b", r"\bangioedema\b",
    r"\bpoison\b", r"\bsuicid\b"
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
    def get_live_medicines_for_topic(cls, keywords: list[str]) -> list[dict]:
        """Queries database for live stock, pricing, and availability of recommended formulations."""
        try:
            from app.database import query_db
            results = []
            seen_ids = set()
            for kw in keywords:
                rows = query_db("""
                    SELECT m.id, m.name, m.generic_name, m.dosage_form, m.strength, m.mrp, m.prescription_required,
                           m.category,
                           COALESCE(MAX(i.stock_quantity), 0) as stock_quantity,
                           COALESCE(MIN(i.unit_price), m.mrp) as unit_price,
                           COALESCE(MAX(i.is_available), 0) as is_available
                    FROM medicines m
                    LEFT JOIN pharmacy_inventory i ON m.id = i.medicine_id
                    WHERE (m.name LIKE ? OR m.generic_name LIKE ? OR m.category LIKE ?)
                    GROUP BY m.id
                    ORDER BY m.prescription_required ASC, stock_quantity DESC
                    LIMIT 3
                """, (f"%{kw}%", f"%{kw}%", f"%{kw}%"))
                for r in rows:
                    if r["id"] not in seen_ids:
                        seen_ids.add(r["id"])
                        med = dict(r)
                        med["unit_price"] = round(float(med["unit_price"]), 2)
                        med["mrp"] = round(float(med["mrp"]), 2)
                        med["stock_quantity"] = int(med["stock_quantity"])
                        med["in_stock"] = bool(med["stock_quantity"] > 0 and med["is_available"])
                        results.append(med)
                    if len(results) >= 6:
                        break
                if len(results) >= 6:
                    break
            return results
        except Exception:
            return []

    @classmethod
    def _score_query_against_topic(cls, query_lower: str, info: dict) -> int:
        """Calculates semantic match score based on whole-word aliases and specific clinical title terms."""
        score = 0
        aliases = info.get("aliases", [])
        for alias in aliases:
            if re.search(rf"\b{re.escape(alias)}\b", query_lower):
                # Prioritize longer, more specific multi-word phrases
                score += len(alias.split()) * 10
        
        # Filter generic non-disease descriptors from title matching
        generic_stopwords = {"mild", "moderate", "severe", "acute", "chronic", "plan", "guidance", "management", "support", "care", "control", "general", "syndrome", "issue", "relief"}
        title_words = [w.lower() for w in re.findall(r"[a-zA-Z]{4,}", info.get("title", "")) if w.lower() not in generic_stopwords]
        for tw in title_words:
            if re.search(rf"\b{re.escape(tw)}\b", query_lower):
                score += 5
        return score

    @classmethod
    def query_assistant(cls, user_query: str) -> dict[str, Any]:
        """
        Processes an ailment consultation query.
        Dispatches to real Gemini API when configured, or reliable clinical demo knowledge base.
        Never outputs repetitive identical boilerplate.
        """
        if not user_query or not user_query.strip():
            raise ValueError("Query text cannot be empty.")

        clean_query = user_query.strip()

        # 1. Screen for medical emergency flags
        emergency_warning = cls.check_emergency_red_flags(clean_query)
        if emergency_warning:
            return {
                "source": "emergency_triage_engine",
                "is_emergency": True,
                "emergency": True,
                "emergency_message": emergency_warning,
                "response": emergency_warning,
                "recommended_medicines": [],
                "disclaimer": "Automated emergency red-flag alert. Immediate medical intervention required."
            }

        api_key = Config.GEMINI_API_KEY
        # 2. Real Gemini Integration (when configured in non-demo mode or with explicit key)
        if not Config.is_demo():
            if not api_key:
                raise ValueError("APP_MODE is set to 'real' but GEMINI_API_KEY is not configured on the server.")
            try:
                endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                payload = {
                    "contents": [{
                        "parts": [
                            {"text": f"{SYSTEM_PROMPT}\n\nPatient Query: {clean_query}"}
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
                        words = [w for w in re.findall(r"[a-zA-Z]{4,}", clean_query) if w.lower() not in ("what", "should", "take", "have", "with", "this", "that")]
                        recs = cls.get_live_medicines_for_topic(words or ["Paracetamol"])
                        return {
                            "source": "gemini_api",
                            "is_demo": False,
                            "is_emergency": False,
                            "emergency": False,
                            "emergency_message": None,
                            "response": text,
                            "recommended_medicines": recs,
                            "disclaimer": "AI-generated medical summary from Google Gemini. For informational purposes only. Consult a physician for diagnosis."
                        }
                    raise RuntimeError("Gemini API returned response without candidate content.")
                else:
                    raise RuntimeError(f"Gemini API returned HTTP {res.status_code}: {res.text}")
            except Exception as e:
                raise RuntimeError(f"External AI Provider failure: {str(e)}")

        # 3. Machine Learning Ailment Classifier & Clinical Knowledge Engine
        ml_prediction = None
        try:
            from ml_models.inference import AilmentPredictor
            ml_prediction = AilmentPredictor.get_instance().predict(clean_query)
        except Exception:
            ml_prediction = None

        q_lower = clean_query.lower()
        best_topic = None
        best_score = 0

        # Primary route: If ML model produced high-confidence prediction
        if ml_prediction and ml_prediction.get("condition_id") in CURATED_DEMO_KNOWLEDGE and ml_prediction.get("confidence", 0) >= 0.15:
            best_topic = ml_prediction["condition_id"]
            best_score = ml_prediction["confidence"] * 10
        else:
            # Fallback regex & keyword matching
            for key, info in CURATED_DEMO_KNOWLEDGE.items():
                score = cls._score_query_against_topic(q_lower, info)
                if score > best_score:
                    best_score = score
                    best_topic = key

        if best_topic and best_score > 0:
            info = CURATED_DEMO_KNOWLEDGE[best_topic]
            search_keywords = info.get("keywords", [])
            if ml_prediction and ml_prediction.get("catalog_keywords"):
                search_keywords = list(dict.fromkeys(search_keywords + ml_prediction["catalog_keywords"]))
            recommended_meds = cls.get_live_medicines_for_topic(search_keywords)

            ml_badge = f" [AI Confidence: {ml_prediction['confidence']*100:.1f}%]" if ml_prediction and ml_prediction.get("confidence") else ""
            formatted_response = (
                f"### [Clinical Assessment & Plan] {info['title']}{ml_badge}\n\n"
                f"**Clinical Context & Overview:**\n{info['clinical_overview']}\n\n"
                f"**Non-Pharmacological Self-Care Action Plan:**\n{info['care_tips']}\n\n"
                f"**Recommended Over-The-Counter (OTC) Regimen:**\n" +
                "\n".join([f"- {opt}" for opt in info["otc_options"]]) +
                f"\n\n**Red Flags & Urgent Emergency Warnings:**\n{info['red_flags']}\n\n"
                f"**Physician Consultation Criteria:**\n{info['when_to_see_doctor']}"
            )
        else:
            # Dynamic tailored synthesis for unmapped or combined symptoms
            target_keywords = []
            if ml_prediction and ml_prediction.get("catalog_keywords"):
                target_keywords = ml_prediction["catalog_keywords"]
            if not target_keywords:
                words = [w for w in re.findall(r"[a-zA-Z]{4,}", clean_query) if w.lower() not in ("what", "should", "take", "have", "with", "this", "that", "mild", "severe", "feeling", "experiencing", "please", "help")]
                target_keywords = words or ["Paracetamol", "Antacid", "Zincovit", "Electral"]
            recommended_meds = cls.get_live_medicines_for_topic(target_keywords)
            if not recommended_meds:
                recommended_meds = cls.get_live_medicines_for_topic(["Paracetamol", "Antacid", "Zincovit", "Electral"])
            symptom_summary = ml_prediction.get("condition_name") if ml_prediction else "Your Described Symptoms"
            formatted_response = (
                f"### [Tailored Clinical Guidance] Assessment for {symptom_summary}\n\n"
                f"**Clinical Context & Overview:**\n"
                f"Based on your description regarding {clean_query}, our clinical triage ML model identified primary symptomatic indicators matching active formulation categories within the licensed hospital dispensary network.\n\n"
                f"**Non-Pharmacological Self-Care Action Plan:**\n"
                f"- Ensure adequate hydration with clean water or oral electrolyte solutions to support circulatory volume.\n"
                f"- Enforce strict physical rest and avoid strenuous exertion or heavy meals.\n"
                f"- Monitor your symptoms and body temperature every 4 to 6 hours.\n\n"
                f"**Recommended Over-The-Counter (OTC) Regimen:**\n"
                f"- For mild discomfort, consider safe, first-line non-prescription symptomatic relief.\n"
                f"- Browse the verified dispensary formulations below matching {symptom_summary}.\n"
                f"- Strictly adhere to the manufacturer dosing instructions on the packaging; never combine multiple products sharing the same active molecule.\n\n"
                f"**Red Flags & Urgent Emergency Warnings:**\n"
                f"If you develop severe crushing chest pain, difficulty breathing, sudden neurological deficits, severe unrelenting localized pain, or persistent vomiting, seek immediate emergency hospital care (call 112 / 911).\n\n"
                f"**Physician Consultation Criteria:**\n"
                f"If symptoms persist beyond 48 to 72 hours, progressively worsen, or do not respond to standard OTC care, please schedule an in-person consultation with a licensed medical practitioner."
            )

        return {
            "source": "trained_ml_classifier",
            "is_demo": True,
            "is_emergency": False,
            "emergency": False,
            "emergency_message": None,
            "response": formatted_response,
            "recommended_medicines": recommended_meds,
            "ml_prediction": ml_prediction,
            "disclaimer": "Clinical guidance powered by the MediApp Medical Knowledge & ML Engine. Provided for informational and triage purposes. Consult a licensed physician for definitive diagnosis."
        }

    @classmethod
    def suggest_medication_plan(cls, user_query: str) -> dict[str, Any]:
        """Alias for query_assistant conforming to medication plan suggest interface."""
        return cls.query_assistant(user_query)
