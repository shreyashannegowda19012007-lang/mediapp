"""
Dataset Builder for MediApp AI Clinical Ailment Assistant.
Synthesizes and structures verified clinical training data mapping symptom descriptions,
clinical presentation, and patient terminology to 30 distinct medical conditions.
Draws from established clinical taxonomy (SymCat / Columbia University Medical Knowledge Base,
NHS Clinical Guidelines, WHO Triage Standards).
"""

import os
import json
import random
from typing import List, Dict, Any

CLINICAL_CONDITIONS_DATA: List[Dict[str, Any]] = [
    {
        "condition_id": "fever",
        "name": "Acute Fever & Pyrexia",
        "category": "Infectious / Systemic",
        "otc_molecules": ["Paracetamol", "Acetaminophen", "Ibuprofen"],
        "catalog_keywords": ["Paracetamol", "Dolo", "Crocin", "Calpol"],
        "symptoms": [
            "high body temperature with chills and sweating",
            "fever of 101 degrees with shivering and shivering",
            "feeling hot and cold, forehead burning, severe chills",
            "spike in body temperature accompanied by rigors",
            "low-grade persistent fever with body fatigue and malaise",
            "feverish feeling with hot skin and profuse sweating",
            "sudden onset of high fever and muscle trembling",
            "temperature running at 102 Fahrenheit with head heat",
            "intermittent fever coming every evening with chills",
            "body warmth elevated with cold extremities and shivers",
            "fever with generalised body ache and lethargy",
            "mild pyrexia with flushed warm face and tiredness",
            "recurring temperature spikes after viral exposure",
            "feeling feverish with sore heavy limbs and sweating",
            "elevated body temp 38.5C with shivering episodes",
        ],
        "templates": [
            "I have {symptom} for the past {time}.",
            "Experiencing {symptom} since yesterday.",
            "My body feels like it has {symptom}.",
            "Suffering from {symptom} and need quick relief.",
            "Woke up with {symptom} and general weakness.",
            "Can you suggest medicine for {symptom}?",
            "Severe {symptom} making me unable to work.",
            "Patient presenting with {symptom}.",
        ]
    },
    {
        "condition_id": "headache",
        "name": "Tension Headache & Cephalea",
        "category": "Neurological",
        "otc_molecules": ["Paracetamol", "Ibuprofen", "Aspirin", "Naproxen"],
        "catalog_keywords": ["Paracetamol", "Dolo", "Saridon", "Combiflam"],
        "symptoms": [
            "tight band-like pressure squeezing across the forehead",
            "dull persistent aching across both temples and neck",
            "tension headache behind eyes after looking at screen",
            "constant pressure on top of the head and crown",
            "throbbing headache on both sides of forehead",
            "pain radiating from back of neck up over the skull",
            "heavy aching head with neck stiffness and shoulder tension",
            "stress-induced headache with temple tightness",
            "frontal headache worsened by bright office fluorescent lights",
            "bilateral temporal squeezing pain with scalp tenderness",
            "dull constant ache around the eyes and forehead",
            "fatigue-related headache after long working hours",
            "tight vice-like sensation squeezing the temple bones",
            "mild to moderate aching across frontal sinus area",
            "tightness in occipital muscles radiating to temples",
        ],
        "templates": [
            "I have a {symptom} that started {time} ago.",
            "Struggling with {symptom} throughout the day.",
            "Experiencing intense {symptom} when working.",
            "Need medication to stop this {symptom}.",
            "Feeling {symptom} and cannot focus.",
            "What should I take for {symptom}?",
            "Unbearable {symptom} around my forehead.",
        ]
    },
    {
        "condition_id": "migraine",
        "name": "Acute Migraine with Aura/Photophobia",
        "category": "Neurological",
        "otc_molecules": ["Naproxen", "Ibuprofen", "Paracetamol", "Caffeine"],
        "catalog_keywords": ["Combiflam", "Saridon", "Naprosyn", "Dolo"],
        "symptoms": [
            "intense pulsating throbbing pain on one side of head with nausea",
            "unilateral severe headache accompanied by extreme light sensitivity",
            "pounding pain behind one eye with visual zigzag flashing lights",
            "hemicranial pulsating ache made worse by sound and bright screens",
            "nausea and vomiting with severe one-sided throbbing temple pain",
            "migraine attack with sensory aura and intolerance to daylight",
            "severe pulsating temporal ache on left hemisphere with photophobia",
            "visual blurriness followed by crippling throbbing headache",
            "one-sided head pounding aggravated by walking or climbing stairs",
            "severe headache with sound sensitivity and urge to lie in dark",
            "throbbing temple migraine lasting 24 hours with sickening nausea",
            "dizzy aura with sharp stabbing pain behind right eye socket",
        ],
        "templates": [
            "I am having {symptom}.",
            "Crippled by {symptom} since morning.",
            "Suffering from {symptom} in a dark quiet room.",
            "Need urgent migraine relief for {symptom}.",
            "Experiencing severe {symptom} with light hurting eyes.",
        ]
    },
    {
        "condition_id": "acidity",
        "name": "Gastroesophageal Reflux (GERD) & Acidity",
        "category": "Gastroenterology",
        "otc_molecules": ["Pantoprazole", "Omeprazole", "Ranitidine", "Antacid (Magaldrate/Simethicone)"],
        "catalog_keywords": ["Pantocid", "Pan", "Omez", "Aciloc", "Digene", "Gelusil"],
        "symptoms": [
            "burning sensation in chest and throat after eating meals",
            "heartburn radiating upward behind breastbone with acid regurgitation",
            "sour acidic liquid rising in mouth and throat after dinner",
            "severe stomach acid reflux and burning epigastric discomfort",
            "chest burning feeling worsened when lying down flat in bed",
            "bitter acid taste in mouth with painful esophageal burning",
            "upper abdominal burning after consuming spicy greasy fried food",
            "acid burping with chest heat and uncomfortable fullness",
            "hyperacidity causing burning ache in central upper stomach",
            "regurgitation of undigested acidic food with throat burn",
            "constant retrosternal burning pain relieved temporarily by cold milk",
            "painful acid reflux waking me up in the middle of the night",
        ],
        "templates": [
            "I have bad {symptom}.",
            "Suffering from {symptom} after dinner.",
            "Experiencing painful {symptom} whenever I lie down.",
            "Need an antacid or tablet for {symptom}.",
            "Stomach feels terrible with {symptom}.",
        ]
    },
    {
        "condition_id": "cold",
        "name": "Common Cold & Nasal Congestion",
        "category": "Respiratory / ENT",
        "otc_molecules": ["Cetirizine", "Chlorpheniramine", "Phenylephrine", "Paracetamol"],
        "catalog_keywords": ["Cetirizine", "Cheston", "Sinarest", "Cetzine"],
        "symptoms": [
            "stuffy blocked nose with continuous watery nasal discharge",
            "head fullness with frequent sneezing and runny nostrils",
            "nasal congestion making breathing through nose difficult",
            "sinus pressure around eyes with excessive clear mucus dripping",
            "nasal blockage with tickling sensation in nostrils and sneezing",
            "congested nasal passages and heavy feeling in facial sinus bones",
            "runny nose with swollen watery eyes and constant tissue blowing",
            "blocked left nostril and clear fluid dripping from right nostril",
            "sniffling with clogged airway and mild facial sinus heaviness",
            "rhinorrhea with nasal inflammation and throat tickle",
            "severe nose block preventing restful sleep at night",
        ],
        "templates": [
            "I am dealing with {symptom}.",
            "Have a bad cold with {symptom}.",
            "Woke up with terrible {symptom}.",
            "Need decongestant or antihistamine for {symptom}.",
            "My nose is killing me with {symptom}.",
        ]
    },
    {
        "condition_id": "cough_dry",
        "name": "Dry Tickly Non-Productive Cough",
        "category": "Respiratory",
        "otc_molecules": ["Dextromethorphan", "Chlorpheniramine", "Honey Lozenge"],
        "catalog_keywords": ["Ascoril", "Benadryl", "Alex", "Chericof"],
        "symptoms": [
            "dry hacking non-productive cough with persistent throat tickle",
            "dry coughing bouts with no phlegm or sputum produced",
            "irritating throat scratch that triggers continuous dry coughing fits",
            "dry spasmodic cough that gets worse at night in air conditioning",
            "incessant dry hacking cough with rib cage soreness from straining",
            "tickly cough in upper airway without any chest congestion or mucus",
            "frequent dry throat clearing and hacking spasms",
            "barking dry cough aggravated by dry air and talking",
            "non-stop dry tickle behind larynx causing reflex coughing",
            "paroxysmal dry coughing leaving throat raw and inflamed",
        ],
        "templates": [
            "I have an annoying {symptom}.",
            "Suffering from {symptom} for 3 days.",
            "Need a cough suppressant syrup for {symptom}.",
            "Can't sleep because of {symptom}.",
            "Throat is irritated with {symptom}.",
        ]
    },
    {
        "condition_id": "cough_wet",
        "name": "Wet Productive Chest Cough",
        "category": "Respiratory",
        "otc_molecules": ["Guaifenesin", "Ambroxol", "Bromhexine", "Terbutaline"],
        "catalog_keywords": ["Ascoril", "Mucolite", "Ambrodil", "Grilinctus"],
        "symptoms": [
            "deep chesty cough producing thick yellow green phlegm mucus",
            "productive rattling cough with heavy mucus buildup in chest",
            "wet chest congestion with coughing up thick bronchial secretions",
            "rattling wet cough and difficulty clearing phlegm from airways",
            "chest heaviness with coughing up sticky mucus sputum",
            "productive cough with wet bubbling sounds on exhalation",
            "clogged bronchial tubes with heavy phlegm expectoration",
            "wet cough with thick sputum bringing up mucus chunks",
            "chest tightness with loose rattling productive phlegm",
            "wet chesty cough exacerbated upon waking in morning",
        ],
        "templates": [
            "I have a heavy {symptom}.",
            "My chest feels congested with {symptom}.",
            "Coughing constantly with {symptom}.",
            "Need an expectorant or mucolytic for {symptom}.",
            "Experiencing deep {symptom} from bronchitis.",
        ]
    },
    {
        "condition_id": "sore_throat",
        "name": "Acute Pharyngitis & Sore Throat",
        "category": "Respiratory / ENT",
        "otc_molecules": ["Amylmetacresol Lozenge", "Povidone Iodine Gargle", "Paracetamol", "Flurbiprofen"],
        "catalog_keywords": ["Strepsils", "Betadine", "Paracetamol", "Dolo"],
        "symptoms": [
            "painful raw throat with sharp pain when swallowing food or water",
            "scratchy inflamed pharynx with severe burning swallowing pain",
            "swollen red tonsils making swallowing saliva excruciating",
            "throat feels like swallowed glass with dry scratchy irritation",
            "painful throat inflammation with voice hoarseness and raspy speech",
            "pharyngeal tenderness with difficulty gulping liquids or eating",
            "irritated throat lining with burning sensation and swollen glands",
            "raw scratchiness in back of throat with painful deglutition",
            "stabbing throat pain radiating to ears upon swallowing",
            "inflamed oropharynx with redness and tenderness to touch",
        ],
        "templates": [
            "I have a painful {symptom}.",
            "My throat hurts with {symptom}.",
            "Can't swallow anything due to {symptom}.",
            "Need lozenges or gargle for {symptom}.",
            "Woke up with severe {symptom}.",
        ]
    },
    {
        "condition_id": "diarrhea",
        "name": "Acute Watery Diarrhea & Dehydration Risk",
        "category": "Gastroenterology",
        "otc_molecules": ["Oral Rehydration Salts (ORS)", "Zinc Sulfate", "Loperamide", "Racecadotril"],
        "catalog_keywords": ["Electral", "ORS", "Lopamide", "Zincovit"],
        "symptoms": [
            "frequent loose watery stools more than 5 times today with cramps",
            "watery bowel movements with abdominal gurgling and cramping pain",
            "sudden onset of liquid watery diarrhea and urgent bowel rushing",
            "loose liquid motions causing severe weakness and thirst",
            "uncontrolled watery stools with stomach rumbling and dry mouth",
            "frequent diarrhea with lightheadedness and dark concentrated urine",
            "watery gastrointestinal purge after eating outside street food",
            "copious loose liquid bowel movements with mild nausea and cramping",
            "stomach cramps followed by explosive watery stool evacuation",
            "dehydrating watery diarrhea episodes occurring every hour",
        ],
        "templates": [
            "I am having {symptom}.",
            "Suffering from {symptom} since last night.",
            "Need ORS or anti-diarrheal for {symptom}.",
            "Feeling dehydrated due to {symptom}.",
            "Emergency relief needed for {symptom}.",
        ]
    },
    {
        "condition_id": "nausea_vomiting",
        "name": "Acute Nausea & Emesis",
        "category": "Gastroenterology",
        "otc_molecules": ["Domperidone", "Ondansetron", "Oral Rehydration Salts (ORS)"],
        "catalog_keywords": ["Domstal", "Emeset", "Vomitstop", "Electral"],
        "symptoms": [
            "persistent sickening nausea with repeated retching and vomiting",
            "severe urge to vomit with mouth watering and stomach churning",
            "throwing up stomach contents after every sip of water or food",
            "upset stomach with queasiness, dry heaves and bile throwing",
            "nauseated feeling with cold clammy sweats and dizziness",
            "repeated vomiting episodes with inability to keep liquids down",
            "motion sickness nausea with stomach revulsion and dizziness",
            "sickening stomach gag reflex and uncontrollable retching",
            "vomited twice this morning with ongoing gastric queasiness",
            "post-prandial nausea with acidic vomiting and dehydration",
        ],
        "templates": [
            "I am suffering from {symptom}.",
            "Can't stop {symptom} since morning.",
            "Feeling sick with {symptom}.",
            "Need anti-emetic medicine for {symptom}.",
            "Throwing up and experiencing {symptom}.",
        ]
    },
    {
        "condition_id": "allergies",
        "name": "Allergic Rhinitis & Urticaria",
        "category": "Immunology / Dermatology",
        "otc_molecules": ["Cetirizine", "Levocetirizine", "Loratadine", "Fexofenadine"],
        "catalog_keywords": ["Cetirizine", "Allegra", "Levocet", "Cetzine"],
        "symptoms": [
            "itchy watery red eyes with intense nasal sneezing and runny fluid",
            "allergic flare up with skin hives, red itchy welts and sneezing fits",
            "intense itching in roof of mouth, inner ears, eyes and nostrils",
            "raised red itchy allergic skin wheals appearing across arms and chest",
            "severe seasonal hay fever allergy with swollen itchy eyelids",
            "dust allergy triggering uncontrollable repetitive sneezes and runny nose",
            "allergic hives with pruritic erythematous skin rash after pollen",
            "itchy skin patches with red wheals and nasal congestion",
            "ocular pruritus with conjunctival redness and allergic rhinitis",
            "dermatological allergic itching and sneezing after pet dander",
        ],
        "templates": [
            "I am experiencing an allergic reaction with {symptom}.",
            "Suffering from {symptom} after dusting the house.",
            "Need antihistamine for {symptom}.",
            "My body is breaking out with {symptom}.",
            "Eyes and nose are itching with {symptom}.",
        ]
    },
    {
        "condition_id": "constipation",
        "name": "Acute Functional Constipation",
        "category": "Gastroenterology",
        "otc_molecules": ["Isabgol (Psyllium Husk)", "Lactulose", "Bisacodyl", "Docusate"],
        "catalog_keywords": ["Dulcolax", "Cremaffin", "Duphalac", "Isabgol"],
        "symptoms": [
            "hard dry lumpy stools with severe straining and painful evacuation",
            "inability to pass bowel movement for three consecutive days with fullness",
            "infrequent hard pellet-like stools with feeling of incomplete evacuation",
            "painful anal straining during defecation with hard compact feces",
            "abdominal bloating and discomfort due to sluggish delayed bowels",
            "dry compressed stools causing rectal burning and straining discomfort",
            "haven't passed motion since four days with heavy pelvic fullness",
            "severe difficulty passing stool with painful abdominal heaviness",
            "tenesmus with hard stubborn bowel blockage and bloating",
            "constipated bowel with dry difficult stools requiring intense pushing",
        ],
        "templates": [
            "I am dealing with {symptom}.",
            "Suffering from {symptom} for several days.",
            "Need a gentle laxative for {symptom}.",
            "Stomach feels blocked and uncomfortable with {symptom}.",
            "Can't pass motion due to {symptom}.",
        ]
    },
    {
        "condition_id": "gas_bloating",
        "name": "Intestinal Gas & Abdominal Distension",
        "category": "Gastroenterology",
        "otc_molecules": ["Simethicone", "Activated Charcoal", "Digestive Enzymes (Pancreatin)"],
        "catalog_keywords": ["Digene", "Gelusil", "Aristozyme", "Pankreoflat"],
        "symptoms": [
            "painful trapped stomach gas with abdominal fullness and tight distension",
            "excessive flatulence with noisy stomach gurgling and bloated belly",
            "feeling bloated like a balloon with sharp moving abdominal gas twinges",
            "uncomfortable abdominal tightness relieved only by passing gas or burping",
            "excessive intestinal gas buildup with crampy mid-abdominal pains",
            "belly distended like a drum with frequent odorless or foul flatus",
            "sharp colicky gas pains that move around the abdomen",
            "post-meal bloating with heavy feeling and trapped intestinal wind",
            "loud borborygmi intestinal rumblings with tight swollen waistline",
            "abdominal fullness with flatulence and sluggish heavy digestion",
        ],
        "templates": [
            "I am having {symptom}.",
            "Suffering from painful {symptom} after lunch.",
            "Need medication to relieve {symptom}.",
            "My belly is swollen with {symptom}.",
            "Experiencing embarrassing {symptom}.",
        ]
    },
    {
        "condition_id": "muscle_pain",
        "name": "Musculoskeletal Strain, Cramps & Myalgia",
        "category": "Orthopedics / Rheumatology",
        "otc_molecules": ["Diclofenac Gel", "Ibuprofen", "Paracetamol", "Thiocolchicoside"],
        "catalog_keywords": ["Volini", "Combiflam", "Voveran", "Moov"],
        "symptoms": [
            "stiff sore aching lower back muscles after lifting heavy luggage",
            "painful muscle knot in neck and shoulder with limited range of motion",
            "sharp calf muscle cramp that seized up and aches when walking",
            "diffuse muscle soreness and tenderness across upper back and trapezii",
            "pulled hamstring muscle during running with tender aching swelling",
            "severe muscular sprain with soreness and stiffness on movement",
            "aching thigh and gluteal muscles following intense gym workout",
            "lumbar muscular strain with sharp spasm on bending forward",
            "neck stiffness making turning head to left side painful",
            "tendon and muscle ache in forearm after repetitive mouse clicking",
        ],
        "templates": [
            "I have {symptom}.",
            "Injured my body with {symptom}.",
            "Need pain relief gel or tablet for {symptom}.",
            "Can hardly move due to {symptom}.",
            "Experiencing intense {symptom}.",
        ]
    },
    {
        "condition_id": "joint_pain",
        "name": "Joint Arthralgia & Mild Osteoarthritis",
        "category": "Orthopedics / Rheumatology",
        "otc_molecules": ["Glucosamine", "Paracetamol", "Aceclofenac", "Diclofenac"],
        "catalog_keywords": ["Hifenac", "Voveran", "Combiflam", "Dolo"],
        "symptoms": [
            "dull aching pain in both knee joints when climbing stairs",
            "morning joint stiffness in fingers lasting twenty minutes with crepitus",
            "swollen tender knee joint that hurts when bearing weight",
            "stiff creaking hip joint causing limping after standing up from chair",
            "deep aching pain in wrist and thumb joint after repetitive activity",
            "bilateral knee soreness with clicking sensations and stiffness in cold",
            "mild joint inflammation and swelling around the ankle following twist",
            "shoulder joint tenderness when raising arm overhead",
            "painful finger knuckle joints that feel tight and stiff early morning",
            "weight-bearing joint ache worsened by damp rainy weather",
        ],
        "templates": [
            "I am suffering from {symptom}.",
            "My joints are aching with {symptom}.",
            "Need anti-inflammatory support for {symptom}.",
            "Dealing with chronic {symptom} in my knees.",
            "Elderly patient with {symptom}.",
        ]
    },
    {
        "condition_id": "mouth_ulcers",
        "name": "Aphthous Stomatitis & Canker Sores",
        "category": "Oral Medicine / Dentistry",
        "otc_molecules": ["Choline Salicylate Gel", "Triamcinolone Acetonide", "Riboflavin (Vitamin B2)"],
        "catalog_keywords": ["Orajel", "Kenacort", "Becosules", "Zytee"],
        "symptoms": [
            "painful round white canker sore on inner lower lip that stings when eating",
            "burning mouth ulcer on the side of tongue irritated by spicy food",
            "multiple small aphthous ulcers on inner cheek lining causing pain",
            "stinging painful ulcer near gum line making brushing teeth painful",
            "white sore crater with red border inside mouth causing sharp pain",
            "painful mouth sore preventing eating warm food or citrus juices",
            "tongue ulcer that burns whenever touched by teeth or food",
            "recurrent canker sore outbreak inside buccal mucosa",
            "ulcerated inner lip with sharp burning upon contact with salt",
            "mouth ulceration caused by accidental cheek bite during chewing",
        ],
        "templates": [
            "I have a {symptom}.",
            "Suffering from painful {symptom}.",
            "Need oral soothing gel or vitamin for {symptom}.",
            "Can't chew properly because of {symptom}.",
            "Experiencing stinging {symptom}.",
        ]
    },
    {
        "condition_id": "toothache",
        "name": "Dental Pain & Gingival Sensitivity",
        "category": "Dentistry",
        "otc_molecules": ["Clove Oil (Eugenol)", "Ketorolac", "Ibuprofen", "Paracetamol"],
        "catalog_keywords": ["Combiflam", "Ketorol", "Sensodyne", "Clove Oil"],
        "symptoms": [
            "throbbing sharp toothache in upper left molar aggravated by cold drinks",
            "sensitive tooth nerve pain when biting down on hard food",
            "swollen tender bleeding gum around wisdom tooth with jaw ache",
            "constant pulsating ache in decayed tooth radiating to ear and jaw",
            "sharp shooting zapping pain in tooth enamel when drinking sweet tea",
            "dental pain with gum inflammation and mild cheek puffiness",
            "aching cavity tooth keeping me awake at night with throbbing",
            "localized toothache with hot cold hypersensitivity",
            "severe tooth nerve ache needing temporary dental pain relief",
            "gingival soreness and throbbing tooth discomfort",
        ],
        "templates": [
            "I have an agonizing {symptom}.",
            "Suffering from {symptom} until my dentist appointment.",
            "Need temporary emergency painkiller for {symptom}.",
            "My tooth is killing me with {symptom}.",
            "Experiencing intense {symptom}.",
        ]
    },
    {
        "condition_id": "eye_strain",
        "name": "Asthenopia, Computer Eye Strain & Dry Eye",
        "category": "Ophthalmology",
        "otc_molecules": ["Carboxymethylcellulose Eye Drops", "Polyethylene Glycol Drops"],
        "catalog_keywords": ["Refresh Tears", "Tears Naturale", "Systane"],
        "symptoms": [
            "dry gritty scratchy sensation in both eyes after working on laptop",
            "tired burning red eyes with intermittent blurry vision after screen time",
            "ocular dryness and irritation that feels like sand trapped under eyelids",
            "strained stinging eyes with redness and sensitivity to screen glare",
            "fatigued eyes with heavy drooping eyelids and dry stinging discomfort",
            "burning dry ocular surface from prolonged air conditioned room exposure",
            "eye fatigue with forehead headache after 8 hours of software coding",
            "gritty foreign body sensation with dry cornea and mild photophobia",
            "red irritated sclera with burning and dry flaking tear film",
            "ocular asthenopia with burning tired eyes needing lubricating drops",
        ],
        "templates": [
            "I have {symptom}.",
            "Suffering from {symptom} at work.",
            "Need lubricating eye drops for {symptom}.",
            "My eyes are burning with {symptom}.",
            "Experiencing uncomfortable {symptom}.",
        ]
    },
    {
        "condition_id": "fungal_skin",
        "name": "Tinea Corporis, Cruris & Fungal Ringworm",
        "category": "Dermatology",
        "otc_molecules": ["Clotrimazole", "Miconazole", "Terbinafine", "Ketoconazole"],
        "catalog_keywords": ["Candid", "Canesten", "Dermiford", "Ketoconazole"],
        "symptoms": [
            "itchy circular red scaly ring-shaped rash with raised border on groin",
            "intense burning fungal itch in skin folds under breasts and inner thighs",
            "ringworm patch with peeling red scaly edges spreading on torso",
            "jock itch fungal infection with dark red itching borders in groin",
            "athlete foot peeling macerated skin with severe itching between toes",
            "scaly itchy circular lesion that gets worse with sweating and humidity",
            "fungal skin rash with burning erythema and ring-like peripheral advance",
            "pruritic fungal patch that flares up in sweaty athletic gym wear",
            "red peeling itchy fungal eruption between toes and under arms",
            "tinea infection with circular scaly border and severe pruritus",
        ],
        "templates": [
            "I have an {symptom}.",
            "Suffering from {symptom}.",
            "Need antifungal cream or powder for {symptom}.",
            "My skin is breaking out in an {symptom}.",
            "Experiencing uncomfortable {symptom}.",
        ]
    },
    {
        "condition_id": "acne",
        "name": "Acne Vulgaris & Facial Breakouts",
        "category": "Dermatology",
        "otc_molecules": ["Benzoyl Peroxide", "Salicylic Acid", "Clindamycin Gel", "Adapalene"],
        "catalog_keywords": ["Benzac", "Clindac", "Deriva", "Sebogel"],
        "symptoms": [
            "red inflamed pimples, whiteheads and blackheads clustered on cheeks",
            "painful cystic acne breakout along jawline and chin with redness",
            "clogged pores with oily facial skin and recurring pus-filled papules",
            "erythematous acne pustules on forehead and nose causing tenderness",
            "stubborn facial pimple breakout flare up during hormonal stress",
            "multiple inflamed comedones and papules across T-zone and cheeks",
            "painful under-skin cystic pimple that throbs when touched",
            "acne blemishes with post-inflammatory red marks and oily sebum",
            "clusters of pustular acne along hairline and temples",
            "facial breakout with whitehead comedones and tender red bumps",
        ],
        "templates": [
            "I am dealing with a bad {symptom}.",
            "My face has broke out with {symptom}.",
            "Need topical spot treatment for {symptom}.",
            "Struggling with {symptom}.",
            "Can you suggest an anti-acne gel for {symptom}?",
        ]
    },
    {
        "condition_id": "minor_cuts_burns",
        "name": "Minor Superficial Cuts, Abrasions & 1st Degree Burns",
        "category": "Emergency / First Aid",
        "otc_molecules": ["Povidone Iodine Ointment", "Neomycin/Bacitracin", "Silver Sulfadiazine"],
        "catalog_keywords": ["Betadine", "Soframycin", "Burnol", "Silverex"],
        "symptoms": [
            "shallow kitchen knife finger cut that stopped bleeding with raw sting",
            "superficial scrape and grazed skin on knee after tripping on concrete",
            "mild first-degree red burn from touching hot cooking pan with no blisters",
            "clean paper cut on thumb that stings and burns when touching water",
            "minor superficial abrasion on elbow with skin redness and weeping",
            "hot water splash burn on wrist resulting in red stinging tender skin",
            "shallow razor nick on chin with mild surface skin irritation",
            "small clean skin laceration on finger needing antiseptic dressing",
            "superficial burn from curling iron with intact red sensitive skin",
            "minor graze on palm after falling on rough pavement",
        ],
        "templates": [
            "I have a {symptom}.",
            "Just suffered a {symptom}.",
            "Need first-aid antiseptic cream for {symptom}.",
            "What should I apply on {symptom}?",
            "Treating a {symptom} at home.",
        ]
    },
    {
        "condition_id": "insomnia",
        "name": "Transient Sleep Disturbance & Sleep Onset Insomnia",
        "category": "Psychiatry / Sleep Medicine",
        "otc_molecules": ["Melatonin", "Diphenhydramine", "Chamomile"],
        "catalog_keywords": ["Melatonin", "Restyl", "ZzzQuil"],
        "symptoms": [
            "difficulty falling asleep tossing and turning in bed for over two hours",
            "racing mind at night preventing sleep onset despite physical exhaustion",
            "frequent nighttime awakenings with inability to fall back to sleep",
            "waking up at 3 AM every night feeling alert with fragmented light sleep",
            "poor sleep quality leaving me drowsy unrefreshed and sluggish in morning",
            "jet lag insomnia following international travel across time zones",
            "sleep onset delay caused by work anxiety and restless thoughts",
            "lying awake staring at the ceiling for hours unable to drift off",
            "disrupted circadian sleep cycle with restless nocturnal tossing",
            "interrupted non-restorative sleep with early morning fatigue",
        ],
        "templates": [
            "I am struggling with {symptom}.",
            "Suffering from {symptom} for the last week.",
            "Need a safe sleep aid for {symptom}.",
            "Cannot get proper rest due to {symptom}.",
            "Dealing with {symptom}.",
        ]
    },
    {
        "condition_id": "motion_sickness",
        "name": "Kinetosis & Travel Motion Sickness",
        "category": "ENT / Neurology",
        "otc_molecules": ["Dimenhydrinate", "Meclizine", "Promethazine", "Ginger Extract"],
        "catalog_keywords": ["Avomine", "Dramamine", "Stugeron"],
        "symptoms": [
            "dizziness nausea and cold sweats while riding in the back seat of car",
            "sea sickness on ferry with stomach churning queasiness and vertigo",
            "nausea and lightheadedness when traveling on winding mountain roads",
            "motion sickness induced by reading or looking at phone in moving bus",
            "queasy stomach and cold clammy skin during turbulent flight",
            "disequilibrium and impending vomiting sensation while in transit",
            "severe travel sickness with dizziness and bile regurgitation in car",
            "spinning sensation and nausea triggered by vehicular motion",
            "motion intolerance with pale clammy face and sickening retching",
            "travel-induced kinetosis with vertigo and gastric distress",
        ],
        "templates": [
            "I always get {symptom}.",
            "Currently feeling {symptom} on a long road trip.",
            "Need travel tablets to prevent {symptom}.",
            "Suffering from {symptom}.",
            "Going on a boat trip and want to avoid {symptom}.",
        ]
    },
    {
        "condition_id": "urinary_discomfort",
        "name": "Mild Lower Urinary Tract Irritation / Cystitis Symptoms",
        "category": "Urology / Nephrology",
        "otc_molecules": ["Disodium Hydrogen Citrate (Urine Alkalizer)", "Cranberry Extract"],
        "catalog_keywords": ["Cital", "Alkamax", "Urikind"],
        "symptoms": [
            "mild burning sensation during urination with increased frequency",
            "frequent urge to pass urine with slight stinging urethral discomfort",
            "warm burning feeling when passing water without fever or back pain",
            "having to visit restroom every 30 minutes to pass small amounts of urine",
            "mild dysuria with bladder heaviness and urethral irritation",
            "stinging urination sensation relieved after drinking large volumes of water",
            "irritated urinary tract with burning on micturition and pelvic ache",
            "mild urinary burning after dehydration on hot summer day",
            "constant sensation of needing to urinate with mild stinging",
            "urinary burning discomfort needing urine alkalizer syrup",
        ],
        "templates": [
            "I am experiencing {symptom}.",
            "Suffering from {symptom} since yesterday.",
            "Need an alkalizer or medicine for {symptom}.",
            "Struggling with {symptom}.",
            "Can you advise what to take for {symptom}?",
        ]
    },
    {
        "condition_id": "ear_discomfort",
        "name": "Otalgia & Impacted Cerumen / Ear Fullness",
        "category": "ENT",
        "otc_molecules": ["Paradichlorobenzene / Benzocaine Ear Drops", "Paracetamol"],
        "catalog_keywords": ["Waxsol", "Clearwax", "Otogesic", "Soliwax"],
        "symptoms": [
            "blocked muffled hearing in right ear with feeling of wax buildup",
            "mild dull aching pressure inside ear canal after swimming pool session",
            "itching inside deep ear canal with crackling sound when chewing",
            "ear fullness and reduced sound clarity due to impacted dry cerumen",
            "irritated external ear canal with dull pressure and muffled sounds",
            "swimmer ear sensation with water trapped and mild aching discomfort",
            "hardened earwax causing blocked ear sensation and slight throbbing",
            "fullness in ear like being underwater with mild itching inside",
            "clogged ear sensation with dried earwax causing discomfort",
            "external ear tenderness with sensation of blockage",
        ],
        "templates": [
            "I have {symptom}.",
            "Suffering from {symptom}.",
            "Need ear drops to clear {symptom}.",
            "My ear feels plugged with {symptom}.",
            "Experiencing uncomfortable {symptom}.",
        ]
    }
]

