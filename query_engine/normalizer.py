"""
CardioGuide Query Normalizer
P1 - Robust deterministic normalization core

Goals:
- Handle realistic human typing errors.
- Handle texting/shorthand.
- Expand cardiovascular abbreviations safely.
- Protect medical terminology.
- Protect numbers, measurements, doses, percentages and BP readings.
- Preserve negation and uncertainty.
- Avoid destructive generic spelling correction.
- Support multi-error queries.
- Never answer the medical question.

Pipeline:

    RAW QUERY
        -> basic cleanup
        -> protect clinical values (placeholders)
        -> typo / shorthand normalization
        -> medical abbreviation expansion
        -> context-aware spelling correction
        -> restore protected values
        -> structural cleanup
        -> semantic validation
        -> (optional) hardened LLM fallback, itself validated
        -> safe normalized query

normalize_query() never returns None and never raises for string input:
if anything goes wrong it falls back to the original query.
"""

from __future__ import annotations

import json
import os
import re
import time
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple

try:  # requests is only needed for the optional LLM fallback
    import requests
except ImportError:  # pragma: no cover
    requests = None  # type: ignore[assignment]


# Private-use characters are used for placeholders because they are never
# matched by the word tokenizer, the abbreviation regex or the digit regexes.
_PH_OPEN = "\ue000"
_PH_CLOSE = "\ue001"
_PLACEHOLDER_RE = re.compile(_PH_OPEN + r"(\d+)" + _PH_CLOSE)


def _terms(block: str, sep: str = ",") -> Set[str]:
    """Turn a multi-line block into a lowercase set of terms."""
    return {
        t.strip().lower()
        for t in block.replace("\n", sep).split(sep)
        if t.strip()
    }


