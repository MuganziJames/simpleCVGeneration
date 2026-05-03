"""
FastAPI backend for CV Generator.

Endpoints:
    POST /generate-cv              { "template": "<template_key>" }  → PDF download (James Muganzi)
    POST /generate-cv-from-form    { form data }                     → PDF download (user-provided data)
    GET  /health                   → { "status": "ok" }
    GET  /templates                → list of available template keys + display names
    GET  /form-templates           → templates available for form (excludes millennial_style)

CORS is configured to allow requests from the live portfolio domain and
common local development origins.  Update ALLOWED_ORIGINS before deploying
if you are serving under a custom domain.
"""

import logging
import os
import re
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

from cv_data import JAMES_MUGANZI_CV
from cvpdfgenerator import DocumentService

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="James Muganzi – CV Generator API",
    description="Generates branded CV PDFs on demand for the portfolio website.",
    version="1.0.0",
)

# ---------------------------------------------------------------------------
# CORS – update ALLOWED_ORIGINS to match your live domain(s)
# ---------------------------------------------------------------------------
ALLOWED_ORIGINS = [
    "https://muganzijamesdev.com",
    "https://www.muganzijamesdev.com",
    # Local development
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5500",
    "http://localhost:8000",
    "http://127.0.0.1",
    "http://127.0.0.1:5500",
    "http://127.0.0.1:8000",
    "null",  # file:// protocol (VS Code Live Server / direct file open)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Accept"],
)

# ---------------------------------------------------------------------------
# Document service (initialised once at startup)
# ---------------------------------------------------------------------------
document_service = DocumentService()

# ---------------------------------------------------------------------------
# Valid templates – keys must match DocumentService.TEMPLATE_CONFIGS
# ---------------------------------------------------------------------------
TEMPLATES = {
    "uk_professional_template": "UK Professional",
    "bizarre_modern": "Bizarre & Modern",
    "minimal_professional": "Minimal Professional",
    "bold": "Bold",
    "millennial_style": "Millennial Style",
    "corporate_classic": "Corporate Classic",
}

# Templates exposed to the form builder (millennial_style excluded)
FORM_TEMPLATES = {k: v for k, v in TEMPLATES.items() if k != "millennial_style"}


# ---------------------------------------------------------------------------
# Schemas – existing
# ---------------------------------------------------------------------------
class CVRequest(BaseModel):
    template: str


# ---------------------------------------------------------------------------
# Schemas – form-based CV generation
# ---------------------------------------------------------------------------
class ExperienceEntry(BaseModel):
    position: str
    company: str
    date_range: str
    bullets: List[str] = []


class EducationEntry(BaseModel):
    degree: str
    institution: str
    year: str = ""


class SkillCategory(BaseModel):
    category: str
    skills: str  # comma-separated skill list


class ProjectEntry(BaseModel):
    name: str
    bullets: List[str] = []
    technologies: Optional[str] = None


class CertificationEntry(BaseModel):
    name: str
    issuer: str = ""
    year: str = ""
    bullets: List[str] = []


class LanguageEntry(BaseModel):
    language: str
    level: str = ""


class CVFormData(BaseModel):
    # Personal info
    full_name: str
    job_title: str
    email: str
    phone: str
    location: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    linkedin: Optional[str] = None

    # Content sections
    summary: Optional[str] = None
    experience: Optional[List[ExperienceEntry]] = None
    education: Optional[List[EducationEntry]] = None
    skills: Optional[List[SkillCategory]] = None
    projects: Optional[List[ProjectEntry]] = None
    certifications: Optional[List[CertificationEntry]] = None
    awards: Optional[List[str]] = None
    languages: Optional[List[LanguageEntry]] = None
    interests: Optional[str] = None

    # Template
    template: str

    @field_validator("full_name", "job_title", "email", "phone")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("This field is required and cannot be blank.")
        return v.strip()

    @field_validator("template")
    @classmethod
    def template_must_be_valid(cls, v: str) -> str:
        if v not in FORM_TEMPLATES:
            raise ValueError(
                f"Unknown template '{v}'. Valid options: {list(FORM_TEMPLATES.keys())}"
            )
        return v