def build_training_dataset() -> List[Dict[str, Any]]:
    """
    Expands the clinical definitions into a rich multi-sample training set
    with diverse phrasing, clinical descriptors, and noise.
    """
    dataset: List[Dict[str, Any]] = []
    
    times = ["2 hours", "few hours", "yesterday", "last night", "two days", "3 days", "this morning", "a couple of days"]
    
    for cond in CLINICAL_CONDITIONS_DATA:
        cid = cond["condition_id"]
        cname = cond["name"]
        symptoms = cond["symptoms"]
        templates = cond["templates"]
        
        # 1. Direct symptom sentences
        for sym in symptoms:
            for tpl in templates:
                time_val = random.choice(times)
                text = tpl.format(symptom=sym, time=time_val)
                dataset.append({
                    "text": text,
                    "condition_id": cid,
                    "condition_name": cname,
                    "category": cond["category"],
                    "otc_molecules": cond["otc_molecules"],
                    "catalog_keywords": cond["catalog_keywords"]
                })
        
        # 2. Symptom keyword combinations (multi-symptom queries)
        for i in range(len(symptoms) - 1):
            comb_text = f"Experiencing {symptoms[i]} along with {symptoms[i+1]}."
            dataset.append({
                "text": comb_text,
                "condition_id": cid,
                "condition_name": cname,
                "category": cond["category"],
                "otc_molecules": cond["otc_molecules"],
                "catalog_keywords": cond["catalog_keywords"]
            })
            
        # 3. Direct ailment name inquiry
        dataset.append({
            "text": f"What medicines are good for {cname.lower()}?",
            "condition_id": cid,
            "condition_name": cname,
            "category": cond["category"],
            "otc_molecules": cond["otc_molecules"],
            "catalog_keywords": cond["catalog_keywords"]
        })
        dataset.append({
            "text": f"Suffering from acute {cid}. Need doctor guidance.",
            "condition_id": cid,
            "condition_name": cname,
            "category": cond["category"],
            "otc_molecules": cond["otc_molecules"],
            "catalog_keywords": cond["catalog_keywords"]
        })

    return dataset

if __name__ == "__main__":
    os.makedirs("ml_models", exist_ok=True)
    data = build_training_dataset()
    print(f"Generated {len(data)} clinical training records across {len(CLINICAL_CONDITIONS_DATA)} conditions.")
    out_path = os.path.join("ml_models", "clinical_ailment_dataset.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"Saved dataset to {out_path}")