class QueryNormalizer:
    """
    Robust query normalizer for CardioGuide.

    The normalizer ONLY transforms user language. It must never answer a
    medical question, diagnose, add medical facts, recommend treatment,
    invent symptoms or modify clinical measurements.
    """

    MIN_FUZZY_SCORE: float = 8.0

    # An LLM pass is only attempted when at least this many words are
    # still unrecognised AND they make up at least this fraction of words.
    UNRESOLVED_MIN_WORDS: int = 2
    UNRESOLVED_MIN_RATIO: float = 0.4

    # =========================================================
    # TEXT / INTERNET / PATIENT SHORTHAND
    # =========================================================

    TEXT_NORMALIZATIONS: Dict[str, str] = {
        # Pronouns / common texting
        "u": "you",
        "ur": "your",
        "urs": "yours",
        "r": "are",
        "n": "and",
        "nd": "and",
        "w": "with",
        "w/": "with",
        "w/o": "without",
        "b4": "before",
        "btwn": "between",
        "b/w": "between",
        "abt": "about",
        "pls": "please",
        "plz": "please",
        "tho": "though",
        "thx": "thanks",
        "ty": "thank you",

        # Question shorthand
        "wat": "what",
        "wht": "what",
        "wut": "what",
        "whut": "what",
        "whats": "what is",
        "whts": "what is",
        "hows": "how is",
        "howd": "how did",
        "whys": "why is",

        # Contractions without apostrophes
        # NOTE: "ill" and "id" are deliberately NOT here: "I feel ill"
        # must never become "I feel I will".
        "im": "I am",
        "ive": "I have",
        "i'm": "I am",
        "i've": "I have",
        "i'll": "I will",
        "dont": "do not",
        "doesnt": "does not",
        "didnt": "did not",
        "cant": "cannot",
        "couldnt": "could not",
        "wouldnt": "would not",
        "shouldnt": "should not",
        "wont": "will not",
        "isnt": "is not",
        "arent": "are not",
        "werent": "were not",
        "wasnt": "was not",
        "havent": "have not",
        "hasnt": "has not",
        "hadnt": "had not",

        # Internet shorthand
        "idk": "I do not know",
        "irl": "in real life",
        "rn": "right now",
        "bc": "because",
        "bcs": "because",
        "cuz": "because",
        "coz": "because",
        "becuz": "because",
        "sumtimes": "sometimes",
        "sometims": "sometimes",
        "rlly": "really",
        "rly": "really",
        "srs": "serious",
        "2day": "today",
        "4get": "forget",

        # Medical conversational shorthand
        "meds": "medications",
        "med": "medication",
        "symp": "symptom",
        "symps": "symptoms",
        "sxs": "symptoms",
        "doc": "doctor",

        # Common patient shorthand
        "prob": "problem",
        "probs": "problems",
        "info": "information",
        "ques": "question",
        "esp": "especially",
        "approx": "approximately",
        "appt": "appointment",
        "fam": "family",

        # More texting / slang
        "dnt": "do not",
        "cudnt": "could not",
        "wudnt": "would not",
        "shudnt": "should not",
        "ovr": "over",
        "nite": "night",
        "tonite": "tonight",
        "tmrw": "tomorrow",
        "wks": "weeks",
        "hrs": "hours",
        "mins": "minutes",
        "yr": "year",
        "ppl": "people",
        "hlp": "help",
        "gud": "good",
        "thnx": "thanks",
        "thanx": "thanks",
        "gonna": "going to",
        "wanna": "want to",
        "gotta": "have to",
        "kinda": "kind of",
        "lemme": "let me",
        "sumthin": "something",
        "somethin": "something",
        "hw": "how",
        "wen": "when",
        "wud": "would",
        "cud": "could",
        "shud": "should",
        "prego": "pregnant",
        "preggo": "pregnant",
    }

    # =========================================================
    # MEDICAL ABBREVIATIONS
    # =========================================================

    MEDICAL_ABBREVIATIONS: Dict[str, str] = {
        # Blood pressure / cardiovascular
        "bp": "blood pressure",
        "htn": "hypertension",
        "hbp": "high blood pressure",
        "hr": "heart rate",
        "bpm": "beats per minute",
        "cad": "coronary artery disease",
        "chd": "coronary heart disease",
        "hf": "heart failure",
        "chf": "heart failure",
        "af": "atrial fibrillation",
        "afib": "atrial fibrillation",
        "a-fib": "atrial fibrillation",
        "mi": "heart attack",
        "acs": "acute coronary syndrome",
        "cvd": "cardiovascular disease",
        "cva": "stroke",
        "tia": "transient ischemic attack",
        "pad": "peripheral artery disease",
        "rhd": "rheumatic heart disease",

        # Heart failure
        "hfref": "heart failure with reduced ejection fraction",
        "hfpef": "heart failure with preserved ejection fraction",
        "hfmref": "heart failure with mildly reduced ejection fraction",
        "ef": "ejection fraction",

        # Lipids
        "tc": "total cholesterol",
        "ldl": "low-density lipoprotein",
        "hdl": "high-density lipoprotein",
        "tg": "triglycerides",

        # Measurements
        "mmhg": "mmHg",
        "mgdl": "mg/dL",
        "mg/dl": "mg/dL",

        # Symptoms / clinical language
        "sob": "shortness of breath",
        "cp": "chest pain",
        "sx": "symptoms",
        "dx": "diagnosis",
        "hx": "history",
        "fhx": "family history",
        "pmh": "past medical history",

        # Medication language
        "rx": "prescription",
        "otc": "over the counter",

        # Rhythm / structure
        "lvh": "left ventricular hypertrophy",
        "svt": "supraventricular tachycardia",
        "pvc": "premature ventricular contraction",
        "pvcs": "premature ventricular contractions",
        "vt": "ventricular tachycardia",
        "vf": "ventricular fibrillation",
        "hocm": "hypertrophic obstructive cardiomyopathy",
        "lv": "left ventricle",
        "rv": "right ventricle",
        "lvef": "left ventricular ejection fraction",
        "aaa": "abdominal aortic aneurysm",

        # Procedures / devices / tests
        "icd": "implantable cardioverter defibrillator",
        "cabg": "coronary artery bypass graft",
        "pci": "percutaneous coronary intervention",
        "tavr": "transcatheter aortic valve replacement",
        "ecg": "electrocardiogram",
        "ekg": "electrocardiogram",
        "bnp": "B-type natriuretic peptide",
        "crp": "C-reactive protein",
        "aed": "automated external defibrillator",
        "cpr": "cardiopulmonary resuscitation",
        "icu": "intensive care unit",
        "er": "emergency room",
        "stemi": "ST-elevation myocardial infarction",
        "nstemi": "non-ST-elevation myocardial infarction",

        # Other conditions
        "dvt": "deep vein thrombosis",
        "pe": "pulmonary embolism",
        "copd": "chronic obstructive pulmonary disease",
        "ckd": "chronic kidney disease",
        "dm": "diabetes mellitus",
        "t1dm": "type 1 diabetes",
        "t2dm": "type 2 diabetes",
        "gerd": "gastroesophageal reflux disease",
        "osa": "obstructive sleep apnea",
        "bmi": "body mass index",
        "nyha": "New York Heart Association",

        # BP components / drug classes
        "sbp": "systolic blood pressure",
        "dbp": "diastolic blood pressure",
        "sys": "systolic",
        "dia": "diastolic",
        "ccb": "calcium channel blocker",
        "doac": "direct oral anticoagulant",
        "acei": "ACE inhibitor",
        "arni": "angiotensin receptor neprilysin inhibitor",
    }

    # Abbreviations that are only expanded when the query looks medical.
    AMBIGUOUS_ABBREVIATIONS: Set[str] = {
        "af", "hr", "mi", "cp", "ef", "pad", "rx", "tc", "tg", "hf",
        "pvc", "pvcs", "icd", "vt", "vf", "pe", "dm", "lv", "rv", "er",
        "sys", "dia", "aaa",
    }

    # In a definition-style question ("what is PVC?") inside a cardiology
    # tool, these ambiguous abbreviations are still expanded. The truly
    # risky ones stay gated behind explicit medical context.
    DEFINITION_UNSAFE: Set[str] = {"hr", "rx", "er", "pe", "dm", "dia", "aaa"}

    # =========================================================
    # HIGH-VALUE MEDICAL VOCABULARY
    # =========================================================

    MEDICAL_VOCABULARY: Set[str] = _terms("""
        hypertension, hypotension, cardiovascular, cardiovascular disease,
        blood pressure, heart disease, heart failure, heart attack, cardiac,
        coronary artery disease, coronary heart disease, coronary,
        atherosclerosis, arrhythmia, arrhythmias, atrial fibrillation,
        fibrillation, atrial, angina, ischemia, stroke, ischemic stroke,
        hemorrhagic stroke, transient ischemic attack,
        rheumatic heart disease, peripheral artery disease,
        acute coronary syndrome, past medical history,
        ejection fraction, reduced ejection fraction,
        preserved ejection fraction, mildly reduced ejection fraction,
        systolic, diastolic, pulse, heartbeat, heart rate,
        cholesterol, total cholesterol, low-density lipoprotein,
        high-density lipoprotein, triglycerides, lipoprotein, lipid,
        symptom, symptoms, headache, dizziness, dizzy, fainting, faint,
        fatigue, swelling, edema, chest pain, shortness of breath,
        breathlessness, breathless, breathing, palpitations, palpitation,
        nausea, vomiting, sweating, weakness, confusion, chest,
        medication, medications, medicine, doctor, diagnosis, treatment,
        disease, condition, complication, complications, risk factor,
        risk factors, prevention, screening, test, tests, blood test,
        medical report, family history, side effect, side effects,
        prescription, tablet, tablets, pill, pills, dose, doses,
        hospital, emergency, ambulance, medical, history,
        exercise, physical activity, diet, sodium, salt, smoking, alcohol,
        weight, obesity, sleep, stress,
        antihypertensive, statin, aspirin, beta blocker, ace inhibitor,
        arb, diuretic, anticoagulant, antiplatelet,
        amlodipine, lisinopril, losartan, valsartan, atenolol, metoprolol,
        warfarin, clopidogrel, atorvastatin, rosuvastatin, simvastatin,
        furosemide, hydrochlorothiazide, spironolactone,
        artery, arteries, vein, veins, heart, blood, blood vessel,
        blood vessels, vessel, vessels, brain, circulation, clotting, clot,
        diabetes, prediabetes, blood glucose, blood sugar, glucose,
        kidney disease, kidney, cardiologist, cardiology, pressure,
        hfref, hfpef, hfmref
    """)

    # =========================================================
    # EXTRA CARDIOLOGY / GENERAL MEDICAL LEXICON
    # =========================================================

    EXTRA_MEDICAL_LEXICON: Set[str] = _terms("""
        tachycardia, bradycardia, cardiomyopathy, hypertrophic cardiomyopathy,
        dilated cardiomyopathy, myocardial infarction, myocardial, infarction,
        pericarditis, myocarditis, endocarditis, cardiomegaly, aneurysm,
        aortic, aorta, aortic stenosis, aortic dissection, stenosis,
        regurgitation, valve, valves, mitral, mitral valve prolapse,
        tricuspid, pulmonary, pulmonary embolism, embolism, embolus,
        thrombosis, deep vein thrombosis, thrombus, varicose veins,
        vasculitis, syncope, presyncope, orthostatic hypotension,
        hypertensive, hypertensive crisis, hyperlipidemia, dyslipidemia,
        hypercholesterolemia, hyperglycemia, hypoglycemia, anemia,
        hypokalemia, hyperkalemia, hyponatremia, angioplasty, stent,
        bypass, pacemaker, defibrillator, cardioversion, ablation,
        catheterization, angiography, angiogram, echocardiogram,
        echocardiography, electrocardiogram, stress test, holter monitor,
        troponin, natriuretic peptide, cardiac arrest, cardiac output,
        congenital heart disease, murmur, heart murmur, heart block,
        bundle branch block, ventricular, ventricle, atrium, atria,
        ventricular tachycardia, ventricular fibrillation,
        supraventricular tachycardia, premature ventricular contractions,
        premature, contractions, atrial flutter, flutter, sinus rhythm,
        sinus, rhythm, irregular heartbeat, hypertrophy,
        left ventricular hypertrophy, cardiogenic shock,
        pulmonary hypertension, pulmonary edema, peripheral edema,
        claudication, intermittent claudication, angina pectoris,
        unstable angina, stable angina, plaque, coagulation, blood clot,
        blood clots, bleeding, hemorrhage, hematoma, platelet, platelets,
        cardiac rehabilitation, rehabilitation, pregnant, pregnancy,
        menopause, thyroid, hyperthyroidism, hypothyroidism, anxiety,
        chest tightness, tightness, chest discomfort, discomfort,
        lightheaded, lightheadedness, vertigo, tiredness, sweats,
        clammy, cyanosis, pallor, swollen, ankles, ankle, legs, feet,
        cough, coughing, wheezing, orthopnea, dyspnea, racing heart,
        heartburn, indigestion, jaw pain, arm pain, lung, lungs,
        lipid panel, lipid profile, hba1c, creatinine, electrolytes,
        potassium, magnesium, calcium, ultrasound, doppler, angina,
        cardiologist, cardiac arrhythmia, hypertension, cholesterol,
        thrombolytic, vasodilator, vasoconstriction, vascular,
        cardiothoracic, cardiopulmonary, resuscitation, oxygen saturation,
        oxygen, saturation, inflammation, infection, sepsis, obesity,
        overweight, metabolic syndrome, insulin resistance, sleep apnea,
        apnea, snoring, caffeine, energy drink, cigarette, cigarettes,
        vaping, tobacco, nicotine, cannabis, cocaine
    """)

    DRUG_NAMES: Set[str] = _terms("""
        metoprolol, carvedilol, bisoprolol, propranolol, nebivolol,
        atenolol, amlodipine, nifedipine, diltiazem, verapamil,
        lisinopril, enalapril, ramipril, perindopril, captopril,
        losartan, valsartan, candesartan, irbesartan, telmisartan,
        olmesartan, sacubitril, hydrochlorothiazide, chlorthalidone,
        indapamide, furosemide, torsemide, bumetanide, spironolactone,
        eplerenone, digoxin, amiodarone, flecainide, sotalol, warfarin,
        apixaban, rivaroxaban, dabigatran, edoxaban, heparin,
        enoxaparin, clopidogrel, ticagrelor, prasugrel, aspirin,
        atorvastatin, rosuvastatin, simvastatin, pravastatin,
        lovastatin, ezetimibe, fenofibrate, gemfibrozil, niacin,
        nitroglycerin, isosorbide, hydralazine, clonidine, methyldopa,
        ivabradine, ranolazine, empagliflozin, dapagliflozin,
        metformin, insulin, ibuprofen, naproxen, paracetamol,
        acetaminophen, diclofenac, omeprazole, pantoprazole,
        levothyroxine, prednisone
    """)

    # Strong medical neighbours: they license fixing a 4-letter typo
    # ("hart attack") and add a scoring bonus.
    CONTEXT_WORDS: Set[str] = _terms("""
        blood, pressure, heart, chest, pain, attack, failure, disease,
        cholesterol, pulse, rate, artery, arteries, stroke, cardiac,
        symptoms, symptom, medication, medicine, dizziness, breath,
        fibrillation, hypertension, sugar, glucose, cardiovascular,
        angina, pill, pills, tablet, tablets, dose, doctor, hospital,
        medical, diagnosis, treatment, cardiologist, palpitations
    """)

    # =========================================================
    # COMMON ENGLISH VOCABULARY
    # =========================================================

    COMMON_VOCABULARY: Set[str] = _terms("""
        a about above after afternoon again against age aged all almost also
        always am an and any anything are around as ask at away back bad be
        because been before being between big both but by can cannot cause
        causes caused child children climb coffee could dangerous day days
        daily did difference different do does doing done down drink
        drinking during each early easy eat eating either else enough even
        evening ever every everyone everything explain fast fat fats father
        fear feel feeling feels felt female few find fine first follow food
        foods for found fried from get gets getting give given go going good
        got great had hard has have having he hear help her here high higher
        him his home hot how however hurt hurts hurting i if important in
        increase increased into is it its just keep kind know known last late
        later least less let level levels life lie light like likely little
        long look lose lot lots low lower made make makes male man many may
        maybe me meal meals mean means meaning might more morning most mother
        much must my near need needs never new next night no none normal not
        now number of off often ok okay old on once one only or other our out
        over own painful parent parents part people per please possible
        possibly prevent preventing probably problem problems put question
        questions quickly quit rate really reduce reduced reducing right run
        running safe same say see seem seems several should show since sit
        sitting slow slowly smoke smoker so some someone something sometimes
        soon stairs stand standing still stop strong such sudden suddenly
        sugar sure take taking tea tell than thanks that the their them then
        there these they thing things think this those though tight time
        times tired to today too try type types under understand until up
        upon us use used using usual usually very walk walking want was water
        way we week weeks well were what when where whether which while who
        whom whose why will with within without woman work works worse would
        wake woke sleeping year years yes yet you young your
        heat heal health healthy hearing heard hearts block blocked blocks
        cold colds cough sore sores arm arms hand hands foot head neck skin
        bone bones body fever flu virus sick sickness illness ache aches
        sharp dull burning burn tightness cramp cramps numb numbness
        tingling fall fell falling passed pass passing tomorrow tonight
        yesterday week month months hour hours minute minutes second
        seconds ago since start started starts starting stopped begin began
        end ended lasting lasts lasted whenever rarely weekly monthly twice
        nurse clinic pharmacy pharmacist recent gradually better best
        worst worse nothing anything everything anyone maybe
        women men girl boy girls boys lady ladies
        pain hurt heavy weak dose breathe breathed beat beats beating
        racing pounding skip skipping skipped fluttering flutter
        lately recently sometimes
    """, " ")

    # =========================================================
    # WORD-LEVEL PROTECTED TERMS
    # =========================================================

    PROTECTED_TOKENS: Set[str] = _terms("""
        hfref, hfpef, hfmref, ldl, hdl, bpm, mmhg, mgdl, cad, chd, chf, htn,
        afib, af, bp, hr, mi, cvd, tia, cva, rhd, ace, arb, otc, acs, ef
    """)

    # =========================================================
    # WORDS THAT GENERIC FUZZY CORRECTION MUST NOT TOUCH
    # =========================================================

    NEVER_FUZZY_CORRECT: Set[str] = _terms("""
        heart, blood, pressure, attack, failure, stroke, disease, artery,
        arteries, vein, veins, brain, chest, pain, breathing, breath,
        headache, dizziness, dizzy, swelling, faint, fainting, diabetes,
        medication, medicine, symptom, symptoms, acute, chronic, severe,
        mild, moderate, sudden, persistent, not, never, without, no
    """)

    # =========================================================
    # NEGATION / UNCERTAINTY / URGENCY
    # =========================================================

    NEGATION_TERMS: Set[str] = _terms("""
        not, no, never, without, cannot, can't, dont, doesnt, didnt, isnt,
        arent, wasnt, werent, havent, hasnt, hadnt, wont, wouldnt, couldnt,
        cant
    """)

    UNCERTAINTY_TERMS: Set[str] = _terms("""
        maybe, possibly, probably, perhaps, might, may, think, guess,
        unsure, uncertain, seems, seem, could
    """)

    URGENCY_TERMS: Set[str] = _terms("""
        sudden, suddenly, severe, severely, worst, extreme, intense, heavy,
        crushing, pressure, tightness, fainting, unconscious, collapse,
        collapsed, breathing, shortness, sweating, nausea, vomiting
    """)

    # Suffixes typical of drug names; such words are never fuzzy-corrected.
    DRUG_SUFFIXES: Tuple[str, ...] = (
        "pril", "sartan", "olol", "statin", "pine", "azole", "mycin",
        "cillin", "afil", "thiazide", "semide", "parin", "xaban", "gatran",
        "dipine", "azepam", "formin", "gliptin", "glutide", "prazole",
    )

    # =========================================================
    # HIGH-CONFIDENCE TYPO CORRECTIONS (words and phrases)
    # Keys must be lowercase. Identity entries are unnecessary.
    # =========================================================

    TYPO_CORRECTIONS: Dict[str, str] = {
        # Blood pressure
        "presure": "pressure", "pressur": "pressure", "pressue": "pressure",
        "preasure": "pressure", "presssure": "pressure",
        "presuree": "pressure", "pressrue": "pressure",

        # Hypertension
        "hypertenshion": "hypertension", "hypertention": "hypertension",
        "hypertensoin": "hypertension", "hypertenssion": "hypertension",
        "hypertenion": "hypertension", "hypertensn": "hypertension",
        "hpertensn": "hypertension",

        # Symptoms
        "symtoms": "symptoms", "symptons": "symptoms",
        "symptms": "symptoms", "symptomes": "symptoms",
        "sypmtom": "symptom",

        # Cholesterol
        "cholestrol": "cholesterol", "cholestrerol": "cholesterol",
        "cholestoral": "cholesterol", "cholesteral": "cholesterol",
        "choleserol": "cholesterol", "cholestrols": "cholesterols",

        # Atherosclerosis
        "atheroclerosis": "atherosclerosis",
        "atherosclorosis": "atherosclerosis",
        "atherosclerossis": "atherosclerosis",
        "atheroscerosis": "atherosclerosis",
        "atherosclersis": "atherosclerosis",

        # Arrhythmia
        "arrythmia": "arrhythmia", "arrythmias": "arrhythmias",
        "arrhythmiaa": "arrhythmia", "arrhytmia": "arrhythmia",
        "arrthymia": "arrhythmia", "arhythmia": "arrhythmia",
        "arhythmias": "arrhythmias",

        # Fibrillation
        "fibrilation": "fibrillation", "fibrilaton": "fibrillation",
        "fibrillatoin": "fibrillation", "fibrilitation": "fibrillation",
        "fibrillationn": "fibrillation",

        # Dizziness
        "dizzyness": "dizziness", "dizzines": "dizziness",
        "diziness": "dizziness",

        # Breathing
        "breathlesness": "breathlessness",
        "breathlessnesss": "breathlessness",
        "breathlesnes": "breathlessness",
        "breathlessnes": "breathlessness",
        "shortnes": "shortness",
        "shortness of breathe": "shortness of breath",
        "shortness of breth": "shortness of breath",
        "shortness of brath": "shortness of breath",
        "brething": "breathing", "breathng": "breathing",
        "breating": "breathing",

        # Chest pain
        "chset": "chest", "cheast": "chest", "chsst": "chest",
        "paim": "pain", "pian": "pain",

        # Coronary artery disease
        "coronry": "coronary", "coronarry": "coronary",
        "coronaryy": "coronary", "artrey": "artery", "arttery": "artery",
        "artary": "artery", "artry": "artery",

        # Heart failure
        "failur": "failure", "failue": "failure", "faillure": "failure",
        "faliure": "failure", "heartfailur": "heart failure",
        "heartfailuer": "heart failure",

        # Edema / palpitations
        "edemma": "edema", "edmea": "edema",
        "palpitaitons": "palpitations", "palpitaions": "palpitations",
        "palpatations": "palpitations", "palpitaiton": "palpitation",

        # Medication
        "medicin": "medicine", "medcine": "medicine", "medecine": "medicine",
        "medicationn": "medication", "medicaton": "medication",

        # Diagnosis / treatment / prevention
        "diagonsis": "diagnosis", "diangosis": "diagnosis",
        "diagnosys": "diagnosis",
        "treament": "treatment", "treatement": "treatment",
        "tratment": "treatment", "treatmentt": "treatment",
        "prevetion": "prevention", "preventon": "prevention",
        "preventionn": "prevention", "prevension": "prevention",
        "compication": "complication", "complicaton": "complication",
        "complicationss": "complications",

        # Risk
        "risck": "risk", "facctors": "factors", "factros": "factors",
        "riskfactor": "risk factor", "riskfactors": "risk factors",

        # Cardiovascular / circulation
        "cardiovascullar": "cardiovascular",
        "cardiovasculer": "cardiovascular",
        "cardiovasular": "cardiovascular",
        "cardiovascualr": "cardiovascular",
        "cardiovasclar": "cardiovascular",
        "cardiovascuar": "cardiovascular",
        "cardiovascual": "cardiovascular",
        "ischaemia": "ischemia", "ischemea": "ischemia", "ischemi": "ischemia",
        "ciruclation": "circulation", "circulaton": "circulation",
        "cloting": "clotting", "clotinng": "clotting",

        # Stroke / heart attack
        "strkoe": "stroke", "storke": "stroke", "stroek": "stroke",
        "strroke": "stroke", "hearrt": "heart", "attcak": "attack",
        "atack": "attack", "attck": "attack",

        # Systolic / diastolic
        "systolci": "systolic", "systolicc": "systolic",
        "systollc": "systolic", "systlic": "systolic",
        "diastolci": "diastolic", "diastolc": "diastolic",
        "diastollc": "diastolic", "diastlic": "diastolic",

        # Ejection fraction
        "ejetion": "ejection", "ejectionn": "ejection", "ejction": "ejection",
        "fracion": "fraction", "fracton": "fraction",
        "fractionn": "fraction",

        # Diabetes / triglycerides
        "diabetis": "diabetes", "diabtes": "diabetes",
        "diabeties": "diabetes",
        "triglycrides": "triglycerides", "triglycerieds": "triglycerides",

        # General medical words
        "conditon": "condition", "condtion": "condition",
        "desease": "disease", "disese": "disease", "diseasee": "disease",
        "caues": "causes", "causees": "causes", "caus": "causes",

        # Question words
        "whatt": "what", "whst": "what", "waht": "what",
        "wher": "where", "hwo": "how", "whyy": "why",
    }

    # =========================================================
    # CLINICAL VALUE PATTERN (single compiled regex)
    # Order matters: structured values first, bare numbers last.
    # =========================================================

    _VALUE_RE = re.compile(
        "|".join([
            r"\b\d{2,3}\s*/\s*\d{2,3}\b",                       # BP 160/100
            r"\b\d+(?:\.\d+)?\s*%",                             # percentages
            r"\b\d+(?:\.\d+)?\s*(?:mmhg|mg/dl|mgdl|mmol/l|bpm)\b",
            r"\b\d+(?:\.\d+)?\s*(?:kgs?|lbs?|mcg|mg|ml|g)\b",   # weight/dose
            r"\b\d+\s*(?:years?|yrs?)\s*old\b",                 # age
            r"\b\d+\s*(?:days?|weeks?|months?|years?)\b",       # duration
            r"\b\d+(?:\.\d+)?\b",                               # bare numbers
        ]),
        re.IGNORECASE,
    )

    # Unicode-aware word tokenizer. Keeps hyphen/apostrophe/slash words
    # ("a-fib", "don't", "mg/dl", "w/") as single tokens and never touches
    # digits, punctuation or placeholders.
    _WORD_RE = re.compile(r"[^\W\d_]+(?:['\-/][^\W\d_]+)*/?")

    # =========================================================
    # INITIALIZATION
    # =========================================================

    def __init__(
        self,
        model: str = "qwen3:1.7b",
        base_url: Optional[str] = None,
        timeout: int = 30,
        enable_llm: bool = True,
        verbose: bool = True,
    ):
        self.model = model
        self.base_url = (
            base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        ).rstrip("/")
        self.timeout = timeout
        self.enable_llm = enable_llm and requests is not None
        self.verbose = verbose

        # Single-word medical vocabulary (phrases contribute their words).
        all_terms = (
            self.MEDICAL_VOCABULARY | self.EXTRA_MEDICAL_LEXICON | self.DRUG_NAMES
        )
        medical_words: Set[str] = set()
        phrase_filler: Set[str] = set()
        for term in all_terms:
            if " " not in term:
                medical_words.add(term)
            else:
                # Short words inside phrases ("left", "test") are treated
                # as ordinary English so they get no medical bonus.
                for part in term.split():
                    (medical_words if len(part) >= 5 else phrase_filler).add(part)
        self._medical_words: Set[str] = {w for w in medical_words if w}
        self._drug_words: Set[str] = {d for d in self.DRUG_NAMES if " " not in d}
        self._context_words: Set[str] = set(self.CONTEXT_WORDS)

        self._common_words: Set[str] = {
            w
            for w in (self.COMMON_VOCABULARY | phrase_filler)
            if w and w not in self._medical_words
        }

        # Candidate pool for fuzzy matching.
        self._vocabulary: Set[str] = self._medical_words | self._common_words

        # Everything that counts as "already a valid word".
        known: Set[str] = set(self._vocabulary)
        known |= {a.lower() for a in self.MEDICAL_ABBREVIATIONS}
        known |= self.PROTECTED_TOKENS
        for expansion in self.MEDICAL_ABBREVIATIONS.values():
            known.add(expansion.lower())
            known.update(expansion.lower().split())
        for expansion in self.TEXT_NORMALIZATIONS.values():
            known.update(expansion.lower().split())
        known |= set(self.TYPO_CORRECTIONS.values())
        self._known: Set[str] = known

        # Compiled typo regex (longest keys first).
        keys = sorted(self.TYPO_CORRECTIONS, key=len, reverse=True)
        self._typo_regex = re.compile(
            r"(?<![A-Za-z0-9])(?:"
            + "|".join(re.escape(k) for k in keys)
            + r")(?![A-Za-z0-9])",
            re.IGNORECASE,
        )

        # Compiled abbreviation regex (longest keys first).
        abbrs = sorted(self.MEDICAL_ABBREVIATIONS, key=len, reverse=True)
        self._abbr_regex = re.compile(
            r"(?<![A-Za-z0-9])(?:"
            + "|".join(re.escape(a) for a in abbrs)
            + r")(?![A-Za-z0-9])",
            re.IGNORECASE,
        )

    def _log(self, message: str) -> None:
        if self.verbose:
            print(f"[NORMALIZER] {message}")

    # =========================================================
    # PUBLIC API
    # =========================================================

    def normalize_query(self, query: str, allow_llm: bool = True) -> str:
        """
        Normalize a user query while preserving meaning.

        Never returns None. On any internal failure the original query is
        returned unchanged.
        """
        if not isinstance(query, str):
            raise TypeError("Query must be a string.")

        original = query.strip()
        if not original:
            return ""

        start = time.perf_counter()

        try:
            normalized = self._deterministic_pipeline(original)
        except Exception as exc:  # never crash the application
            self._log(f"Deterministic pipeline failed: {type(exc).__name__}: {exc}")
            return original

        valid = self._preserves_important_content(original, normalized)

        if not valid:
            self._log(
                "Deterministic result rejected by validation: "
                f"{original!r} -> {normalized!r}"
            )

        use_llm = (
            allow_llm
            and self.enable_llm
            and (not valid or self._has_unresolved_noise(normalized))
        )

        if use_llm:
            candidate = normalized if valid else original
            llm_result = self._normalize_with_llm(original, candidate)
            if llm_result and self._preserves_important_content(
                original, llm_result
            ):
                self._log(f"LLM normalization: {original!r} -> {llm_result!r}")
                return llm_result

        result = normalized if valid else original

        elapsed = time.perf_counter() - start
        if result != original:
            self._log(f"{original!r} -> {result!r}")
        else:
            self._log("Query already normalized.")
        self._log(f"Completed in {elapsed:.3f}s")
        return result

    def _deterministic_pipeline(self, original: str) -> str:
        cleaned = self._basic_cleanup(original)

        # Decide medical context BEFORE values become placeholders.
        medical_context = self._looks_like_medical_context(
            self._correct_medical_phrases(cleaned)
        )

        if medical_context:
            cleaned = self._normalize_bp_phrases(cleaned)

        protected, values = self._protect_clinical_values(cleaned)
        text = self._normalize_text(protected)
        text = self._expand_medical_abbreviations(text, medical_context)
        text = self._correct_spelling(text)
        text = self._restore_protected_values(text, values)
        return self._final_cleanup(text)

    # =========================================================
    # BASIC CLEANUP / PROTECTION / RESTORE
    # =========================================================

    def _basic_cleanup(self, text: str) -> str:
        text = text.replace("\u2019", "'").replace("\u2018", "'")
        text = text.replace("\u201c", '"').replace("\u201d", '"')
        # Remove zero-width characters and our private placeholder chars.
        text = re.sub(r"[\u200b\u200c\u200d\ufeff\ue000\ue001]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    def _normalize_bp_phrases(self, text: str) -> str:
        """'150 over 95' / '150 ovr 95' -> '150/95' (numbers unchanged)."""
        return re.sub(
            r"\b(\d{2,3})\s*(?:over|ovr)\s*(\d{2,3})\b",
            r"\1/\2",
            text,
            flags=re.IGNORECASE,
        )

    def _protect_clinical_values(self, text: str) -> Tuple[str, List[str]]:
        values: List[str] = []

        def repl(match: re.Match) -> str:
            values.append(match.group(0))
            return f" {_PH_OPEN}{len(values) - 1}{_PH_CLOSE} "

        return self._VALUE_RE.sub(repl, text), values

    def _restore_protected_values(self, text: str, values: List[str]) -> str:
        def repl(match: re.Match) -> str:
            index = int(match.group(1))
            return values[index] if index < len(values) else ""

        return _PLACEHOLDER_RE.sub(repl, text)

    def _final_cleanup(self, text: str) -> str:
        text = re.sub(r"[\ue000\ue001]", "", text)
        text = re.sub(r"\s+([?.!,;:)\]])", r"\1", text)
        text = re.sub(r"([(\[])\s+", r"\1", text)
        text = re.sub(r"([?!])\1+", r"\1", text)
        text = re.sub(r"([.,;:])\1+", r"\1", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    # =========================================================
    # TYPO / TEXT NORMALIZATION
    # =========================================================

    def _correct_medical_phrases(self, query: str) -> str:
        """Apply high-confidence word and phrase typo corrections."""
        return self._typo_regex.sub(
            lambda m: self.TYPO_CORRECTIONS[m.group(0).lower()], query
        )

    def _explicit_word_correction(self, word: str) -> Optional[str]:
        """High-confidence single-word correction, if any."""
        correction = self.TYPO_CORRECTIONS.get(word.lower())
        if correction and " " not in correction:
            return correction
        return None

    def _collapse_repeats(self, word: str) -> str:
        """
        Collapse stretched letters: "whhhat" -> "what", "pleeease" -> "please".
        Prefers a variant that is a known word; otherwise keeps double letters.
        """
        pattern = r"(.)\1{2,}"
        if not re.search(pattern, word):
            return word

        single = re.sub(pattern, r"\1", word)
        double = re.sub(pattern, r"\1\1", word)

        for variant in (single, double):
            lower = variant.lower()
            if self._is_known(lower) or lower in self.TEXT_NORMALIZATIONS:
                return variant
        return double

    def _normalize_text(self, query: str) -> str:
        query = self._correct_medical_phrases(query)
        query = re.sub(
            r"\by\b(?=\s+(?:do|does|did|is|are|am|can|cant|cannot|would|"
            r"should|dont|doesnt|isnt)\b)",
            "why",
            query,
            flags=re.IGNORECASE,
        )

        def repl(match: re.Match) -> str:
            word = self._collapse_repeats(match.group(0))
            replacement = self.TEXT_NORMALIZATIONS.get(word.lower())
            return replacement if replacement is not None else word

        result = self._WORD_RE.sub(repl, query)
        return re.sub(r"\s+", " ", result).strip()

    # =========================================================
    # ABBREVIATION EXPANSION
    # =========================================================

    def _looks_like_medical_context(self, query: str) -> bool:
        """True when there is enough medical context for ambiguous abbreviations."""
        lower = query.lower()

        markers = (
            "heart", "blood", "pressure", "chest", "pain", "symptom",
            "disease", "hypertension", "cholesterol", "artery", "stroke",
            "breath", "dizz", "palpitation", "medication", "medicine",
            "doctor", "diagnos", "treatment", "systolic", "diastolic",
            "ejection", "cardiac", "cardio", "pulse", "fibrillation",
            "failure", "angina", "lipid", "triglycerid", "sweat", "nause",
            "vomit", "faint", "swell", "swollen", "fatigue", "palpit",
            "infarct", "valve", "ventric", "atrial", "aort", "embol",
            "thromb", "tachy", "brady", "ecg", "ekg", "lightheaded",
            "cough", "ankle", "anticoag", "statin", "cardio",
        )
        score = sum(
            1 for m in markers if re.search(r"(?<![a-z])" + m, lower)
        )

        if re.search(r"\b\d{2,3}\s*/\s*\d{2,3}\b", lower):
            score += 2
        if re.search(r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|bpm|mmhg|mg/dl)\b", lower):
            score += 2
        if re.search(r"\b(?:ef|lvef)\b[^.?!]*\d+(?:\.\d+)?\s*%", lower):
            score += 2
        if re.search(r"\b(?:sys|dia|sbp|dbp)\b[^.?!]*\d", lower):
            score += 2
        if re.search(r"\b(?:bp|hbp|htn|chf|cad|afib|hfref|hfpef)\b", lower):
            score += 1

        return score >= 1

    def _expand_medical_abbreviations(
        self,
        query: str,
        medical_context: Optional[bool] = None,
    ) -> str:
        """
        Expand medical abbreviations. Ambiguous ones (hr, mi, ef, ...) are
        expanded only when the query has medical context.
        """
        context = bool(medical_context) or self._looks_like_medical_context(query)
        definition = self._is_definition_query(query)

        def repl(match: re.Match) -> str:
            key = match.group(0).lower()
            if key in self.AMBIGUOUS_ABBREVIATIONS:
                allowed = context or (
                    definition and key not in self.DEFINITION_UNSAFE
                )
                if not allowed:
                    return match.group(0)
                # "6 hr" is hours, not heart rate.
                if key == "hr" and re.search(
                    r"(?:\d|" + _PH_CLOSE + r")\s*$", query[:match.start()]
                ):
                    return match.group(0)
            return self.MEDICAL_ABBREVIATIONS.get(key, match.group(0))

        return self._abbr_regex.sub(repl, query)

    _DEFINITION_RE = re.compile(
        r"^\s*(?:what is|what are|what does|what do|define|meaning of|"
        r"explain|tell me about)\b",
        re.IGNORECASE,
    )

    def _is_definition_query(self, text: str) -> bool:
        """Short 'what is X' style question."""
        plain = re.sub(r"[\ue000\ue001\d]", "", text)
        return bool(self._DEFINITION_RE.match(plain)) and (
            len(re.findall(r"[^\W_]+", plain)) <= 7
        )

    # =========================================================
    # SPELLING CORRECTION
    # =========================================================

    def _is_known(self, word: str) -> bool:
        """Known word, or a simple inflection of a known word."""
        if word in self._known:
            return True

        for suffix in ("ies",):
            if word.endswith(suffix) and word[: -len(suffix)] + "y" in self._known:
                return True
        for suffix in ("s", "es", "ed", "d", "ing", "ly", "er", "est"):
            if not (
                word.endswith(suffix)
                and len(word) - len(suffix) >= 3
                and word[: -len(suffix)] in self._known
            ):
                continue
            stem = word[: -len(suffix)]
            # Short consonant-vowel-consonant stems double their last
            # letter (skip -> skipping), so "skiping" is a typo, not a word.
            if (
                suffix in ("ing", "ed", "er", "est")
                and len(stem) <= 4
                and re.search(r"[^aeiou][aeiou][^aeiouwxy]$", stem)
            ):
                continue
            return True
        return False

    def _looks_like_drug(self, word: str) -> bool:
        return len(word) >= 7 and word.endswith(self.DRUG_SUFFIXES)

    def _restore_word_case(self, original: str, corrected: str) -> str:
        if not original:
            return corrected
        if len(original) > 1 and original.isupper():
            return corrected.upper()
        if original.istitle():
            return corrected.capitalize()
        return corrected

    def _correct_spelling(self, query: str) -> str:
        """
        Deterministic spelling correction.

        Order: known word -> protected -> explicit typo -> conservative
        contextual fuzzy match (medical vocabulary preferred).
        """
        query = self._correct_medical_phrases(query)

        matches = list(self._WORD_RE.finditer(query))
        lowers = [m.group(0).lower() for m in matches]

        pieces: List[str] = []
        last = 0

        for i, match in enumerate(matches):
            pieces.append(query[last:match.start()])
            token = match.group(0)

            preceding = query[:match.start()].rstrip()
            sentence_start = (not preceding) or preceding[-1] in ".?!"

            previous_word = lowers[i - 1] if i > 0 else ""
            next_word = lowers[i + 1] if i + 1 < len(lowers) else ""

            pieces.append(
                self._correct_word(token, previous_word, next_word, sentence_start)
            )
            last = match.end()

        pieces.append(query[last:])
        return "".join(pieces)

    def _correct_word(
        self,
        token: str,
        previous_word: str,
        next_word: str,
        sentence_start: bool,
    ) -> str:
        lower = token.lower()

        # Hyphen / apostrophe / slash words are left alone.
        if any(c in lower for c in "'-/"):
            return token

        # Very short words are too ambiguous for fuzzy matching.
        if len(lower) <= 3:
            return token

        if self._is_known(lower):
            return token

        if lower in self.PROTECTED_TOKENS or lower in self.NEVER_FUZZY_CORRECT:
            return token

        explicit = self._explicit_word_correction(lower)
        if explicit is not None:
            return self._restore_word_case(token, explicit)

        # Abbreviations typed in caps, or mixed-case tokens (brand names).
        if token.isupper() or any(c.isupper() for c in token[1:]):
            return token

        # Capitalised mid-sentence words are probably proper nouns / brands.
        if token[0].isupper() and not sentence_start:
            return token

        if self._looks_like_drug(lower):
            drug = self._find_drug_candidate(lower)
            return self._restore_word_case(token, drug) if drug else token

        # Run-together words: "bloodpressure" -> "blood pressure".
        split = self._split_compound(lower)
        if split:
            return split

        if len(lower) == 4:
            # 4-letter words are too ambiguous, unless a strong medical
            # neighbour makes the intent clear ("hart attack", "blod pressure").
            if (
                previous_word not in self._context_words
                and next_word not in self._context_words
            ):
                return token
            candidate = self._find_contextual_spelling_candidate(
                lower, previous_word, next_word, medical_only=True
            )
        else:
            candidate = self._find_contextual_spelling_candidate(
                lower, previous_word, next_word
            )

        if candidate is None:
            return token
        return self._restore_word_case(token, candidate)

    def _find_drug_candidate(self, word: str) -> Optional[str]:
        """Fix a typo of a KNOWN drug name; unknown drugs are left alone."""
        scored: List[Tuple[int, str]] = []
        for drug in self._drug_words:
            if drug[0] != word[0] or abs(len(drug) - len(word)) > 2:
                continue
            distance = self._levenshtein_distance(word, drug)
            if distance <= 2:
                scored.append((distance, drug))
        if not scored:
            return None
        scored.sort()
        if len(scored) > 1 and scored[0][0] == scored[1][0]:
            return None  # ambiguous
        return scored[0][1]

    def _split_compound(self, word: str) -> Optional[str]:
        """Split a run-together word into 2-3 known words, if unambiguous."""
        n = len(word)
        if n < 7 or n > 30:
            return None

        best: List[Optional[List[str]]] = [None] * (n + 1)
        best[0] = []
        for i in range(1, n + 1):
            for j in range(max(0, i - 20), i):
                prefix = best[j]
                if prefix is None:
                    continue
                piece = word[j:i]
                if len(piece) < 3 or piece not in self._vocabulary:
                    continue
                candidate = prefix + [piece]
                if len(candidate) > 3:
                    continue
                if best[i] is None or len(candidate) < len(best[i]):
                    best[i] = candidate

        result = best[n]
        if (
            result
            and len(result) >= 2
            and any(p in self._medical_words and len(p) >= 4 for p in result)
        ):
            return " ".join(result)
        return None

    @staticmethod
    def _levenshtein_distance(a: str, b: str) -> int:
        """Optimal string alignment distance (adjacent transpositions = 1)."""
        if a == b:
            return 0
        if not a:
            return len(b)
        if not b:
            return len(a)

        rows = len(a) + 1
        cols = len(b) + 1
        d = [[0] * cols for _ in range(rows)]
        for i in range(rows):
            d[i][0] = i
        for j in range(cols):
            d[0][j] = j

        for i in range(1, rows):
            for j in range(1, cols):
                cost = 0 if a[i - 1] == b[j - 1] else 1
                d[i][j] = min(
                    d[i - 1][j] + 1,
                    d[i][j - 1] + 1,
                    d[i - 1][j - 1] + cost,
                )
                if (
                    i > 1
                    and j > 1
                    and a[i - 1] == b[j - 2]
                    and a[i - 2] == b[j - 1]
                ):
                    d[i][j] = min(d[i][j], d[i - 2][j - 2] + 1)
        return d[-1][-1]

    @staticmethod
    def _allowed_edit_distance(word: str) -> int:
        n = len(word)
        if n <= 6:
            return 1
        if n <= 10:
            return 2
        return 3

    @staticmethod
    def _is_morphology_risk(source: str, candidate: str) -> bool:
        for suffix in ("s", "es", "ed", "ing", "ly", "er"):
            if candidate == source + suffix or source == candidate + suffix:
                return True
        return False

    def _score_spelling_candidate(
        self,
        source: str,
        candidate: str,
        previous_word: str = "",
        next_word: str = "",
    ) -> float:
        source = source.lower()
        candidate = candidate.lower()

        if source == candidate:
            return 100.0

        distance = self._levenshtein_distance(source, candidate)
        score = 0.0

        if distance == 1:
            score += 5.0
        elif distance == 2:
            score += 3.5
        elif distance == 3:
            score += 1.5

        # A single edit in a longer word is a strong typo signal.
        if distance == 1 and len(source) >= 6:
            score += 1.0

        length_difference = abs(len(source) - len(candidate))
        if length_difference == 0:
            score += 2.0
        elif length_difference == 1:
            score += 1.0

        common_prefix = 0
        for x, y in zip(source, candidate):
            if x != y:
                break
            common_prefix += 1
        if common_prefix >= 3:
            score += 1.5
        elif common_prefix >= 2:
            score += 0.5

        common_suffix = 0
        for x, y in zip(reversed(source), reversed(candidate)):
            if x != y:
                break
            common_suffix += 1
        if common_suffix >= 3:
            score += 1.0
        elif common_suffix >= 2:
            score += 0.5

        context_words = self._context_words
        if previous_word in context_words or next_word in context_words:
            score += 2.0

        # Medical vocabulary priority (applied exactly once).
        if candidate in self._medical_words:
            score += 2.5

        if self._is_morphology_risk(source, candidate):
            score -= 3.0

        return score

    def _find_contextual_spelling_candidate(
        self,
        word: str,
        previous_word: str = "",
        next_word: str = "",
        medical_only: bool = False,
    ) -> Optional[str]:
        """
        Find a safe correction, or None.

        Safety rules: same first letter, bounded edit distance, minimum
        score, and no answer when two candidates are nearly tied.
        """
        word = word.lower()
        if not word or word in self.PROTECTED_TOKENS:
            return None
        if word in self.NEVER_FUZZY_CORRECT:
            return None

        explicit = self._explicit_word_correction(word)
        if explicit:
            return explicit

        allowed = self._allowed_edit_distance(word)
        scored: List[Tuple[float, str]] = []

        pool = self._medical_words if medical_only else self._vocabulary
        for candidate in pool:
            if candidate[0] != word[0]:
                continue
            if abs(len(candidate) - len(word)) > allowed:
                continue
            if self._levenshtein_distance(word, candidate) > allowed:
                continue
            score = self._score_spelling_candidate(
                word, candidate, previous_word, next_word
            )
            scored.append((score, candidate))

        if not scored:
            return None

        scored.sort(key=lambda item: (-item[0], item[1]))
        best_score, best_candidate = scored[0]

        if best_score < self.MIN_FUZZY_SCORE:
            return None

        # Ambiguous: two different candidates are practically tied.
        if len(scored) > 1 and best_score - scored[1][0] < 0.5:
            return None

        return best_candidate

    # =========================================================
    # UNRESOLVED NOISE DETECTION (decides whether to try the LLM)
    # =========================================================

    _MEDICAL_STEM_RE = re.compile(
        r"itis|emia|pathy|cardi|osis|ectomy|plasty|stenosis|tensi|ology|"
        r"ogram|graphy|thromb|ischem|infarct|vascul|arteri|ventric|atrial|"
        r"aort|angi|embol|fibril|lipid|cholest"
    )

    def _has_unresolved_noise(self, text: str) -> bool:
        """
        Decide whether the deterministic result still contains words the
        LLM fallback should look at.

        Triggers when:
          (a) many words are unrecognised, or
          (b) an unrecognised word sits next to a strong medical word,
              looks medical (medical stem), or is the subject of a
              definition-style question.
        """
        matches = list(self._WORD_RE.finditer(text))
        words = [m.group(0) for m in matches]
        if not words:
            return False
        lowers = [w.lower() for w in words]
        definition = self._is_definition_query(text)

        unknown: List[int] = []
        for i, (word, lower) in enumerate(zip(words, lowers)):
            if len(lower) < 4 or self._is_known(lower):
                continue
            if word.isupper() or any(c in lower for c in "'-/"):
                continue
            if self._looks_like_drug(lower):
                continue
            if word[0].isupper() and i > 0:
                continue
            unknown.append(i)

        if not unknown:
            return False

        if (
            len(unknown) >= self.UNRESOLVED_MIN_WORDS
            and len(unknown) / len(words) >= self.UNRESOLVED_MIN_RATIO
        ):
            return True

        for i in unknown:
            lower = lowers[i]
            prev_word = lowers[i - 1] if i > 0 else ""
            next_word = lowers[i + 1] if i + 1 < len(lowers) else ""
            if prev_word in self._context_words or next_word in self._context_words:
                return True
            if len(lower) >= 6 and self._MEDICAL_STEM_RE.search(lower):
                return True
            if definition:
                return True
        return False

    # =========================================================
    # HARDENED LLM FALLBACK
    # =========================================================

    def _normalize_with_llm(
        self,
        query: str,
        deterministic_candidate: str,
    ) -> Optional[str]:
        """
        Language-cleaning fallback using a local Ollama model.

        Its output is ALWAYS re-validated by the caller. It is not allowed
        to answer, diagnose, add or remove information.
        """
        if not self.enable_llm or requests is None:
            return None
        if not query.strip():
            return None

        safety_context = ", ".join(self._extract_safety_terms(query))

        prompt = f"""
You are a text normalization component.

Your ONLY task is to rewrite the user's query into clear, natural English
while preserving exactly what the user meant.

DO NOT answer the question.
DO NOT provide medical advice.
DO NOT diagnose.
DO NOT add information.
DO NOT remove information.

DO NOT change: numbers, blood pressure readings, doses, percentages,
units, symptoms, negation, uncertainty, urgency, medication names,
medical conditions.

The deterministic normalizer already produced this candidate:

{deterministic_candidate}

The original user query is:

{query}

Important safety-sensitive terms detected:

{safety_context}

Return ONLY valid JSON:

{{"normalized_query": "..."}}

If the candidate is already clear, return it unchanged.
If you are uncertain about a correction, keep the original word.
""".strip()

        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "format": "json",
            "options": {"temperature": 0, "num_ctx": 1536, "num_predict": 180},
            "think": False,
            "keep_alive": "5m",
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=min(max(self.timeout, 3), 15),
            )
            response.raise_for_status()

            raw_response = response.json().get("response", "")
            if not isinstance(raw_response, str):
                return None

            parsed = self._parse_json_response(raw_response)
            if not parsed:
                return None

            candidate = parsed.get("normalized_query")
            if not isinstance(candidate, str):
                return None

            candidate = candidate.strip()
            if not candidate:
                return None

            # Reject answers, unless the user's own query already contained
            # that kind of language (e.g. "should I stop taking my meds?").
            if self._looks_like_an_answer(candidate) and not (
                self._looks_like_an_answer(query)
            ):
                self._log("LLM output rejected: appears to answer the question.")
                return None

            if len(candidate) > max(len(query) * 3, 500):
                self._log("LLM output rejected: unexpectedly long.")
                return None

            return candidate

        except Exception as exc:  # network, JSON, anything
            self._log(f"LLM fallback unavailable: {type(exc).__name__}")
            return None

    def _parse_json_response(self, raw_response: str) -> Optional[Dict[str, Any]]:
        """Parse an LLM JSON response defensively."""
        if not raw_response:
            return None

        text = raw_response.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text).strip()

        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end <= start:
            return None

        try:
            parsed = json.loads(text[start:end + 1])
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            return None
        return None

    # =========================================================
    # SEMANTIC PRESERVATION
    # =========================================================

    def _preserves_important_content(self, original: str, normalized: str) -> bool:
        """
        Conservative gate: accept a normalization only if important clinical
        information survives. (Answer-detection is applied only to LLM
        output, never here, so legitimate queries like "i take 5 mg X"
        are not rejected.)
        """
        if not isinstance(original, str) or not isinstance(normalized, str):
            return False

        original = original.strip()
        normalized = normalized.strip()

        if not original:
            return not normalized
        if not normalized:
            return False

        o = original.lower()
        n = normalized.lower()

        checks = (
            self._preserves_numbers,
            self._preserves_measurements,
            self._preserves_negation,
            self._preserves_uncertainty,
            self._preserves_urgency,
            self._preserves_medical_concepts,
            self._preserves_symptoms,
            self._preserves_medication_information,
            self._passes_length_sanity_check,
        )
        return all(check(o, n) for check in checks)

    def _preserves_numbers(self, original: str, normalized: str) -> bool:
        pattern = r"\b\d+(?:\.\d+)?\b"
        needed = Counter(re.findall(pattern, original))
        have = Counter(re.findall(pattern, normalized))
        return all(have[num] >= count for num, count in needed.items())

    def _preserves_measurements(self, original: str, normalized: str) -> bool:
        compact_n = re.sub(r"\s+", "", normalized)

        # Blood pressure readings
        for value in re.findall(r"\b\d{2,3}\s*/\s*\d{2,3}\b", original):
            if re.sub(r"\s+", "", value) not in compact_n:
                return False

        # Percentages
        for value in re.findall(r"\b\d+(?:\.\d+)?\s*%", original):
            if re.sub(r"\s+", "", value) not in compact_n:
                return False

        # Doses / units
        unit_patterns = (
            r"\b\d+(?:\.\d+)?\s*mg\b",
            r"\b\d+(?:\.\d+)?\s*mcg\b",
            r"\b\d+(?:\.\d+)?\s*g\b",
            r"\b\d+(?:\.\d+)?\s*ml\b",
            r"\b\d+(?:\.\d+)?\s*kgs?\b",
            r"\b\d+(?:\.\d+)?\s*lbs?\b",
            r"\b\d+(?:\.\d+)?\s*bpm\b",
            r"\b\d+(?:\.\d+)?\s*mmhg\b",
            r"\b\d+(?:\.\d+)?\s*mg/dl\b",
            r"\b\d+(?:\.\d+)?\s*mmol/l\b",
        )
        for pattern in unit_patterns:
            for value in re.findall(pattern, original):
                if re.sub(r"\s+", "", value) not in compact_n:
                    return False
        return True

    _NEGATION_PATTERNS: Dict[str, Tuple[str, ...]] = {
        "not": (r"\bnot\b", r"\bnever\b", r"\bwithout\b"),
        "no": (r"\bno\b",),
        "do_not": (r"\bdon['\u2019]?t\b", r"\bdo\s+not\b"),
        "does_not": (r"\bdoesn['\u2019]?t\b", r"\bdoes\s+not\b"),
        "did_not": (r"\bdidn['\u2019]?t\b", r"\bdid\s+not\b"),
        "cannot": (r"\bcan['\u2019]?t\b", r"\bcannot\b"),
        "will_not": (r"\bwon['\u2019]?t\b", r"\bwill\s+not\b"),
    }

    def _extract_negation_signature(self, text: str) -> Counter:
        signature: Counter = Counter()
        for category, patterns in self._NEGATION_PATTERNS.items():
            for pattern in patterns:
                signature[category] += len(
                    re.findall(pattern, text, flags=re.IGNORECASE)
                )
        return signature

    def _preserves_negation(self, original: str, normalized: str) -> bool:
        o = self._extract_negation_signature(original)
        n = self._extract_negation_signature(normalized)
        return all(n[category] >= count for category, count in o.items())

    def _preserves_uncertainty(self, original: str, normalized: str) -> bool:
        for marker in self.UNCERTAINTY_TERMS:
            if self._contains_term(original, marker) and not self._contains_term(
                normalized, marker
            ):
                return False
        return True

    def _preserves_urgency(self, original: str, normalized: str) -> bool:
        for term in self.URGENCY_TERMS:
            if self._contains_term(original, term) and not self._contains_term(
                normalized, term
            ):
                return False
        return True

    _CONCEPT_GROUPS: Tuple[Tuple[str, ...], ...] = (
        ("blood pressure", "bp"),
        ("high blood pressure", "hypertension", "htn"),
        ("heart failure", "hf", "chf"),
        ("atrial fibrillation", "afib", "a-fib", "af"),
        ("coronary artery disease", "cad"),
        ("coronary heart disease", "chd"),
        ("heart attack", "mi"),
        ("stroke", "cva"),
        ("transient ischemic attack", "tia"),
        ("peripheral artery disease", "pad"),
        ("rheumatic heart disease", "rhd"),
        ("shortness of breath", "sob", "breathlessness"),
        ("chest pain", "cp"),
        ("symptoms", "symptom", "sx"),
        ("low-density lipoprotein", "ldl"),
        ("high-density lipoprotein", "hdl"),
        ("ejection fraction", "ef"),
    )

    def _preserves_medical_concepts(self, original: str, normalized: str) -> bool:
        for group in self._CONCEPT_GROUPS:
            if any(self._contains_term(original, t) for t in group):
                if not any(self._contains_term(normalized, t) for t in group):
                    return False
        return True

    def _contains_term(self, text: str, term: str) -> bool:
        pattern = r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])"
        return bool(re.search(pattern, text, flags=re.IGNORECASE))

    _SYMPTOM_GROUPS: Tuple[Tuple[str, ...], ...] = (
        ("chest pain", "chest pressure", "chest tightness"),
        ("shortness of breath", "breathlessness"),
        ("dizziness", "dizzy"),
        ("fainting", "faint"),
        ("swelling", "edema"),
        ("palpitations",),
        ("headache",),
        ("nausea",),
        ("vomiting",),
        ("sweating",),
        ("fatigue",),
        ("weakness",),
        ("confusion",),
    )

    def _preserves_symptoms(self, original: str, normalized: str) -> bool:
        for group in self._SYMPTOM_GROUPS:
            if any(self._contains_term(original, s) for s in group):
                if not any(self._contains_term(normalized, s) for s in group):
                    return False
        return True

    _MEDICATION_TERMS: Tuple[str, ...] = (
        "medication", "medications", "medicine", "med", "meds",
        "prescription", "rx", "amlodipine", "lisinopril", "losartan",
        "valsartan", "atenolol", "metoprolol", "aspirin", "warfarin",
        "clopidogrel", "atorvastatin", "rosuvastatin", "simvastatin",
        "furosemide", "hydrochlorothiazide", "spironolactone",
    )

    def _preserves_medication_information(
        self, original: str, normalized: str
    ) -> bool:
        for medication in self._MEDICATION_TERMS:
            if not self._contains_term(original, medication):
                continue
            if self._contains_term(normalized, medication):
                continue
            if medication in ("med", "meds") and (
                self._contains_term(normalized, "medication")
                or self._contains_term(normalized, "medications")
            ):
                continue
            if medication == "rx" and self._contains_term(
                normalized, "prescription"
            ):
                continue
            return False
        return True

    def _passes_length_sanity_check(self, original: str, normalized: str) -> bool:
        original_words = re.findall(r"\b\w+\b", original)
        normalized_words = re.findall(r"\b\w+\b", normalized)

        if not original_words:
            return not normalized_words
        if len(original_words) <= 5:
            return True

        minimum = max(3, int(len(original_words) * 0.45))
        return len(normalized_words) >= minimum

    # =========================================================
    # SAFETY TERM EXTRACTION / ANSWER DETECTION (LLM path only)
    # =========================================================

    def _extract_safety_terms(self, query: str) -> List[str]:
        lower = query.lower()
        groups = (
            self.NEGATION_TERMS,
            self.UNCERTAINTY_TERMS,
            self.URGENCY_TERMS,
            self.MEDICAL_VOCABULARY,
        )
        seen: Set[str] = set()
        terms: List[str] = []
        for group in groups:
            for term in sorted(group):
                if term not in seen and self._contains_term(lower, term):
                    seen.add(term)
                    terms.append(term)
        return terms

    def _looks_like_an_answer(self, text: str) -> bool:
        lower = text.lower().strip()
        if not lower:
            return False

        answer_prefixes = (
            "you should", "you need to", "you may want to", "you can take",
            "i recommend", "i would recommend", "this means",
            "this is caused by", "the answer is", "you likely have",
            "you probably have", "you may have", "this could be",
            "seek medical attention", "go to the emergency room",
        )
        if lower.startswith(answer_prefixes):
            return True

        recommendation_patterns = (
            r"\byou should\b", r"\byou need to\b", r"\byou ought to\b",
            r"\bi recommend\b", r"\bi suggest\b", r"\btake \d+",
            r"\bincrease your\b", r"\bdecrease your\b", r"\bstop taking\b",
            r"\bstart taking\b", r"\bseek emergency\b",
        )
        if any(re.search(p, lower) for p in recommendation_patterns):
            return True

        return len(re.findall(r"[.!?]+", lower)) >= 3

    # =========================================================
    # SELF TEST
    # =========================================================

    def run_self_test(self) -> Dict[str, Any]:
        """Run deterministic internal tests (LLM disabled)."""
        test_cases = [
            ("wat is high blood presure?", "what is high blood pressure?"),
            ("what causes hbp?", "what causes high blood pressure?"),
            ("what are symtoms of hypertenshion?",
             "what are symptoms of hypertension?"),
            ("what is AFib?", "what is atrial fibrillation?"),
            ("what is CAD?", "what is coronary artery disease?"),
            ("what is CHF?", "what is heart failure?"),
            ("how do i lower bp?", "how do i lower blood pressure?"),
            ("wht is chf n wht r symtoms?",
             "what is heart failure and what are symptoms?"),
            ("I dont have chest pain but I feel dizzy",
             "I do not have chest pain but I feel dizzy"),
            ("my bp is 160/100 mmHg", "my blood pressure is 160/100 mmHg"),
            ("my hr is 110 bpm", "my heart rate is 110 bpm"),
            ("i take 5 mg amlodipine", "i take 5 mg amlodipine"),
            ("my ef is 35%", "my ejection fraction is 35%"),
            ("I feel ill", "I feel ill"),
            ("whhhat are the symtoms of hypertenshion???",
             "what are the symptoms of hypertension?"),
            ("can medicine xyzabc lower blood pressure?",
             "can medicine xyzabc lower blood pressure?"),
            ("what is tachycardya", "what is tachycardia"),
            ("high blod presure", "high blood pressure"),
            ("how to lower my bloodpressure", "how to lower my blood pressure"),
            ("my bp is 150 over 95", "my blood pressure is 150/95"),
            ("what is SVT?", "what is supraventricular tachycardia?"),
            ("i take metaprolol", "i take metoprolol"),
        ]

        passed = 0
        failed: List[Dict[str, str]] = []

        for original, expected in test_cases:
            actual = self.normalize_query(original, allow_llm=False)
            if actual == expected:
                passed += 1
            else:
                failed.append(
                    {"input": original, "expected": expected, "actual": actual}
                )

        return {
            "passed": passed,
            "total": len(test_cases),
            "failed": failed,
            "success": not failed,
        }