# ---------------------------------------------------------------------------
# CV text builder – converts structured form data into the plain-text format
# the DocumentService parser expects
# ---------------------------------------------------------------------------
def build_cv_text(data: CVFormData) -> str:
    """
    Convert structured CVFormData into the plain-text format consumed by
    DocumentService._parse_*_content() methods.

    Parsing contract (must be preserved):
      Line 1  : Full name
      Line 2  : Job title (no @, +, http, .com, .io, .dev, |, • characters)
      Line 3  : Contact  (contains @ or +)
      Line 4  : Portfolio/links (contains github, .dev, linkedin, etc.)
      Sections: Whitelisted ALL-CAPS headers
      Experience: "Position | Company\\nDate\\n- bullet"
      Skills   : "Category: Skill1, Skill2, ..."
      Bullets  : lines starting with -
      Blank lines separate multi-entry sections
    """
    lines: List[str] = []

    # ── Header ──────────────────────────────────────────────────────────────
    lines.append(data.full_name.strip())
    lines.append(data.job_title.strip())

    contact_parts = [p for p in [data.email, data.phone, data.location] if p and p.strip()]
    if contact_parts:
        lines.append(" | ".join(p.strip() for p in contact_parts))

    link_parts = [p for p in [data.github, data.portfolio, data.linkedin] if p and p.strip()]
    if link_parts:
        lines.append(" | ".join(p.strip() for p in link_parts))

    # ── Professional Summary ─────────────────────────────────────────────────
    if data.summary and data.summary.strip():
        lines.append("")
        lines.append("PROFESSIONAL SUMMARY")
        lines.append(data.summary.strip())

    # ── Technical Skills ────────────────────────────────────────────────────
    if data.skills:
        lines.append("")
        lines.append("TECHNICAL SKILLS")
        for s in data.skills:
            if s.category.strip() and s.skills.strip():
                lines.append(f"{s.category.strip()}: {s.skills.strip()}")

    # ── Professional Experience ──────────────────────────────────────────────
    if data.experience:
        lines.append("")
        lines.append("PROFESSIONAL EXPERIENCE")
        for i, exp in enumerate(data.experience):
            lines.append("")
            lines.append(f"{exp.position.strip()} | {exp.company.strip()}")
            lines.append(exp.date_range.strip())
            for bullet in exp.bullets:
                if bullet.strip():
                    lines.append(f"- {bullet.strip()}")

    # ── Key Projects ────────────────────────────────────────────────────────
    if data.projects:
        lines.append("")
        lines.append("KEY PROJECTS")
        lines.append("")
        for i, proj in enumerate(data.projects):
            if i > 0:
                lines.append("")
            lines.append(proj.name.strip())
            for bullet in proj.bullets:
                if bullet.strip():
                    lines.append(f"- {bullet.strip()}")
            if proj.technologies and proj.technologies.strip():
                lines.append(f"Technologies: {proj.technologies.strip()}")

    # ── Education ───────────────────────────────────────────────────────────
    if data.education:
        lines.append("")
        lines.append("EDUCATION")
        lines.append("")
        for i, edu in enumerate(data.education):
            if i > 0:
                lines.append("")
            lines.append(edu.degree.strip())
            lines.append(edu.institution.strip())
            if edu.year and edu.year.strip():
                lines.append(edu.year.strip())

    # ── Certifications ──────────────────────────────────────────────────────
    if data.certifications:
        lines.append("")
        lines.append("CERTIFICATIONS")
        lines.append("")
        for i, cert in enumerate(data.certifications):
            if i > 0:
                lines.append("")
            lines.append(cert.name.strip())
            issuer_year_parts = [p for p in [cert.issuer, cert.year] if p and p.strip()]
            if issuer_year_parts:
                lines.append(" · ".join(p.strip() for p in issuer_year_parts))
            for bullet in cert.bullets:
                if bullet.strip():
                    lines.append(f"- {bullet.strip()}")

    # ── Awards and Achievements ──────────────────────────────────────────────
    if data.awards:
        non_empty = [a.strip() for a in data.awards if a and a.strip()]
        if non_empty:
            lines.append("")
            lines.append("AWARDS AND ACHIEVEMENTS")
            for award in non_empty:
                lines.append(f"- {award}")

    # ── Languages ───────────────────────────────────────────────────────────
    if data.languages:
        non_empty = [lg for lg in data.languages if lg.language and lg.language.strip()]
        if non_empty:
            lines.append("")
            lines.append("LANGUAGES")
            for lg in non_empty:
                entry = lg.language.strip()
                if lg.level and lg.level.strip():
                    entry += f": {lg.level.strip()}"
                lines.append(entry)

    # ── Interests ───────────────────────────────────────────────────────────
    if data.interests and data.interests.strip():
        lines.append("")
        lines.append("INTERESTS AND HOBBIES")
        lines.append(data.interests.strip())

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/health", tags=["utility"])
async def health():
    """Quick health-check for load-balancers / uptime monitors."""
    return {"status": "ok"}


