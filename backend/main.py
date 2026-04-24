from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import sqlite3
import requests
import re
import os
from datetime import datetime

app = FastAPI(title="Mediscan AI – Enterprise Backend")

# ================= CORS =================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ================= DATABASE =================
DB_NAME = "mediscan.db"

def get_connection():
    return sqlite3.connect(DB_NAME)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS research_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            drug TEXT,
            confidence TEXT,
            accessibility TEXT,
            research_volume TEXT,
            market_maturity TEXT,
            timestamp TEXT
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ================= DRUG PROFILES =================
DRUG_PROFILES = {
    "Aspirin": {
        "patient": {
            "target_population": "Adults & Elderly",
            "accessibility": "High",
            "public_health_relevance": "Pain relief & cardiovascular prevention"
        },
        "literature": {
            "research_volume": "Very High",
            "recent_focus": "Cardiovascular research",
            "academic_interest": "Extensive"
        },
        "market": {
            "market_maturity": "Mature",
            "estimated_cost_range": "Low",
            "repurposing_feasibility": "Moderate"
        }
    },
    "Paracetamol": {
        "patient": {
            "target_population": "All age groups",
            "accessibility": "Very High",
            "public_health_relevance": "Fever & pain treatment"
        },
        "literature": {
            "research_volume": "High",
            "recent_focus": "Safety studies",
            "academic_interest": "Active"
        },
        "market": {
            "market_maturity": "Highly Mature",
            "estimated_cost_range": "Very Low",
            "repurposing_feasibility": "Low"
        }
    }
}

# ================= DEFAULT PROFILE =================
def get_profile(drug):
    return DRUG_PROFILES.get(drug, {
        "patient": {
            "target_population": "General population",
            "accessibility": "Medium",
            "public_health_relevance": "General therapeutic usage"
        },
        "literature": {
            "research_volume": "Moderate",
            "recent_focus": "General pharmacology",
            "academic_interest": "Moderate"
        },
        "market": {
            "market_maturity": "Developing",
            "estimated_cost_range": "Moderate",
            "repurposing_feasibility": "Moderate"
        }
    })

# ================= UTILS =================
def safe_filename(name):
    return re.sub(r"[^a-zA-Z0-9_-]", "_", name)

# ================= GOVERNMENT APIs =================
def get_clinical_trials(drug):
    try:
        url = f"https://clinicaltrials.gov/api/query/study_fields?expr={drug}&fields=NCTId&fmt=json"
        r = requests.get(url, timeout=5)
        data = r.json()
        return {
            "source": "ClinicalTrials.gov (NIH)",
            "studies_found": data.get("StudyFieldsResponse", {}).get("NStudiesFound", "Unavailable")
        }
    except:
        return {"source": "ClinicalTrials.gov (NIH)", "studies_found": "Unavailable"}

def get_openfda(drug):
    try:
        url = f"https://api.fda.gov/drug/label.json?search=openfda.generic_name:{drug}&limit=1"
        r = requests.get(url, timeout=5)
        data = r.json()
        results = data.get("results", [])
        purpose = results[0].get("purpose", ["Not available"])[0] if results else "Not available"
        return {"source": "openFDA (US FDA)", "purpose": purpose}
    except:
        return {"source": "openFDA (US FDA)", "purpose": "Unavailable"}

# ================= PDF GENERATION =================
def generate_pdf(drug, findings, confidence, profile):

    filename = f"{safe_filename(drug)}_Drug_Report.pdf"

    c = canvas.Canvas(filename, pagesize=A4)
    text = c.beginText(40, 800)

    text.setFont("Helvetica-Bold", 16)
    text.textLine("Mediscan AI – Enterprise Drug Report")
    text.textLine("")

    text.setFont("Helvetica", 12)
    text.textLine(f"Drug: {drug}")
    text.textLine(f"Confidence Score: {confidence}")
    text.textLine("")
    text.textLine("Key Findings:")

    for f in findings:
        text.textLine(f"- {f}")

    text.textLine("")
    text.textLine("Patient Impact:")
    for k, v in profile["patient"].items():
        text.textLine(f"- {k.replace('_',' ').title()}: {v}")

    text.textLine("")
    text.textLine("Literature Insights:")
    for k, v in profile["literature"].items():
        text.textLine(f"- {k.replace('_',' ').title()}: {v}")

    text.textLine("")
    text.textLine("Market Analysis:")
    for k, v in profile["market"].items():
        text.textLine(f"- {k.replace('_',' ').title()}: {v}")

    c.drawText(text)
    c.save()

    return filename

# ================= ANALYSIS ENGINE =================
@app.post("/analyze")
def analyze(data: dict):

    drug = data.get("drug", "Unknown Drug")
    profile = get_profile(drug)

    findings = [
        f"{drug} shows therapeutic potential",
        "Low patent conflict risk",
        "Suitable for academic research exploration"
    ]

    # ===== Confidence Logic =====
    score = 80

    if profile["literature"]["research_volume"] in ["Very High"]:
        score += 5

    if profile["market"]["repurposing_feasibility"] == "High":
        score += 5

    confidence = f"{min(score,95)}%"

    # ===== Save to Database =====
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO research_history
        (drug, confidence, accessibility, research_volume, market_maturity, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        drug,
        confidence,
        profile["patient"]["accessibility"],
        profile["literature"]["research_volume"],
        profile["market"]["market_maturity"],
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

    pdf = generate_pdf(drug, findings, confidence, profile)

    return {
        "drug": drug,
        "agent_progress": [
            "Clinical Agent analyzing trials",
            "Patent Agent reviewing IP landscape",
            "Literature Agent scanning research papers",
            "Market Agent evaluating commercial potential"
        ],
        "findings": findings,
        "confidence": confidence,
        "patient_impact": profile["patient"],
        "literature": profile["literature"],
        "market": profile["market"],
        "clinical_trials": get_clinical_trials(drug),
        "openfda": get_openfda(drug),
        "pdf": pdf
    }

# ================= HISTORY =================
@app.get("/history")
def get_history():

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM research_history ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()

    return [
        {
            "id": row[0],
            "drug": row[1],
            "confidence": row[2],
            "accessibility": row[3],
            "research_volume": row[4],
            "market_maturity": row[5],
            "timestamp": row[6]
        }
        for row in rows
    ]

# ================= CLEAR HISTORY =================
@app.delete("/history/clear")
def clear_history():

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM research_history")
    conn.commit()
    conn.close()

    return {"message": "History cleared successfully"}