# =============================================================
# DEFAULT NORMALIZER
# =============================================================

_default_normalizer = QueryNormalizer()


def normalize_query(query: str) -> str:
    """
    Public convenience function.

    Keeps the rest of CardioGuide independent from the normalizer
    implementation.
    """
    return _default_normalizer.normalize_query(query)


# =============================================================
# MANUAL TESTING
# =============================================================

if __name__ == "__main__":
    normalizer = QueryNormalizer(enable_llm=False, verbose=False)

    test_queries = [
        "wat is high blood presure?",
        "wht r symptms of high blood presure?",
        "what causes hbp?",
        "how do i lower bp?",
        "what is AFib?",
        "what is CAD?",
        "what is CHF?",
        "what is HFrEF?",
        "what is HFpEF?",
        "wht is chf n wht r symtoms?",
        "my bp is 160/100 mmHg",
        "my hr is 110 bpm",
        "i take 5 mg amlodipine",
        "my ef is 35%",
        "I dont have chest pain but I feel dizzy",
        "whhhat are the symtoms of hypertenshion???",
        "wat r the symptms of high blood presure",
        "could high cholestrol cause heart disease?",
        "can medicine xyzabc lower blood pressure?",
    ]

    print("=" * 80)
    print("CARDIOGUIDE QUERY NORMALIZER")
    print("=" * 80)

    for q in test_queries:
        print()
        print("INPUT:     ", q)
        print("NORMALIZED:", normalizer.normalize_query(q, allow_llm=False))

    print()
    print("=" * 80)
    print("SELF TEST RESULT")
    print("=" * 80)

    result = normalizer.run_self_test()
    print(f"PASSED: {result['passed']}/{result['total']}")

    if result["success"]:
        print("STATUS: ALL TESTS PASSED")
    else:
        print("STATUS: FAILURES DETECTED")
        for failure in result["failed"]:
            print()
            print("INPUT:   ", failure["input"])
            print("EXPECTED:", failure["expected"])
            print("ACTUAL:  ", failure["actual"])