@app.get("/templates", tags=["utility"])
async def list_templates():
    """Return available template keys and their display names."""
    return {
        "templates": [
            {"key": key, "name": name} for key, name in TEMPLATES.items()
        ]
    }


@app.get("/form-templates", tags=["utility"])
async def list_form_templates():
    """Return templates available for the form builder (millennial_style excluded)."""
    return {
        "templates": [
            {"key": key, "name": name} for key, name in FORM_TEMPLATES.items()
        ]
    }


@app.post("/generate-cv", tags=["cv"])
async def generate_cv(request: CVRequest):
    """
    Generate a CV PDF for James Muganzi using the requested template.

    Body:
        { "template": "bizarre_modern" }

    Returns:
        application/pdf  –  ready to download
    """
    if request.template not in TEMPLATES:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown template '{request.template}'. "
            f"Valid options: {list(TEMPLATES.keys())}",
        )

    logger.info(f"Generating CV with template: {request.template}")

    try:
        pdf_bytes = await document_service.generate_cv_pdf(
            content=JAMES_MUGANZI_CV,
            candidate_name="James Muganzi",
            template_name=request.template,
        )
    except Exception as exc:
        logger.error(f"PDF generation failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="CV generation failed. Please try again.")

    # Produce a clean filename for the download
    template_slug = request.template.replace("_", "-")
    filename = f"James_Muganzi_CV_{template_slug}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
            "Cache-Control": "no-store",
        },
    )


@app.post("/generate-cv-from-form", tags=["cv"])
async def generate_cv_from_form(data: CVFormData):
    """
    Generate a CV PDF from user-submitted form data.

    Accepts structured CV data, converts it to the plain-text format the
    document service expects, then returns the generated PDF.

    Returns:
        application/pdf  –  ready to download
    """
    cv_text = build_cv_text(data)
    logger.info(f"Generating form CV for '{data.full_name}' with template: {data.template}")

    try:
        pdf_bytes = await document_service.generate_cv_pdf(
            content=cv_text,
            candidate_name=data.full_name,
            template_name=data.template,
        )
    except Exception as exc:
        logger.error(f"PDF generation failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="CV generation failed. Please try again.")

    # Sanitise filename: keep alphanumerics, hyphens, underscores only
    safe_name = re.sub(r"[^\w\s-]", "", data.full_name).strip().replace(" ", "_")
    template_slug = data.template.replace("_", "-")
    filename = f"{safe_name}_CV_{template_slug}.pdf"

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(pdf_bytes)),
            "Cache-Control": "no-store",
        },
    )


# ---------------------------------------------------------------------------
# Static file serving – must be mounted AFTER all API routes
# ---------------------------------------------------------------------------
_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isdir(_frontend_dir):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")


# ---------------------------------------------------------------------------
# Entry point (for local dev: python main.py)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
