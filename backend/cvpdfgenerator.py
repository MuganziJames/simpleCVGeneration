"""
Document Service - PDF Generation

Generates professional PDF documents from AI-generated content.
Supports CV and cover letter templates with clean, modern design.

Features:
- Professional CV template with clean layout
- Professional cover letter template with business format
- Configurable styling and formatting
- A4 page size with proper margins
- Font management with fallbacks
- Error handling and validation
"""

import asyncio
import io
import logging
import os
import sys
from datetime import datetime
from typing import Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    FrameBreak,
    KeepTogether,
    ListFlowable,
    ListItem,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

logger = logging.getLogger(__name__)


class DocumentService:
    """
    Service for generating professional PDF documents from text content.

    Supports:
    - CV/Resume templates
    - Cover letter templates
    - Custom styling and formatting
    """

    # Page settings
    PAGE_WIDTH, PAGE_HEIGHT = A4
    MARGIN_LEFT = 0.75 * inch
    MARGIN_RIGHT = 0.75 * inch
    MARGIN_TOP = 0.75 * inch
    MARGIN_BOTTOM = 0.75 * inch

    # Color scheme (professional blue-gray) - UK Professional Template
    PRIMARY_COLOR = colors.HexColor("#2C3E50")  # Dark blue-gray
    SECONDARY_COLOR = colors.HexColor("#34495E")  # Lighter blue-gray
    ACCENT_COLOR = colors.HexColor("#3498DB")  # Professional blue
    DIVIDER_COLOR = colors.HexColor("#BDC3C7")  # Light gray

    # ============ TEMPLATE CONFIGURATIONS ============

    TEMPLATE_CONFIGS = {
        "uk_professional_template": {
            "name": "UK Professional",
            "layout": "single_column",
            "font_heading": "Times-Bold",
            "font_body": "Times-Roman",
            "font_accent": "Times-Italic",
            "primary_color": "#2C3E50",
            "secondary_color": "#34495E",
            "accent_color": "#3498DB",
            "divider_color": "#BDC3C7",
        },
        "bizarre_modern": {
            "name": "Bizarre & Modern",
            "layout": "single_column",  # Clean single-column with modern styling
            "font_heading": "Helvetica-Bold",
            "font_body": "Helvetica",
            "font_accent": "Helvetica-Oblique",
            "primary_color": "#1A1A1A",  # Near black for text
            "secondary_color": "#4A4A4A",  # Dark gray
            "accent_color": "#E85D04",  # Vibrant orange (from the design)
            "divider_color": "#1A1A1A",  # Black divider lines
            "section_header_underline": True,
            "skills_show_proficiency": True,
            "contact_with_icons": True,
        },
        "minimal_professional": {
            "name": "Minimal Professional",
            "layout": "single_column",  # Clean single-column with dark header
            "font_heading": "Helvetica-Bold",
            "font_body": "Helvetica",
            "font_accent": "Helvetica",
            "header_color": "#404040",  # Dark charcoal header background
            "header_text_color": "#FFFFFF",  # White text in header
            "primary_color": "#000000",  # Black text in body
            "secondary_color": "#666666",  # Gray for contact info
            "accent_color": "#000000",  # Black accents
            "clean_minimal_design": True,
            "dark_header": True,
        },
        "bold": {
            "name": "Bold",
            "layout": "two_column",  # Section labels LEFT, content RIGHT
            "font_heading": "Helvetica-Bold",
            "font_body": "Helvetica",
            "font_accent": "Helvetica-Oblique",
            "header_color": "#3D3D3D",  # Dark charcoal header background
            "header_text_color": "#FFFFFF",  # White text in header
            "primary_color": "#000000",  # Black text in body
            "secondary_color": "#666666",  # Gray for dates/contact
            "accent_color": "#000000",  # Black accents
            "left_column_width": 0.22,  # 22% for section labels
            "right_column_width": 0.78,  # 78% for content
            "separator": "//",  # Use // as separator for contact/company info
            "dark_header": True,
            "bold_lead_in_bullets": True,  # First part of bullet is bold
        },
        "millennial_style": {
            "name": "Millennial Style",
            "layout": "two_column_sidebar",  # White content LEFT, dark sidebar RIGHT
            "font_heading": "Helvetica-Bold",
            "font_body": "Helvetica",
            "font_accent": "Helvetica-Oblique",
            "sidebar_color": "#1B3A4B",  # Dark navy blue sidebar (RIGHT side)
            "sidebar_text_color": "#FFFFFF",  # White text in sidebar
            "primary_color": "#1B3A4B",  # Dark navy for left column text
            "secondary_color": "#666666",  # Gray for dates/secondary text
            "accent_color": "#2B7A78",  # Teal accent for position titles on right
            "left_column_width": 0.60,  # 60% for white content (name, experience, education, etc.)
            "right_column_width": 0.40,  # 40% for dark sidebar (contact, skills, languages, certs)
            "section_header_spaced": True,  # L E T T E R  S P A C E D headers
            "section_header_underline": True,  # Colored underline below headers
        },
        "corporate_classic": {
            "name": "Corporate Classic",
            "layout": "single_column",  # Single column with two-column sub-layouts for experience/skills
            "font_heading": "Times-Bold",  # Serif fonts throughout
            "font_body": "Times-Roman",
            "font_accent": "Times-Italic",
            "primary_color": "#000000",  # Monochromatic - black only
            "secondary_color": "#000000",  # All black text
            "accent_color": "#000000",  # No color accents
            "divider_color": "#000000",  # Black underlines for sections
            "section_header_underline": True,  # Section headers have black underline
            "stacked_name": True,  # First name above, last name below (larger)
            "italic_summary": True,  # Professional summary in italics
            "two_column_experience": True,  # Older experience entries in two columns
            "two_column_skills": True,  # Skills displayed in two-column grid
        },
    }

    # Valid CV section headers - based on UserProfile model structure
    # This whitelist ensures only legitimate section headers are styled as such
    VALID_CV_HEADERS = {
        # Core sections
        "professional summary",
        "summary",
        "profile",
        "objective",
        "work experience",
        "experience",
        "professional experience",
        "employment history",
        "career history",
        "education",
        "academic background",
        "qualifications",
        "skills",
        "technical skills",
        "core competencies",
        "key skills",
        "certifications",
        "certificates",
        "licenses",
        "credentials",
        "projects",
        "key projects",
        "portfolio",
        "notable projects",
        "languages",
        "language proficiency",
        "awards and achievements",
        "awards",
        "achievements",
        "honors",
        "volunteer experience",
        "volunteering",
        "community service",
        "publications",
        "research",
        "papers",
        "professional memberships",
        "memberships",
        "affiliations",
        "conferences and talks",
        "conferences",
        "speaking engagements",
        "patents",
        "intellectual property",
        "interests and hobbies",
        "interests",
        "hobbies",
        "personal interests",
        "references",
        "referees",
        "additional information",
        "other information",
    }

    def __init__(self):
        """Initialize document service with default styles."""
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Create custom paragraph styles for professional documents."""

        # Helper function to add style if it doesn't exist
        def add_style_if_not_exists(style_obj):
            # Always update the style to ensure correct values
            if style_obj.name in self.styles:
                # Remove existing style first, then add updated one
                try:
                    del self.styles[style_obj.name]
                except KeyError:
                    pass
            self.styles.add(style_obj)

        # Header style - Name/Title (Times New Roman 16pt Bold)
        add_style_if_not_exists(
            ParagraphStyle(
                name="CustomHeader",
                parent=self.styles["Heading1"],
                fontSize=16,
                textColor=self.PRIMARY_COLOR,
                spaceAfter=6,
                alignment=TA_CENTER,
                fontName="Times-Bold",
            )
        )

        # Subheader style - Job title/subtitle (Times New Roman 12pt)
        add_style_if_not_exists(
            ParagraphStyle(
                name="CustomSubheader",
                parent=self.styles["Heading2"],
                fontSize=12,
                textColor=self.SECONDARY_COLOR,
                spaceAfter=12,
                alignment=TA_CENTER,
                fontName="Times-Roman",
            )
        )

        # Section header style - Clean, no border (Times New Roman 12pt Bold, uppercase)
        add_style_if_not_exists(
            ParagraphStyle(
                name="SectionHeader",
                parent=self.styles["Heading2"],
                fontSize=12,
                textColor=self.PRIMARY_COLOR,
                spaceAfter=8,
                spaceBefore=16,
                fontName="Times-Bold",
            )
        )

        # Contact info style (Times New Roman 11pt)
        add_style_if_not_exists(
            ParagraphStyle(
                name="ContactInfo",
                parent=self.styles["Normal"],
                fontSize=11,
                textColor=self.SECONDARY_COLOR,
                alignment=TA_CENTER,
                spaceAfter=12,
                fontName="Times-Roman",
            )
        )

        # Body text style - Times New Roman 11pt with proper spacing
        add_style_if_not_exists(
            ParagraphStyle(
                name="CVBodyText",
                parent=self.styles["Normal"],
                fontSize=11,
                textColor=colors.black,
                alignment=TA_LEFT,
                spaceAfter=6,
                spaceBefore=2,
                leading=14,
                fontName="Times-Roman",
            )
        )

        # Bullet point style - Times New Roman 11pt
        add_style_if_not_exists(
            ParagraphStyle(
                name="BulletPoint",
                parent=self.styles["Normal"],
                fontSize=11,
                textColor=colors.black,
                leftIndent=20,
                spaceAfter=4,
                bulletIndent=10,
                leading=14,
                fontName="Times-Roman",
            )
        )

        # Job title/role style (Bold for job title | company)
        add_style_if_not_exists(
            ParagraphStyle(
                name="JobTitle",
                parent=self.styles["Normal"],
                fontSize=11,
                textColor=colors.black,
                spaceAfter=2,
                spaceBefore=8,
                fontName="Times-Bold",
            )
        )

        # Sub-item style for details under education/projects (indented)
        add_style_if_not_exists(
            ParagraphStyle(
                name="SubItem",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                leftIndent=15,
                spaceAfter=3,
                leading=13,
                fontName="Times-Roman",
            )
        )

        # Date/Duration style (Times New Roman 10pt Italic - black, not blue)
        add_style_if_not_exists(
            ParagraphStyle(
                name="DateStyle",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                spaceAfter=6,
                spaceBefore=2,
                fontName="Times-Italic",
            )
        )

        # Cover letter paragraph style - Times New Roman 12pt with DOUBLE SPACING
        add_style_if_not_exists(
            ParagraphStyle(
                name="CoverLetterBody",
                parent=self.styles["Normal"],
                fontSize=12,
                textColor=colors.black,
                alignment=TA_JUSTIFY,
                spaceAfter=12,
                leading=24,  # Double spacing: 2 x 12pt font size = 24pt
                firstLineIndent=0,
                fontName="Times-Roman",
            )
        )

        # ============ BIZARRE & MODERN TEMPLATE STYLES ============

        # Bizarre Modern - Name header (large, bold, left-aligned)
        add_style_if_not_exists(
            ParagraphStyle(
                name="BM_Name",
                parent=self.styles["Heading1"],
                fontSize=28,
                textColor=colors.HexColor("#1A1A1A"),
                spaceAfter=2,
                spaceBefore=0,
                alignment=TA_LEFT,
                fontName="Helvetica-Bold",
                leading=32,
            )
        )

        # Bizarre Modern - Job title (orange accent color)
        add_style_if_not_exists(
            ParagraphStyle(
                name="BM_JobTitle",
                parent=self.styles["Normal"],
                fontSize=12,
                textColor=colors.HexColor("#E85D04"),  # Orange accent
                spaceAfter=15,
                spaceBefore=0,
                alignment=TA_LEFT,
                fontName="Helvetica",
            )
        )

        # Bizarre Modern - Contact info (right-aligned, with bullet separators)
        add_style_if_not_exists(
            ParagraphStyle(
                name="BM_Contact",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#1A1A1A"),
                spaceAfter=2,
                alignment=TA_RIGHT,
                fontName="Helvetica",
                leading=14,
            )
        )

        # Bizarre Modern - Section header (uppercase, letter-spaced, with underline)
        add_style_if_not_exists(
            ParagraphStyle(
                name="BM_SectionHeader",
                parent=self.styles["Heading2"],
                fontSize=11,
                textColor=colors.HexColor("#1A1A1A"),
                spaceAfter=8,
                spaceBefore=18,
                fontName="Helvetica-Bold",
                tracking=2,  # Letter spacing
            )
        )

        # Bizarre Modern - Experience title (orange for position)
        add_style_if_not_exists(
            ParagraphStyle(
                name="BM_ExperienceTitle",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.HexColor("#E85D04"),  # Orange
                spaceAfter=0,
                spaceBefore=8,
                fontName="Helvetica-Bold",
                leftIndent=0,  # Flush with main text margin
            )
        )

        # Bizarre Modern - Company/Institution name (smaller, gray)
        add_style_if_not_exists(
            ParagraphStyle(
                name="BM_Company",
                parent=self.styles["Normal"],
                fontSize=9,  # Smaller than position title
                textColor=colors.HexColor("#4A4A4A"),  # Gray
                spaceAfter=4,
                spaceBefore=0,
                fontName="Helvetica",
            )
        )

        # Bizarre Modern - Date (right-aligned, gray)
        add_style_if_not_exists(
            ParagraphStyle(
                name="BM_Date",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#4A4A4A"),
                spaceAfter=4,
                alignment=TA_RIGHT,
                fontName="Helvetica",
            )
        )

        # Bizarre Modern - Body text
        add_style_if_not_exists(
            ParagraphStyle(
                name="BM_BodyText",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#1A1A1A"),
                alignment=TA_LEFT,
                spaceAfter=4,
                spaceBefore=2,
                leading=13,
                fontName="Helvetica",
                leftIndent=0,  # No left indentation for proper alignment
            )
        )

        # Bizarre Modern - Bullet points
        add_style_if_not_exists(
            ParagraphStyle(
                name="BM_Bullet",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#1A1A1A"),
                leftIndent=0,  # Fully left-aligned bullets (Interests, etc.)
                spaceAfter=3,
                bulletIndent=0,  # No bullet indent
                leading=13,
                fontName="Helvetica",
            )
        )

        # Bizarre Modern - Skills category label
        add_style_if_not_exists(
            ParagraphStyle(
                name="BM_SkillCategory",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#1A1A1A"),
                spaceAfter=2,
                fontName="Helvetica-Bold",
            )
        )

        # Bizarre Modern - Skills proficiency level
        add_style_if_not_exists(
            ParagraphStyle(
                name="BM_SkillLevel",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#4A4A4A"),
                spaceAfter=2,
                fontName="Helvetica",
            )
        )

        # Bizarre Modern - Education degree (orange)
        add_style_if_not_exists(
            ParagraphStyle(
                name="BM_Degree",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.HexColor("#E85D04"),  # Orange
                spaceAfter=1,
                spaceBefore=6,
                fontName="Helvetica-Bold",
            )
        )

        # Bizarre Modern - Link style (orange, for URLs)
        add_style_if_not_exists(
            ParagraphStyle(
                name="BM_Link",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#E85D04"),
                fontName="Helvetica",
            )
        )

        # ============ MINIMAL PROFESSIONAL TEMPLATE STYLES ============

        # Minimal Professional - Name in header (large, bold, white)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MP_HeaderName",
                parent=self.styles["Heading1"],
                fontSize=24,
                textColor=colors.white,
                spaceAfter=4,
                spaceBefore=0,
                alignment=TA_LEFT,
                fontName="Helvetica-Bold",
                leading=28,
            )
        )

        # Minimal Professional - Job title in header (white)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MP_HeaderTitle",
                parent=self.styles["Normal"],
                fontSize=14,
                textColor=colors.white,
                spaceAfter=0,
                spaceBefore=0,
                alignment=TA_LEFT,
                fontName="Helvetica",
            )
        )

        # Minimal Professional - Contact info (gray, clean)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MP_Contact",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.HexColor("#666666"),
                spaceAfter=4,
                alignment=TA_LEFT,
                fontName="Helvetica",
                leading=14,
            )
        )

        # Minimal Professional - Section header (uppercase, clean)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MP_SectionHeader",
                parent=self.styles["Heading2"],
                fontSize=11,
                textColor=colors.black,
                spaceAfter=8,
                spaceBefore=16,
                fontName="Helvetica-Bold",
                alignment=TA_LEFT,
            )
        )

        # Minimal Professional - Position title (bold black)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MP_PositionTitle",
                parent=self.styles["Normal"],
                fontSize=11,
                textColor=colors.black,
                spaceAfter=2,
                spaceBefore=8,
                fontName="Helvetica-Bold",
            )
        )

        # Minimal Professional - Company name (regular black)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MP_Company",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                spaceAfter=2,
                spaceBefore=0,
                fontName="Helvetica",
            )
        )

        # Minimal Professional - Date range (gray)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MP_Date",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.HexColor("#666666"),
                spaceAfter=6,
                spaceBefore=0,
                fontName="Helvetica",
            )
        )

        # Minimal Professional - Body text (clean black)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MP_BodyText",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                alignment=TA_LEFT,
                spaceAfter=4,
                spaceBefore=0,
                leading=14,
                fontName="Helvetica",
            )
        )

        # Minimal Professional - Bullet points (clean)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MP_Bullet",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                leftIndent=15,
                spaceAfter=3,
                bulletIndent=10,
                leading=14,
                fontName="Helvetica",
            )
        )

        # Minimal Professional - Profile summary
        add_style_if_not_exists(
            ParagraphStyle(
                name="MP_ProfileSummary",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                alignment=TA_LEFT,
                spaceAfter=6,
                leading=15,
                fontName="Helvetica",
            )
        )

        # ============ BOLD TEMPLATE STYLES ============

        # Bold - Header name (large, elegant, white, LEFT-aligned)
        add_style_if_not_exists(
            ParagraphStyle(
                name="Bold_HeaderName",
                parent=self.styles["Heading1"],
                fontSize=28,
                textColor=colors.white,
                spaceAfter=4,
                spaceBefore=0,
                alignment=TA_LEFT,
                fontName="Helvetica",
                leading=32,
            )
        )

        # Bold - Header job title (smaller, white/light gray, RIGHT-aligned)
        add_style_if_not_exists(
            ParagraphStyle(
                name="Bold_HeaderTitle",
                parent=self.styles["Normal"],
                fontSize=12,
                textColor=colors.HexColor("#E0E0E0"),
                spaceAfter=0,
                spaceBefore=0,
                alignment=TA_RIGHT,
                fontName="Helvetica-Oblique",
            )
        )

        # Bold - Contact info (gray, small, with // separators) - below header
        add_style_if_not_exists(
            ParagraphStyle(
                name="Bold_Contact",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#666666"),
                spaceAfter=0,
                spaceBefore=0,
                alignment=TA_LEFT,
                fontName="Helvetica",
                leading=14,
            )
        )

        # Bold - Contact info INSIDE header (white/light, small, centered)
        add_style_if_not_exists(
            ParagraphStyle(
                name="Bold_ContactInHeader",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#CCCCCC"),
                spaceAfter=0,
                spaceBefore=0,
                alignment=TA_LEFT,
                fontName="Helvetica",
                leading=12,
            )
        )

        # Bold - Section label (LEFT column, uppercase, bold)
        add_style_if_not_exists(
            ParagraphStyle(
                name="Bold_SectionLabel",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.black,
                spaceAfter=0,
                spaceBefore=0,
                alignment=TA_LEFT,
                fontName="Helvetica-Bold",
            )
        )

        # Bold - Position title (bold, uppercase in content)
        add_style_if_not_exists(
            ParagraphStyle(
                name="Bold_PositionTitle",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                spaceAfter=2,
                spaceBefore=6,
                fontName="Helvetica-Bold",
            )
        )

        # Bold - Company/Location/Date line (regular text with // separators)
        add_style_if_not_exists(
            ParagraphStyle(
                name="Bold_CompanyLine",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                spaceAfter=4,
                spaceBefore=0,
                fontName="Helvetica",
            )
        )

        # Bold - Body text (regular content)
        add_style_if_not_exists(
            ParagraphStyle(
                name="Bold_BodyText",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                alignment=TA_LEFT,
                spaceAfter=4,
                spaceBefore=0,
                leading=14,
                fontName="Helvetica",
            )
        )

        # Bold - Sub-header (like "ACHIEVEMENTS + HIGHLIGHTS")
        add_style_if_not_exists(
            ParagraphStyle(
                name="Bold_SubHeader",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                spaceAfter=6,
                spaceBefore=10,
                fontName="Helvetica-Bold",
            )
        )

        # Bold - Bullet point with bold lead-in
        add_style_if_not_exists(
            ParagraphStyle(
                name="Bold_Bullet",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                leftIndent=12,
                spaceAfter=4,
                spaceBefore=0,
                bulletIndent=0,
                leading=14,
                fontName="Helvetica",
            )
        )

        # Bold - Profile/Summary text
        add_style_if_not_exists(
            ParagraphStyle(
                name="Bold_ProfileText",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                alignment=TA_LEFT,
                spaceAfter=0,
                spaceBefore=0,
                leading=15,
                fontName="Helvetica",
            )
        )

        # ============ MILLENNIAL STYLE TEMPLATE STYLES ============
        # Two-column layout: WHITE content (LEFT 60%) + DARK NAVY sidebar (RIGHT 40%)

        # ===== LEFT COLUMN STYLES (White background, dark text) =====

        # Millennial - Name in left content (large, bold, dark navy)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_LeftName",
                parent=self.styles["Heading1"],
                fontSize=26,
                textColor=colors.HexColor("#1B3A4B"),  # Dark navy
                spaceAfter=2,
                spaceBefore=0,
                alignment=TA_LEFT,
                fontName="Helvetica-Bold",
                leading=30,
            )
        )

        # Millennial - Job title in left content (gray)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_LeftTitle",
                parent=self.styles["Normal"],
                fontSize=11,
                textColor=colors.HexColor("#666666"),  # Gray
                spaceAfter=15,
                spaceBefore=0,
                alignment=TA_LEFT,
                fontName="Helvetica",
            )
        )

        # Millennial - Section header in left column (dark, letter-spaced)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_LeftSectionHeader",
                parent=self.styles["Heading2"],
                fontSize=10,
                textColor=colors.HexColor("#1B3A4B"),  # Dark navy
                spaceAfter=8,
                spaceBefore=14,
                fontName="Helvetica-Bold",
                alignment=TA_LEFT,
            )
        )

        # Millennial - Position title in left (teal accent)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_LeftPositionTitle",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.HexColor("#2B7A78"),  # Teal accent
                spaceAfter=1,
                spaceBefore=10,
                fontName="Helvetica-Bold",
                alignment=TA_LEFT,
            )
        )

        # Millennial - Company name in left (dark)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_LeftCompany",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#1B3A4B"),
                spaceAfter=1,
                spaceBefore=0,
                fontName="Helvetica",
                alignment=TA_LEFT,
            )
        )

        # Millennial - Date in left (gray)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_LeftDate",
                parent=self.styles["Normal"],
                fontSize=8,
                textColor=colors.HexColor("#666666"),  # Gray
                spaceAfter=4,
                spaceBefore=0,
                fontName="Helvetica",
                alignment=TA_LEFT,
            )
        )

        # Millennial - Bullet point in left (dark)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_LeftBullet",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#333333"),
                leftIndent=10,
                spaceAfter=3,
                spaceBefore=0,
                bulletIndent=0,
                leading=12,
                fontName="Helvetica",
            )
        )

        # Millennial - Education degree in left (teal)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_LeftDegree",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.HexColor("#2B7A78"),  # Teal
                spaceAfter=1,
                spaceBefore=10,
                fontName="Helvetica-Bold",
                alignment=TA_LEFT,
            )
        )

        # Millennial - Institution in left (dark)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_LeftInstitution",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#1B3A4B"),
                spaceAfter=1,
                spaceBefore=0,
                fontName="Helvetica",
                alignment=TA_LEFT,
            )
        )

        # Millennial - Summary/body text in left (dark)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_LeftBody",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#333333"),
                spaceAfter=6,
                spaceBefore=0,
                fontName="Helvetica",
                leading=13,
                alignment=TA_LEFT,
            )
        )

        # ===== RIGHT SIDEBAR STYLES (Dark navy background, white/teal text) =====

        # Millennial - Contact in sidebar (white)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_SidebarContact",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.white,
                spaceAfter=3,
                spaceBefore=0,
                fontName="Helvetica",
                alignment=TA_LEFT,
            )
        )

        # Millennial - Name in sidebar (for header area - large, bold, white)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_SidebarName",
                parent=self.styles["Heading1"],
                fontSize=24,
                textColor=colors.white,
                spaceAfter=4,
                spaceBefore=0,
                alignment=TA_LEFT,
                fontName="Helvetica-Bold",
                leading=28,
            )
        )

        # Millennial - Job title in sidebar (smaller, white)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_SidebarTitle",
                parent=self.styles["Normal"],
                fontSize=12,
                textColor=colors.white,
                spaceAfter=20,
                spaceBefore=0,
                alignment=TA_LEFT,
                fontName="Helvetica",
            )
        )

        # Millennial - Section header in sidebar (white, letter-spaced, uppercase)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_SidebarSectionHeader",
                parent=self.styles["Heading2"],
                fontSize=10,
                textColor=colors.white,
                spaceAfter=8,
                spaceBefore=16,
                fontName="Helvetica-Bold",
                alignment=TA_LEFT,
            )
        )

        # Millennial - Position title in sidebar (teal accent color)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_SidebarPositionTitle",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.HexColor("#2B7A78"),  # Teal accent
                spaceAfter=1,
                spaceBefore=10,
                fontName="Helvetica-Bold",
                alignment=TA_LEFT,
            )
        )

        # Millennial - Company name in sidebar (white)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_SidebarCompany",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.white,
                spaceAfter=1,
                spaceBefore=0,
                fontName="Helvetica",
                alignment=TA_LEFT,
            )
        )

        # Millennial - Date in sidebar (smaller, white/light gray)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_SidebarDate",
                parent=self.styles["Normal"],
                fontSize=8,
                textColor=colors.HexColor("#B0C4CC"),  # Light blue-gray
                spaceAfter=4,
                spaceBefore=0,
                fontName="Helvetica",
                alignment=TA_LEFT,
            )
        )

        # Millennial - Bullet point in sidebar (white)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_SidebarBullet",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.white,
                leftIndent=10,
                spaceAfter=3,
                spaceBefore=0,
                bulletIndent=0,
                leading=12,
                fontName="Helvetica",
            )
        )

        # Millennial - Education degree in sidebar (teal accent)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_SidebarDegree",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.HexColor("#4A9B9B"),  # Teal accent
                spaceAfter=1,
                spaceBefore=10,
                fontName="Helvetica-Bold",
                alignment=TA_LEFT,
            )
        )

        # Millennial - Education institution in sidebar (white)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_SidebarInstitution",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.white,
                spaceAfter=1,
                spaceBefore=0,
                fontName="Helvetica",
                alignment=TA_LEFT,
            )
        )

        # Millennial - Section header in right column (for left content now - dark)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_RightSectionHeader",
                parent=self.styles["Heading2"],
                fontSize=10,
                textColor=colors.HexColor("#1B3A4B"),  # Dark navy
                spaceAfter=8,
                spaceBefore=14,
                fontName="Helvetica-Bold",
                alignment=TA_LEFT,
            )
        )

        # Millennial - Contact label (not used in new layout, kept for compat)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_ContactLabel",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#1B3A4B"),
                spaceAfter=2,
                spaceBefore=0,
                fontName="Helvetica",
                alignment=TA_LEFT,
            )
        )

        # Millennial - Contact value (not used in new layout, kept for compat)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_ContactValue",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#666666"),
                spaceAfter=6,
                spaceBefore=0,
                fontName="Helvetica",
                alignment=TA_LEFT,
            )
        )

        # Millennial - Skill name in sidebar (white on dark)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_SkillName",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.white,  # White text on dark sidebar
                spaceAfter=0,
                spaceBefore=0,
                fontName="Helvetica",
                alignment=TA_LEFT,
            )
        )

        # Millennial - Skill level in sidebar (teal accent)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_SkillLevel",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#2B7A78"),  # Teal accent
                spaceAfter=0,
                spaceBefore=0,
                fontName="Helvetica",
                alignment=TA_RIGHT,
            )
        )

        # Millennial - Language name in sidebar (white)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_LanguageName",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.white,  # White on dark sidebar
                spaceAfter=0,
                spaceBefore=0,
                fontName="Helvetica",
                alignment=TA_LEFT,
            )
        )

        # Millennial - Language level in sidebar (teal)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_LanguageLevel",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#2B7A78"),  # Teal
                spaceAfter=0,
                spaceBefore=0,
                fontName="Helvetica",
                alignment=TA_RIGHT,
            )
        )

        # Millennial - Certificate name in sidebar (teal)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_CertName",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#2B7A78"),  # Teal
                spaceAfter=1,
                spaceBefore=6,
                fontName="Helvetica-Bold",
                alignment=TA_LEFT,
            )
        )

        # Millennial - Certificate date in sidebar (white/light)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_CertDate",
                parent=self.styles["Normal"],
                fontSize=8,
                textColor=colors.HexColor("#B0C4CC"),  # Light blue-gray
                spaceAfter=0,
                spaceBefore=0,
                fontName="Helvetica",
                alignment=TA_LEFT,
            )
        )

        # Millennial - Body text in right column (dark)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_RightBodyText",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#1B3A4B"),
                spaceAfter=4,
                spaceBefore=0,
                leading=12,
                fontName="Helvetica",
                alignment=TA_LEFT,
            )
        )

        # Millennial - Bullet in right column (dark)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_RightBullet",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#1B3A4B"),
                leftIndent=10,
                spaceAfter=3,
                spaceBefore=0,
                bulletIndent=0,
                leading=12,
                fontName="Helvetica",
            )
        )

        # Millennial - Project/Award title in right column (teal)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_RightTitle",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.HexColor("#4A9B9B"),
                spaceAfter=1,
                spaceBefore=8,
                fontName="Helvetica-Bold",
                alignment=TA_LEFT,
            )
        )

        # Millennial - Subtitle/organization in right column (gray)
        add_style_if_not_exists(
            ParagraphStyle(
                name="MS_RightSubtitle",
                parent=self.styles["Normal"],
                fontSize=8,
                textColor=colors.HexColor("#666666"),
                spaceAfter=2,
                spaceBefore=0,
                fontName="Helvetica",
                alignment=TA_LEFT,
            )
        )

        # ============ CORPORATE CLASSIC TEMPLATE STYLES ============
        # Monochromatic serif design with stacked name, section underlines

        # Corporate Classic - First name (smaller, above last name)
        add_style_if_not_exists(
            ParagraphStyle(
                name="CC_FirstName",
                parent=self.styles["Heading1"],
                fontSize=16,
                textColor=colors.black,
                spaceAfter=0,
                spaceBefore=0,
                alignment=TA_LEFT,
                fontName="Times-Bold",
                leading=18,
            )
        )

        # Corporate Classic - Last name (larger, below first name)
        add_style_if_not_exists(
            ParagraphStyle(
                name="CC_LastName",
                parent=self.styles["Heading1"],
                fontSize=28,
                textColor=colors.black,
                spaceAfter=4,
                spaceBefore=0,
                alignment=TA_LEFT,
                fontName="Times-Bold",
                leading=32,
            )
        )

        # Corporate Classic - Contact info (right-aligned, stacked)
        add_style_if_not_exists(
            ParagraphStyle(
                name="CC_Contact",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                spaceAfter=2,
                spaceBefore=0,
                alignment=TA_RIGHT,
                fontName="Times-Roman",
                leading=14,
            )
        )

        # Corporate Classic - Professional summary (italic)
        add_style_if_not_exists(
            ParagraphStyle(
                name="CC_Summary",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                spaceAfter=12,
                spaceBefore=8,
                alignment=TA_LEFT,
                fontName="Times-Italic",
                leading=14,
            )
        )

        # Corporate Classic - Section header (bold, uppercase, with underline)
        add_style_if_not_exists(
            ParagraphStyle(
                name="CC_SectionHeader",
                parent=self.styles["Normal"],
                fontSize=11,
                textColor=colors.black,
                spaceAfter=8,
                spaceBefore=16,
                fontName="Times-Bold",
                alignment=TA_LEFT,
                leftIndent=0,
                firstLineIndent=0,
            )
        )

        # Corporate Classic - Job title (bold, no left indent)
        add_style_if_not_exists(
            ParagraphStyle(
                name="CC_JobTitle",
                parent=self.styles["Normal"],
                fontSize=11,
                textColor=colors.black,
                spaceAfter=1,
                spaceBefore=6,
                fontName="Times-Bold",
                alignment=TA_LEFT,
                leftIndent=0,
                firstLineIndent=0,
            )
        )

        # Corporate Classic - Company name (regular)
        add_style_if_not_exists(
            ParagraphStyle(
                name="CC_Company",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                spaceAfter=1,
                spaceBefore=0,
                fontName="Times-Roman",
                alignment=TA_LEFT,
                leftIndent=0,
                firstLineIndent=0,
            )
        )

        # Corporate Classic - Date range (italic, right-aligned for two-column)
        add_style_if_not_exists(
            ParagraphStyle(
                name="CC_Date",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                spaceAfter=1,
                spaceBefore=0,
                fontName="Times-Italic",
                alignment=TA_RIGHT,
            )
        )

        # Corporate Classic - Location (regular)
        add_style_if_not_exists(
            ParagraphStyle(
                name="CC_Location",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                spaceAfter=4,
                spaceBefore=0,
                fontName="Times-Roman",
                alignment=TA_LEFT,
                leftIndent=0,
                firstLineIndent=0,
            )
        )

        # Corporate Classic - Body text (no left indent)
        add_style_if_not_exists(
            ParagraphStyle(
                name="CC_BodyText",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                spaceAfter=4,
                spaceBefore=0,
                leading=14,
                fontName="Times-Roman",
                alignment=TA_LEFT,
                leftIndent=0,
                firstLineIndent=0,
            )
        )

        # Corporate Classic - Bullet points (minimal left indent for bullet only)
        add_style_if_not_exists(
            ParagraphStyle(
                name="CC_Bullet",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                leftIndent=0,
                spaceAfter=3,
                spaceBefore=0,
                bulletIndent=0,
                leading=14,
                fontName="Times-Roman",
                firstLineIndent=0,
            )
        )

        # Corporate Classic - Skills category/name
        add_style_if_not_exists(
            ParagraphStyle(
                name="CC_SkillName",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                spaceAfter=2,
                spaceBefore=0,
                fontName="Times-Bold",
                alignment=TA_LEFT,
                leftIndent=0,
                firstLineIndent=0,
            )
        )

        # Corporate Classic - Skills level
        add_style_if_not_exists(
            ParagraphStyle(
                name="CC_SkillLevel",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                spaceAfter=2,
                spaceBefore=0,
                fontName="Times-Roman",
                alignment=TA_LEFT,
                leftIndent=0,
                firstLineIndent=0,
            )
        )

        # Corporate Classic - Degree/Certificate title (bold, no left indent)
        add_style_if_not_exists(
            ParagraphStyle(
                name="CC_Degree",
                parent=self.styles["Normal"],
                fontSize=11,
                textColor=colors.black,
                spaceAfter=1,
                spaceBefore=6,
                fontName="Times-Bold",
                alignment=TA_LEFT,
                leftIndent=0,
                firstLineIndent=0,
            )
        )

        # Corporate Classic - Institution name
        add_style_if_not_exists(
            ParagraphStyle(
                name="CC_Institution",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                spaceAfter=1,
                spaceBefore=0,
                fontName="Times-Roman",
                alignment=TA_LEFT,
                leftIndent=0,
                firstLineIndent=0,
            )
        )

        # Corporate Classic - Small text (for two-column entries)
        add_style_if_not_exists(
            ParagraphStyle(
                name="CC_SmallText",
                parent=self.styles["Normal"],
                fontSize=9,
                textColor=colors.black,
                spaceAfter=2,
                spaceBefore=0,
                fontName="Times-Roman",
                alignment=TA_LEFT,
                leading=12,
                leftIndent=0,
                firstLineIndent=0,
            )
        )

        # Corporate Classic - Link style
        add_style_if_not_exists(
            ParagraphStyle(
                name="CC_Link",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                fontName="Times-Roman",
                alignment=TA_LEFT,
                leftIndent=0,
                firstLineIndent=0,
            )
        )

        # Corporate Classic - Award/Project title (no left indent)
        add_style_if_not_exists(
            ParagraphStyle(
                name="CC_Title",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                spaceAfter=1,
                spaceBefore=6,
                fontName="Times-Bold",
                alignment=TA_LEFT,
                leftIndent=0,
                firstLineIndent=0,
            )
        )

        # Corporate Classic - Subtitle/Organization (no left indent)
        add_style_if_not_exists(
            ParagraphStyle(
                name="CC_Subtitle",
                parent=self.styles["Normal"],
                fontSize=10,
                textColor=colors.black,
                spaceAfter=2,
                spaceBefore=0,
                fontName="Times-Italic",
                alignment=TA_LEFT,
                leftIndent=0,
                firstLineIndent=0,
            )
        )

    async def generate_cv_pdf(
        self,
        content: str,
        candidate_name: str = "Candidate",
        template_name: str = "uk_professional_template",
    ) -> bytes:
        """
        Generate a professional CV PDF from text content.

        Args:
            content: CV text content (plain text or structured)
            candidate_name: Candidate's name for metadata
            template_name: Name of the template to use (default: uk_professional_template)
                          Options: "uk_professional_template", "bizarre_modern"

        Returns:
            PDF file as bytes

        Raises:
            ValueError: If content is empty or invalid
            Exception: If PDF generation fails
        """
        if not content or not content.strip():
            raise ValueError("CV content cannot be empty")

        # Validate template name
        valid_templates = list(self.TEMPLATE_CONFIGS.keys())
        if template_name not in valid_templates:
            logger.warning(
                f"Unknown template '{template_name}', falling back to uk_professional_template"
            )
            template_name = "uk_professional_template"

        try:
            logger.info(
                f"Generating CV PDF for candidate: {candidate_name} using template: {template_name}"
            )

            # Create PDF buffer
            buffer = io.BytesIO()

            # Create document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                leftMargin=self.MARGIN_LEFT,
                rightMargin=self.MARGIN_RIGHT,
                topMargin=self.MARGIN_TOP,
                bottomMargin=self.MARGIN_BOTTOM,
                title=f"CV - {candidate_name}",
                author=candidate_name,
                subject="Curriculum Vitae",
            )

            # Route to appropriate template renderer
            if template_name == "bizarre_modern":
                elements = self._parse_bizarre_modern_content(content)
                footer_func = self._add_bizarre_modern_footer
            elif template_name == "minimal_professional":
                elements = self._parse_minimal_professional_content(content)
                footer_func = self._add_minimal_professional_footer
            elif template_name == "bold":
                elements = self._parse_bold_content(content)
                footer_func = self._add_bold_footer
            elif template_name == "millennial_style":
                # Millennial style uses BaseDocTemplate with two-frame layout
                # for independent column flow across pages
                pdf_bytes = self._build_millennial_style_pdf(
                    content, candidate_name, buffer
                )
                return pdf_bytes
            elif template_name == "corporate_classic":
                elements = self._parse_corporate_classic_content(content)
                footer_func = self._add_corporate_classic_footer
            else:
                # Default: UK Professional Template
                elements = self._parse_cv_content(content)
                footer_func = self._add_cv_footer

            # Build PDF
            doc.build(
                elements,
                onFirstPage=footer_func,
                onLaterPages=footer_func,
            )

            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()

            logger.info(f"Successfully generated CV PDF ({len(pdf_bytes)} bytes)")
            return pdf_bytes

        except Exception as e:
            logger.error(f"Failed to generate CV PDF: {str(e)}", exc_info=True)
            raise Exception(f"PDF generation failed: {str(e)}")

    async def generate_cover_letter_pdf(
        self,
        content: str,
        candidate_name: str = "Candidate",
        company_name: str = "Company",
    ) -> bytes:
        """
        Generate a professional cover letter PDF from text content.

        Args:
            content: Cover letter text content
            candidate_name: Candidate's name for metadata
            company_name: Target company name for metadata

        Returns:
            PDF file as bytes

        Raises:
            ValueError: If content is empty or invalid
            Exception: If PDF generation fails
        """
        if not content or not content.strip():
            raise ValueError("Cover letter content cannot be empty")

        try:
            logger.info(
                f"Generating cover letter PDF for {candidate_name} -> {company_name}"
            )

            # Create PDF buffer
            buffer = io.BytesIO()

            # Create document
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                leftMargin=self.MARGIN_LEFT,
                rightMargin=self.MARGIN_RIGHT,
                topMargin=self.MARGIN_TOP,
                bottomMargin=self.MARGIN_BOTTOM,
                title=f"Cover Letter - {candidate_name}",
                author=candidate_name,
                subject=f"Cover Letter for {company_name}",
            )

            # Parse content and build PDF elements
            elements = self._parse_cover_letter_content(content, candidate_name)

            # Build PDF
            doc.build(
                elements,
                onFirstPage=self._add_cover_letter_footer,
                onLaterPages=self._add_cover_letter_footer,
            )

            # Get PDF bytes
            pdf_bytes = buffer.getvalue()
            buffer.close()

            logger.info(
                f"Successfully generated cover letter PDF ({len(pdf_bytes)} bytes)"
            )
            return pdf_bytes

        except Exception as e:
            logger.error(
                f"Failed to generate cover letter PDF: {str(e)}", exc_info=True
            )
            raise Exception(f"PDF generation failed: {str(e)}")

    def _parse_cv_content(self, content: str) -> list:
        """
        Parse CV text content and convert to PDF elements.

        Handles:
        - Name and contact information (first few lines)
        - Section headers (lines ending with ':' or uppercase)
        - Bullet points (lines starting with '-', '•', or '*')
        - Body text (paragraphs)

        Args:
            content: Raw CV text content

        Returns:
            List of reportlab flowables
        """
        elements = []
        # Preserve blank lines so section formatters can detect entry boundaries
        lines = [line.strip() for line in content.split("\n")]

        if not any(lines):
            raise ValueError("CV content is empty after parsing")

        # Skip leading blank lines to find the name
        _si = 0
        while _si < len(lines) and not lines[_si]:
            _si += 1
        name = lines[_si] if _si < len(lines) else "Candidate Name"
        elements.append(Paragraph(self._escape_text(name), self.styles["CustomHeader"]))

        # Second line might be job title (if it doesn't contain contact markers)
        job_title = ""
        idx = _si + 1
        while idx < len(lines) and not lines[idx]:
            idx += 1
        if idx < len(lines):
            potential_title = lines[idx]
            if not any(
                marker in potential_title
                for marker in ["@", "+", "http", ".com", ".io", ".dev", "|", "•"]
            ):
                if not self._is_section_header(potential_title):
                    job_title = potential_title
                    elements.append(
                        Paragraph(
                            self._escape_text(job_title), self.styles["CustomSubheader"]
                        )
                    )
                    idx += 1

        # Process contact info - collect ALL contact lines including portfolio links
        # These should all appear ABOVE the divider line
        contact_lines = []
        portfolio_lines = []

        # Scan through early lines for contact info and portfolio links
        _header_end = min(_si + 15, len(lines))
        while idx < _header_end:
            line = lines[idx]
            if not line:
                idx += 1
                continue
            # Stop if we hit a section header (check against whitelist)
            if self._is_section_header(line):
                break

            # Check if line is portfolio/links (contains common portfolio indicators)
            is_portfolio = any(
                marker in line.lower()
                for marker in [
                    "portfolio",
                    "github",
                    "linkedin",
                    "gitlab",
                    ".dev",
                    ".io",
                    ".com/",
                ]
            )

            # Check if line looks like contact info (contains @, +, or common separators)
            is_contact = (
                any(marker in line for marker in ["@", "+", "|", "•", "·"])
                and len(line) < 120
                and not line.rstrip().endswith(":")
            )

            if is_portfolio:
                portfolio_lines.append(line)
                idx += 1
            elif is_contact:
                contact_lines.append(line)
                idx += 1
            else:
                break

        # Add contact info
        if contact_lines:
            contact_text = " | ".join(contact_lines)
            elements.append(
                Paragraph(self._escape_text(contact_text), self.styles["ContactInfo"])
            )

        # Add portfolio/links (also above divider)
        if portfolio_lines:
            portfolio_text = " | ".join(portfolio_lines)
            # Clean up any "Portfolio:" prefix if present
            portfolio_text = portfolio_text.replace("Portfolio: ", "").replace(
                "Portfolio:", ""
            )
            elements.append(
                Paragraph(self._escape_text(portfolio_text), self.styles["ContactInfo"])
            )

        # Add divider line
        elements.append(Spacer(1, 0.15 * inch))
        elements.append(self._create_divider_line())
        elements.append(Spacer(1, 0.2 * inch))

        # Process remaining content
        current_section = []
        current_section_name = ""

        for line in lines[idx:]:
            # Check if it's a section header
            if self._is_section_header(line):
                # Add previous section content
                if current_section:
                    elements.extend(
                        self._format_section_content(
                            current_section, current_section_name
                        )
                    )
                    current_section = []

                # Add section header
                elements.append(Spacer(1, 0.15 * inch))
                section_title = line.rstrip(":").strip()
                current_section_name = section_title  # Track current section
                elements.append(
                    Paragraph(
                        self._escape_text(section_title.upper()),
                        self.styles["SectionHeader"],
                    )
                )
                elements.append(Spacer(1, 0.1 * inch))
            else:
                # Add to current section
                current_section.append(line)

        # Add final section
        if current_section:
            elements.extend(
                self._format_section_content(current_section, current_section_name)
            )

        return elements

    def _parse_cover_letter_content(
        self, content: str, candidate_name: str = "Candidate"
    ) -> list:
        """
        Parse cover letter text content and convert to PDF elements.

        Handles:
        - Date
        - Recipient address
        - Salutation
        - Body paragraphs
        - Closing

        Args:
            content: Raw cover letter text content
            candidate_name: Name of the candidate for signature

        Returns:
            List of reportlab flowables
        """
        elements = []
        # DON'T filter out empty lines - we need them to detect paragraph breaks!
        lines = [line.strip() for line in content.split("\n")]

        if not any(line for line in lines if line):  # Check if ALL lines are empty
            raise ValueError("Cover letter content is empty after parsing")

        # Add date
        current_date = datetime.now().strftime("%B %d, %Y")
        elements.append(Paragraph(current_date, self.styles["CoverLetterBody"]))
        elements.append(Spacer(1, 0.3 * inch))

        # Process content - split into paragraphs using blank lines as separators
        paragraphs = []
        current_para = []

        for line in lines:
            # Empty line indicates paragraph break
            if not line:
                if current_para:
                    paragraphs.append(" ".join(current_para))
                    current_para = []
            else:
                current_para.append(line)

        # Add final paragraph
        if current_para:
            paragraphs.append(" ".join(current_para))

        # Add all paragraphs to document with CoverLetterBody style (double-spaced)
        closing_found = False
        for i, para_text in enumerate(paragraphs):
            if para_text:
                # Check if this paragraph contains ONLY a closing phrase
                # (not "Best regards, John Doe" together)
                para_stripped = para_text.strip().rstrip(",").rstrip(".")

                # Check if it's EXACTLY a closing phrase (not mixed with other text)
                if para_stripped in [
                    "Best regards",
                    "Sincerely",
                    "Yours faithfully",
                    "Yours sincerely",
                    "Respectfully",
                    "Kind regards",
                    "Warm regards",
                ]:
                    # Add space before closing
                    elements.append(Spacer(1, 0.2 * inch))
                    # Add closing
                    elements.append(
                        Paragraph(
                            self._escape_text(para_text), self.styles["CoverLetterBody"]
                        )
                    )
                    # Add small space for signature
                    elements.append(Spacer(1, 0.05 * inch))
                    # Add candidate name
                    elements.append(
                        Paragraph(candidate_name, self.styles["CoverLetterBody"])
                    )
                    closing_found = True
                    # Stop processing - ignore anything after the closing
                    break

                # Check if paragraph starts with closing but has more text (like "Best regards, John Doe")
                # In this case, split it and handle separately
                for closing_phrase in [
                    "Best regards,",
                    "Sincerely,",
                    "Yours faithfully,",
                    "Yours sincerely,",
                    "Respectfully,",
                    "Kind regards,",
                    "Warm regards,",
                ]:
                    if para_text.strip().startswith(closing_phrase):
                        # This paragraph has closing + name together, just use the closing part
                        elements.append(Spacer(1, 0.2 * inch))
                        elements.append(
                            Paragraph(
                                self._escape_text(closing_phrase),
                                self.styles["CoverLetterBody"],
                            )
                        )
                        elements.append(Spacer(1, 0.05 * inch))
                        elements.append(
                            Paragraph(candidate_name, self.styles["CoverLetterBody"])
                        )
                        closing_found = True
                        break

                if closing_found:
                    break

                # All text uses the double-spaced CoverLetterBody style
                elements.append(
                    Paragraph(
                        self._escape_text(para_text), self.styles["CoverLetterBody"]
                    )
                )

                # Add extra space after salutation
                if para_text.startswith(("Dear", "To Whom", "Hello")):
                    elements.append(Spacer(1, 0.2 * inch))

        # If no closing was found in the AI content, add a default one
        if not closing_found:
            elements.append(Spacer(1, 0.2 * inch))
            elements.append(Paragraph("Best regards,", self.styles["CoverLetterBody"]))
            elements.append(Spacer(1, 0.05 * inch))
            elements.append(Paragraph(candidate_name, self.styles["CoverLetterBody"]))

        return elements

    def _format_section_content(self, lines: list, section_name: str = "") -> list:
        """
        Format section content with proper styling for different content types.

        Different sections need different formatting:
        - Experience/Projects: Job title bold, date italic, bullets for achievements
        - Education: Degree bold, institution + year on same line
        - Publications/Awards: Title normal, description as sub-item
        - Skills: Each category on its own line

        Args:
            lines: List of text lines in the section
            section_name: Name of the current section for context-aware formatting

        Returns:
            List of formatted PDF elements
        """
        elements = []
        i = 0
        section_lower = section_name.lower()
        is_multi_entry = any(
            sec in section_lower
            for sec in [
                "education",
                "academic",
                "qualification",
                "certification",
                "certificate",
                "license",
                "project",
                "portfolio",
                "award",
                "achievement",
                "honor",
                "volunteer",
                "community",
                "publication",
                "research",
                "paper",
            ]
        )

        # Grade keywords for detecting education grade lines with | separator
        _grade_kws = [
            "honours",
            "honor",
            "distinction",
            "first class",
            "second class",
            "gpa",
            "cgpa",
            "grade",
            "cum laude",
            "merit",
            "dean",
            "upper",
            "lower",
            "pass",
            "credit",
        ]

        # Degree/cert keywords for detecting education entry headings
        _degree_kws = [
            "bachelor",
            "master",
            "phd",
            "diploma",
            "degree",
            "bsc",
            "msc",
            "mba",
            "associate",
            "certificate",
            "doctor",
        ]

        # Track whether we just inserted a spacer (entry boundary)
        _after_spacer = True  # True at start so first line can be a heading

        while i < len(lines):
            line = lines[i]

            # Blank lines serve as entry separators in multi-entry sections
            if not line:
                if is_multi_entry and elements:
                    elements.append(Spacer(1, 0.08 * inch))
                    _after_spacer = True
                i += 1
                continue

            # In education sections, detect degree/cert heading lines (first line after entry break)
            is_edu_section = any(
                sec in section_lower
                for sec in ["education", "academic", "qualification"]
            )
            if (
                is_edu_section
                and _after_spacer
                and not line.startswith(("-", "•", "*", "○", "·"))
                and not self._is_date_line(line)
                and "|" not in line
            ):
                elements.append(
                    Paragraph(
                        f"<b>{self._escape_text(line)}</b>",
                        self.styles["JobTitle"],
                    )
                )
                _after_spacer = False
                i += 1
                continue

            _after_spacer = False

            # Check if it's a bullet point
            if line.startswith(("-", "•", "*", "○", "·")):
                bullet_text = line.lstrip("-•*○·").strip()

                # For publications/awards - bullet is the TITLE (should be bold)
                if any(
                    sec in section_lower
                    for sec in ["publication", "award", "achievement", "honor"]
                ):
                    elements.append(
                        Paragraph(
                            f"<b>{self._escape_text(bullet_text)}</b>",
                            self.styles["CVBodyText"],
                        )
                    )
                else:
                    # Normal bullet point
                    elements.append(
                        Paragraph(
                            f"• {self._escape_text(bullet_text)}",
                            self.styles["BulletPoint"],
                        )
                    )
                i += 1

            # Check if it's a job/project title line (contains | separator)
            elif "|" in line and not line.lower().startswith("technologies"):
                line_lower = line.lower()
                # In education sections, | might be a grade line not a title
                if any(
                    sec in section_lower
                    for sec in ["education", "academic", "qualification"]
                ) and any(kw in line_lower for kw in _grade_kws):
                    elements.append(
                        Paragraph(self._escape_text(line), self.styles["SubItem"])
                    )
                else:
                    # This is "Job Title | Company" or "Project Name | Role" format
                    elements.append(
                        Paragraph(
                            f"<b>{self._escape_text(line)}</b>",
                            self.styles["JobTitle"],
                        )
                    )
                i += 1

            # Check if it's a standalone project title (in projects section)
            elif "project" in section_lower and self._is_project_title(line, lines, i):
                # Standalone project title in projects section
                elements.append(
                    Paragraph(
                        f"<b>{self._escape_text(line)}</b>",
                        self.styles["JobTitle"],
                    )
                )
                i += 1

            # Check if it's a date/duration line
            elif self._is_date_line(line):
                elements.append(
                    Paragraph(self._escape_text(line), self.styles["DateStyle"])
                )
                i += 1

            # Check if it's a "Technologies:" line
            elif line.lower().startswith("technologies:"):
                elements.append(
                    Paragraph(self._escape_text(line), self.styles["SubItem"])
                )
                i += 1

            # For publications/awards - non-bullet lines after the title are descriptions
            elif any(
                sec in section_lower
                for sec in ["publication", "award", "achievement", "honor"]
            ):
                # Check if previous line was a bullet (title) - this is the description
                elements.append(
                    Paragraph(self._escape_text(line), self.styles["SubItem"])
                )
                i += 1

            # Regular body text
            else:
                elements.append(
                    Paragraph(self._escape_text(line), self.styles["CVBodyText"])
                )
                i += 1

        return elements

    def _is_date_line(self, line: str) -> bool:
        """Check if a line is a date/duration line using dynamic year range."""
        line_lower = line.lower()

        # Dynamic year range: 50 years back to 10 years forward
        current_year = datetime.now().year
        year_range = [str(y) for y in range(current_year - 50, current_year + 11)]

        # Month names and keywords
        month_markers = [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
            "jan",
            "feb",
            "mar",
            "apr",
            "jun",
            "jul",
            "aug",
            "sep",
            "oct",
            "nov",
            "dec",
            "present",
            "current",
            "ongoing",
            "now",
        ]

        # Combine all date markers
        date_markers = month_markers + year_range

        # Must contain a date marker
        has_date_marker = any(marker in line_lower for marker in date_markers)

        # Should be reasonably short (not a full sentence with dates in it)
        is_short = len(line) < 60

        # Should not start with bullet
        not_bullet = not line.startswith(("-", "•", "*", "○", "·"))

        return has_date_marker and is_short and not_bullet

    def _is_project_title(self, line: str, lines: list, current_index: int) -> bool:
        """
        Check if a line is a standalone project title in the projects section.

        A project title is typically:
        - Not too long (not a description)
        - Followed by description lines or technologies
        - Not starting with bullet points or "Technologies:"
        - Not containing obvious description markers
        """
        # Basic checks
        if not line or line.startswith(("-", "•", "*", "○", "·")):
            return False

        if line.lower().startswith("technologies:") or len(line) > 80:
            return False

        # Look ahead to see if next lines are descriptions or technologies
        next_index = current_index + 1
        if next_index < len(lines):
            next_line = lines[next_index]
            # If next line is a bullet, description, or technologies - current line is likely a title
            if (
                next_line.startswith(("-", "•", "*", "○", "·"))
                or next_line.lower().startswith("technologies:")
                or (len(next_line) > 50 and not next_line.endswith(":"))
            ):
                return True

        # Also check if it's a short, title-like line
        return len(line.strip()) < 80 and not any(
            word in line.lower()
            for word in ["developed", "built", "created", "implemented"]
        )

    # ============ BIZARRE & MODERN TEMPLATE METHODS ============

    def _parse_bizarre_modern_content(self, content: str) -> list:
        """
        Parse CV content and render using the Bizarre & Modern template.

        Features:
        - Large name with orange job title
        - Contact info with icons on the right side of header
        - Section headers with underlines (letter-spaced, uppercase)
        - Orange accent for position titles and degree names
        - Skills displayed in a grid with proficiency levels
        - Clean, modern typography (Helvetica)

        Args:
            content: Raw CV text content

        Returns:
            List of reportlab flowables
        """
        elements = []
        # Preserve blank lines so section formatters can detect entry boundaries
        lines = [line.strip() for line in content.split("\n")]

        if not any(lines):
            raise ValueError("CV content is empty after parsing")

        # ============ HEADER SECTION ============
        # Skip leading blank lines to find the name
        _si = 0
        while _si < len(lines) and not lines[_si]:
            _si += 1
        name = lines[_si] if _si < len(lines) else "Candidate Name"

        # Look for job title and contact info in the next few lines
        job_title = ""
        contact_lines = []
        portfolio_lines = []
        idx = _si + 1

        # Skip blank lines before job title
        while idx < len(lines) and not lines[idx]:
            idx += 1

        # Scan for job title (usually second line, not containing @ or common contact markers)
        if idx < len(lines):
            potential_title = lines[idx]
            # Job title usually doesn't contain @, +, http, .com, etc.
            if not any(
                marker in potential_title.lower()
                for marker in ["@", "+", "http", ".com", ".io", ".dev", "|", "•"]
            ):
                if not self._is_section_header(potential_title):
                    job_title = potential_title
                    idx += 1

        # Collect contact info and portfolio links
        _header_end = min(_si + 15, len(lines))
        while idx < _header_end:
            line = lines[idx]
            if not line:
                idx += 1
                continue
            if self._is_section_header(line):
                break

            is_portfolio = any(
                marker in line.lower()
                for marker in [
                    "portfolio",
                    "github",
                    "linkedin",
                    "gitlab",
                    ".dev",
                    ".io",
                    "http",
                    "www.",
                ]
            )

            is_contact = any(marker in line for marker in ["@", "+"])

            if is_portfolio:
                portfolio_lines.append(line)
                idx += 1
            elif is_contact or "|" in line or "•" in line:
                contact_lines.append(line)
                idx += 1
            else:
                break

        # Build header as a table (name/title on left, contact on right)
        header_elements = self._build_bizarre_modern_header(
            name, job_title, contact_lines, portfolio_lines
        )
        elements.extend(header_elements)

        # ============ CONTENT SECTIONS ============
        current_section = []
        current_section_name = ""
        pending_section_header = None  # Store header elements for KeepTogether

        for line in lines[idx:]:
            if self._is_section_header(line):
                # Process previous section
                if current_section:
                    section_content = self._format_bizarre_modern_section(
                        current_section, current_section_name
                    )

                    # If we have a pending header, combine with first content items
                    if pending_section_header:
                        # Keep header + first few content items together
                        keep_together_items = (
                            pending_section_header + section_content[:3]
                        )
                        remaining_items = section_content[3:]
                        elements.append(KeepTogether(keep_together_items))
                        elements.extend(remaining_items)
                        pending_section_header = None
                    else:
                        elements.extend(section_content)

                    current_section = []

                # Store section header for KeepTogether with content
                section_title = line.rstrip(":").strip()
                current_section_name = section_title
                pending_section_header = [
                    Spacer(1, 0.15 * inch),
                    self._create_bizarre_modern_section_header(section_title),
                    Spacer(1, 0.08 * inch),  # Spacing after underline
                ]
            else:
                current_section.append(line)

        # Add final section
        if current_section:
            section_content = self._format_bizarre_modern_section(
                current_section, current_section_name
            )

            if pending_section_header:
                # Keep header + first few content items together
                keep_together_items = pending_section_header + section_content[:3]
                remaining_items = section_content[3:]
                elements.append(KeepTogether(keep_together_items))
                elements.extend(remaining_items)
            else:
                elements.extend(section_content)

        return elements

    def _build_bizarre_modern_header(
        self, name: str, job_title: str, contact_lines: list, portfolio_lines: list
    ) -> list:
        """
        Build the header section for Bizarre & Modern template.

        Layout: Name and job title on the left, contact info on the right.

        Args:
            name: Candidate's name
            job_title: Current job title
            contact_lines: List of contact info lines
            portfolio_lines: List of portfolio/link lines

        Returns:
            List of flowables for the header
        """
        elements = []

        # Parse contact info for individual items
        contact_items = []
        for line in contact_lines:
            # Split by common separators
            parts = line.replace("•", "|").replace("·", "|").split("|")
            for part in parts:
                part = part.strip()
                if part:
                    contact_items.append(part)

        # Add portfolio items
        for line in portfolio_lines:
            parts = line.replace("•", "|").replace("·", "|").split("|")
            for part in parts:
                part = part.strip()
                if part:
                    contact_items.append(part)

        # Build left side (name + job title)
        left_content = []
        left_content.append(Paragraph(self._escape_text(name), self.styles["BM_Name"]))
        if job_title:
            left_content.append(
                Paragraph(self._escape_text(job_title), self.styles["BM_JobTitle"])
            )

        # Build right side (contact info with icons on left)
        right_content = []
        for item in contact_items:
            # Add icon prefix based on content type (icon on left like original design)
            icon = ""
            if item.startswith("+") or (
                item.replace("-", "")
                .replace(" ", "")
                .replace("(", "")
                .replace(")", "")
                .isdigit()
            ):
                icon = '<font name="Helvetica">&#x260E;</font>  '  # Phone
            elif "@" in item and "http" not in item.lower():
                icon = '<font name="Helvetica">&#x2709;</font>  '  # Email envelope
            elif "linkedin" in item.lower():
                icon = '<font name="Helvetica-Bold">in</font>  '  # LinkedIn
            elif (
                any(marker in item.lower() for marker in ["portfolio", ".dev", ".io"])
                and "github" not in item.lower()
            ):
                icon = '<font name="Helvetica">&#x2605;</font>  '  # Star for portfolio
            elif "github" in item.lower():
                icon = '<font name="Helvetica">&#x2318;</font>  '  # GitHub
            elif any(marker in item.lower() for marker in ["http", "www.", ".com"]):
                icon = '<font name="Helvetica">&#x2302;</font>  '  # Website/home
            elif any(
                marker in item.lower() for marker in ["location", "city", ","]
            ) or (len(item.split(",")) >= 2):
                icon = '<font name="Helvetica">&#x25CF;</font>  '  # Location dot

            right_content.append(
                Paragraph(f"{icon}{self._escape_text(item)}", self.styles["BM_Contact"])
            )

        # Create a table with left and right columns
        # Left column: ~60%, Right column: ~40%
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT
        left_width = available_width * 0.55
        right_width = available_width * 0.45

        # Combine left content into a single cell
        left_cell_content = (
            left_content if left_content else [Paragraph("", self.styles["BM_Name"])]
        )

        # Combine right content
        right_cell_content = (
            right_content
            if right_content
            else [Paragraph("", self.styles["BM_Contact"])]
        )

        # Create the header table
        header_data = [[left_cell_content, right_cell_content]]

        header_table = Table(
            header_data,
            colWidths=[left_width, right_width],
            style=TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (0, 0), (0, 0), "LEFT"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            ),
        )

        elements.append(header_table)
        elements.append(Spacer(1, 0.2 * inch))

        return elements

    def _create_bizarre_modern_section_header(self, title: str) -> Table:
        """
        Create a section header with underline for Bizarre & Modern template.

        Style: Uppercase, letter-spaced, with a black underline.

        Args:
            title: Section title text

        Returns:
            Table containing the styled section header
        """
        # Add letter spacing by inserting spaces between characters
        # Keep word spacing by handling each word separately
        words = title.upper().split()
        spaced_words = []
        for word in words:
            spaced_word = " ".join(word)  # Single space between letters
            spaced_words.append(spaced_word)
        # Use multiple non-breaking spaces between words to ensure visible gap
        word_separator = "\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0"  # 6 non-breaking spaces
        spaced_title = word_separator.join(spaced_words)

        header_para = Paragraph(
            self._escape_text(spaced_title), self.styles["BM_SectionHeader"]
        )

        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT

        # Create table with underline
        header_table = Table(
            [[header_para]],
            colWidths=[available_width],
            style=TableStyle(
                [
                    ("LINEBELOW", (0, 0), (-1, 0), 1, colors.HexColor("#1A1A1A")),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            ),
        )

        return header_table

    def _format_bizarre_modern_section(
        self, lines: list, section_name: str = ""
    ) -> list:
        """
        Format section content for Bizarre & Modern template.

        Args:
            lines: List of text lines in the section
            section_name: Name of the section for context-aware formatting

        Returns:
            List of formatted PDF elements
        """
        elements = []
        section_lower = section_name.lower()

        # Special handling for Skills section - create a grid
        if "skill" in section_lower:
            elements.extend(self._format_bizarre_modern_skills(lines))
            return elements

        # Special handling for Languages section - create a grid
        if "language" in section_lower:
            elements.extend(self._format_bizarre_modern_languages(lines))
            return elements

        # Special handling for Education section
        if "education" in section_lower:
            elements.extend(self._format_bizarre_modern_education(lines))
            return elements

        # Special handling for Certifications section
        if "certif" in section_lower:
            elements.extend(self._format_bizarre_modern_certifications(lines))
            return elements

        # Special handling for Projects section
        if "project" in section_lower:
            elements.extend(self._format_bizarre_modern_projects(lines))
            return elements

        # Special handling for Experience section
        if "experience" in section_lower:
            elements.extend(self._format_bizarre_modern_experience(lines))
            return elements

        # Special handling for Interests/Hobbies section (no bold, plain text)
        if "interest" in section_lower or "hobbi" in section_lower:
            elements.extend(self._format_bizarre_modern_interests(lines))
            return elements

        # Awards & Achievements
        if (
            "award" in section_lower
            or "achievement" in section_lower
            or "honor" in section_lower
        ):
            elements.extend(self._format_bizarre_modern_awards(lines))
            return elements

        # Volunteer / Community experience
        if "volunteer" in section_lower or "community" in section_lower:
            elements.extend(self._format_bizarre_modern_volunteer(lines))
            return elements

        # Publications / Research
        if (
            "publication" in section_lower
            or "research" in section_lower
            or "paper" in section_lower
        ):
            elements.extend(self._format_bizarre_modern_publications(lines))
            return elements

        # Professional memberships / affiliations
        if "membership" in section_lower or "affiliation" in section_lower:
            elements.extend(self._format_bizarre_modern_memberships(lines))
            return elements

        # Conferences & talks
        if (
            "conference" in section_lower
            or "talk" in section_lower
            or "speaking" in section_lower
        ):
            elements.extend(self._format_bizarre_modern_conferences(lines))
            return elements

        # Patents / intellectual property
        if "patent" in section_lower or "intellectual" in section_lower:
            elements.extend(self._format_bizarre_modern_patents(lines))
            return elements

        # References / referees
        if "reference" in section_lower or "referees" in section_lower:
            elements.extend(self._format_bizarre_modern_references(lines))
            return elements

        i = 0
        while i < len(lines):
            line = lines[i]

            if not line:
                i += 1
                continue

            # Check for experience/education entry with dates
            # Pattern: "Position | Company" followed by dates
            if "|" in line and not line.lower().startswith("technologies"):
                # This is a job/education title line
                parts = line.split("|")
                if len(parts) >= 2:
                    position = parts[0].strip()
                    company = parts[1].strip()

                    # Check if next line is a date
                    date_line = ""
                    if i + 1 < len(lines) and self._is_date_line(lines[i + 1]):
                        date_line = lines[i + 1]
                        i += 1

                    # Create a two-column layout: position/company on left, date on right
                    elements.extend(
                        self._create_bizarre_modern_entry_header(
                            position, company, date_line
                        )
                    )
                else:
                    # Just one part, treat as title
                    elements.append(
                        Paragraph(
                            self._escape_text(line), self.styles["BM_ExperienceTitle"]
                        )
                    )
                i += 1

            # Check for bullet points
            elif line.startswith(("-", "•", "*", "○", "·")):
                bullet_text = line.lstrip("-•*○·").strip()
                elements.append(
                    Paragraph(
                        f"• {self._escape_text(bullet_text)}", self.styles["BM_Bullet"]
                    )
                )
                i += 1

            # Check for date line (standalone)
            elif self._is_date_line(line):
                elements.append(
                    Paragraph(self._escape_text(line), self.styles["BM_Date"])
                )
                i += 1

            # Technologies line
            elif line.lower().startswith("technologies:"):
                elements.append(
                    Paragraph(
                        f"<i>{self._escape_text(line)}</i>", self.styles["BM_BodyText"]
                    )
                )
                i += 1

            # Regular body text
            else:
                elements.append(
                    Paragraph(self._escape_text(line), self.styles["BM_BodyText"])
                )
                i += 1

        return elements

    def _create_bizarre_modern_entry_header(
        self, position: str, company: str, date_line: str
    ) -> list:
        """
        Create an experience/education entry header with position, company, and date.

        Layout: Position (orange) + Company (gray) on left, Date on right

        Args:
            position: Job title or degree
            company: Company or institution name
            date_line: Date range string

        Returns:
            List of flowables
        """
        elements = []

        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT

        # Position in orange
        position_para = Paragraph(
            self._escape_text(position), self.styles["BM_ExperienceTitle"]
        )

        # Company in gray
        company_para = Paragraph(self._escape_text(company), self.styles["BM_Company"])

        # Date on right
        date_para = Paragraph(
            self._escape_text(date_line) if date_line else "", self.styles["BM_Date"]
        )

        # Create table for position + date
        if date_line:
            header_data = [[[position_para, company_para], date_para]]

            header_table = Table(
                header_data,
                colWidths=[available_width * 0.7, available_width * 0.3],
                style=TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ALIGN", (0, 0), (0, 0), "LEFT"),
                        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 6),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ]
                ),
            )
            elements.append(header_table)
        else:
            elements.append(position_para)
            elements.append(company_para)

        return elements

    def _format_bizarre_modern_skills(self, lines: list) -> list:
        """
        Format skills section as a two-column grid with proficiency levels.

        Args:
            lines: List of skill lines

        Returns:
            List of flowables
        """
        elements = []

        # Parse skills - can be in format "Skill: Level" or "Skill - Level" or just "Skill"
        skill_items = []

        for line in lines:
            # Skip empty lines and bullet-only lines
            if not line or line in ["-", "•", "*"]:
                continue

            # Remove bullet prefix
            clean_line = line.lstrip("-•*○·").strip()

            if not clean_line:
                continue

            # Check if line has multiple skills (comma or | separated)
            if "," in clean_line and ":" not in clean_line:
                parts = clean_line.split(",")
                for part in parts:
                    part = part.strip()
                    if part:
                        skill_items.append({"name": part, "level": ""})
            elif "|" in clean_line and ":" not in clean_line:
                parts = clean_line.split("|")
                for part in parts:
                    part = part.strip()
                    if part:
                        skill_items.append({"name": part, "level": ""})
            else:
                # Check for skill with proficiency level
                # Patterns: "Skill: Level", "Skill - Level", "Skill (Level)"
                name = clean_line
                level = ""

                if ":" in clean_line:
                    parts = clean_line.split(":", 1)
                    name = parts[0].strip()
                    level = parts[1].strip() if len(parts) > 1 else ""
                elif " - " in clean_line:
                    parts = clean_line.split(" - ", 1)
                    name = parts[0].strip()
                    level = parts[1].strip() if len(parts) > 1 else ""
                elif "(" in clean_line and ")" in clean_line:
                    name = clean_line.split("(")[0].strip()
                    level = clean_line.split("(")[1].rstrip(")").strip()

                # Common proficiency levels
                proficiency_keywords = [
                    "expert",
                    "advanced",
                    "intermediate",
                    "beginner",
                    "native",
                    "fluent",
                    "proficient",
                    "basic",
                ]

                # If name contains a proficiency keyword, it might be the level
                name_lower = name.lower()
                for prof in proficiency_keywords:
                    if prof in name_lower and not level:
                        # The name might contain the level at the end
                        break

                if name:
                    skill_items.append({"name": name, "level": level})

        # Create a two-column grid
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT
        col_width = available_width / 2 - 5

        # Build table data (two skills per row)
        table_data = []
        for i in range(0, len(skill_items), 2):
            row = []

            # First skill
            skill1 = skill_items[i]
            if skill1["level"]:
                cell1 = Paragraph(
                    f"<b>{self._escape_text(skill1['name'])}</b>  <font color='#4A4A4A'>{self._escape_text(skill1['level'])}</font>",
                    self.styles["BM_BodyText"],
                )
            else:
                cell1 = Paragraph(
                    f"<b>{self._escape_text(skill1['name'])}</b>",
                    self.styles["BM_BodyText"],
                )
            row.append(cell1)

            # Second skill (if exists)
            if i + 1 < len(skill_items):
                skill2 = skill_items[i + 1]
                if skill2["level"]:
                    cell2 = Paragraph(
                        f"<b>{self._escape_text(skill2['name'])}</b>  <font color='#4A4A4A'>{self._escape_text(skill2['level'])}</font>",
                        self.styles["BM_BodyText"],
                    )
                else:
                    cell2 = Paragraph(
                        f"<b>{self._escape_text(skill2['name'])}</b>",
                        self.styles["BM_BodyText"],
                    )
                row.append(cell2)
            else:
                row.append(Paragraph("", self.styles["BM_BodyText"]))

            table_data.append(row)

        if table_data:
            skills_table = Table(
                table_data,
                colWidths=[col_width, col_width],
                style=TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                ),
            )
            elements.append(skills_table)

        return elements

    def _format_bizarre_modern_languages(self, lines: list) -> list:
        """
        Format languages section as a two-column grid with proficiency.

        Args:
            lines: List of language lines

        Returns:
            List of flowables
        """
        elements = []

        # Parse languages - format "Language: Proficiency" or "Language - Proficiency"
        lang_items = []

        for line in lines:
            if not line:
                continue

            clean_line = line.lstrip("-•*○·").strip()
            if not clean_line:
                continue

            name = clean_line
            level = ""

            if ":" in clean_line:
                parts = clean_line.split(":", 1)
                name = parts[0].strip()
                level = parts[1].strip() if len(parts) > 1 else ""
            elif " - " in clean_line:
                parts = clean_line.split(" - ", 1)
                name = parts[0].strip()
                level = parts[1].strip() if len(parts) > 1 else ""
            elif "(" in clean_line and ")" in clean_line:
                name = clean_line.split("(")[0].strip()
                level = clean_line.split("(")[1].rstrip(")").strip()

            if name:
                lang_items.append({"name": name, "level": level})

        # Create two-column table
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT
        col_width = available_width / 2 - 5

        table_data = []
        for i in range(0, len(lang_items), 2):
            row = []

            lang1 = lang_items[i]
            cell1_text = f"<b>{self._escape_text(lang1['name'])}</b>"
            if lang1["level"]:
                cell1_text += f"  <font color='#4A4A4A'>{self._escape_text(lang1['level'])}</font>"
            row.append(Paragraph(cell1_text, self.styles["BM_BodyText"]))

            if i + 1 < len(lang_items):
                lang2 = lang_items[i + 1]
                cell2_text = f"<b>{self._escape_text(lang2['name'])}</b>"
                if lang2["level"]:
                    cell2_text += f"  <font color='#4A4A4A'>{self._escape_text(lang2['level'])}</font>"
                row.append(Paragraph(cell2_text, self.styles["BM_BodyText"]))
            else:
                row.append(Paragraph("", self.styles["BM_BodyText"]))

            table_data.append(row)

        if table_data:
            lang_table = Table(
                table_data,
                colWidths=[col_width, col_width],
                style=TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                ),
            )
            elements.append(lang_table)

        return elements

    def _format_bizarre_modern_education(self, lines: list) -> list:
        """
        Format education section matching the exact template layout.

        Layout per entry:
        Line 1: Degree/Program Name (orange, left) + Year (right, same line)
        Line 2: University Name - Degree Type (gray)
        Line 3: Grade if provided (plain black text)
        Then: One blank line before next entry

        Args:
            lines: List of education entry lines

        Returns:
            List of flowables
        """
        elements = []
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT

        # Parse education entries
        # Expected input formats:
        # Format 1: "Business Administration" / "Yale University - Bachelor of Science" / "2013"
        # Format 2: "Bachelor of Science in Computer Science" / "Imperial College London" / "2017" / "Upper Second Class Honours (2:1)"

        entries = []
        current_entry = {"degree": "", "institution": "", "year": "", "grade": ""}

        grade_keywords = [
            "honours",
            "honors",
            "class",
            "gpa",
            "grade",
            "distinction",
            "merit",
            "first",
            "second",
            "third",
            "2:1",
            "2:2",
            "1st",
            "2nd",
            "3rd",
        ]
        inst_keywords = [
            "university",
            "college",
            "institute",
            "school",
            "academy",
            "polytechnic",
        ]
        degree_keywords = [
            "bachelor",
            "master",
            "phd",
            "diploma",
            "degree",
            "bsc",
            "msc",
            "mba",
            "associate",
            "certificate",
            "science",
            "arts",
            "engineering",
            "business",
            "administration",
        ]

        def _has_primary_data(entry: dict) -> bool:
            return bool(entry["degree"] or entry["institution"])

        def _flush_current_entry():
            nonlocal current_entry
            if _has_primary_data(current_entry):
                entries.append(current_entry.copy())
            current_entry = {
                "degree": "",
                "institution": "",
                "year": "",
                "grade": "",
            }

        for raw_line in lines:
            line = (raw_line or "").strip()

            if not line:
                _flush_current_entry()
                continue

            line_lower = line.lower()
            is_date_line = self._is_date_line(line) and len(line) <= 40
            is_grade_line = any(
                kw in line_lower for kw in grade_keywords
            ) or line_lower.startswith("grade:")
            has_inst_keyword = any(kw in line_lower for kw in inst_keywords)
            is_degree_line = any(kw in line_lower for kw in degree_keywords)

            if is_date_line:
                if current_entry["year"] and _has_primary_data(current_entry):
                    _flush_current_entry()
                current_entry["year"] = line
                continue

            if is_grade_line:
                clean_grade = (
                    line.split(":", 1)[1].strip()
                    if line_lower.startswith("grade:")
                    else line
                )
                if current_entry["grade"] and clean_grade:
                    current_entry["grade"] = f"{current_entry['grade']}; {clean_grade}"
                else:
                    current_entry["grade"] = clean_grade
                continue

            if is_degree_line:
                if current_entry["degree"] and (
                    current_entry["institution"]
                    or current_entry["year"]
                    or current_entry["grade"]
                ):
                    _flush_current_entry()
                current_entry["degree"] = line
                continue

            if has_inst_keyword:
                if current_entry["institution"] and (
                    current_entry["degree"]
                    or current_entry["year"]
                    or current_entry["grade"]
                ):
                    _flush_current_entry()
                current_entry["institution"] = line
                continue

            # Fallback assignment for unclassified lines.
            if not current_entry["degree"]:
                current_entry["degree"] = line
            elif not current_entry["institution"]:
                current_entry["institution"] = line
            elif not current_entry["grade"]:
                current_entry["grade"] = line
            else:
                current_entry["grade"] = f"{current_entry['grade']}; {line}"

        _flush_current_entry()

        # Now render each entry
        for idx, entry in enumerate(entries):
            # Line 1: Degree name (orange) + Year (right-aligned) on same line
            degree_para = Paragraph(
                self._escape_text(entry["degree"]), self.styles["BM_Degree"]
            )
            year_para = Paragraph(
                self._escape_text(entry["year"]) if entry["year"] else "",
                self.styles["BM_Date"],
            )

            line1_table = Table(
                [[degree_para, year_para]],
                colWidths=[available_width * 0.75, available_width * 0.25],
                style=TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ALIGN", (0, 0), (0, 0), "LEFT"),
                        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ]
                ),
            )
            elements.append(line1_table)

            # Line 2: Institution - Degree Type (gray)
            if entry["institution"]:
                elements.append(
                    Paragraph(
                        self._escape_text(entry["institution"]),
                        self.styles["BM_Company"],
                    )
                )

            # Line 3: Grade (gray text) with Grade: prefix if provided
            if entry["grade"]:
                clean_grade = (
                    entry["grade"].split(":", 1)[1].strip()
                    if entry["grade"].lower().startswith("grade:")
                    else entry["grade"]
                )
                elements.append(
                    Paragraph(
                        f"<font color='#4A4A4A'>Grade: {self._escape_text(clean_grade)}</font>",
                        self.styles["BM_BodyText"],
                    )
                )

            # Add spacing between entries (but not after the last one)
            if idx < len(entries) - 1:
                elements.append(Spacer(1, 0.15 * inch))

        return elements

    def _format_bizarre_modern_certifications(self, lines: list) -> list:
        """
        Format certifications section for Bizarre & Modern template.

        Layout per entry:
        - Certificate name in bold BLACK (not orange)
        - Date right-aligned in GRAY on same line

        Args:
            lines: List of certification entry lines

        Returns:
            List of flowables
        """
        elements = []
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT

        i = 0
        while i < len(lines):
            line = lines[i]

            if not line:
                i += 1
                continue

            # Remove bullet prefix if present
            clean_line = line.lstrip("-•*○·").strip()

            if not clean_line:
                i += 1
                continue

            cert_name = clean_line
            date_str = ""

            # Check if the line contains a date at the end (format: "Cert Name (2023)" or "Cert Name - 2023")
            if "(" in clean_line and ")" in clean_line:
                paren_content = clean_line.split("(")[-1].rstrip(")")
                if self._is_date_line(paren_content):
                    cert_name = clean_line.split("(")[0].strip()
                    date_str = paren_content

            # Check next line for date
            if not date_str and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if self._is_date_line(next_line):
                    date_str = next_line
                    i += 1

            # Create row with cert name (bold black), date (gray) right-aligned
            cert_para = Paragraph(
                f"<b>{self._escape_text(cert_name)}</b>",
                self.styles["BM_BodyText"],  # Bold black text
            )
            date_para = Paragraph(
                f"<font color='#4A4A4A'>{self._escape_text(date_str)}</font>"
                if date_str
                else "",
                self.styles["BM_Date"],
            )

            cert_table = Table(
                [[cert_para, date_para]],
                colWidths=[available_width * 0.7, available_width * 0.3],
                style=TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ALIGN", (0, 0), (0, 0), "LEFT"),
                        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 4),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ]
                ),
            )
            elements.append(cert_table)

            i += 1

        return elements

    def _format_bizarre_modern_projects(self, lines: list) -> list:
        """
        Format projects section for Bizarre & Modern template.

        Layout per project:
        - Project name in ORANGE
        - Description as body text
        - Technologies line in gray italics

        Args:
            lines: List of project entry lines

        Returns:
            List of flowables
        """
        elements = []

        i = 0
        while i < len(lines):
            line = lines[i]

            if not line:
                i += 1
                continue

            # Check if this is a technologies line - gray italic
            if line.lower().startswith("technologies:"):
                elements.append(
                    Paragraph(
                        f"<i><font color='#4A4A4A'>{self._escape_text(line)}</font></i>",
                        self.styles["BM_BodyText"],
                    )
                )
                i += 1
                continue

            # Check if this is a project title (short line, not a bullet, not technologies)
            is_bullet = line.startswith(("-", "•", "*", "○", "·"))
            is_short = len(line) < 80
            is_technologies = "technologies:" in line.lower()

            # Determine if it's a title based on context
            is_title = is_short and not is_bullet and not is_technologies

            if is_title and i + 1 < len(lines):
                next_line = lines[i + 1] if i + 1 < len(lines) else ""
                # If next line is longer or is a description, this is a title
                if len(next_line) > len(line) or not next_line.startswith(("-", "•")):
                    is_title = True

            if is_title:
                # Project title - display in ORANGE
                elements.append(
                    Paragraph(
                        self._escape_text(line),
                        self.styles["BM_ExperienceTitle"],  # Orange title
                    )
                )
            elif is_bullet:
                bullet_text = line.lstrip("-•*○·").strip()
                elements.append(
                    Paragraph(
                        f"• {self._escape_text(bullet_text)}", self.styles["BM_Bullet"]
                    )
                )
            else:
                # Regular description text - convert to bullet point if it's a long description
                if len(line) > 50 and not line.startswith(
                    ("Technologies:", "Tech Stack:")
                ):
                    elements.append(
                        Paragraph(
                            f"• {self._escape_text(line)}", self.styles["BM_Bullet"]
                        )
                    )
                else:
                    elements.append(
                        Paragraph(self._escape_text(line), self.styles["BM_BodyText"])
                    )

            i += 1

        return elements

    def _format_bizarre_modern_experience(self, lines: list) -> list:
        """
        Format experience section exactly matching the screenshot.

        Layout per entry:
        Line 1: Position (orange, left) + Date (gray, right) - same line
        Line 2: Company (gray) - directly below position
        Then: Bullet points
        Finally: Technologies line at bottom

        Args:
            lines: List of experience entry lines

        Returns:
            List of flowables
        """
        elements = []
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT

        # Group lines into experience entries
        entries = []
        current_entry = {
            "position": "",
            "company": "",
            "date": "",
            "bullets": [],
            "technologies": "",
        }

        i = 0
        while i < len(lines):
            line = lines[i]

            if not line:
                # Empty line might indicate end of entry
                if current_entry["position"]:
                    entries.append(current_entry)
                    current_entry = {
                        "position": "",
                        "company": "",
                        "date": "",
                        "bullets": [],
                        "technologies": "",
                    }
                i += 1
                continue

            # Check for "Position | Company" format - this starts a new entry
            if "|" in line and not line.lower().startswith("technologies"):
                # Save previous entry if exists
                if current_entry["position"]:
                    entries.append(current_entry)
                    current_entry = {
                        "position": "",
                        "company": "",
                        "date": "",
                        "bullets": [],
                        "technologies": "",
                    }

                parts = line.split("|")
                current_entry["position"] = parts[0].strip()
                current_entry["company"] = parts[1].strip() if len(parts) > 1 else ""
                i += 1
                continue

            # Check for date line
            elif self._is_date_line(line):
                current_entry["date"] = line
                i += 1
                continue

            # Check for bullet points
            elif line.startswith(("-", "•", "*", "○", "·")):
                bullet_text = line.lstrip("-•*○·").strip()
                current_entry["bullets"].append(bullet_text)
                i += 1
                continue

            # Check for technologies line
            elif line.lower().startswith("technologies:"):
                current_entry["technologies"] = line
                i += 1
                continue

            # If we don't have a position yet, this might be one
            elif not current_entry["position"]:
                current_entry["position"] = line
                i += 1
                continue

            # If we have position but no company, this might be company
            elif not current_entry["company"]:
                current_entry["company"] = line
                i += 1
                continue

            # Otherwise treat as bullet point
            else:
                current_entry["bullets"].append(line)
                i += 1

        # Don't forget the last entry
        if current_entry["position"]:
            entries.append(current_entry)

        # Now render each entry exactly like the screenshot
        for idx, entry in enumerate(entries):
            # Add spacing before entry (except first one)
            if idx > 0:
                elements.append(Spacer(1, 0.12 * inch))

            # Line 1: Position (orange, left) + Date (gray, right) on same line
            position_para = Paragraph(
                self._escape_text(entry["position"]),
                self.styles["BM_ExperienceTitle"],  # Orange
            )
            date_para = Paragraph(
                f"<font color='#4A4A4A'>{self._escape_text(entry['date'])}</font>"
                if entry["date"]
                else "",
                self.styles["BM_Date"],
            )

            line1_table = Table(
                [[position_para, date_para]],
                colWidths=[available_width * 0.75, available_width * 0.25],
                style=TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ALIGN", (0, 0), (0, 0), "LEFT"),
                        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ]
                ),
            )
            elements.append(line1_table)

            # Line 2: Company (gray) - directly below position
            if entry["company"]:
                elements.append(
                    Paragraph(
                        f"<font color='#4A4A4A'>{self._escape_text(entry['company'])}</font>",
                        self.styles["BM_Company"],
                    )
                )

            # Bullet points - with proper bullet character like screenshot
            for bullet in entry["bullets"]:
                elements.append(
                    Paragraph(
                        f"• {self._escape_text(bullet)}", self.styles["BM_Bullet"]
                    )
                )

            # Technologies at bottom (gray italic) - no extra spacing needed
            if entry["technologies"]:
                elements.append(
                    Paragraph(
                        f"<i><font color='#4A4A4A'>{self._escape_text(entry['technologies'])}</font></i>",
                        self.styles["BM_BodyText"],
                    )
                )

        return elements

    def _format_bizarre_modern_interests(self, lines: list) -> list:
        """
        Format interests/hobbies section for Bizarre & Modern template.

        Layout: Plain text, NO bold - just bullet points with regular text.

        Args:
            lines: List of interest lines

        Returns:
            List of flowables
        """
        elements = []

        for line in lines:
            if not line:
                continue

            # Remove bullet prefix if present
            clean_line = line.lstrip("-•*○·").strip()

            if not clean_line:
                continue

            # Plain bullet point, no bold
            elements.append(
                Paragraph(
                    f"• {self._escape_text(clean_line)}", self.styles["BM_Bullet"]
                )
            )

        return elements

    def _format_bizarre_modern_awards(self, lines: list) -> list:
        """Format awards using Award | Organization pattern."""
        elements = []
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Check for Award | Organization pattern
            if "|" in line:
                parts = line.split("|", 1)
                award = parts[0].strip()
                org = parts[1].strip() if len(parts) > 1 else ""

                # Create award + org header
                award_para = Paragraph(
                    self._escape_text(award), self.styles["BM_ExperienceTitle"]
                )
                org_para = Paragraph(self._escape_text(org), self.styles["BM_Company"])

                elements.append(award_para)
                if org:
                    elements.append(org_para)

                i += 1

                # Next line might be year/date
                if i < len(lines) and self._is_date_line(lines[i].strip()):
                    date_para = Paragraph(
                        self._escape_text(lines[i].strip()), self.styles["BM_Date"]
                    )
                    elements.append(date_para)
                    i += 1
            else:
                # Handle other content
                clean = line.lstrip("-•*○·").strip()
                if line.startswith(("-", "•", "*", "○", "·")):
                    elements.append(
                        Paragraph(
                            f"• {self._escape_text(clean)}", self.styles["BM_Bullet"]
                        )
                    )
                else:
                    elements.append(
                        Paragraph(self._escape_text(clean), self.styles["BM_BodyText"])
                    )
                i += 1

        return elements

    def _format_bizarre_modern_volunteer(self, lines: list) -> list:
        """Format volunteer experience similar to experience but usually without technologies."""
        elements = []
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT

        entries = []
        current = {"role": "", "org": "", "date": "", "bullets": []}

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                if current["role"]:
                    entries.append(current)
                    current = {"role": "", "org": "", "date": "", "bullets": []}
                i += 1
                continue

            if "|" in line and not line.lower().startswith("technologies"):
                if current["role"]:
                    entries.append(current)
                    current = {"role": "", "org": "", "date": "", "bullets": []}
                parts = [p.strip() for p in line.split("|")]
                current["role"] = parts[0]
                current["org"] = parts[1] if len(parts) > 1 else ""
            elif self._is_date_line(line):
                current["date"] = line
            elif line.startswith(("-", "•", "*", "○", "·")):
                current["bullets"].append(line.lstrip("-•*○·").strip())
            elif not current["role"]:
                current["role"] = line
            elif not current["org"]:
                current["org"] = line
            else:
                current["bullets"].append(line)
            i += 1

        if current["role"]:
            entries.append(current)

        for idx, entry in enumerate(entries):
            if idx > 0:
                elements.append(Spacer(1, 0.12 * inch))

            role_para = Paragraph(
                self._escape_text(entry["role"]),
                self.styles["BM_ExperienceTitle"],
            )
            date_para = Paragraph(
                f"<font color='#4A4A4A'>{self._escape_text(entry['date'])}</font>"
                if entry["date"]
                else "",
                self.styles["BM_Date"],
            )
            header = Table(
                [[role_para, date_para]],
                colWidths=[available_width * 0.75, available_width * 0.25],
                style=TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ALIGN", (0, 0), (0, 0), "LEFT"),
                        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ]
                ),
            )
            elements.append(header)

            if entry["org"]:
                elements.append(
                    Paragraph(
                        f"<font color='#4A4A4A'>{self._escape_text(entry['org'])}</font>",
                        self.styles["BM_Company"],
                    )
                )

            for b in entry["bullets"]:
                elements.append(
                    Paragraph(f"• {self._escape_text(b)}", self.styles["BM_Bullet"])
                )

        return elements

    def _format_bizarre_modern_publications(self, lines: list) -> list:
        """Format publications using Title | Venue pattern."""
        elements = []
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Check for Title | Venue pattern
            if "|" in line and not line.lower().startswith("technologies"):
                parts = line.split("|", 1)
                title = parts[0].strip()
                venue = parts[1].strip() if len(parts) > 1 else ""

                # Create title + venue header
                title_para = Paragraph(
                    self._escape_text(title), self.styles["BM_ExperienceTitle"]
                )
                venue_para = Paragraph(
                    self._escape_text(venue), self.styles["BM_ExperienceTitle"]
                )

                # Show title first, then venue below
                elements.append(title_para)
                if venue:
                    elements.append(venue_para)

                i += 1

                # Next line might be year/date
                if i < len(lines) and self._is_date_line(lines[i].strip()):
                    date_para = Paragraph(
                        self._escape_text(lines[i].strip()), self.styles["BM_Date"]
                    )
                    elements.append(date_para)
                    i += 1

            else:
                # Handle description lines and bullets
                clean = line.lstrip("-•*○·").strip()
                if line.startswith(("-", "•", "*", "○", "·")):
                    elements.append(
                        Paragraph(
                            f"• {self._escape_text(clean)}", self.styles["BM_Bullet"]
                        )
                    )
                else:
                    elements.append(
                        Paragraph(self._escape_text(clean), self.styles["BM_BodyText"])
                    )
                i += 1

        return elements

    def _format_bizarre_modern_memberships(self, lines: list) -> list:
        """Format professional memberships as simple lines or bullets."""
        elements = []

        for line in lines:
            if not line.strip():
                continue
            clean = line.lstrip("-•*○·").strip()
            if not clean:
                continue
            elements.append(
                Paragraph(
                    f"• {self._escape_text(clean)}",
                    self.styles["BM_Bullet"],
                )
            )

        return elements

    def _format_bizarre_modern_conferences(self, lines: list) -> list:
        """Format conferences and talks: title + event/date details."""
        elements = []

        for line in lines:
            if not line.strip():
                continue
            clean = line.lstrip("-•*○·").strip()
            if not clean:
                continue

            # Check if line contains talk title and event (separated by colon or "at")
            if ":" in clean or " at " in clean:
                # This is a talk title with event - make title orange
                if ":" in clean:
                    parts = clean.split(":", 1)
                    title = parts[0].strip()
                    event = parts[1].strip() if len(parts) > 1 else ""
                else:
                    parts = clean.split(" at ", 1)
                    title = parts[0].strip()
                    event = "at " + parts[1].strip() if len(parts) > 1 else ""

                elements.append(
                    Paragraph(
                        self._escape_text(title),
                        self.styles["BM_ExperienceTitle"],
                    )
                )
                if event:
                    elements.append(
                        Paragraph(
                            self._escape_text(event),
                            self.styles["BM_BodyText"],
                        )
                    )
            else:
                # Simple bullet point
                elements.append(
                    Paragraph(
                        f"• {self._escape_text(clean)}",
                        self.styles["BM_Bullet"],
                    )
                )

        return elements

    def _format_bizarre_modern_patents(self, lines: list) -> list:
        """Format patents using Patent Title | Patent Number pattern."""
        elements = []

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Check for Patent Title | Patent Number pattern
            if "|" in line:
                parts = line.split("|", 1)
                title = parts[0].strip()
                number = parts[1].strip() if len(parts) > 1 else ""

                # Patent title (orange)
                elements.append(
                    Paragraph(
                        self._escape_text(title), self.styles["BM_ExperienceTitle"]
                    )
                )

                # Patent number (orange)
                if number:
                    elements.append(
                        Paragraph(
                            self._escape_text(number), self.styles["BM_ExperienceTitle"]
                        )
                    )

                i += 1

                # Next line might be year
                if i < len(lines) and self._is_date_line(lines[i].strip()):
                    elements.append(
                        Paragraph(
                            self._escape_text(lines[i].strip()), self.styles["BM_Date"]
                        )
                    )
                    i += 1
            else:
                # Handle description lines
                clean = line.lstrip("-•*○·").strip()
                elements.append(
                    Paragraph(self._escape_text(clean), self.styles["BM_BodyText"])
                )
                i += 1

        return elements

    def _format_bizarre_modern_references(self, lines: list) -> list:
        """Format references: name | role plus contact line."""
        elements = []

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            clean = line.lstrip("-•*○·").strip()
            if not clean:
                i += 1
                continue

            # First line: name and role / company
            elements.append(
                Paragraph(
                    self._escape_text(clean),
                    self.styles["BM_ExperienceTitle"],
                )
            )
            i += 1

            # Optional contact line immediately after
            if i < len(lines):
                contact = lines[i].strip()
                if contact and not self._is_section_header(contact):
                    elements.append(
                        Paragraph(
                            self._escape_text(contact),
                            self.styles["BM_BodyText"],
                        )
                    )
                    i += 1

        return elements

    def _add_bizarre_modern_footer(
        self, canvas_obj: canvas.Canvas, doc: SimpleDocTemplate
    ):
        """
        Add footer to Bizarre & Modern template pages.

        Args:
            canvas_obj: ReportLab canvas object
            doc: Document object
        """
        canvas_obj.saveState()

        page_num = canvas_obj.getPageNumber()
        text = f"Page {page_num}"

        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(colors.HexColor("#4A4A4A"))
        canvas_obj.drawCentredString(self.PAGE_WIDTH / 2, 0.4 * inch, text)

        canvas_obj.restoreState()

    # ============ MINIMAL PROFESSIONAL TEMPLATE METHODS ============

    def _parse_minimal_professional_content(self, content: str) -> list:
        """
        Parse CV content for the Minimal Professional template.

        Features:
        - Dark header with white text (name + job title)
        - Clean white body with black text
        - Minimal typography with Helvetica
        - Simple section headers
        - Clean bullet points and layout

        Args:
            content: Raw CV text content

        Returns:
            List of reportlab flowables
        """
        elements = []
        # Preserve blank lines so section formatters can detect entry boundaries
        lines = [line.strip() for line in content.split("\n")]

        if not any(lines):
            raise ValueError("CV content is empty after parsing")

        # ============ PARSE HEADER INFORMATION ============
        _si = 0
        while _si < len(lines) and not lines[_si]:
            _si += 1
        name = lines[_si] if _si < len(lines) else "Candidate Name"
        job_title = ""
        contact_lines = []
        portfolio_lines = []
        idx = _si + 1

        # Skip blank lines before job title
        while idx < len(lines) and not lines[idx]:
            idx += 1

        # Look for job title (usually second line)
        if idx < len(lines):
            potential_title = lines[idx]
            if not any(
                marker in potential_title.lower()
                for marker in ["@", "+", "http", ".com", ".io", ".dev", "|", "•"]
            ):
                if not self._is_section_header(potential_title):
                    job_title = potential_title
                    idx += 1

        # Collect contact and portfolio info
        _header_end = min(_si + 15, len(lines))
        while idx < _header_end:
            line = lines[idx]
            if not line:
                idx += 1
                continue
            if self._is_section_header(line):
                break

            is_portfolio = any(
                marker in line.lower()
                for marker in [
                    "portfolio",
                    "github",
                    "linkedin",
                    "gitlab",
                    ".dev",
                    ".io",
                    "http",
                    "www.",
                ]
            )

            is_contact = (
                any(marker in line for marker in ["@", "+"])
                or "|" in line
                or "•" in line
            )

            if is_portfolio:
                portfolio_lines.append(line)
            elif is_contact:
                contact_lines.append(line)
            else:
                break
            idx += 1

        # Build header with dark background
        header_elements = self._build_minimal_professional_header(
            name, job_title, contact_lines, portfolio_lines
        )
        elements.extend(header_elements)

        # ============ PARSE CONTENT SECTIONS ============
        current_section = []
        current_section_name = ""

        for line in lines[idx:]:
            if self._is_section_header(line):
                # Process previous section
                if current_section:
                    section_elements = self._format_minimal_professional_section(
                        current_section, current_section_name
                    )
                    elements.extend(section_elements)
                    current_section = []

                # Add section header
                section_title = line.rstrip(":").strip()
                current_section_name = section_title
                elements.append(Spacer(1, 0.15 * inch))
                elements.append(
                    Paragraph(
                        self._escape_text(section_title.upper()),
                        self.styles["MP_SectionHeader"],
                    )
                )
                elements.append(Spacer(1, 0.08 * inch))
            else:
                current_section.append(line)

        # Add final section
        if current_section:
            section_elements = self._format_minimal_professional_section(
                current_section, current_section_name
            )
            elements.extend(section_elements)

        return elements

    def _build_minimal_professional_header(
        self, name: str, job_title: str, contact_lines: list, portfolio_lines: list
    ) -> list:
        """
        Build the dark header section for Minimal Professional template.

        Creates a dark charcoal header with white text containing:
        - Name (large, bold)
        - Job title (medium)
        - Contact information (clean layout)

        Args:
            name: Candidate's name
            job_title: Current job title
            contact_lines: List of contact info lines
            portfolio_lines: List of portfolio/link lines

        Returns:
            List of flowables for the header
        """
        elements = []

        # Create dark header background with white text
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT

        # Header content in white text
        header_content = []

        # Name (large, bold, white)
        header_content.append(
            Paragraph(self._escape_text(name), self.styles["MP_HeaderName"])
        )

        # Job title (medium, white)
        if job_title:
            header_content.append(
                Paragraph(self._escape_text(job_title), self.styles["MP_HeaderTitle"])
            )

        # Create header table with dark background
        header_table = Table(
            [[header_content]],
            colWidths=[available_width],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#404040")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 20),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 20),
                    ("TOPPADDING", (0, 0), (-1, -1), 20),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 20),
                ]
            ),
        )

        elements.append(header_table)
        elements.append(Spacer(1, 0.2 * inch))

        # Contact information below header (gray text on white)
        contact_items = []
        for line in contact_lines + portfolio_lines:
            parts = line.replace("•", "|").replace("·", "|").split("|")
            for part in parts:
                part = part.strip()
                if part:
                    contact_items.append(part)

        if contact_items:
            contact_text = " // ".join(contact_items)
            elements.append(
                Paragraph(self._escape_text(contact_text), self.styles["MP_Contact"])
            )
            elements.append(Spacer(1, 0.1 * inch))

        return elements

    def _format_minimal_professional_section(
        self, lines: list, section_name: str = ""
    ) -> list:
        """
        Format section content for Minimal Professional template.

        Args:
            lines: List of text lines in the section
            section_name: Name of the section for context-aware formatting

        Returns:
            List of formatted PDF elements
        """
        elements = []
        section_lower = section_name.lower()
        is_multi_entry = any(
            sec in section_lower
            for sec in [
                "education",
                "academic",
                "qualification",
                "certification",
                "certificate",
                "license",
                "project",
                "portfolio",
                "award",
                "achievement",
                "honor",
                "volunteer",
                "community",
                "publication",
                "research",
                "paper",
            ]
        )

        # Grade keywords for detecting education grade lines with | separator
        _grade_kws = [
            "honours",
            "honor",
            "distinction",
            "first class",
            "second class",
            "gpa",
            "cgpa",
            "grade",
            "cum laude",
            "merit",
            "dean",
            "upper",
            "lower",
            "pass",
            "credit",
        ]

        # Special handling for Professional Summary section
        if "summary" in section_lower or "profile" in section_lower:
            for line in lines:
                if line.strip():
                    elements.append(
                        Paragraph(
                            self._escape_text(line), self.styles["MP_ProfileSummary"]
                        )
                    )
            return elements

        # Detect education and project sections for heading detection
        _is_education = any(
            sec in section_lower for sec in ["education", "academic", "qualification"]
        )
        _is_project = any(sec in section_lower for sec in ["project", "portfolio"])

        # Degree / heading keywords for education entries
        _degree_kws = [
            "bachelor",
            "master",
            "doctor",
            "phd",
            "diploma",
            "associate",
            "certificate",
            "degree",
            "b.sc",
            "m.sc",
            "b.a",
            "m.a",
            "mba",
            "b.eng",
            "m.eng",
            "bsc",
            "msc",
            "llb",
            "llm",
            "md",
        ]

        # Track entry boundaries for heading detection
        _after_spacer = True  # True at start to catch first entry

        # General section processing
        i = 0
        while i < len(lines):
            line = lines[i]

            # Blank lines serve as entry separators in multi-entry sections
            if not line:
                if is_multi_entry and elements:
                    elements.append(Spacer(1, 0.08 * inch))
                    _after_spacer = True
                i += 1
                continue

            # Check for job/position title with company (contains |)
            if "|" in line and not line.lower().startswith("technologies"):
                line_lower = line.lower()
                # In education sections, | might be a grade line not a title
                if _is_education and any(kw in line_lower for kw in _grade_kws):
                    elements.append(
                        Paragraph(self._escape_text(line), self.styles["MP_BodyText"])
                    )
                    i += 1
                    continue

                parts = line.split("|", 1)
                position = parts[0].strip()
                company = parts[1].strip() if len(parts) > 1 else ""

                # Position title (bold)
                elements.append(
                    Paragraph(
                        self._escape_text(position), self.styles["MP_PositionTitle"]
                    )
                )

                # Company name (regular)
                if company:
                    elements.append(
                        Paragraph(self._escape_text(company), self.styles["MP_Company"])
                    )

                _after_spacer = False
                i += 1

                # Check if next line is a date
                if i < len(lines) and self._is_date_line(lines[i]):
                    elements.append(
                        Paragraph(self._escape_text(lines[i]), self.styles["MP_Date"])
                    )
                    i += 1

            # Check for bullet points
            elif line.startswith(("-", "•", "*", "○", "·")):
                bullet_text = line.lstrip("-•*○·").strip()
                elements.append(
                    Paragraph(
                        f"• {self._escape_text(bullet_text)}", self.styles["MP_Bullet"]
                    )
                )
                _after_spacer = False
                i += 1

            # Check for date line
            elif self._is_date_line(line):
                elements.append(
                    Paragraph(self._escape_text(line), self.styles["MP_Date"])
                )
                i += 1

            # Education heading: first line after entry boundary
            elif (
                _after_spacer
                and _is_education
                and not any(kw in line.lower() for kw in _grade_kws)
            ):
                elements.append(
                    Paragraph(self._escape_text(line), self.styles["MP_PositionTitle"])
                )
                _after_spacer = False
                i += 1

            # Project heading: first line after entry boundary
            elif _after_spacer and _is_project and len(line) < 80:
                elements.append(
                    Paragraph(self._escape_text(line), self.styles["MP_PositionTitle"])
                )
                _after_spacer = False
                i += 1

            # Regular body text
            else:
                elements.append(
                    Paragraph(self._escape_text(line), self.styles["MP_BodyText"])
                )
                _after_spacer = False
                i += 1

        return elements

    def _add_minimal_professional_footer(
        self, canvas_obj: canvas.Canvas, doc: SimpleDocTemplate
    ):
        """
        Add footer to Minimal Professional template pages.

        Args:
            canvas_obj: ReportLab canvas object
            doc: Document object
        """
        canvas_obj.saveState()

        page_num = canvas_obj.getPageNumber()
        text = f"Page {page_num}"

        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(colors.HexColor("#666666"))
        canvas_obj.drawCentredString(self.PAGE_WIDTH / 2, 0.4 * inch, text)

        canvas_obj.restoreState()

    # ============ BOLD TEMPLATE METHODS ============

    def _parse_bold_content(self, content: str) -> list:
        """
        Parse CV content for the Bold template with TWO-COLUMN layout.

        Features:
        - Dark header with name LEFT, job title RIGHT
        - Contact info with // separators
        - TWO-COLUMN body: Section labels LEFT (~22%), content RIGHT (~78%)
        - Bold lead-in text on bullet points
        - ACHIEVEMENTS + HIGHLIGHTS sub-headers

        Args:
            content: Raw CV text content

        Returns:
            List of reportlab flowables
        """
        elements = []
        # Preserve blank lines so section formatters can detect entry boundaries
        lines = [line.strip() for line in content.split("\n")]

        if not any(lines):
            raise ValueError("CV content is empty after parsing")

        # ============ PARSE HEADER INFORMATION ============
        _si = 0
        while _si < len(lines) and not lines[_si]:
            _si += 1
        name = lines[_si] if _si < len(lines) else "Candidate Name"
        job_title = ""
        contact_lines = []
        portfolio_lines = []
        idx = _si + 1

        # Skip blank lines before job title
        while idx < len(lines) and not lines[idx]:
            idx += 1

        # Look for job title (usually second line)
        if idx < len(lines):
            potential_title = lines[idx]
            if not any(
                marker in potential_title.lower()
                for marker in ["@", "+", "http", ".com", ".io", ".dev", "|", "•", "//"]
            ):
                if not self._is_section_header(potential_title):
                    job_title = potential_title
                    idx += 1

        # Collect contact and portfolio info
        _header_end = min(_si + 15, len(lines))
        while idx < _header_end:
            line = lines[idx]
            if not line:
                idx += 1
                continue
            if self._is_section_header(line):
                break

            is_portfolio = any(
                marker in line.lower()
                for marker in [
                    "portfolio",
                    "github",
                    "linkedin",
                    "gitlab",
                    ".dev",
                    ".io",
                    "http",
                    "www.",
                ]
            )

            is_contact = (
                any(marker in line for marker in ["@", "+"])
                or "//" in line
                or "|" in line
                or "•" in line
            )

            if is_portfolio or is_contact:
                contact_lines.append(line)
            else:
                break
            idx += 1

        # Build header with dark background (name LEFT, title RIGHT)
        header_elements = self._build_bold_header(name, job_title, contact_lines)
        elements.extend(header_elements)

        # ============ PARSE CONTENT SECTIONS ============
        # Group content by sections for two-column layout
        sections = []
        current_section_name = ""
        current_section_content = []

        for line in lines[idx:]:
            if self._is_section_header(line):
                # Save previous section
                if current_section_name or current_section_content:
                    sections.append(
                        {
                            "name": current_section_name,
                            "content": current_section_content,
                        }
                    )
                # Start new section
                current_section_name = line.rstrip(":").strip()
                current_section_content = []
            else:
                current_section_content.append(line)

        # Add final section
        if current_section_name or current_section_content:
            sections.append(
                {"name": current_section_name, "content": current_section_content}
            )

        # Render each section with two-column layout
        for section in sections:
            section_elements = self._render_bold_section(
                section["name"], section["content"]
            )
            elements.extend(section_elements)

        return elements

    def _build_bold_header(
        self, name: str, job_title: str, contact_lines: list
    ) -> list:
        """
        Build the dark header for Bold template - like screenshot 2.

        Layout:
        - Dark header bar: Name (LEFT), Job Title (RIGHT) - ONLY
        - Below header (white bg): Contact info with // separators
        - Separator line

        Args:
            name: Candidate's name
            job_title: Current job title
            contact_lines: List of contact info lines

        Returns:
            List of flowables for the header
        """
        elements = []

        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT

        # Create header content - name on left, title on right (ONLY these in dark bar)
        name_para = Paragraph(self._escape_text(name), self.styles["Bold_HeaderName"])

        title_para = Paragraph(
            self._escape_text(job_title) if job_title else "",
            self.styles["Bold_HeaderTitle"],
        )

        # Create dark header table with ONLY name and title
        header_data = [[name_para, title_para]]

        header_table = Table(
            header_data,
            colWidths=[available_width * 0.55, available_width * 0.45],
            style=TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#3D3D3D")),
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (0, 0), (0, 0), "LEFT"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 20),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 20),
                    ("TOPPADDING", (0, 0), (-1, -1), 18),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 18),
                ]
            ),
        )

        elements.append(header_table)
        elements.append(Spacer(1, 0.15 * inch))

        # Build contact info string with // separators - BELOW header on white background
        contact_items = []
        for line in contact_lines:
            # Split by various separators and collect items
            parts = (
                line.replace("•", "//")
                .replace("|", "//")
                .replace("·", "//")
                .split("//")
            )
            for part in parts:
                part = part.strip()
                if part:
                    contact_items.append(part)

        if contact_items:
            contact_text = "  //  ".join(contact_items)
            elements.append(
                Paragraph(self._escape_text(contact_text), self.styles["Bold_Contact"])
            )
            elements.append(Spacer(1, 0.1 * inch))

            # Add separator line after contact info
            separator_line = Table(
                [[""]],
                colWidths=[available_width],
                style=TableStyle(
                    [
                        (
                            "LINEBELOW",
                            (0, 0),
                            (-1, -1),
                            0.5,
                            colors.HexColor("#CCCCCC"),
                        ),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ]
                ),
            )
            elements.append(separator_line)
            elements.append(Spacer(1, 0.15 * inch))

        return elements

    def _render_bold_section(self, section_name: str, content_lines: list) -> list:
        """
        Render a section with TWO-COLUMN layout.

        LEFT column (~22%): Section label (uppercase, bold)
        RIGHT column (~78%): Section content

        Uses individual rows for each content item to allow proper page breaks.

        Args:
            section_name: Name of the section (e.g., "PROFILE", "EXPERIENCE")
            content_lines: List of content lines for the section

        Returns:
            List of flowables
        """
        elements = []

        if not section_name and not content_lines:
            return elements

        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT
        left_width = available_width * 0.22
        right_width = available_width * 0.78

        # Format content for right column - returns list of flowables
        right_content_list = self._format_bold_section_content(
            content_lines, section_name
        )

        if not right_content_list:
            return elements

        # Build table rows - first row has section label, rest have empty left cell
        table_data = []
        for i, content_item in enumerate(right_content_list):
            if i == 0:
                # First row: section label on left, content on right
                section_label = Paragraph(
                    self._escape_text(section_name.upper()) if section_name else "",
                    self.styles["Bold_SectionLabel"],
                )
                table_data.append([section_label, content_item])
            else:
                # Subsequent rows: empty left cell, content on right
                table_data.append(["", content_item])

        # Create the section table with all rows
        section_table = Table(
            table_data,
            colWidths=[left_width, right_width],
            style=TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("ALIGN", (1, 0), (1, -1), "LEFT"),
                    ("LEFTPADDING", (0, 0), (0, -1), 0),
                    ("LEFTPADDING", (1, 0), (1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ]
            ),
            splitByRow=True,  # Allow table to split across pages
        )

        elements.append(section_table)

        # Add horizontal separator line after each section
        elements.append(Spacer(1, 0.08 * inch))
        separator_line = Table(
            [[""]],
            colWidths=[available_width],
            style=TableStyle(
                [
                    ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            ),
        )
        elements.append(separator_line)
        elements.append(Spacer(1, 0.12 * inch))

        return elements

    def _format_bold_section_content(self, lines: list, section_name: str = "") -> list:
        """
        Format section content for the RIGHT column of Bold template.

        Handles:
        - Profile/Summary text
        - Experience entries with company//location//date format
        - ACHIEVEMENTS + HIGHLIGHTS sub-headers
        - Bold lead-in bullet points
        - Education, Skills, etc.

        Args:
            lines: Content lines for the section
            section_name: Section name for context-aware formatting

        Returns:
            List of flowables for the right column
        """
        content = []
        section_lower = section_name.lower()

        # Profile/Summary - just paragraph text
        if "profile" in section_lower or "summary" in section_lower:
            for line in lines:
                if line.strip():
                    content.append(
                        Paragraph(
                            self._escape_text(line), self.styles["Bold_ProfileText"]
                        )
                    )
            return content

        # Experience section - special handling
        if "experience" in section_lower:
            content.extend(self._format_bold_experience(lines))
            return content

        # Education section
        if "education" in section_lower:
            content.extend(self._format_bold_education(lines))
            return content

        # Skills section
        if "skill" in section_lower:
            content.extend(self._format_bold_skills(lines))
            return content

        # Certifications section
        if "certif" in section_lower:
            content.extend(self._format_bold_certifications(lines))
            return content

        # Projects section
        if "project" in section_lower:
            content.extend(self._format_bold_projects(lines))
            return content

        # Languages section
        if "language" in section_lower:
            content.extend(self._format_bold_languages(lines))
            return content

        # Awards/Achievements section
        if "award" in section_lower or "achievement" in section_lower:
            content.extend(self._format_bold_awards(lines))
            return content

        # Volunteer section
        if "volunteer" in section_lower:
            content.extend(self._format_bold_volunteer(lines))
            return content

        # Publications section
        if "publication" in section_lower:
            content.extend(self._format_bold_publications(lines))
            return content

        # Memberships section
        if "membership" in section_lower:
            content.extend(self._format_bold_memberships(lines))
            return content

        # Conferences section
        if "conference" in section_lower or "talk" in section_lower:
            content.extend(self._format_bold_conferences(lines))
            return content

        # Patents section
        if "patent" in section_lower:
            content.extend(self._format_bold_patents(lines))
            return content

        # References section
        if "reference" in section_lower:
            content.extend(self._format_bold_references(lines))
            return content

        # Interests section
        if "interest" in section_lower or "hobbi" in section_lower:
            content.extend(self._format_bold_interests(lines))
            return content

        # Default: generic formatting
        content.extend(self._format_bold_generic(lines))
        return content

    def _format_bold_experience(self, lines: list) -> list:
        """
        Format experience section for Bold template.

        Layout:
        - POSITION TITLE (bold, uppercase)
        - Company // Location // Date
        - Description paragraph
        - ACHIEVEMENTS + HIGHLIGHTS (sub-header)
        - Bullet points with bold lead-in

        Args:
            lines: Experience content lines

        Returns:
            List of flowables
        """
        content = []
        i = 0

        while i < len(lines):
            line = lines[i]

            if not line:
                i += 1
                continue

            # Check for position title with company (contains |)
            if "|" in line and not line.lower().startswith("technologies"):
                parts = line.split("|", 1)
                position = parts[0].strip()
                company_info = parts[1].strip() if len(parts) > 1 else ""

                # Position title (bold, uppercase)
                content.append(
                    Paragraph(
                        f"<b>{self._escape_text(position.upper())}</b>",
                        self.styles["Bold_PositionTitle"],
                    )
                )

                # Company // Location // Date line
                # Look ahead for date line
                date_str = ""
                if i + 1 < len(lines) and self._is_date_line(lines[i + 1]):
                    date_str = lines[i + 1]
                    i += 1

                company_line_parts = [company_info] if company_info else []
                if date_str:
                    company_line_parts.append(date_str)

                if company_line_parts:
                    company_line = " // ".join(company_line_parts)
                    content.append(
                        Paragraph(
                            self._escape_text(company_line),
                            self.styles["Bold_CompanyLine"],
                        )
                    )
                i += 1
                continue

            # Check for sub-header like "ACHIEVEMENTS + HIGHLIGHTS"
            if self._is_bold_subheader(line):
                content.append(
                    Paragraph(
                        f"<b>{self._escape_text(line.upper())}</b>",
                        self.styles["Bold_SubHeader"],
                    )
                )
                i += 1
                continue

            # Check for bullet points
            if line.startswith(("-", "•", "*", "○", "·")):
                bullet_text = line.lstrip("-•*○·").strip()
                # Format with bold lead-in if there's a period or colon
                formatted_bullet = self._format_bold_lead_in(bullet_text)
                content.append(
                    Paragraph(f"• {formatted_bullet}", self.styles["Bold_Bullet"])
                )
                i += 1
                continue

            # Check for date line
            if self._is_date_line(line):
                i += 1
                continue

            # Technologies line
            if line.lower().startswith("technologies:"):
                content.append(
                    Paragraph(
                        f"<i>{self._escape_text(line)}</i>",
                        self.styles["Bold_BodyText"],
                    )
                )
                i += 1
                continue

            # Regular body text (description)
            content.append(
                Paragraph(self._escape_text(line), self.styles["Bold_BodyText"])
            )
            i += 1

        return content

    def _format_bold_lead_in(self, text: str) -> str:
        """
        Format text with bold lead-in (first sentence or phrase bold).

        Looks for patterns like "Contract review and negotiation. Review and..."
        Makes "Contract review and negotiation." bold.

        Args:
            text: Bullet point text

        Returns:
            Formatted text with bold lead-in
        """
        # Look for period followed by space (sentence boundary)
        if ". " in text:
            parts = text.split(". ", 1)
            lead_in = parts[0] + "."
            rest = parts[1] if len(parts) > 1 else ""
            return f"<b>{self._escape_text(lead_in)}</b> {self._escape_text(rest)}"

        # Look for colon followed by space
        if ": " in text:
            parts = text.split(": ", 1)
            lead_in = parts[0] + ":"
            rest = parts[1] if len(parts) > 1 else ""
            return f"<b>{self._escape_text(lead_in)}</b> {self._escape_text(rest)}"

        # No clear lead-in, return as-is
        return self._escape_text(text)

    def _is_bold_subheader(self, line: str) -> bool:
        """
        Check if a line is a sub-header like "ACHIEVEMENTS + HIGHLIGHTS".

        Args:
            line: Text line to check

        Returns:
            True if line is a sub-header
        """
        subheader_patterns = [
            "achievements",
            "highlights",
            "key accomplishments",
            "responsibilities",
            "key responsibilities",
            "notable achievements",
        ]

        line_lower = line.lower().strip()

        # Check if line matches sub-header patterns
        for pattern in subheader_patterns:
            if pattern in line_lower:
                # Make sure it's not too long (sub-headers are short)
                if len(line.split()) <= 5:
                    return True

        return False

    def _format_bold_education(self, lines: list) -> list:
        """Format education section for Bold template."""
        content = []

        # Grade keywords for detecting grade lines with | separator
        _grade_kws = [
            "honours",
            "honor",
            "distinction",
            "first class",
            "second class",
            "gpa",
            "cgpa",
            "grade",
            "cum laude",
            "merit",
            "dean",
            "upper",
            "lower",
            "pass",
            "credit",
        ]
        # Degree keywords for detecting entry headers
        _degree_kws = [
            "bachelor",
            "master",
            "phd",
            "diploma",
            "degree",
            "bsc",
            "msc",
            "mba",
            "associate",
            "certificate",
            "doctor",
        ]

        entries = []
        current_entry = {"degree": "", "institution": "", "date": "", "details": []}

        def _flush():
            nonlocal current_entry
            if current_entry["degree"] or current_entry["institution"]:
                entries.append(current_entry)
            current_entry = {"degree": "", "institution": "", "date": "", "details": []}

        for line in lines:
            if not line:
                _flush()
                continue

            line_lower = line.lower()

            # Pipe-separated degree | institution
            if "|" in line and any(kw in line_lower for kw in _degree_kws):
                if current_entry["degree"]:
                    _flush()
                parts = line.split("|", 1)
                current_entry["degree"] = parts[0].strip()
                current_entry["institution"] = (
                    parts[1].strip() if len(parts) > 1 else ""
                )
                continue

            # Grade line with | (e.g., "First Class Honours | GPA 3.9 / 4.0")
            if "|" in line and any(kw in line_lower for kw in _grade_kws):
                current_entry["details"].append(line)
                continue

            # Date line
            if self._is_date_line(line) and len(line) <= 40:
                current_entry["date"] = line
                continue

            # Degree keyword on its own line
            if (
                any(kw in line_lower for kw in _degree_kws)
                and not current_entry["degree"]
            ):
                current_entry["degree"] = line
                continue

            # Institution keyword on its own line
            inst_kws = [
                "university",
                "college",
                "institute",
                "school",
                "academy",
                "polytechnic",
            ]
            if (
                any(kw in line_lower for kw in inst_kws)
                and not current_entry["institution"]
            ):
                current_entry["institution"] = line
                continue

            # Bullet point → detail
            if line.startswith(("-", "•", "*")):
                current_entry["details"].append(line.lstrip("-•*").strip())
                continue

            # Fallback assignment
            if not current_entry["degree"]:
                current_entry["degree"] = line
            elif not current_entry["institution"]:
                current_entry["institution"] = line
            else:
                current_entry["details"].append(line)

        _flush()

        # Render entries
        for idx, entry in enumerate(entries):
            if idx > 0:
                content.append(Spacer(1, 0.08 * inch))

            if entry["degree"]:
                content.append(
                    Paragraph(
                        f"<b>{self._escape_text(entry['degree'].upper())}</b>",
                        self.styles["Bold_PositionTitle"],
                    )
                )

            info_parts = []
            if entry["institution"]:
                info_parts.append(entry["institution"])
            if entry["date"]:
                info_parts.append(entry["date"])

            if info_parts:
                content.append(
                    Paragraph(
                        self._escape_text(" // ".join(info_parts)),
                        self.styles["Bold_CompanyLine"],
                    )
                )

            for detail in entry["details"]:
                content.append(
                    Paragraph(self._escape_text(detail), self.styles["Bold_BodyText"])
                )

        return content

    def _format_bold_skills(self, lines: list) -> list:
        """Format skills section for Bold template."""
        content = []

        for line in lines:
            if not line:
                continue

            clean_line = line.lstrip("-•*").strip()
            if clean_line:
                # Check for skill: level format
                if ":" in clean_line:
                    parts = clean_line.split(":", 1)
                    skill = parts[0].strip()
                    level = parts[1].strip() if len(parts) > 1 else ""
                    content.append(
                        Paragraph(
                            f"<b>{self._escape_text(skill)}:</b> {self._escape_text(level)}",
                            self.styles["Bold_BodyText"],
                        )
                    )
                else:
                    content.append(
                        Paragraph(
                            f"• {self._escape_text(clean_line)}",
                            self.styles["Bold_Bullet"],
                        )
                    )

        return content

    def _format_bold_certifications(self, lines: list) -> list:
        """Format certifications section for Bold template."""
        content = []
        i = 0

        while i < len(lines):
            line = lines[i]

            if not line:
                i += 1
                continue

            clean_line = line.lstrip("-•*").strip()

            # Check for date on next line
            date_str = ""
            if i + 1 < len(lines) and self._is_date_line(lines[i + 1]):
                date_str = lines[i + 1]
                i += 1

            if date_str:
                content.append(
                    Paragraph(
                        f"<b>{self._escape_text(clean_line)}</b> // {self._escape_text(date_str)}",
                        self.styles["Bold_BodyText"],
                    )
                )
            else:
                content.append(
                    Paragraph(
                        f"• {self._escape_text(clean_line)}", self.styles["Bold_Bullet"]
                    )
                )
            i += 1

        return content

    def _format_bold_projects(self, lines: list) -> list:
        """Format projects section for Bold template."""
        content = []
        i = 0

        while i < len(lines):
            line = lines[i]

            if not line:
                i += 1
                continue

            # Check for project title (short line, not a bullet)
            if (
                not line.startswith(("-", "•", "*"))
                and len(line) < 80
                and not line.lower().startswith("technologies")
            ):
                # Likely a project title
                content.append(
                    Paragraph(
                        f"<b>{self._escape_text(line.upper())}</b>",
                        self.styles["Bold_PositionTitle"],
                    )
                )
            elif line.lower().startswith("technologies:"):
                content.append(
                    Paragraph(
                        f"<i>{self._escape_text(line)}</i>",
                        self.styles["Bold_BodyText"],
                    )
                )
            elif line.startswith(("-", "•", "*")):
                bullet_text = line.lstrip("-•*").strip()
                content.append(
                    Paragraph(
                        f"• {self._escape_text(bullet_text)}",
                        self.styles["Bold_Bullet"],
                    )
                )
            else:
                content.append(
                    Paragraph(self._escape_text(line), self.styles["Bold_BodyText"])
                )
            i += 1

        return content

    def _format_bold_languages(self, lines: list) -> list:
        """Format languages section for Bold template."""
        content = []

        for line in lines:
            if not line:
                continue

            clean_line = line.lstrip("-•*").strip()
            if clean_line:
                # Check for language: level format
                if ":" in clean_line:
                    parts = clean_line.split(":", 1)
                    lang = parts[0].strip()
                    level = parts[1].strip() if len(parts) > 1 else ""
                    content.append(
                        Paragraph(
                            f"<b>{self._escape_text(lang)}:</b> {self._escape_text(level)}",
                            self.styles["Bold_BodyText"],
                        )
                    )
                else:
                    content.append(
                        Paragraph(
                            f"• {self._escape_text(clean_line)}",
                            self.styles["Bold_Bullet"],
                        )
                    )

        return content

    def _format_bold_awards(self, lines: list) -> list:
        """Format awards section for Bold template."""
        content = []
        i = 0

        while i < len(lines):
            line = lines[i]

            if not line:
                i += 1
                continue

            # Check for award | organization format
            if "|" in line:
                parts = line.split("|", 1)
                award = parts[0].strip()
                org = parts[1].strip() if len(parts) > 1 else ""

                content.append(
                    Paragraph(
                        f"<b>{self._escape_text(award)}</b>",
                        self.styles["Bold_PositionTitle"],
                    )
                )

                date_str = ""
                if i + 1 < len(lines) and self._is_date_line(lines[i + 1]):
                    date_str = lines[i + 1]
                    i += 1

                info_parts = [org] if org else []
                if date_str:
                    info_parts.append(date_str)

                if info_parts:
                    content.append(
                        Paragraph(
                            self._escape_text(" // ".join(info_parts)),
                            self.styles["Bold_CompanyLine"],
                        )
                    )
            elif line.startswith(("-", "•", "*")):
                bullet_text = line.lstrip("-•*").strip()
                content.append(
                    Paragraph(
                        f"• {self._escape_text(bullet_text)}",
                        self.styles["Bold_Bullet"],
                    )
                )
            else:
                content.append(
                    Paragraph(self._escape_text(line), self.styles["Bold_BodyText"])
                )
            i += 1

        return content

    def _format_bold_volunteer(self, lines: list) -> list:
        """Format volunteer section for Bold template (same as experience)."""
        return self._format_bold_experience(lines)

    def _format_bold_publications(self, lines: list) -> list:
        """Format publications section for Bold template."""
        content = []
        i = 0

        while i < len(lines):
            line = lines[i]

            if not line:
                i += 1
                continue

            # Check for title | venue format
            if "|" in line:
                parts = line.split("|", 1)
                title = parts[0].strip()
                venue = parts[1].strip() if len(parts) > 1 else ""

                content.append(
                    Paragraph(
                        f"<b>{self._escape_text(title)}</b>",
                        self.styles["Bold_PositionTitle"],
                    )
                )

                date_str = ""
                if i + 1 < len(lines) and self._is_date_line(lines[i + 1]):
                    date_str = lines[i + 1]
                    i += 1

                info_parts = [venue] if venue else []
                if date_str:
                    info_parts.append(date_str)

                if info_parts:
                    content.append(
                        Paragraph(
                            self._escape_text(" // ".join(info_parts)),
                            self.styles["Bold_CompanyLine"],
                        )
                    )
            elif line.startswith(("-", "•", "*")):
                bullet_text = line.lstrip("-•*").strip()
                content.append(
                    Paragraph(
                        f"• {self._escape_text(bullet_text)}",
                        self.styles["Bold_Bullet"],
                    )
                )
            else:
                content.append(
                    Paragraph(self._escape_text(line), self.styles["Bold_BodyText"])
                )
            i += 1

        return content

    def _format_bold_memberships(self, lines: list) -> list:
        """Format memberships section for Bold template."""
        content = []

        for line in lines:
            if not line:
                continue

            clean_line = line.lstrip("-•*").strip()
            if clean_line:
                content.append(
                    Paragraph(
                        f"• {self._escape_text(clean_line)}", self.styles["Bold_Bullet"]
                    )
                )

        return content

    def _format_bold_conferences(self, lines: list) -> list:
        """Format conferences section for Bold template."""
        content = []

        for line in lines:
            if not line:
                continue

            clean_line = line.lstrip("-•*").strip()
            if clean_line:
                content.append(
                    Paragraph(
                        f"• {self._escape_text(clean_line)}", self.styles["Bold_Bullet"]
                    )
                )

        return content

    def _format_bold_patents(self, lines: list) -> list:
        """Format patents section for Bold template."""
        content = []
        i = 0

        while i < len(lines):
            line = lines[i]

            if not line:
                i += 1
                continue

            # Check for title | patent number format
            if "|" in line:
                parts = line.split("|", 1)
                title = parts[0].strip()
                patent_num = parts[1].strip() if len(parts) > 1 else ""

                content.append(
                    Paragraph(
                        f"<b>{self._escape_text(title)}</b>",
                        self.styles["Bold_PositionTitle"],
                    )
                )

                date_str = ""
                if i + 1 < len(lines) and self._is_date_line(lines[i + 1]):
                    date_str = lines[i + 1]
                    i += 1

                info_parts = [patent_num] if patent_num else []
                if date_str:
                    info_parts.append(date_str)

                if info_parts:
                    content.append(
                        Paragraph(
                            self._escape_text(" // ".join(info_parts)),
                            self.styles["Bold_CompanyLine"],
                        )
                    )
            else:
                content.append(
                    Paragraph(self._escape_text(line), self.styles["Bold_BodyText"])
                )
            i += 1

        return content

    def _format_bold_references(self, lines: list) -> list:
        """Format references section for Bold template."""
        content = []
        i = 0

        while i < len(lines):
            line = lines[i]

            if not line:
                i += 1
                continue

            # Check for name | role format
            if "|" in line:
                parts = line.split("|", 1)
                name = parts[0].strip()
                role = parts[1].strip() if len(parts) > 1 else ""

                ref_text = f"<b>{self._escape_text(name)}</b>"
                if role:
                    ref_text += f" // {self._escape_text(role)}"

                content.append(Paragraph(ref_text, self.styles["Bold_BodyText"]))
            else:
                content.append(
                    Paragraph(self._escape_text(line), self.styles["Bold_BodyText"])
                )
            i += 1

        return content

    def _format_bold_interests(self, lines: list) -> list:
        """Format interests section for Bold template."""
        content = []

        for line in lines:
            if not line:
                continue

            clean_line = line.lstrip("-•*").strip()
            if clean_line:
                content.append(
                    Paragraph(
                        f"• {self._escape_text(clean_line)}", self.styles["Bold_Bullet"]
                    )
                )

        return content

    def _format_bold_generic(self, lines: list) -> list:
        """Format generic section content for Bold template."""
        content = []

        for line in lines:
            if not line:
                continue

            if line.startswith(("-", "•", "*")):
                bullet_text = line.lstrip("-•*").strip()
                content.append(
                    Paragraph(
                        f"• {self._escape_text(bullet_text)}",
                        self.styles["Bold_Bullet"],
                    )
                )
            else:
                content.append(
                    Paragraph(self._escape_text(line), self.styles["Bold_BodyText"])
                )

        return content

    def _add_bold_footer(self, canvas_obj: canvas.Canvas, doc: SimpleDocTemplate):
        """
        Add footer to Bold template pages.

        Args:
            canvas_obj: ReportLab canvas object
            doc: Document object
        """
        canvas_obj.saveState()

        page_num = canvas_obj.getPageNumber()
        text = f"Page {page_num}"

        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(colors.HexColor("#666666"))
        canvas_obj.drawCentredString(self.PAGE_WIDTH / 2, 0.4 * inch, text)

        canvas_obj.restoreState()

    # ============ MILLENNIAL STYLE TEMPLATE METHODS ============

    def _build_millennial_style_pdf(
        self, content: str, candidate_name: str, buffer: io.BytesIO
    ) -> bytes:
        """
        Build the Millennial Style PDF using BaseDocTemplate.

        Layout (matching screenshot):
        - LEFT (60%, white): Name/title header + Experience, Education, Projects, etc.
        - RIGHT (40%, dark navy #1B3A4B): Contact, Skills, Languages, Certificates ONLY

        The right sidebar content is drawn directly on the canvas for page 1 only.
        The left content flows freely across all pages using a single frame.
        The dark blue background appears on all pages (empty after page 1).

        Args:
            content: Raw CV text content
            candidate_name: Name for PDF metadata
            buffer: BytesIO buffer for PDF output

        Returns:
            PDF bytes
        """
        # Calculate dimensions
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT
        left_width = available_width * 0.60  # 60% for white content area
        right_width = available_width * 0.40  # 40% for dark sidebar
        frame_height = self.PAGE_HEIGHT - self.MARGIN_TOP - self.MARGIN_BOTTOM - 20

        # Parse content to get left and right elements
        left_elements, right_elements = self._parse_millennial_style_content(content)

        # Store sidebar content and dimensions for canvas callback
        self._ms_right_width = right_width
        self._ms_left_width = left_width
        self._ms_sidebar_elements = right_elements
        self._ms_sidebar_drawn = False  # Track if sidebar has been drawn

        def draw_page_background(canvas_obj, doc):
            """Draw the dark sidebar background on all pages, content only on page 1."""
            canvas_obj.saveState()

            # Draw dark navy sidebar on RIGHT side (all pages)
            canvas_obj.setFillColor(colors.HexColor("#1B3A4B"))
            sidebar_x = self.MARGIN_LEFT + self._ms_left_width
            canvas_obj.rect(
                sidebar_x,
                0,
                self._ms_right_width + self.MARGIN_RIGHT,
                self.PAGE_HEIGHT,
                fill=1,
                stroke=0,
            )

            # Draw sidebar CONTENT only on page 1
            page_num = canvas_obj.getPageNumber()
            if page_num == 1 and not self._ms_sidebar_drawn:
                self._draw_sidebar_content(
                    canvas_obj, sidebar_x + 15, self._ms_right_width - 25
                )
                self._ms_sidebar_drawn = True

            # Draw footer
            canvas_obj.setFont("Helvetica", 8)
            canvas_obj.setFillColor(colors.HexColor("#666666"))
            canvas_obj.drawString(self.MARGIN_LEFT, 0.4 * inch, f"Page {page_num}")

            canvas_obj.restoreState()

        # Only LEFT frame - content flows here across all pages
        left_frame = Frame(
            self.MARGIN_LEFT,
            self.MARGIN_BOTTOM + 15,
            left_width - 10,
            frame_height,
            id="left",
            leftPadding=0,
            rightPadding=15,
            topPadding=10,
            bottomPadding=10,
        )

        # Single page template with only left frame
        page_template = PageTemplate(
            id="MainTemplate",
            frames=[left_frame],
            onPage=draw_page_background,
        )

        # Create the BaseDocTemplate
        doc = BaseDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=self.MARGIN_LEFT,
            rightMargin=self.MARGIN_RIGHT,
            topMargin=self.MARGIN_TOP,
            bottomMargin=self.MARGIN_BOTTOM,
            title=f"CV - {candidate_name}",
            author=candidate_name,
            subject="Curriculum Vitae",
        )
        doc.addPageTemplates([page_template])

        # Build with only left elements - right sidebar is drawn via canvas
        doc.build(left_elements)

        # Get PDF bytes
        pdf_bytes = buffer.getvalue()
        buffer.close()

        logger.info(
            f"Successfully generated Millennial Style CV PDF ({len(pdf_bytes)} bytes)"
        )
        return pdf_bytes

    def _draw_sidebar_content(self, canvas_obj, x_start: float, width: float):
        """
        Draw the right sidebar content directly on the canvas.

        This is called only on page 1 to render Contact, Skills, Languages, Certificates.

        Args:
            canvas_obj: ReportLab canvas object
            x_start: X coordinate to start drawing
            width: Available width for content
        """
        # Start position should align horizontally with left column name header
        # Left frame has topPadding=10, then Spacer(1,5), then the name
        # Name style MS_LeftName has fontSize=24, so text baseline is about 24pt from top
        # To align contact with name, start sidebar contact at similar position
        y_pos = self.PAGE_HEIGHT - self.MARGIN_TOP - 35  # Lower to align with name text

        # Get the parsed sidebar data
        sidebar_data = getattr(self, "_ms_parsed_sidebar_data", {})
        contact_info = sidebar_data.get("contact", {})
        sections = sidebar_data.get("sections", [])

        # ===== CONTACT INFO =====
        if contact_info:
            canvas_obj.setFont("Helvetica", 9)
            canvas_obj.setFillColor(colors.white)

            contact_items = []
            if contact_info.get("phone"):
                contact_items.append(contact_info["phone"])
            if contact_info.get("email"):
                contact_items.append(contact_info["email"])
            if contact_info.get("website"):
                contact_items.append(contact_info["website"])
            if contact_info.get("location"):
                contact_items.append(contact_info["location"])

            for item in contact_items:
                canvas_obj.drawString(x_start, y_pos, item)
                y_pos -= 14

            y_pos -= 10

        # ===== SECTIONS (Skills, Languages, Certificates) =====
        for section_name, section_lines in sections:
            # Section header (letter-spaced)
            y_pos -= 10
            spaced_title = self._create_spaced_title(section_name)

            canvas_obj.setFont("Helvetica-Bold", 10)
            canvas_obj.setFillColor(colors.white)
            canvas_obj.drawString(x_start, y_pos, spaced_title)
            y_pos -= 3

            # Underline
            canvas_obj.setStrokeColor(colors.HexColor("#2B7A78"))
            canvas_obj.setLineWidth(2)
            canvas_obj.line(x_start, y_pos, x_start + width, y_pos)
            y_pos -= 15

            # Section content
            section_lower = section_name.lower()

            if "skill" in section_lower or "competenc" in section_lower:
                y_pos = self._draw_sidebar_skills(
                    canvas_obj, section_lines, x_start, y_pos, width
                )
            elif "language" in section_lower:
                y_pos = self._draw_sidebar_languages(
                    canvas_obj, section_lines, x_start, y_pos, width
                )
            elif (
                "certif" in section_lower
                or "credential" in section_lower
                or "license" in section_lower
            ):
                y_pos = self._draw_sidebar_certifications(
                    canvas_obj, section_lines, x_start, y_pos, width
                )
            else:
                y_pos = self._draw_sidebar_generic(
                    canvas_obj, section_lines, x_start, y_pos, width
                )

            y_pos -= 5

    def _create_spaced_title(self, title: str) -> str:
        """Create letter-spaced uppercase title with clear word separation."""
        words = title.upper().split()
        spaced_words = []
        for word in words:
            spaced_word = " ".join(word)  # Single space between letters
            spaced_words.append(spaced_word)
        # Use non-breaking spaces between words (like Bizarre Modern template)
        # Regular spaces collapse, non-breaking spaces preserve the gap
        word_separator = "\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0"  # 6 non-breaking spaces
        return word_separator.join(spaced_words)

    def _draw_sidebar_skills(
        self, canvas_obj, lines: list, x: float, y: float, width: float
    ) -> float:
        """Draw skills with name and level."""
        for line in lines:
            if not line.strip():
                continue

            skill_name = line
            skill_level = ""

            for sep in [" - ", ": ", " – ", " — "]:
                if sep in line:
                    parts = line.split(sep, 1)
                    skill_name = parts[0].strip()
                    skill_level = parts[1].strip() if len(parts) > 1 else ""
                    break

            # Skill name (white)
            canvas_obj.setFont("Helvetica", 9)
            canvas_obj.setFillColor(colors.white)
            canvas_obj.drawString(x, y, skill_name)

            # Skill level (teal, right-aligned)
            if skill_level:
                canvas_obj.setFillColor(colors.HexColor("#2B7A78"))
                level_width = canvas_obj.stringWidth(skill_level, "Helvetica", 9)
                canvas_obj.drawString(x + width - level_width, y, skill_level)

            y -= 14

        return y

    def _draw_sidebar_languages(
        self, canvas_obj, lines: list, x: float, y: float, width: float
    ) -> float:
        """Draw languages with name and level."""
        for line in lines:
            if not line.strip():
                continue

            lang_name = line
            lang_level = ""

            for sep in [" - ", ": ", " – ", " — ", " ("]:
                if sep in line:
                    parts = line.split(sep, 1)
                    lang_name = parts[0].strip()
                    lang_level = parts[1].strip().rstrip(")") if len(parts) > 1 else ""
                    break

            # Language name (white)
            canvas_obj.setFont("Helvetica", 9)
            canvas_obj.setFillColor(colors.white)
            canvas_obj.drawString(x, y, lang_name)

            # Language level (teal, right-aligned)
            if lang_level:
                canvas_obj.setFillColor(colors.HexColor("#2B7A78"))
                level_width = canvas_obj.stringWidth(lang_level, "Helvetica", 9)
                canvas_obj.drawString(x + width - level_width, y, lang_level)

            y -= 14

        return y

    def _draw_sidebar_certifications(
        self, canvas_obj, lines: list, x: float, y: float, width: float
    ) -> float:
        """Draw certifications with name and date."""
        current_cert = {"name": "", "date": ""}

        for line in lines:
            if not line.strip():
                continue

            # Check if it's a date line
            if self._is_date_line(line) and len(line) <= 25:
                current_cert["date"] = line
                # Output the cert
                if current_cert["name"]:
                    # Cert name (teal)
                    canvas_obj.setFont("Helvetica-Bold", 9)
                    canvas_obj.setFillColor(colors.HexColor("#2B7A78"))
                    canvas_obj.drawString(x, y, current_cert["name"])
                    y -= 12

                    # Cert date (light gray)
                    if current_cert["date"]:
                        canvas_obj.setFont("Helvetica", 8)
                        canvas_obj.setFillColor(colors.HexColor("#B0C4CC"))
                        canvas_obj.drawString(x, y, current_cert["date"])
                        y -= 14

                    current_cert = {"name": "", "date": ""}
            else:
                # If we have a pending cert, output it first
                if current_cert["name"]:
                    canvas_obj.setFont("Helvetica-Bold", 9)
                    canvas_obj.setFillColor(colors.HexColor("#2B7A78"))
                    canvas_obj.drawString(x, y, current_cert["name"])
                    y -= 12

                    if current_cert["date"]:
                        canvas_obj.setFont("Helvetica", 8)
                        canvas_obj.setFillColor(colors.HexColor("#B0C4CC"))
                        canvas_obj.drawString(x, y, current_cert["date"])
                        y -= 14

                current_cert = {"name": line, "date": ""}

        # Don't forget last one
        if current_cert["name"]:
            canvas_obj.setFont("Helvetica-Bold", 9)
            canvas_obj.setFillColor(colors.HexColor("#2B7A78"))
            canvas_obj.drawString(x, y, current_cert["name"])
            y -= 12

            if current_cert["date"]:
                canvas_obj.setFont("Helvetica", 8)
                canvas_obj.setFillColor(colors.HexColor("#B0C4CC"))
                canvas_obj.drawString(x, y, current_cert["date"])
                y -= 14

        return y

    def _draw_sidebar_generic(
        self, canvas_obj, lines: list, x: float, y: float, width: float
    ) -> float:
        """Draw generic sidebar content."""
        for line in lines:
            if line.strip():
                canvas_obj.setFont("Helvetica", 9)
                canvas_obj.setFillColor(colors.white)
                canvas_obj.drawString(x, y, line)
                y -= 14
        return y

    def _parse_millennial_style_content(self, content: str) -> tuple:
        """
        Parse CV content for the Millennial Style template.

        Features:
        - Two-column layout: Dark sidebar (left 55%) + White content (right 45%)
        - Left sidebar: Name, Title, Experience, Education
        - Right column: Contact, Skills, Languages, Certifications, etc.
        - Letter-spaced uppercase section headers with colored underlines
        - Teal accent color for titles and skill levels

        Args:
            content: Raw CV text content

        Returns:
            Tuple of (left_elements, right_elements) - flowables for each column
        """
        # Preserve blank lines so section formatters can detect entry boundaries
        lines = [line.strip() for line in content.split("\n")]

        if not any(lines):
            raise ValueError("CV content is empty after parsing")

        # ============ PARSE ALL CONTENT FIRST ============
        # Extract header info
        _si = 0
        while _si < len(lines) and not lines[_si]:
            _si += 1
        name = lines[_si] if _si < len(lines) else "Candidate Name"
        job_title = ""
        contact_info = {}
        idx = _si + 1

        # Skip blank lines before job title
        while idx < len(lines) and not lines[idx]:
            idx += 1

        # Look for job title (usually second line)
        if idx < len(lines):
            potential_title = lines[idx]
            if not any(
                marker in potential_title.lower()
                for marker in ["@", "+", "http", ".com", ".io", ".dev", "|", "•"]
            ):
                if not self._is_section_header(potential_title):
                    job_title = potential_title
                    idx += 1

        # Collect contact information
        _header_end = min(_si + 15, len(lines))
        while idx < _header_end:
            line = lines[idx]
            if not line:
                idx += 1
                continue
            if self._is_section_header(line):
                break

            # Parse contact items
            if "@" in line and "http" not in line.lower():
                contact_info["email"] = (
                    line.split("|")[0].strip() if "|" in line else line
                )
            elif line.startswith("+") or (
                len(line) < 20 and any(c.isdigit() for c in line) and "-" in line
            ):
                contact_info["phone"] = (
                    line.split("|")[0].strip() if "|" in line else line
                )
            elif any(
                marker in line.lower()
                for marker in ["http", "www.", ".com", ".io", ".dev"]
            ):
                contact_info["website"] = line
            elif "," in line and len(line.split(",")) >= 2 and len(line) < 50:
                contact_info["location"] = line

            # Also check for combined lines with | or •
            if "|" in line or "•" in line:
                parts = line.replace("•", "|").split("|")
                for part in parts:
                    part = part.strip()
                    if "@" in part and "http" not in part.lower():
                        contact_info["email"] = part
                    elif part.startswith("+") or (
                        len(part) < 20 and any(c.isdigit() for c in part)
                    ):
                        contact_info["phone"] = part
                    elif any(m in part.lower() for m in ["http", "www.", ".com"]):
                        contact_info["website"] = part
                    elif "," in part and len(part) < 50:
                        contact_info["location"] = part

            idx += 1

        # ============ PARSE SECTIONS ============
        sections = {}
        current_section_name = ""
        current_section_content = []

        for line in lines[idx:]:
            if self._is_section_header(line):
                # Save previous section
                if current_section_name:
                    sections[current_section_name.lower()] = current_section_content
                # Start new section
                current_section_name = line.rstrip(":").strip()
                current_section_content = []
            else:
                current_section_content.append(line)

        # Add final section
        if current_section_name:
            sections[current_section_name.lower()] = current_section_content

        # ============ DETERMINE WHICH SECTIONS GO WHERE ============
        # LEFT (white, 60%): Name header + Experience, Education, Summary, Projects, etc.
        # RIGHT (dark sidebar, 40%): Contact, Skills, Languages, Certificates ONLY

        left_sections = []
        right_sections = []

        # RIGHT sidebar ONLY contains: Skills, Languages, Certificates
        # Everything else goes to LEFT
        right_section_keywords = [
            "skills",
            "technical skills",
            "core competencies",
            "key skills",
            "languages",
            "language proficiency",
            "certifications",
            "certificates",
            "credentials",
            "licenses",
        ]

        for section_name, section_content in sections.items():
            section_lower = section_name.lower()
            assigned_to_right = False

            for keyword in right_section_keywords:
                if keyword in section_lower:
                    right_sections.append((section_name, section_content))
                    assigned_to_right = True
                    break

            # Everything else goes to LEFT (white content area)
            if not assigned_to_right:
                left_sections.append((section_name, section_content))

        # ============ BUILD SEPARATE FLOWABLE LISTS FOR EACH COLUMN ============
        # Calculate column widths
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT
        left_width = available_width * 0.60 - 25  # Account for frame padding
        right_width = available_width * 0.40 - 25  # Account for frame padding

        # Store sidebar data for canvas drawing (used by _draw_sidebar_content)
        self._ms_parsed_sidebar_data = {
            "contact": contact_info,
            "sections": right_sections,
        }

        # Build LEFT content (white background) - Name, Experience, Education, etc.
        left_elements = self._build_millennial_left_content_flowables(
            name, job_title, left_sections, left_width
        )

        # Right elements not needed as flowables - drawn directly on canvas
        right_elements = []

        return (left_elements, right_elements)

    def _build_millennial_left_content_flowables(
        self, name: str, job_title: str, sections: list, width: float
    ) -> list:
        """
        Build the LEFT content flowables (white background) for Millennial Style.

        Contains: Name/title header, Experience, Education, Projects, Awards, etc.
        Uses dark navy text on white background.

        Args:
            name: Candidate's name
            job_title: Current job title
            sections: List of (section_name, content_lines) tuples
            width: Width of the content area

        Returns:
            List of flowables for the left content area
        """
        content = []

        # ===== NAME HEADER (dark navy on white) =====
        content.append(Spacer(1, 5))
        content.append(Paragraph(self._escape_text(name), self.styles["MS_LeftName"]))

        # Job title (gray, smaller)
        if job_title:
            content.append(
                Paragraph(self._escape_text(job_title), self.styles["MS_LeftTitle"])
            )

        content.append(Spacer(1, 15))

        # ===== PROCESS EACH SECTION =====
        for section_name, section_lines in sections:
            section_lower = section_name.lower()

            # Add section header with underline
            content.append(Spacer(1, 8))
            content.append(
                self._create_millennial_section_header(
                    section_name, is_sidebar=False, width=width
                )
            )
            content.append(Spacer(1, 6))

            # Format section content based on type
            if "experience" in section_lower or "employment" in section_lower:
                section_content = self._format_millennial_left_experience(section_lines)
            elif "education" in section_lower or "academic" in section_lower:
                section_content = self._format_millennial_left_education(section_lines)
            elif (
                "summary" in section_lower
                or "profile" in section_lower
                or "objective" in section_lower
            ):
                section_content = self._format_millennial_left_summary(section_lines)
            elif "volunteer" in section_lower:
                section_content = self._format_millennial_left_volunteer(section_lines)
            elif "project" in section_lower:
                section_content = self._format_millennial_left_projects(section_lines)
            elif "award" in section_lower or "achievement" in section_lower:
                section_content = self._format_millennial_left_awards(section_lines)
            elif "publication" in section_lower or "research" in section_lower:
                section_content = self._format_millennial_left_publications(
                    section_lines
                )
            elif "membership" in section_lower or "affiliation" in section_lower:
                section_content = self._format_millennial_left_memberships(
                    section_lines
                )
            elif "conference" in section_lower or "talk" in section_lower:
                section_content = self._format_millennial_left_conferences(
                    section_lines
                )
            elif "patent" in section_lower:
                section_content = self._format_millennial_left_patents(section_lines)
            elif "reference" in section_lower:
                section_content = self._format_millennial_left_references(section_lines)
            elif "interest" in section_lower or "hobbi" in section_lower:
                section_content = self._format_millennial_left_interests(section_lines)
            else:
                section_content = self._format_millennial_left_generic(section_lines)

            content.extend(section_content)

        return content

    def _build_millennial_right_sidebar_flowables(
        self, contact_info: dict, sections: list, width: float
    ) -> list:
        """
        Build the RIGHT sidebar flowables (dark navy background) for Millennial Style.

        Contains ONLY: Contact info, Skills, Languages, Certificates
        Uses white text on dark navy background.

        Args:
            contact_info: Dictionary with email, phone, website, location
            sections: List of (section_name, content_lines) tuples - only skills/lang/certs
            width: Width of the sidebar

        Returns:
            List of flowables for the right sidebar
        """
        content = []

        content.append(Spacer(1, 5))

        # ===== CONTACT INFO (white text) =====
        if contact_info:
            contact_items = []
            if contact_info.get("phone"):
                contact_items.append(contact_info["phone"])
            if contact_info.get("email"):
                contact_items.append(contact_info["email"])
            if contact_info.get("website"):
                contact_items.append(contact_info["website"])
            if contact_info.get("location"):
                contact_items.append(contact_info["location"])

            for value in contact_items:
                content.append(
                    Paragraph(
                        self._escape_text(value), self.styles["MS_SidebarContact"]
                    )
                )

            content.append(Spacer(1, 10))

        # ===== PROCESS SECTIONS (Skills, Languages, Certificates) =====
        for section_name, section_lines in sections:
            section_lower = section_name.lower()

            # Add section header with underline (white text, teal underline)
            content.append(Spacer(1, 8))
            content.append(
                self._create_millennial_section_header(
                    section_name, is_sidebar=True, width=width
                )
            )
            content.append(Spacer(1, 6))

            # Format section content based on type
            if "skill" in section_lower or "competenc" in section_lower:
                section_content = self._format_millennial_sidebar_skills(
                    section_lines, width
                )
            elif "language" in section_lower:
                section_content = self._format_millennial_sidebar_languages(
                    section_lines, width
                )
            elif (
                "certif" in section_lower
                or "credential" in section_lower
                or "license" in section_lower
            ):
                section_content = self._format_millennial_sidebar_certifications(
                    section_lines
                )
            else:
                section_content = self._format_millennial_sidebar_generic(section_lines)

            content.extend(section_content)

        return content

    # Keep old methods for backward compatibility but they won't be called
    def _build_millennial_left_sidebar_flowables(
        self, name: str, job_title: str, sections: list, width: float
    ) -> list:
        """
        Build the left sidebar flowables for Millennial Style template.

        Returns individual flowables that can flow across pages within the left frame.
        The dark background is drawn by the page template callback.

        Args:
            name: Candidate's name
            job_title: Current job title
            sections: List of (section_name, content_lines) tuples
            width: Width of the sidebar

        Returns:
            List of flowables for the left sidebar
        """
        content = []

        # Name (large, white, bold)
        content.append(Spacer(1, 5))
        content.append(
            Paragraph(self._escape_text(name), self.styles["MS_SidebarName"])
        )

        # Job title (smaller, white)
        if job_title:
            content.append(
                Paragraph(self._escape_text(job_title), self.styles["MS_SidebarTitle"])
            )

        content.append(Spacer(1, 10))

        # Process each section for the sidebar
        for section_name, section_lines in sections:
            section_lower = section_name.lower()

            # Add section header with underline
            content.append(Spacer(1, 8))
            content.append(
                self._create_millennial_section_header(
                    section_name, is_sidebar=True, width=width
                )
            )
            content.append(Spacer(1, 4))

            # Format section content based on type
            if "experience" in section_lower or "employment" in section_lower:
                section_content = self._format_millennial_sidebar_experience(
                    section_lines
                )
            elif "education" in section_lower or "academic" in section_lower:
                section_content = self._format_millennial_sidebar_education(
                    section_lines
                )
            elif (
                "summary" in section_lower
                or "profile" in section_lower
                or "objective" in section_lower
            ):
                section_content = self._format_millennial_sidebar_summary(section_lines)
            elif "volunteer" in section_lower:
                section_content = self._format_millennial_sidebar_volunteer(
                    section_lines
                )
            else:
                section_content = self._format_millennial_sidebar_generic(section_lines)

            content.extend(section_content)

        return content

    def _build_millennial_right_column_flowables(
        self, contact_info: dict, sections: list, width: float
    ) -> list:
        """
        Build the right column flowables for Millennial Style template.

        Returns individual flowables that can flow across pages within the right frame.

        Args:
            contact_info: Dictionary with email, phone, website, location
            sections: List of (section_name, content_lines) tuples
            width: Width of the column

        Returns:
            List of flowables for the right column
        """
        content = []

        content.append(Spacer(1, 5))

        # Contact info at top
        if contact_info:
            contact_items = []
            if contact_info.get("phone"):
                contact_items.append(("Phone", contact_info["phone"]))
            if contact_info.get("email"):
                contact_items.append(("Email", contact_info["email"]))
            if contact_info.get("website"):
                contact_items.append(("Website", contact_info["website"]))
            if contact_info.get("location"):
                contact_items.append(("Location", contact_info["location"]))

            for label, value in contact_items:
                content.append(
                    Paragraph(
                        f"<b>{self._escape_text(label)}</b>",
                        self.styles["MS_ContactLabel"],
                    )
                )
                content.append(
                    Paragraph(self._escape_text(value), self.styles["MS_ContactValue"])
                )

        # Process each section for the right column
        for section_name, section_lines in sections:
            section_lower = section_name.lower()

            # Add section header with underline
            content.append(Spacer(1, 8))
            content.append(
                self._create_millennial_section_header(
                    section_name, is_sidebar=False, width=width
                )
            )
            content.append(Spacer(1, 4))

            # Format section content based on type
            if "skill" in section_lower or "competenc" in section_lower:
                section_content = self._format_millennial_right_skills(
                    section_lines, width
                )
            elif "language" in section_lower:
                section_content = self._format_millennial_right_languages(
                    section_lines, width
                )
            elif "certif" in section_lower or "credential" in section_lower:
                section_content = self._format_millennial_right_certifications(
                    section_lines
                )
            elif "award" in section_lower or "achievement" in section_lower:
                section_content = self._format_millennial_right_awards(section_lines)
            elif "interest" in section_lower or "hobbi" in section_lower:
                section_content = self._format_millennial_right_interests(section_lines)
            elif "project" in section_lower:
                section_content = self._format_millennial_right_projects(section_lines)
            elif "publication" in section_lower or "research" in section_lower:
                section_content = self._format_millennial_right_publications(
                    section_lines
                )
            elif "membership" in section_lower or "affiliation" in section_lower:
                section_content = self._format_millennial_right_memberships(
                    section_lines
                )
            elif "conference" in section_lower or "talk" in section_lower:
                section_content = self._format_millennial_right_conferences(
                    section_lines
                )
            elif "patent" in section_lower:
                section_content = self._format_millennial_right_patents(section_lines)
            elif "reference" in section_lower:
                section_content = self._format_millennial_right_references(
                    section_lines
                )
            else:
                section_content = self._format_millennial_right_generic(section_lines)

            content.extend(section_content)

        return content

    def _build_millennial_left_sidebar(
        self, name: str, job_title: str, sections: list, width: float
    ) -> list:
        """
        Build the left sidebar content for Millennial Style template.

        Contains: Name, Job Title, Experience, Education sections
        Dark navy background with white/teal text.

        Args:
            name: Candidate's name
            job_title: Current job title
            sections: List of (section_name, content_lines) tuples
            width: Width of the sidebar

        Returns:
            List of flowables for the sidebar
        """
        content = []

        # Add padding around content
        inner_width = width - 20  # 10px padding on each side

        # Name (large, white, bold)
        content.append(Spacer(1, 10))
        content.append(
            Paragraph(self._escape_text(name), self.styles["MS_SidebarName"])
        )

        # Job title (smaller, white)
        if job_title:
            content.append(
                Paragraph(self._escape_text(job_title), self.styles["MS_SidebarTitle"])
            )

        # Process each section for the sidebar
        for section_name, section_lines in sections:
            section_lower = section_name.lower()

            # Add section header with underline
            content.append(Spacer(1, 12))
            content.append(
                self._create_millennial_section_header(
                    section_name, is_sidebar=True, width=inner_width
                )
            )
            content.append(Spacer(1, 6))

            # Format section content based on type
            if "experience" in section_lower or "employment" in section_lower:
                section_content = self._format_millennial_sidebar_experience(
                    section_lines
                )
            elif "education" in section_lower or "academic" in section_lower:
                section_content = self._format_millennial_sidebar_education(
                    section_lines
                )
            elif (
                "summary" in section_lower
                or "profile" in section_lower
                or "objective" in section_lower
            ):
                section_content = self._format_millennial_sidebar_summary(section_lines)
            elif "volunteer" in section_lower:
                section_content = self._format_millennial_sidebar_volunteer(
                    section_lines
                )
            else:
                section_content = self._format_millennial_sidebar_generic(section_lines)

            content.extend(section_content)

        content.append(Spacer(1, 20))

        # Wrap content in a table with padding and background
        padded_table = Table(
            [[content]],
            colWidths=[width],
            style=TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 15),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 15),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            ),
        )

        return padded_table

    def _build_millennial_right_column(
        self, contact_info: dict, sections: list, width: float
    ) -> list:
        """
        Build the right column content for Millennial Style template.

        Contains: Contact info, Skills, Languages, Certifications, etc.
        White background with dark/teal text.

        Args:
            contact_info: Dictionary with email, phone, website, location
            sections: List of (section_name, content_lines) tuples
            width: Width of the column

        Returns:
            List of flowables for the right column
        """
        content = []

        inner_width = width - 20  # Padding

        content.append(Spacer(1, 10))

        # Contact info at top
        if contact_info:
            contact_items = []
            if contact_info.get("phone"):
                contact_items.append(("Phone", contact_info["phone"]))
            if contact_info.get("email"):
                contact_items.append(("Email", contact_info["email"]))
            if contact_info.get("website"):
                contact_items.append(("Website", contact_info["website"]))
            if contact_info.get("location"):
                contact_items.append(("Location", contact_info["location"]))

            for label, value in contact_items:
                content.append(
                    Paragraph(
                        f"<b>{self._escape_text(label)}</b>",
                        self.styles["MS_ContactLabel"],
                    )
                )
                content.append(
                    Paragraph(self._escape_text(value), self.styles["MS_ContactValue"])
                )

        # Process each section for the right column
        for section_name, section_lines in sections:
            section_lower = section_name.lower()

            # Add section header with underline
            content.append(Spacer(1, 10))
            content.append(
                self._create_millennial_section_header(
                    section_name, is_sidebar=False, width=inner_width
                )
            )
            content.append(Spacer(1, 6))

            # Format section content based on type
            if "skill" in section_lower or "competenc" in section_lower:
                section_content = self._format_millennial_right_skills(
                    section_lines, inner_width
                )
            elif "language" in section_lower:
                section_content = self._format_millennial_right_languages(
                    section_lines, inner_width
                )
            elif "certif" in section_lower or "credential" in section_lower:
                section_content = self._format_millennial_right_certifications(
                    section_lines
                )
            elif "award" in section_lower or "achievement" in section_lower:
                section_content = self._format_millennial_right_awards(section_lines)
            elif "interest" in section_lower or "hobbi" in section_lower:
                section_content = self._format_millennial_right_interests(section_lines)
            elif "project" in section_lower:
                section_content = self._format_millennial_right_projects(section_lines)
            elif "publication" in section_lower or "research" in section_lower:
                section_content = self._format_millennial_right_publications(
                    section_lines
                )
            elif "membership" in section_lower or "affiliation" in section_lower:
                section_content = self._format_millennial_right_memberships(
                    section_lines
                )
            elif "conference" in section_lower or "talk" in section_lower:
                section_content = self._format_millennial_right_conferences(
                    section_lines
                )
            elif "patent" in section_lower:
                section_content = self._format_millennial_right_patents(section_lines)
            elif "reference" in section_lower:
                section_content = self._format_millennial_right_references(
                    section_lines
                )
            else:
                section_content = self._format_millennial_right_generic(section_lines)

            content.extend(section_content)

        content.append(Spacer(1, 20))

        # Wrap content in a table with padding
        padded_table = Table(
            [[content]],
            colWidths=[width],
            style=TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 15),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            ),
        )

        return padded_table

    def _create_millennial_section_header(
        self, title: str, is_sidebar: bool, width: float
    ) -> Table:
        """
        Create a letter-spaced section header with colored underline.

        Style: UPPERCASE, letter-spaced (E X P E R I E N C E), with accent underline

        Args:
            title: Section title text
            is_sidebar: True if in dark sidebar (white text), False if in right column (dark text)
            width: Available width for the header

        Returns:
            Table containing the styled section header
        """
        # Create letter-spaced title with clear word separation
        words = title.upper().split()
        spaced_words = []
        for word in words:
            spaced_word = " ".join(word)  # Single space between letters
            spaced_words.append(spaced_word)
        # Use non-breaking spaces between words - regular spaces collapse
        word_separator = "\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0"  # 6 non-breaking spaces
        spaced_title = word_separator.join(spaced_words)

        if is_sidebar:
            style = self.styles["MS_SidebarSectionHeader"]
            underline_color = colors.HexColor("#4A9B9B")  # Teal accent
        else:
            style = self.styles["MS_RightSectionHeader"]
            underline_color = colors.HexColor("#4A9B9B")  # Teal accent

        header_para = Paragraph(self._escape_text(spaced_title), style)

        header_table = Table(
            [[header_para]],
            colWidths=[width],
            style=TableStyle(
                [
                    ("LINEBELOW", (0, 0), (-1, 0), 2, underline_color),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            ),
        )

        return header_table

    # ============ LEFT COLUMN SECTION FORMATTERS (White background) ============

    def _format_millennial_left_experience(self, lines: list) -> list:
        """Format experience section for the LEFT white content area."""
        content = []

        entries = []
        current_entry = {
            "position": "",
            "company": "",
            "date": "",
            "bullets": [],
        }

        i = 0
        while i < len(lines):
            line = lines[i]

            if not line:
                if current_entry["position"]:
                    entries.append(current_entry)
                    current_entry = {
                        "position": "",
                        "company": "",
                        "date": "",
                        "bullets": [],
                    }
                i += 1
                continue

            # Check for "Position | Company" format
            if "|" in line and not line.lower().startswith("technologies"):
                if current_entry["position"]:
                    entries.append(current_entry)
                    current_entry = {
                        "position": "",
                        "company": "",
                        "date": "",
                        "bullets": [],
                    }

                parts = line.split("|", 1)
                current_entry["position"] = parts[0].strip()
                current_entry["company"] = parts[1].strip() if len(parts) > 1 else ""
                i += 1
                continue

            # Check for date line
            if self._is_date_line(line):
                current_entry["date"] = line
                i += 1
                continue

            # Check for bullet points
            if line.startswith(("-", "•", "*", "○", "·")):
                bullet_text = line.lstrip("-•*○·").strip()
                current_entry["bullets"].append(bullet_text)
                i += 1
                continue

            # Check if this might be position or company
            if not current_entry["position"]:
                current_entry["position"] = line
            elif not current_entry["company"]:
                current_entry["company"] = line
            else:
                current_entry["bullets"].append(line)
            i += 1

        # Don't forget last entry
        if current_entry["position"]:
            entries.append(current_entry)

        # Render each entry
        for entry in entries:
            # Position title (teal)
            if entry["position"]:
                content.append(
                    Paragraph(
                        self._escape_text(entry["position"]),
                        self.styles["MS_LeftPositionTitle"],
                    )
                )

            # Company name (dark)
            if entry["company"]:
                content.append(
                    Paragraph(
                        self._escape_text(entry["company"]),
                        self.styles["MS_LeftCompany"],
                    )
                )

            # Date (gray)
            if entry["date"]:
                content.append(
                    Paragraph(
                        self._escape_text(entry["date"]), self.styles["MS_LeftDate"]
                    )
                )

            # Bullet points (dark)
            for bullet in entry["bullets"]:
                content.append(
                    Paragraph(
                        f"• {self._escape_text(bullet)}", self.styles["MS_LeftBullet"]
                    )
                )

        return content

    def _format_millennial_left_education(self, lines: list) -> list:
        """Format education section for the LEFT white content area."""
        content = []

        entries = []
        current_entry = {"degree": "", "institution": "", "year": "", "details": []}

        for line in lines:
            if not line:
                if current_entry["degree"] or current_entry["institution"]:
                    entries.append(current_entry)
                    current_entry = {
                        "degree": "",
                        "institution": "",
                        "year": "",
                        "details": [],
                    }
                continue

            # Check for year/date
            if self._is_date_line(line) and len(line) <= 40:
                current_entry["year"] = line
                continue

            # Check for institution keywords
            inst_keywords = ["university", "college", "institute", "school", "academy"]
            is_institution = any(kw in line.lower() for kw in inst_keywords)

            # Check for degree keywords
            degree_keywords = [
                "bachelor",
                "master",
                "phd",
                "diploma",
                "degree",
                "bsc",
                "msc",
                "mba",
                "associate",
                "certificate",
            ]
            is_degree = any(kw in line.lower() for kw in degree_keywords)

            if is_degree and not current_entry["degree"]:
                current_entry["degree"] = line
            elif is_institution and not current_entry["institution"]:
                current_entry["institution"] = line
            elif not current_entry["degree"]:
                current_entry["degree"] = line
            elif not current_entry["institution"]:
                current_entry["institution"] = line
            else:
                current_entry["details"].append(line)

        if current_entry["degree"] or current_entry["institution"]:
            entries.append(current_entry)

        # Render each entry
        for idx, entry in enumerate(entries):
            if idx > 0:
                content.append(Spacer(1, 0.08 * inch))

            # Degree (teal)
            if entry["degree"]:
                content.append(
                    Paragraph(
                        self._escape_text(entry["degree"]), self.styles["MS_LeftDegree"]
                    )
                )

            # Institution (dark)
            if entry["institution"]:
                content.append(
                    Paragraph(
                        self._escape_text(entry["institution"]),
                        self.styles["MS_LeftInstitution"],
                    )
                )

            # Year (gray)
            if entry["year"]:
                content.append(
                    Paragraph(
                        self._escape_text(entry["year"]), self.styles["MS_LeftDate"]
                    )
                )

            # Additional details
            for detail in entry["details"]:
                content.append(
                    Paragraph(self._escape_text(detail), self.styles["MS_LeftBullet"])
                )

        return content

    def _format_millennial_left_summary(self, lines: list) -> list:
        """Format professional summary for the LEFT white content area."""
        content = []
        text = " ".join(lines)
        if text.strip():
            content.append(
                Paragraph(self._escape_text(text), self.styles["MS_LeftBody"])
            )
        return content

    def _format_millennial_left_volunteer(self, lines: list) -> list:
        """Format volunteer section for the LEFT white content area."""
        return self._format_millennial_left_experience(lines)

    def _format_millennial_left_projects(self, lines: list) -> list:
        """Format projects section for the LEFT white content area."""
        content = []

        entries = []
        current_project = {"name": "", "details": []}

        def _flush_project():
            nonlocal current_project
            if current_project["name"]:
                entries.append(current_project)
            current_project = {"name": "", "details": []}

        for line in lines:
            if not line:
                _flush_project()
                continue

            # Lines with | are project headers
            if "|" in line and not line.lower().startswith("technologies"):
                if current_project["name"]:
                    _flush_project()
                current_project["name"] = line
            elif line.startswith(("-", "•", "*")):
                current_project["details"].append(line.lstrip("-•*").strip())
            elif line.lower().startswith("technologies:"):
                current_project["details"].append(line)
            elif not current_project["name"]:
                current_project["name"] = line
            else:
                current_project["details"].append(line)

        _flush_project()

        # Render
        for project in entries:
            content.append(
                Paragraph(
                    self._escape_text(project["name"]),
                    self.styles["MS_LeftPositionTitle"],
                )
            )
            for d in project["details"]:
                if d.lower().startswith("technologies:"):
                    content.append(
                        Paragraph(
                            f"<i>{self._escape_text(d)}</i>",
                            self.styles["MS_LeftBullet"],
                        )
                    )
                else:
                    content.append(
                        Paragraph(
                            f"• {self._escape_text(d)}",
                            self.styles["MS_LeftBullet"],
                        )
                    )

        return content

    def _format_millennial_left_awards(self, lines: list) -> list:
        """
        Format awards section for the LEFT white content area.

        Expected format (from AI service):
        - Line 1: "Award Name | Organization"
        - Line 2: Year
        """
        content = []
        i = 0

        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Check for "Award | Organization" format
            if "|" in line:
                parts = line.split("|", 1)
                award = parts[0].strip()
                org = parts[1].strip() if len(parts) > 1 else ""

                # Award name in teal/bold
                content.append(
                    Paragraph(
                        f"<b>{self._escape_text(award)}</b>",
                        self.styles["MS_LeftPositionTitle"],
                    )
                )

                # Organization in gray
                if org:
                    content.append(
                        Paragraph(self._escape_text(org), self.styles["MS_LeftCompany"])
                    )

                i += 1

                # Next line might be year/date
                if i < len(lines) and self._is_date_line(lines[i].strip()):
                    content.append(
                        Paragraph(
                            self._escape_text(lines[i].strip()),
                            self.styles["MS_LeftDate"],
                        )
                    )
                    i += 1

                content.append(Spacer(1, 4))
            elif line.startswith(("-", "•", "*")):
                content.append(
                    Paragraph(
                        f"• {self._escape_text(line.lstrip('-•*').strip())}",
                        self.styles["MS_LeftBullet"],
                    )
                )
                i += 1
            else:
                content.append(
                    Paragraph(self._escape_text(line), self.styles["MS_LeftBody"])
                )
                i += 1

        return content

    def _format_millennial_left_publications(self, lines: list) -> list:
        """
        Format publications section for the LEFT white content area.

        Expected format (from AI service):
        - Line 1: "Publication Title | Venue/Journal"
        - Line 2: Year
        - Line 3+: Optional description
        """
        content = []
        i = 0

        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Check for "Title | Venue" format
            if "|" in line:
                parts = line.split("|", 1)
                title = parts[0].strip()
                venue = parts[1].strip() if len(parts) > 1 else ""

                # Title in teal/bold
                content.append(
                    Paragraph(
                        f"<b>{self._escape_text(title)}</b>",
                        self.styles["MS_LeftPositionTitle"],
                    )
                )

                # Venue in gray
                if venue:
                    content.append(
                        Paragraph(
                            self._escape_text(venue), self.styles["MS_LeftCompany"]
                        )
                    )

                i += 1

                # Next line might be year
                if i < len(lines) and self._is_date_line(lines[i].strip()):
                    content.append(
                        Paragraph(
                            self._escape_text(lines[i].strip()),
                            self.styles["MS_LeftDate"],
                        )
                    )
                    i += 1

                # Collect description lines until next publication or end
                while i < len(lines):
                    desc_line = lines[i].strip()
                    if not desc_line:
                        i += 1
                        continue
                    # If we hit another title line with |, stop
                    if "|" in desc_line:
                        break
                    content.append(
                        Paragraph(
                            self._escape_text(desc_line), self.styles["MS_LeftBody"]
                        )
                    )
                    i += 1

                content.append(Spacer(1, 4))
            elif line.startswith(("-", "•", "*")):
                content.append(
                    Paragraph(
                        f"• {self._escape_text(line.lstrip('-•*').strip())}",
                        self.styles["MS_LeftBullet"],
                    )
                )
                i += 1
            else:
                content.append(
                    Paragraph(self._escape_text(line), self.styles["MS_LeftBody"])
                )
                i += 1

        return content

    def _format_millennial_left_memberships(self, lines: list) -> list:
        """
        Format memberships section for the LEFT white content area.

        Expected format: Bullet list of memberships
        """
        content = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Memberships are typically bullet points
            clean = line.lstrip("-•*").strip()
            content.append(
                Paragraph(f"• {self._escape_text(clean)}", self.styles["MS_LeftBullet"])
            )
        return content

    def _format_millennial_left_conferences(self, lines: list) -> list:
        """
        Format conferences section for the LEFT white content area.

        Expected format (from AI service): Bullet points like
        "• Talk title - Event Year"
        """
        content = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Conferences are typically bullet points
            clean = line.lstrip("-•*").strip()
            content.append(
                Paragraph(f"• {self._escape_text(clean)}", self.styles["MS_LeftBullet"])
            )
        return content

    def _format_millennial_left_patents(self, lines: list) -> list:
        """
        Format patents section for the LEFT white content area.

        Expected format per patent:
        - Line 1: "Patent Title | Patent Number" (e.g., "System Name | US12,345,678")
        - Line 2: Year (e.g., "2022")
        - Line 3+: Description text
        """
        content = []

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Check if this line looks like a patent title (contains | with patent number)
            if "|" in line:
                parts = line.split("|")
                patent_title = parts[0].strip()
                patent_number = parts[1].strip() if len(parts) > 1 else ""

                # Title in teal/bold (use MS_LeftPositionTitle)
                content.append(
                    Paragraph(
                        f"<b>{self._escape_text(patent_title)}</b>",
                        self.styles["MS_LeftPositionTitle"],
                    )
                )

                # Patent number in gray (use MS_LeftDate)
                if patent_number:
                    content.append(
                        Paragraph(
                            self._escape_text(patent_number), self.styles["MS_LeftDate"]
                        )
                    )

                i += 1

                # Next line might be a year
                if i < len(lines):
                    next_line = lines[i].strip()
                    # Check if it's a year (4 digits, possibly with range)
                    if (
                        next_line
                        and len(next_line) <= 15
                        and any(c.isdigit() for c in next_line)
                    ):
                        content.append(
                            Paragraph(
                                self._escape_text(next_line), self.styles["MS_LeftDate"]
                            )
                        )
                        i += 1

                # Collect description lines until next patent or end
                desc_lines = []
                while i < len(lines):
                    desc_line = lines[i].strip()
                    if not desc_line:
                        i += 1
                        continue
                    # If we hit another patent title line, stop
                    if "|" in desc_line and any(
                        c.isdigit() for c in desc_line.split("|")[-1]
                    ):
                        break
                    desc_lines.append(desc_line)
                    i += 1

                # Add description
                if desc_lines:
                    desc_text = " ".join(desc_lines)
                    content.append(
                        Paragraph(
                            self._escape_text(desc_text), self.styles["MS_LeftBody"]
                        )
                    )

                content.append(Spacer(1, 6))
            else:
                # Fallback: treat as regular text
                if line.startswith(("-", "•", "*")):
                    content.append(
                        Paragraph(
                            f"• {self._escape_text(line.lstrip('-•*').strip())}",
                            self.styles["MS_LeftBullet"],
                        )
                    )
                else:
                    content.append(
                        Paragraph(self._escape_text(line), self.styles["MS_LeftBody"])
                    )
                i += 1

        return content

    def _format_millennial_left_references(self, lines: list) -> list:
        """
        Format references section for the LEFT white content area.

        Expected format (from AI service):
        - Line 1: "Name | Role, Company"
        - Line 2: Contact details (email, phone)
        """
        content = []
        i = 0

        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Check for "Name | Role, Company" format
            if "|" in line:
                parts = line.split("|", 1)
                name = parts[0].strip()
                role = parts[1].strip() if len(parts) > 1 else ""

                # Name in teal/bold
                content.append(
                    Paragraph(
                        f"<b>{self._escape_text(name)}</b>",
                        self.styles["MS_LeftPositionTitle"],
                    )
                )

                # Role/Company in gray
                if role:
                    content.append(
                        Paragraph(
                            self._escape_text(role), self.styles["MS_LeftCompany"]
                        )
                    )

                i += 1

                # Next line is contact details
                if i < len(lines):
                    contact = lines[i].strip()
                    if contact and "|" not in contact:  # Not another reference
                        content.append(
                            Paragraph(
                                self._escape_text(contact), self.styles["MS_LeftDate"]
                            )
                        )
                        i += 1

                content.append(Spacer(1, 6))
            else:
                content.append(
                    Paragraph(self._escape_text(line), self.styles["MS_LeftBody"])
                )
                i += 1

        return content

    def _format_millennial_left_interests(self, lines: list) -> list:
        """
        Format interests section for the LEFT white content area.

        Expected format: Bullet points
        """
        content = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            clean = line.lstrip("-•*").strip()
            content.append(
                Paragraph(f"• {self._escape_text(clean)}", self.styles["MS_LeftBullet"])
            )
        return content

    def _format_millennial_left_generic(self, lines: list) -> list:
        """Format generic section for the LEFT white content area."""
        content = []
        i = 0

        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue

            # Try to parse "Title | Source" format
            if "|" in line:
                parts = line.split("|", 1)
                title = parts[0].strip()
                source = parts[1].strip() if len(parts) > 1 else ""

                content.append(
                    Paragraph(
                        f"<b>{self._escape_text(title)}</b>",
                        self.styles["MS_LeftPositionTitle"],
                    )
                )

                if source:
                    content.append(
                        Paragraph(
                            self._escape_text(source), self.styles["MS_LeftCompany"]
                        )
                    )

                i += 1

                # Check for date on next line
                if i < len(lines) and self._is_date_line(lines[i].strip()):
                    content.append(
                        Paragraph(
                            self._escape_text(lines[i].strip()),
                            self.styles["MS_LeftDate"],
                        )
                    )
                    i += 1

                content.append(Spacer(1, 4))
            elif line.startswith(("-", "•", "*")):
                content.append(
                    Paragraph(
                        f"• {self._escape_text(line.lstrip('-•*').strip())}",
                        self.styles["MS_LeftBullet"],
                    )
                )
                i += 1
            else:
                content.append(
                    Paragraph(self._escape_text(line), self.styles["MS_LeftBody"])
                )
                i += 1

        return content

    # ============ SIDEBAR SECTION FORMATTERS (Dark background) ============

    def _format_millennial_sidebar_skills(self, lines: list, width: float) -> list:
        """Format skills section for the dark sidebar with skill name + level."""
        content = []

        for line in lines:
            if not line.strip():
                continue

            # Check for "Skill - Level" or "Skill: Level" format
            skill_name = line
            skill_level = ""

            for sep in [" - ", ": ", " – ", " — "]:
                if sep in line:
                    parts = line.split(sep, 1)
                    skill_name = parts[0].strip()
                    skill_level = parts[1].strip() if len(parts) > 1 else ""
                    break

            # Create two-column table for skill name and level
            skill_table = Table(
                [
                    [
                        Paragraph(
                            self._escape_text(skill_name), self.styles["MS_SkillName"]
                        ),
                        Paragraph(
                            self._escape_text(skill_level), self.styles["MS_SkillLevel"]
                        )
                        if skill_level
                        else Paragraph("", self.styles["MS_SkillLevel"]),
                    ]
                ],
                colWidths=[width * 0.65, width * 0.35],
                style=TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ]
                ),
            )
            content.append(skill_table)

        return content

    def _format_millennial_sidebar_languages(self, lines: list, width: float) -> list:
        """Format languages section for the dark sidebar."""
        content = []

        for line in lines:
            if not line.strip():
                continue

            # Check for "Language - Level" format
            lang_name = line
            lang_level = ""

            for sep in [" - ", ": ", " – ", " — ", " ("]:
                if sep in line:
                    parts = line.split(sep, 1)
                    lang_name = parts[0].strip()
                    lang_level = parts[1].strip().rstrip(")") if len(parts) > 1 else ""
                    break

            # Two-column table
            lang_table = Table(
                [
                    [
                        Paragraph(
                            self._escape_text(lang_name), self.styles["MS_LanguageName"]
                        ),
                        Paragraph(
                            self._escape_text(lang_level),
                            self.styles["MS_LanguageLevel"],
                        )
                        if lang_level
                        else Paragraph("", self.styles["MS_LanguageLevel"]),
                    ]
                ],
                colWidths=[width * 0.55, width * 0.45],
                style=TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ]
                ),
            )
            content.append(lang_table)

        return content

    def _format_millennial_sidebar_certifications(self, lines: list) -> list:
        """Format certifications section for the dark sidebar."""
        content = []

        current_cert = {"name": "", "date": ""}

        for line in lines:
            if not line.strip():
                continue

            # Check if it's a date line
            if self._is_date_line(line) and len(line) <= 25:
                current_cert["date"] = line
                # Output the cert
                if current_cert["name"]:
                    content.append(
                        Paragraph(
                            self._escape_text(current_cert["name"]),
                            self.styles["MS_CertName"],
                        )
                    )
                    if current_cert["date"]:
                        content.append(
                            Paragraph(
                                self._escape_text(current_cert["date"]),
                                self.styles["MS_CertDate"],
                            )
                        )
                    current_cert = {"name": "", "date": ""}
            else:
                # If we have a pending cert, output it first
                if current_cert["name"]:
                    content.append(
                        Paragraph(
                            self._escape_text(current_cert["name"]),
                            self.styles["MS_CertName"],
                        )
                    )
                    if current_cert["date"]:
                        content.append(
                            Paragraph(
                                self._escape_text(current_cert["date"]),
                                self.styles["MS_CertDate"],
                            )
                        )
                current_cert = {"name": line, "date": ""}

        # Don't forget last one
        if current_cert["name"]:
            content.append(
                Paragraph(
                    self._escape_text(current_cert["name"]), self.styles["MS_CertName"]
                )
            )
            if current_cert["date"]:
                content.append(
                    Paragraph(
                        self._escape_text(current_cert["date"]),
                        self.styles["MS_CertDate"],
                    )
                )

        return content

    def _format_millennial_sidebar_generic(self, lines: list) -> list:
        """Format generic section for the dark sidebar."""
        content = []
        for line in lines:
            if line.strip():
                # Use white text style
                content.append(
                    Paragraph(self._escape_text(line), self.styles["MS_SidebarBullet"])
                )
        return content

    # ============ OLD SIDEBAR SECTION FORMATTERS (kept for compatibility) ============

    def _format_millennial_sidebar_experience(self, lines: list) -> list:
        """Format experience section for the dark sidebar."""
        content = []

        entries = []
        current_entry = {
            "position": "",
            "company": "",
            "date": "",
            "bullets": [],
        }

        i = 0
        while i < len(lines):
            line = lines[i]

            if not line:
                if current_entry["position"]:
                    entries.append(current_entry)
                    current_entry = {
                        "position": "",
                        "company": "",
                        "date": "",
                        "bullets": [],
                    }
                i += 1
                continue

            # Check for "Position | Company" format
            if "|" in line and not line.lower().startswith("technologies"):
                if current_entry["position"]:
                    entries.append(current_entry)
                    current_entry = {
                        "position": "",
                        "company": "",
                        "date": "",
                        "bullets": [],
                    }

                parts = line.split("|", 1)
                current_entry["position"] = parts[0].strip()
                current_entry["company"] = parts[1].strip() if len(parts) > 1 else ""
                i += 1
                continue

            # Check for date line
            if self._is_date_line(line):
                current_entry["date"] = line
                i += 1
                continue

            # Check for bullet points
            if line.startswith(("-", "•", "*", "○", "·")):
                bullet_text = line.lstrip("-•*○·").strip()
                current_entry["bullets"].append(bullet_text)
                i += 1
                continue

            # Check if this might be position or company
            if not current_entry["position"]:
                current_entry["position"] = line
            elif not current_entry["company"]:
                current_entry["company"] = line
            else:
                current_entry["bullets"].append(line)
            i += 1

        # Don't forget last entry
        if current_entry["position"]:
            entries.append(current_entry)

        # Render each entry
        for entry in entries:
            # Position title (teal)
            if entry["position"]:
                content.append(
                    Paragraph(
                        self._escape_text(entry["position"]),
                        self.styles["MS_SidebarPositionTitle"],
                    )
                )

            # Company name (white)
            if entry["company"]:
                content.append(
                    Paragraph(
                        self._escape_text(entry["company"]),
                        self.styles["MS_SidebarCompany"],
                    )
                )

            # Date (light gray)
            if entry["date"]:
                content.append(
                    Paragraph(
                        self._escape_text(entry["date"]), self.styles["MS_SidebarDate"]
                    )
                )

            # Bullet points
            for bullet in entry["bullets"]:
                content.append(
                    Paragraph(
                        f"• {self._escape_text(bullet)}",
                        self.styles["MS_SidebarBullet"],
                    )
                )

        return content

    def _format_millennial_sidebar_education(self, lines: list) -> list:
        """Format education section for the dark sidebar."""
        content = []

        entries = []
        current_entry = {"degree": "", "institution": "", "year": "", "details": []}

        for line in lines:
            if not line:
                if current_entry["degree"] or current_entry["institution"]:
                    entries.append(current_entry)
                    current_entry = {
                        "degree": "",
                        "institution": "",
                        "year": "",
                        "details": [],
                    }
                continue

            # Check for year/date
            if self._is_date_line(line) and len(line) <= 40:
                current_entry["year"] = line
                continue

            # Check for institution keywords
            inst_keywords = ["university", "college", "institute", "school", "academy"]
            is_institution = any(kw in line.lower() for kw in inst_keywords)

            # Check for degree keywords
            degree_keywords = [
                "bachelor",
                "master",
                "phd",
                "diploma",
                "degree",
                "bsc",
                "msc",
                "mba",
                "associate",
                "certificate",
            ]
            is_degree = any(kw in line.lower() for kw in degree_keywords)

            if is_degree and not current_entry["degree"]:
                current_entry["degree"] = line
            elif is_institution and not current_entry["institution"]:
                current_entry["institution"] = line
            elif not current_entry["degree"]:
                current_entry["degree"] = line
            elif not current_entry["institution"]:
                current_entry["institution"] = line
            else:
                current_entry["details"].append(line)

        if current_entry["degree"] or current_entry["institution"]:
            entries.append(current_entry)

        # Render each entry
        for entry in entries:
            # Degree (teal)
            if entry["degree"]:
                content.append(
                    Paragraph(
                        self._escape_text(entry["degree"]),
                        self.styles["MS_SidebarDegree"],
                    )
                )

            # Institution (white)
            if entry["institution"]:
                content.append(
                    Paragraph(
                        self._escape_text(entry["institution"]),
                        self.styles["MS_SidebarInstitution"],
                    )
                )

            # Year (light gray)
            if entry["year"]:
                content.append(
                    Paragraph(
                        self._escape_text(entry["year"]), self.styles["MS_SidebarDate"]
                    )
                )

            # Additional details
            for detail in entry["details"]:
                content.append(
                    Paragraph(
                        self._escape_text(detail), self.styles["MS_SidebarBullet"]
                    )
                )

        return content

    def _format_millennial_sidebar_summary(self, lines: list) -> list:
        """Format professional summary for the dark sidebar."""
        content = []
        for line in lines:
            if line.strip():
                content.append(
                    Paragraph(self._escape_text(line), self.styles["MS_SidebarBullet"])
                )
        return content

    def _format_millennial_sidebar_volunteer(self, lines: list) -> list:
        """Format volunteer experience (same as regular experience)."""
        return self._format_millennial_sidebar_experience(lines)

    # ============ RIGHT COLUMN SECTION FORMATTERS ============

    def _format_millennial_right_skills(self, lines: list, width: float) -> list:
        """
        Format skills section as two-column layout: Skill name (left) + Level (right, teal).
        """
        content = []

        skill_items = []
        for line in lines:
            if not line:
                continue

            clean_line = line.lstrip("-•*○·").strip()
            if not clean_line:
                continue

            name = clean_line
            level = ""

            # Parse skill: level format
            if ":" in clean_line:
                parts = clean_line.split(":", 1)
                name = parts[0].strip()
                level = parts[1].strip() if len(parts) > 1 else ""
            elif " - " in clean_line:
                parts = clean_line.split(" - ", 1)
                name = parts[0].strip()
                level = parts[1].strip() if len(parts) > 1 else ""

            if name:
                skill_items.append({"name": name, "level": level})

        # Create table with skill name left, level right
        for skill in skill_items:
            name_para = Paragraph(
                self._escape_text(skill["name"]), self.styles["MS_SkillName"]
            )
            level_para = Paragraph(
                self._escape_text(skill["level"]), self.styles["MS_SkillLevel"]
            )

            skill_row = Table(
                [[name_para, level_para]],
                colWidths=[width * 0.6, width * 0.4],
                style=TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ALIGN", (0, 0), (0, 0), "LEFT"),
                        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                ),
            )
            content.append(skill_row)

        return content

    def _format_millennial_right_languages(self, lines: list, width: float) -> list:
        """
        Format languages section as two-column layout: Language (left) + Level (right, teal).
        """
        content = []

        lang_items = []
        for line in lines:
            if not line:
                continue

            clean_line = line.lstrip("-•*○·").strip()
            if not clean_line:
                continue

            name = clean_line
            level = ""

            if ":" in clean_line:
                parts = clean_line.split(":", 1)
                name = parts[0].strip()
                level = parts[1].strip() if len(parts) > 1 else ""
            elif " - " in clean_line:
                parts = clean_line.split(" - ", 1)
                name = parts[0].strip()
                level = parts[1].strip() if len(parts) > 1 else ""

            if name:
                lang_items.append({"name": name, "level": level})

        for lang in lang_items:
            name_para = Paragraph(
                self._escape_text(lang["name"]), self.styles["MS_LanguageName"]
            )
            level_para = Paragraph(
                self._escape_text(lang["level"]), self.styles["MS_LanguageLevel"]
            )

            lang_row = Table(
                [[name_para, level_para]],
                colWidths=[width * 0.6, width * 0.4],
                style=TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                        ("ALIGN", (0, 0), (0, 0), "LEFT"),
                        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ]
                ),
            )
            content.append(lang_row)

        return content

    def _format_millennial_right_certifications(self, lines: list) -> list:
        """Format certifications section for right column."""
        content = []

        i = 0
        while i < len(lines):
            line = lines[i]

            if not line:
                i += 1
                continue

            clean_line = line.lstrip("-•*○·").strip()
            if not clean_line:
                i += 1
                continue

            cert_name = clean_line
            date_str = ""

            # Check if date is embedded in parentheses
            if "(" in clean_line and ")" in clean_line:
                paren_content = clean_line.split("(")[-1].rstrip(")")
                if self._is_date_line(paren_content):
                    cert_name = clean_line.split("(")[0].strip()
                    date_str = paren_content

            # Check next line for date
            if not date_str and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if self._is_date_line(next_line):
                    date_str = next_line
                    i += 1

            # Certificate name (bold, dark)
            content.append(
                Paragraph(self._escape_text(cert_name), self.styles["MS_CertName"])
            )

            # Date (teal accent)
            if date_str:
                content.append(
                    Paragraph(self._escape_text(date_str), self.styles["MS_CertDate"])
                )

            i += 1

        return content

    def _format_millennial_right_awards(self, lines: list) -> list:
        """Format awards section for right column."""
        content = []

        i = 0
        while i < len(lines):
            line = lines[i]

            if not line:
                i += 1
                continue

            # Check for Award | Organization pattern
            if "|" in line:
                parts = line.split("|", 1)
                award = parts[0].strip()
                org = parts[1].strip() if len(parts) > 1 else ""

                content.append(
                    Paragraph(self._escape_text(award), self.styles["MS_RightTitle"])
                )
                if org:
                    content.append(
                        Paragraph(
                            self._escape_text(org), self.styles["MS_RightSubtitle"]
                        )
                    )

                # Check next line for date
                if i + 1 < len(lines) and self._is_date_line(lines[i + 1].strip()):
                    content.append(
                        Paragraph(
                            self._escape_text(lines[i + 1].strip()),
                            self.styles["MS_CertDate"],
                        )
                    )
                    i += 1
            else:
                clean = line.lstrip("-•*○·").strip()
                if clean:
                    content.append(
                        Paragraph(
                            self._escape_text(clean), self.styles["MS_RightBodyText"]
                        )
                    )
            i += 1

        return content

    def _format_millennial_right_interests(self, lines: list) -> list:
        """Format interests section for right column."""
        content = []
        for line in lines:
            if not line:
                continue
            clean = line.lstrip("-•*○·").strip()
            if clean:
                content.append(
                    Paragraph(
                        f"• {self._escape_text(clean)}", self.styles["MS_RightBullet"]
                    )
                )
        return content

    def _format_millennial_right_projects(self, lines: list) -> list:
        """Format projects section for right column."""
        content = []

        i = 0
        while i < len(lines):
            line = lines[i]

            if not line:
                i += 1
                continue

            # Check for project title (short line, not bullet)
            is_bullet = line.startswith(("-", "•", "*", "○", "·"))
            is_tech = line.lower().startswith("technologies:")

            if not is_bullet and not is_tech and len(line) < 80:
                # This is likely a project title
                content.append(
                    Paragraph(self._escape_text(line), self.styles["MS_RightTitle"])
                )
            elif is_tech:
                content.append(
                    Paragraph(
                        f"<i>{self._escape_text(line)}</i>",
                        self.styles["MS_RightSubtitle"],
                    )
                )
            elif is_bullet:
                bullet_text = line.lstrip("-•*○·").strip()
                content.append(
                    Paragraph(
                        f"• {self._escape_text(bullet_text)}",
                        self.styles["MS_RightBullet"],
                    )
                )
            else:
                content.append(
                    Paragraph(self._escape_text(line), self.styles["MS_RightBodyText"])
                )
            i += 1

        return content

    def _format_millennial_right_publications(self, lines: list) -> list:
        """Format publications section for right column."""
        content = []

        i = 0
        while i < len(lines):
            line = lines[i]

            if not line:
                i += 1
                continue

            # Check for Title | Venue pattern
            if "|" in line:
                parts = line.split("|", 1)
                title = parts[0].strip()
                venue = parts[1].strip() if len(parts) > 1 else ""

                content.append(
                    Paragraph(self._escape_text(title), self.styles["MS_RightTitle"])
                )
                if venue:
                    content.append(
                        Paragraph(
                            self._escape_text(venue), self.styles["MS_RightSubtitle"]
                        )
                    )

                # Check for date
                if i + 1 < len(lines) and self._is_date_line(lines[i + 1].strip()):
                    content.append(
                        Paragraph(
                            self._escape_text(lines[i + 1].strip()),
                            self.styles["MS_CertDate"],
                        )
                    )
                    i += 1
            else:
                clean = line.lstrip("-•*○·").strip()
                if clean:
                    content.append(
                        Paragraph(
                            self._escape_text(clean), self.styles["MS_RightBodyText"]
                        )
                    )
            i += 1

        return content

    def _format_millennial_right_memberships(self, lines: list) -> list:
        """Format memberships section for right column."""
        content = []
        for line in lines:
            if not line:
                continue
            clean = line.lstrip("-•*○·").strip()
            if clean:
                content.append(
                    Paragraph(
                        f"• {self._escape_text(clean)}", self.styles["MS_RightBullet"]
                    )
                )
        return content

    def _format_millennial_right_conferences(self, lines: list) -> list:
        """Format conferences section for right column."""
        content = []
        for line in lines:
            if not line:
                continue
            clean = line.lstrip("-•*○·").strip()
            if clean:
                content.append(
                    Paragraph(
                        f"• {self._escape_text(clean)}", self.styles["MS_RightBullet"]
                    )
                )
        return content

    def _format_millennial_right_patents(self, lines: list) -> list:
        """Format patents section for right column."""
        content = []

        i = 0
        while i < len(lines):
            line = lines[i]

            if not line:
                i += 1
                continue

            # Check for Title | Patent Number pattern
            if "|" in line:
                parts = line.split("|", 1)
                title = parts[0].strip()
                number = parts[1].strip() if len(parts) > 1 else ""

                content.append(
                    Paragraph(self._escape_text(title), self.styles["MS_RightTitle"])
                )
                if number:
                    content.append(
                        Paragraph(
                            self._escape_text(number), self.styles["MS_RightSubtitle"]
                        )
                    )

                # Check for date
                if i + 1 < len(lines) and self._is_date_line(lines[i + 1].strip()):
                    content.append(
                        Paragraph(
                            self._escape_text(lines[i + 1].strip()),
                            self.styles["MS_CertDate"],
                        )
                    )
                    i += 1
            else:
                content.append(
                    Paragraph(self._escape_text(line), self.styles["MS_RightBodyText"])
                )
            i += 1

        return content

    def _format_millennial_right_references(self, lines: list) -> list:
        """Format references section for right column."""
        content = []

        i = 0
        while i < len(lines):
            line = lines[i]

            if not line:
                i += 1
                continue

            # Check for Name | Role pattern
            if "|" in line:
                parts = line.split("|", 1)
                name = parts[0].strip()
                role = parts[1].strip() if len(parts) > 1 else ""

                content.append(
                    Paragraph(self._escape_text(name), self.styles["MS_RightTitle"])
                )
                if role:
                    content.append(
                        Paragraph(
                            self._escape_text(role), self.styles["MS_RightSubtitle"]
                        )
                    )
            else:
                content.append(
                    Paragraph(self._escape_text(line), self.styles["MS_RightBodyText"])
                )
            i += 1

        return content

    def _format_millennial_right_generic(self, lines: list) -> list:
        """Format generic content for right column."""
        content = []
        for line in lines:
            if not line:
                continue
            if line.startswith(("-", "•", "*")):
                bullet_text = line.lstrip("-•*").strip()
                content.append(
                    Paragraph(
                        f"• {self._escape_text(bullet_text)}",
                        self.styles["MS_RightBullet"],
                    )
                )
            else:
                content.append(
                    Paragraph(self._escape_text(line), self.styles["MS_RightBodyText"])
                )
        return content

    def _add_millennial_style_footer(
        self, canvas_obj: canvas.Canvas, doc: SimpleDocTemplate
    ):
        """
        Add footer to Millennial Style template pages.

        Args:
            canvas_obj: ReportLab canvas object
            doc: Document object
        """
        canvas_obj.saveState()

        page_num = canvas_obj.getPageNumber()
        text = f"Page {page_num}"

        canvas_obj.setFont("Helvetica", 8)
        canvas_obj.setFillColor(colors.HexColor("#666666"))
        canvas_obj.drawCentredString(self.PAGE_WIDTH / 2, 0.4 * inch, text)

        canvas_obj.restoreState()

    # ============ CORPORATE CLASSIC TEMPLATE METHODS ============

    def _parse_corporate_classic_content(self, content: str) -> list:
        """
        Parse CV content for the Corporate Classic template.

        Features:
        - Stacked name (first name smaller above, last name larger below)
        - Contact info stacked on right side
        - Italic professional summary
        - Section headers with black underlines
        - Two-column layout for older experience entries
        - Two-column grid for skills
        - Serif fonts (Times family) throughout
        - Monochromatic (black only)

        Args:
            content: Raw CV text content

        Returns:
            List of reportlab flowables
        """
        elements = []
        # Preserve blank lines so section formatters can detect entry boundaries
        lines = [line.strip() for line in content.split("\n")]

        if not any(lines):
            raise ValueError("CV content is empty after parsing")

        # ============ PARSE HEADER INFORMATION ============
        _si = 0
        while _si < len(lines) and not lines[_si]:
            _si += 1
        name = lines[_si] if _si < len(lines) else "Candidate Name"
        job_title = ""
        contact_lines = []
        portfolio_lines = []
        idx = _si + 1

        # Skip blank lines before job title
        while idx < len(lines) and not lines[idx]:
            idx += 1

        # Look for job title (usually second line)
        if idx < len(lines):
            potential_title = lines[idx]
            if not any(
                marker in potential_title.lower()
                for marker in ["@", "+", "http", ".com", ".io", ".dev", "|", "•"]
            ):
                if not self._is_section_header(potential_title):
                    job_title = potential_title
                    idx += 1

        # Collect contact and portfolio info
        _header_end = min(_si + 15, len(lines))
        while idx < _header_end:
            line = lines[idx]
            if not line:
                idx += 1
                continue
            if self._is_section_header(line):
                break

            is_portfolio = any(
                marker in line.lower()
                for marker in [
                    "portfolio",
                    "github",
                    "linkedin",
                    "gitlab",
                    ".dev",
                    ".io",
                    "http",
                    "www.",
                ]
            )

            is_contact = (
                any(marker in line for marker in ["@", "+"])
                or "|" in line
                or "•" in line
            )

            if is_portfolio:
                portfolio_lines.append(line)
            elif is_contact:
                contact_lines.append(line)
            else:
                break
            idx += 1

        # Build header with stacked name and right-aligned contact
        header_elements = self._build_corporate_classic_header(
            name, job_title, contact_lines, portfolio_lines
        )
        elements.extend(header_elements)

        # ============ PARSE CONTENT SECTIONS ============
        current_section = []
        current_section_name = ""

        for line in lines[idx:]:
            if self._is_section_header(line):
                # Process previous section
                if current_section:
                    section_elements = self._format_corporate_classic_section(
                        current_section, current_section_name
                    )
                    elements.extend(section_elements)
                    current_section = []

                # Add section header with underline
                section_title = line.rstrip(":").strip()
                current_section_name = section_title
                elements.append(Spacer(1, 0.15 * inch))
                elements.append(
                    Paragraph(
                        self._escape_text(section_title.upper()),
                        self.styles["CC_SectionHeader"],
                    )
                )
                # Add underline below header
                elements.append(self._create_corporate_classic_underline())
                elements.append(Spacer(1, 0.08 * inch))
            else:
                current_section.append(line)

        # Add final section
        if current_section:
            section_elements = self._format_corporate_classic_section(
                current_section, current_section_name
            )
            elements.extend(section_elements)

        return elements

    def _build_corporate_classic_header(
        self, name: str, job_title: str, contact_lines: list, portfolio_lines: list
    ) -> list:
        """
        Build the header section for Corporate Classic template.

        Layout:
        - Left side: Stacked name (first name smaller, last name larger below)
        - Right side: Contact info stacked vertically
        - Below: Job title (if any) and professional summary will be added by section

        Args:
            name: Candidate's full name
            job_title: Current job title
            contact_lines: List of contact info lines
            portfolio_lines: List of portfolio/link lines

        Returns:
            List of flowables for the header
        """
        elements = []
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT

        # Split name into first and last
        name_parts = name.split()
        if len(name_parts) >= 2:
            first_name = name_parts[0].upper()
            last_name = " ".join(name_parts[1:]).upper()
        else:
            first_name = ""
            last_name = name.upper()

        # Build left side: stacked name
        left_content = []
        if first_name:
            left_content.append(
                Paragraph(self._escape_text(first_name), self.styles["CC_FirstName"])
            )
        left_content.append(
            Paragraph(self._escape_text(last_name), self.styles["CC_LastName"])
        )

        # Build right side: contact info stacked
        right_content = []
        all_contact = contact_lines + portfolio_lines

        # Parse contact items from lines
        contact_items = []
        for line in all_contact:
            parts = line.replace("•", "|").replace("·", "|").split("|")
            for part in parts:
                part = part.strip()
                if part:
                    contact_items.append(part)

        # Add each contact item on separate line
        for item in contact_items:
            right_content.append(
                Paragraph(self._escape_text(item), self.styles["CC_Contact"])
            )

        # Create header table
        left_cell = (
            left_content
            if left_content
            else [Paragraph("", self.styles["CC_LastName"])]
        )
        right_cell = (
            right_content
            if right_content
            else [Paragraph("", self.styles["CC_Contact"])]
        )

        header_table = Table(
            [[left_cell, right_cell]],
            colWidths=[available_width * 0.55, available_width * 0.45],
            style=TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("ALIGN", (0, 0), (0, 0), "LEFT"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            ),
        )

        elements.append(header_table)
        elements.append(Spacer(1, 0.15 * inch))

        return elements

    def _create_corporate_classic_underline(self) -> Table:
        """Create a black underline for section headers."""
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT
        underline = Table(
            [[""]],
            colWidths=[available_width],
            style=TableStyle(
                [
                    ("LINEBELOW", (0, 0), (-1, 0), 1, colors.black),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            ),
        )
        return underline

    def _format_corporate_classic_section(
        self, lines: list, section_name: str = ""
    ) -> list:
        """
        Format section content for Corporate Classic template.

        Routes to specialized formatters based on section type.

        Args:
            lines: List of text lines in the section
            section_name: Name of the section for context-aware formatting

        Returns:
            List of formatted PDF elements
        """
        section_lower = section_name.lower()

        # Route to specialized formatters
        if (
            "summary" in section_lower
            or "profile" in section_lower
            or "objective" in section_lower
        ):
            return self._format_corporate_classic_summary(lines)
        elif (
            "experience" in section_lower
            or "employment" in section_lower
            or "career" in section_lower
        ):
            return self._format_corporate_classic_experience(lines)
        elif (
            "education" in section_lower
            or "academic" in section_lower
            or "qualification" in section_lower
        ):
            return self._format_corporate_classic_education(lines)
        elif "skill" in section_lower or "competenc" in section_lower:
            return self._format_corporate_classic_skills(lines)
        elif (
            "certification" in section_lower
            or "certificate" in section_lower
            or "license" in section_lower
        ):
            return self._format_corporate_classic_certifications(lines)
        elif "project" in section_lower or "portfolio" in section_lower:
            return self._format_corporate_classic_projects(lines)
        elif "language" in section_lower:
            return self._format_corporate_classic_languages(lines)
        elif "interest" in section_lower or "hobbi" in section_lower:
            return self._format_corporate_classic_interests(lines)
        elif (
            "award" in section_lower
            or "achievement" in section_lower
            or "honor" in section_lower
        ):
            return self._format_corporate_classic_awards(lines)
        elif "volunteer" in section_lower or "community" in section_lower:
            return self._format_corporate_classic_volunteer(lines)
        elif (
            "publication" in section_lower
            or "research" in section_lower
            or "paper" in section_lower
        ):
            return self._format_corporate_classic_publications(lines)
        elif "membership" in section_lower or "affiliation" in section_lower:
            return self._format_corporate_classic_memberships(lines)
        elif (
            "conference" in section_lower
            or "speaking" in section_lower
            or "talk" in section_lower
        ):
            return self._format_corporate_classic_conferences(lines)
        elif "patent" in section_lower or "intellectual" in section_lower:
            return self._format_corporate_classic_patents(lines)
        elif "reference" in section_lower or "referee" in section_lower:
            return self._format_corporate_classic_references(lines)
        else:
            return self._format_corporate_classic_generic(lines)

    def _format_corporate_classic_summary(self, lines: list) -> list:
        """Format professional summary in italic."""
        elements = []
        for line in lines:
            if line.strip():
                elements.append(
                    Paragraph(self._escape_text(line), self.styles["CC_Summary"])
                )
        return elements

    def _format_corporate_classic_experience(self, lines: list) -> list:
        """
        Format experience section for Corporate Classic template.

        Layout:
        - First job: Full width, alone
        - Subsequent jobs: Two-column layout (pairs side by side)

        Args:
            lines: List of experience entry lines

        Returns:
            List of flowables
        """
        elements = []
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT

        # Group lines into experience entries
        entries = []
        current_entry = {
            "position": "",
            "company": "",
            "location": "",
            "date": "",
            "bullets": [],
            "technologies": "",
        }

        i = 0
        while i < len(lines):
            line = lines[i]

            if not line:
                if current_entry["position"]:
                    entries.append(current_entry)
                    current_entry = {
                        "position": "",
                        "company": "",
                        "location": "",
                        "date": "",
                        "bullets": [],
                        "technologies": "",
                    }
                i += 1
                continue

            # Check for "Position | Company" format
            if "|" in line and not line.lower().startswith("technologies"):
                if current_entry["position"]:
                    entries.append(current_entry)
                    current_entry = {
                        "position": "",
                        "company": "",
                        "location": "",
                        "date": "",
                        "bullets": [],
                        "technologies": "",
                    }

                parts = line.split("|")
                current_entry["position"] = parts[0].strip()
                if len(parts) > 1:
                    current_entry["company"] = parts[1].strip()
                if len(parts) > 2:
                    current_entry["location"] = parts[2].strip()
                i += 1
                continue

            # Check for date line
            elif self._is_date_line(line):
                current_entry["date"] = line
                i += 1
                continue

            # Check for bullet points
            elif line.startswith(("-", "•", "*", "○", "·")):
                bullet_text = line.lstrip("-•*○·").strip()
                current_entry["bullets"].append(bullet_text)
                i += 1
                continue

            # Check for technologies line
            elif line.lower().startswith("technologies:"):
                current_entry["technologies"] = line
                i += 1
                continue

            # If we don't have a position yet, this might be one
            elif not current_entry["position"]:
                current_entry["position"] = line
                i += 1
                continue

            # If we have position but no company, this might be company
            elif not current_entry["company"]:
                current_entry["company"] = line
                i += 1
                continue

            # Otherwise treat as bullet point
            else:
                current_entry["bullets"].append(line)
                i += 1

        # Don't forget the last entry
        if current_entry["position"]:
            entries.append(current_entry)

        # Render entries: first one full width, rest in two-column pairs
        for idx, entry in enumerate(entries):
            if idx == 0:
                # First entry: full width layout
                elements.extend(
                    self._render_corporate_classic_experience_entry(
                        entry, available_width, is_compact=False
                    )
                )
            else:
                # Subsequent entries: collect pairs for two-column layout
                if idx == 1:
                    # Start collecting pairs from index 1
                    elements.append(Spacer(1, 0.15 * inch))

                # Check if this is an odd-indexed entry (left column) or even (right column)
                pair_idx = (
                    idx - 1
                )  # 0-based index for pairs (entry 1 -> pair 0, entry 2 -> pair 0, etc.)

                if pair_idx % 2 == 0:
                    # Left column entry - check if there's a right partner
                    left_entry = entry
                    right_entry = entries[idx + 1] if idx + 1 < len(entries) else None

                    # Build two-column table for this pair
                    left_content = (
                        self._render_corporate_classic_experience_entry_compact(
                            left_entry, available_width * 0.48
                        )
                    )
                    right_content = (
                        self._render_corporate_classic_experience_entry_compact(
                            right_entry, available_width * 0.48
                        )
                        if right_entry
                        else [Paragraph("", self.styles["CC_BodyText"])]
                    )

                    pair_table = Table(
                        [[left_content, right_content]],
                        colWidths=[available_width * 0.48, available_width * 0.48],
                        style=TableStyle(
                            [
                                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                ("RIGHTPADDING", (0, 0), (0, 0), 10),
                                ("RIGHTPADDING", (1, 0), (1, 0), 0),
                                ("TOPPADDING", (0, 0), (-1, -1), 0),
                                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                            ]
                        ),
                    )
                    elements.append(pair_table)
                # Skip right column entries as they're handled with their left partner

        return elements

    def _render_corporate_classic_experience_entry(
        self, entry: dict, width: float, is_compact: bool = False
    ) -> list:
        """
        Render a single experience entry for full-width display.

        Args:
            entry: Experience entry dictionary
            width: Available width
            is_compact: Whether to use compact styling

        Returns:
            List of flowables
        """
        elements = []

        # Job Title (bold, uppercase)
        elements.append(
            Paragraph(
                self._escape_text(entry["position"].upper()),
                self.styles["CC_JobTitle"],
            )
        )

        # Company | Location on same line
        company_text = entry["company"]
        if entry["location"]:
            company_text += f" | {entry['location']}"

        if company_text:
            elements.append(
                Paragraph(self._escape_text(company_text), self.styles["CC_Company"])
            )

        # Date
        if entry["date"]:
            elements.append(
                Paragraph(self._escape_text(entry["date"]), self.styles["CC_Location"])
            )

        # Description/Bullets as paragraph text (not bullet points for cleaner look)
        if entry["bullets"]:
            # Join bullets into flowing paragraph
            description = " ".join(entry["bullets"])
            elements.append(
                Paragraph(self._escape_text(description), self.styles["CC_BodyText"])
            )

        # Technologies at bottom (italic)
        if entry["technologies"]:
            elements.append(
                Paragraph(
                    f"<i>{self._escape_text(entry['technologies'])}</i>",
                    self.styles["CC_BodyText"],
                )
            )

        return elements

    def _render_corporate_classic_experience_entry_compact(
        self, entry: dict, width: float
    ) -> list:
        """
        Render a single experience entry for compact two-column display.

        Args:
            entry: Experience entry dictionary
            width: Available width for this column

        Returns:
            List of flowables for table cell
        """
        if not entry:
            return [Paragraph("", self.styles["CC_BodyText"])]

        content = []

        # Job Title (bold, uppercase)
        content.append(
            Paragraph(
                self._escape_text(entry["position"].upper()),
                self.styles["CC_JobTitle"],
            )
        )

        # Company | Location on same line
        company_text = entry["company"]
        if entry["location"]:
            company_text += f" | {entry['location']}"

        if company_text:
            content.append(
                Paragraph(self._escape_text(company_text), self.styles["CC_Company"])
            )

        # Date
        if entry["date"]:
            content.append(
                Paragraph(self._escape_text(entry["date"]), self.styles["CC_Location"])
            )

        # Description/Bullets as paragraph text
        if entry["bullets"]:
            description = " ".join(entry["bullets"])
            content.append(
                Paragraph(self._escape_text(description), self.styles["CC_SmallText"])
            )

        return content

    def _format_corporate_classic_education(self, lines: list) -> list:
        """Format education section for Corporate Classic template."""
        elements = []
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT

        entries = []
        current_entry = {
            "degree": "",
            "institution": "",
            "location": "",
            "date": "",
            "details": [],
        }

        i = 0
        while i < len(lines):
            line = lines[i]

            if not line:
                if current_entry["degree"]:
                    entries.append(current_entry)
                    current_entry = {
                        "degree": "",
                        "institution": "",
                        "location": "",
                        "date": "",
                        "details": [],
                    }
                i += 1
                continue

            # Check for "Degree | Institution" format
            if "|" in line:
                if current_entry["degree"]:
                    entries.append(current_entry)
                    current_entry = {
                        "degree": "",
                        "institution": "",
                        "location": "",
                        "date": "",
                        "details": [],
                    }

                parts = line.split("|")
                current_entry["degree"] = parts[0].strip()
                if len(parts) > 1:
                    current_entry["institution"] = parts[1].strip()
                if len(parts) > 2:
                    current_entry["location"] = parts[2].strip()
                i += 1
                continue

            elif self._is_date_line(line):
                current_entry["date"] = line
                i += 1
                continue

            elif line.startswith(("-", "•", "*", "○", "·")):
                current_entry["details"].append(line.lstrip("-•*○·").strip())
                i += 1
                continue

            elif not current_entry["degree"]:
                current_entry["degree"] = line
                i += 1
                continue

            elif not current_entry["institution"]:
                current_entry["institution"] = line
                i += 1
                continue

            else:
                current_entry["details"].append(line)
                i += 1

        if current_entry["degree"]:
            entries.append(current_entry)

        for idx, entry in enumerate(entries):
            if idx > 0:
                elements.append(Spacer(1, 0.1 * inch))

            # Degree (bold)
            elements.append(
                Paragraph(self._escape_text(entry["degree"]), self.styles["CC_Degree"])
            )

            # Institution and Date on same line
            inst_text = entry["institution"]
            if entry["location"]:
                inst_text += f", {entry['location']}"

            if inst_text or entry["date"]:
                inst_para = Paragraph(
                    self._escape_text(inst_text), self.styles["CC_Institution"]
                )
                date_para = Paragraph(
                    self._escape_text(entry["date"]), self.styles["CC_Date"]
                )

                inst_date_table = Table(
                    [[inst_para, date_para]],
                    colWidths=[available_width * 0.70, available_width * 0.30],
                    style=TableStyle(
                        [
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("ALIGN", (0, 0), (0, 0), "LEFT"),
                            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                        ]
                    ),
                )
                elements.append(inst_date_table)

            # Details (bullets or plain text)
            for detail in entry["details"]:
                elements.append(
                    Paragraph(
                        f"• {self._escape_text(detail)}", self.styles["CC_Bullet"]
                    )
                )

        return elements

    def _format_corporate_classic_skills(self, lines: list) -> list:
        """
        Format skills section in two-column grid for Corporate Classic template.

        Layout: Two columns of skill names only (no proficiency levels)

        Args:
            lines: List of skill lines

        Returns:
            List of flowables
        """
        elements = []
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT

        # Parse skills from lines - extract skill names only, remove levels
        skills = []
        for line in lines:
            if not line:
                continue

            # Remove proficiency levels like "Expert", "Advanced", "Intermediate", etc.
            clean_line = line.strip()

            # Handle "Skill: Level" format - keep only the skill name
            if ":" in clean_line and not self._is_date_line(clean_line):
                parts = clean_line.split(":")
                skill_name = parts[0].strip()
                # Check if second part is a proficiency level
                if len(parts) > 1:
                    level_part = parts[1].strip().lower()
                    if level_part in [
                        "expert",
                        "advanced",
                        "intermediate",
                        "beginner",
                        "basic",
                        "fluent",
                        "native",
                        "proficient",
                    ]:
                        # It's a "Skill: Level" format - just keep skill name
                        if skill_name:
                            skills.append(skill_name)
                    else:
                        # It's "Category: items" format - expand items
                        skill_items = [s.strip() for s in parts[1].split(",")]
                        for skill in skill_items:
                            if skill:
                                skills.append(skill)
                else:
                    if skill_name:
                        skills.append(skill_name)
            # Handle bullet points
            elif clean_line.startswith(("-", "•", "*", "○", "·")):
                skill = clean_line.lstrip("-•*○·").strip()
                # Also strip level if present
                if ":" in skill:
                    skill = skill.split(":")[0].strip()
                if skill:
                    skills.append(skill)
            else:
                # Plain skill name
                if ":" in clean_line:
                    clean_line = clean_line.split(":")[0].strip()
                if clean_line:
                    skills.append(clean_line)

        # Create two-column layout
        if skills:
            # Split into two columns
            mid = (len(skills) + 1) // 2
            left_skills = skills[:mid]
            right_skills = skills[mid:]

            # Build table rows
            rows = []
            for i in range(max(len(left_skills), len(right_skills))):
                left_text = left_skills[i] if i < len(left_skills) else ""
                right_text = right_skills[i] if i < len(right_skills) else ""

                left_para = Paragraph(
                    f"• {self._escape_text(left_text)}" if left_text else "",
                    self.styles["CC_BodyText"],
                )
                right_para = Paragraph(
                    f"• {self._escape_text(right_text)}" if right_text else "",
                    self.styles["CC_BodyText"],
                )
                rows.append([left_para, right_para])

            skills_table = Table(
                rows,
                colWidths=[available_width * 0.50, available_width * 0.50],
                style=TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ]
                ),
            )
            elements.append(skills_table)

        return elements

    def _format_corporate_classic_certifications(self, lines: list) -> list:
        """Format certifications section for Corporate Classic template."""
        elements = []
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT

        entries = []
        current = {"name": "", "issuer": "", "date": "", "details": []}

        i = 0
        while i < len(lines):
            line = lines[i]

            if not line:
                if current["name"]:
                    entries.append(current)
                    current = {"name": "", "issuer": "", "date": "", "details": []}
                i += 1
                continue

            if "|" in line:
                if current["name"]:
                    entries.append(current)
                    current = {"name": "", "issuer": "", "date": "", "details": []}
                parts = line.split("|")
                current["name"] = parts[0].strip()
                if len(parts) > 1:
                    current["issuer"] = parts[1].strip()
            elif self._is_date_line(line):
                current["date"] = line
            elif line.startswith(("-", "•", "*", "○", "·")):
                current["details"].append(line.lstrip("-•*○·").strip())
            elif not current["name"]:
                current["name"] = line
            elif not current["issuer"]:
                current["issuer"] = line
            else:
                current["details"].append(line)
            i += 1

        if current["name"]:
            entries.append(current)

        for idx, entry in enumerate(entries):
            if idx > 0:
                elements.append(Spacer(1, 0.08 * inch))

            # Certification name (bold)
            elements.append(
                Paragraph(self._escape_text(entry["name"]), self.styles["CC_Title"])
            )

            # Issuer and Date
            if entry["issuer"] or entry["date"]:
                issuer_para = Paragraph(
                    self._escape_text(entry["issuer"]), self.styles["CC_Subtitle"]
                )
                date_para = Paragraph(
                    self._escape_text(entry["date"]), self.styles["CC_Date"]
                )
                row_table = Table(
                    [[issuer_para, date_para]],
                    colWidths=[available_width * 0.70, available_width * 0.30],
                    style=TableStyle(
                        [
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("ALIGN", (0, 0), (0, 0), "LEFT"),
                            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                        ]
                    ),
                )
                elements.append(row_table)

            for detail in entry["details"]:
                elements.append(
                    Paragraph(
                        f"• {self._escape_text(detail)}", self.styles["CC_Bullet"]
                    )
                )

        return elements

    def _format_corporate_classic_projects(self, lines: list) -> list:
        """Format projects section for Corporate Classic template."""
        elements = []
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT

        entries = []
        current = {
            "name": "",
            "role": "",
            "date": "",
            "bullets": [],
            "technologies": "",
        }

        i = 0
        while i < len(lines):
            line = lines[i]

            if not line:
                if current["name"]:
                    entries.append(current)
                    current = {
                        "name": "",
                        "role": "",
                        "date": "",
                        "bullets": [],
                        "technologies": "",
                    }
                i += 1
                continue

            if "|" in line and not line.lower().startswith("technologies"):
                if current["name"]:
                    entries.append(current)
                    current = {
                        "name": "",
                        "role": "",
                        "date": "",
                        "bullets": [],
                        "technologies": "",
                    }
                parts = line.split("|")
                current["name"] = parts[0].strip()
                if len(parts) > 1:
                    current["role"] = parts[1].strip()
            elif self._is_date_line(line):
                current["date"] = line
            elif line.lower().startswith("technologies:"):
                current["technologies"] = line
            elif line.startswith(("-", "•", "*", "○", "·")):
                current["bullets"].append(line.lstrip("-•*○·").strip())
            elif not current["name"]:
                current["name"] = line
            else:
                current["bullets"].append(line)
            i += 1

        if current["name"]:
            entries.append(current)

        for idx, entry in enumerate(entries):
            if idx > 0:
                elements.append(Spacer(1, 0.1 * inch))

            elements.append(
                Paragraph(self._escape_text(entry["name"]), self.styles["CC_Title"])
            )

            if entry["role"] or entry["date"]:
                role_para = Paragraph(
                    self._escape_text(entry["role"]), self.styles["CC_Subtitle"]
                )
                date_para = Paragraph(
                    self._escape_text(entry["date"]), self.styles["CC_Date"]
                )
                row_table = Table(
                    [[role_para, date_para]],
                    colWidths=[available_width * 0.70, available_width * 0.30],
                    style=TableStyle(
                        [
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("ALIGN", (0, 0), (0, 0), "LEFT"),
                            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                        ]
                    ),
                )
                elements.append(row_table)

            for bullet in entry["bullets"]:
                elements.append(
                    Paragraph(
                        f"• {self._escape_text(bullet)}", self.styles["CC_Bullet"]
                    )
                )

            if entry["technologies"]:
                elements.append(
                    Paragraph(
                        f"<i>{self._escape_text(entry['technologies'])}</i>",
                        self.styles["CC_BodyText"],
                    )
                )

        return elements

    def _format_corporate_classic_languages(self, lines: list) -> list:
        """Format languages section in two-column layout."""
        elements = []
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT

        languages = []
        for line in lines:
            if not line:
                continue
            clean = line.lstrip("-•*○·").strip()
            if clean:
                languages.append(clean)

        if languages:
            mid = (len(languages) + 1) // 2
            left_langs = languages[:mid]
            right_langs = languages[mid:]

            rows = []
            for i in range(max(len(left_langs), len(right_langs))):
                left_text = left_langs[i] if i < len(left_langs) else ""
                right_text = right_langs[i] if i < len(right_langs) else ""

                left_para = Paragraph(
                    f"• {self._escape_text(left_text)}" if left_text else "",
                    self.styles["CC_BodyText"],
                )
                right_para = Paragraph(
                    f"• {self._escape_text(right_text)}" if right_text else "",
                    self.styles["CC_BodyText"],
                )
                rows.append([left_para, right_para])

            lang_table = Table(
                rows,
                colWidths=[available_width * 0.50, available_width * 0.50],
                style=TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                        ("TOPPADDING", (0, 0), (-1, -1), 2),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                    ]
                ),
            )
            elements.append(lang_table)

        return elements

    def _format_corporate_classic_interests(self, lines: list) -> list:
        """Format interests/hobbies section as simple bullet list."""
        elements = []
        for line in lines:
            if not line:
                continue
            clean = line.lstrip("-•*○·").strip()
            if clean:
                elements.append(
                    Paragraph(f"• {self._escape_text(clean)}", self.styles["CC_Bullet"])
                )
        return elements

    def _format_corporate_classic_awards(self, lines: list) -> list:
        """Format awards section for Corporate Classic template."""
        elements = []
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT

        entries = []
        current = {"name": "", "org": "", "date": "", "details": []}

        i = 0
        while i < len(lines):
            line = lines[i]

            if not line:
                if current["name"]:
                    entries.append(current)
                    current = {"name": "", "org": "", "date": "", "details": []}
                i += 1
                continue

            if "|" in line:
                if current["name"]:
                    entries.append(current)
                    current = {"name": "", "org": "", "date": "", "details": []}
                parts = line.split("|")
                current["name"] = parts[0].strip()
                if len(parts) > 1:
                    current["org"] = parts[1].strip()
            elif self._is_date_line(line):
                current["date"] = line
            elif line.startswith(("-", "•", "*", "○", "·")):
                current["details"].append(line.lstrip("-•*○·").strip())
            elif not current["name"]:
                current["name"] = line
            else:
                current["details"].append(line)
            i += 1

        if current["name"]:
            entries.append(current)

        for idx, entry in enumerate(entries):
            if idx > 0:
                elements.append(Spacer(1, 0.08 * inch))

            elements.append(
                Paragraph(self._escape_text(entry["name"]), self.styles["CC_Title"])
            )

            if entry["org"] or entry["date"]:
                org_para = Paragraph(
                    self._escape_text(entry["org"]), self.styles["CC_Subtitle"]
                )
                date_para = Paragraph(
                    self._escape_text(entry["date"]), self.styles["CC_Date"]
                )
                row_table = Table(
                    [[org_para, date_para]],
                    colWidths=[available_width * 0.70, available_width * 0.30],
                    style=TableStyle(
                        [
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("ALIGN", (0, 0), (0, 0), "LEFT"),
                            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                        ]
                    ),
                )
                elements.append(row_table)

            for detail in entry["details"]:
                elements.append(
                    Paragraph(
                        f"• {self._escape_text(detail)}", self.styles["CC_Bullet"]
                    )
                )

        return elements

    def _format_corporate_classic_volunteer(self, lines: list) -> list:
        """Format volunteer experience section (similar to experience)."""
        return self._format_corporate_classic_experience(lines)

    def _format_corporate_classic_publications(self, lines: list) -> list:
        """Format publications section for Corporate Classic template."""
        elements = []
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT

        entries = []
        current = {"title": "", "publication": "", "date": "", "details": []}

        i = 0
        while i < len(lines):
            line = lines[i]

            if not line:
                if current["title"]:
                    entries.append(current)
                    current = {
                        "title": "",
                        "publication": "",
                        "date": "",
                        "details": [],
                    }
                i += 1
                continue

            if "|" in line:
                if current["title"]:
                    entries.append(current)
                    current = {
                        "title": "",
                        "publication": "",
                        "date": "",
                        "details": [],
                    }
                parts = line.split("|")
                current["title"] = parts[0].strip()
                if len(parts) > 1:
                    current["publication"] = parts[1].strip()
            elif self._is_date_line(line):
                current["date"] = line
            elif line.startswith(("-", "•", "*", "○", "·")):
                current["details"].append(line.lstrip("-•*○·").strip())
            elif not current["title"]:
                current["title"] = line
            else:
                current["details"].append(line)
            i += 1

        if current["title"]:
            entries.append(current)

        for idx, entry in enumerate(entries):
            if idx > 0:
                elements.append(Spacer(1, 0.08 * inch))

            elements.append(
                Paragraph(self._escape_text(entry["title"]), self.styles["CC_Title"])
            )

            if entry["publication"] or entry["date"]:
                pub_para = Paragraph(
                    self._escape_text(entry["publication"]), self.styles["CC_Subtitle"]
                )
                date_para = Paragraph(
                    self._escape_text(entry["date"]), self.styles["CC_Date"]
                )
                row_table = Table(
                    [[pub_para, date_para]],
                    colWidths=[available_width * 0.70, available_width * 0.30],
                    style=TableStyle(
                        [
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("ALIGN", (0, 0), (0, 0), "LEFT"),
                            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                        ]
                    ),
                )
                elements.append(row_table)

            for detail in entry["details"]:
                elements.append(
                    Paragraph(
                        f"• {self._escape_text(detail)}", self.styles["CC_Bullet"]
                    )
                )

        return elements

    def _format_corporate_classic_memberships(self, lines: list) -> list:
        """Format professional memberships section."""
        elements = []
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT

        for line in lines:
            if not line:
                continue

            if "|" in line:
                parts = line.split("|")
                org = parts[0].strip()
                role = parts[1].strip() if len(parts) > 1 else ""

                elements.append(
                    Paragraph(self._escape_text(org), self.styles["CC_Title"])
                )
                if role:
                    elements.append(
                        Paragraph(self._escape_text(role), self.styles["CC_Subtitle"])
                    )
            elif line.startswith(("-", "•", "*", "○", "·")):
                clean = line.lstrip("-•*○·").strip()
                elements.append(
                    Paragraph(f"• {self._escape_text(clean)}", self.styles["CC_Bullet"])
                )
            else:
                elements.append(
                    Paragraph(self._escape_text(line), self.styles["CC_BodyText"])
                )

        return elements

    def _format_corporate_classic_conferences(self, lines: list) -> list:
        """Format conferences and talks section."""
        elements = []
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT

        entries = []
        current = {"title": "", "event": "", "date": "", "location": "", "details": []}

        i = 0
        while i < len(lines):
            line = lines[i]

            if not line:
                if current["title"]:
                    entries.append(current)
                    current = {
                        "title": "",
                        "event": "",
                        "date": "",
                        "location": "",
                        "details": [],
                    }
                i += 1
                continue

            if "|" in line:
                if current["title"]:
                    entries.append(current)
                    current = {
                        "title": "",
                        "event": "",
                        "date": "",
                        "location": "",
                        "details": [],
                    }
                parts = line.split("|")
                current["title"] = parts[0].strip()
                if len(parts) > 1:
                    current["event"] = parts[1].strip()
                if len(parts) > 2:
                    current["location"] = parts[2].strip()
            elif self._is_date_line(line):
                current["date"] = line
            elif line.startswith(("-", "•", "*", "○", "·")):
                current["details"].append(line.lstrip("-•*○·").strip())
            elif not current["title"]:
                current["title"] = line
            else:
                current["details"].append(line)
            i += 1

        if current["title"]:
            entries.append(current)

        for idx, entry in enumerate(entries):
            if idx > 0:
                elements.append(Spacer(1, 0.08 * inch))

            elements.append(
                Paragraph(self._escape_text(entry["title"]), self.styles["CC_Title"])
            )

            subtitle = entry["event"]
            if entry["location"]:
                subtitle += f", {entry['location']}" if subtitle else entry["location"]

            if subtitle or entry["date"]:
                sub_para = Paragraph(
                    self._escape_text(subtitle), self.styles["CC_Subtitle"]
                )
                date_para = Paragraph(
                    self._escape_text(entry["date"]), self.styles["CC_Date"]
                )
                row_table = Table(
                    [[sub_para, date_para]],
                    colWidths=[available_width * 0.70, available_width * 0.30],
                    style=TableStyle(
                        [
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("ALIGN", (0, 0), (0, 0), "LEFT"),
                            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                        ]
                    ),
                )
                elements.append(row_table)

            for detail in entry["details"]:
                elements.append(
                    Paragraph(
                        f"• {self._escape_text(detail)}", self.styles["CC_Bullet"]
                    )
                )

        return elements

    def _format_corporate_classic_patents(self, lines: list) -> list:
        """Format patents section for Corporate Classic template."""
        elements = []
        available_width = self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT

        entries = []
        current = {"title": "", "number": "", "date": "", "details": []}

        i = 0
        while i < len(lines):
            line = lines[i]

            if not line:
                if current["title"]:
                    entries.append(current)
                    current = {"title": "", "number": "", "date": "", "details": []}
                i += 1
                continue

            if "|" in line:
                if current["title"]:
                    entries.append(current)
                    current = {"title": "", "number": "", "date": "", "details": []}
                parts = line.split("|")
                current["title"] = parts[0].strip()
                if len(parts) > 1:
                    current["number"] = parts[1].strip()
            elif self._is_date_line(line):
                current["date"] = line
            elif line.startswith(("-", "•", "*", "○", "·")):
                current["details"].append(line.lstrip("-•*○·").strip())
            elif not current["title"]:
                current["title"] = line
            else:
                current["details"].append(line)
            i += 1

        if current["title"]:
            entries.append(current)

        for idx, entry in enumerate(entries):
            if idx > 0:
                elements.append(Spacer(1, 0.08 * inch))

            elements.append(
                Paragraph(self._escape_text(entry["title"]), self.styles["CC_Title"])
            )

            if entry["number"] or entry["date"]:
                num_para = Paragraph(
                    self._escape_text(entry["number"]), self.styles["CC_Subtitle"]
                )
                date_para = Paragraph(
                    self._escape_text(entry["date"]), self.styles["CC_Date"]
                )
                row_table = Table(
                    [[num_para, date_para]],
                    colWidths=[available_width * 0.70, available_width * 0.30],
                    style=TableStyle(
                        [
                            ("VALIGN", (0, 0), (-1, -1), "TOP"),
                            ("ALIGN", (0, 0), (0, 0), "LEFT"),
                            ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                            ("LEFTPADDING", (0, 0), (-1, -1), 0),
                            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                            ("TOPPADDING", (0, 0), (-1, -1), 0),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
                        ]
                    ),
                )
                elements.append(row_table)

            for detail in entry["details"]:
                elements.append(
                    Paragraph(
                        f"• {self._escape_text(detail)}", self.styles["CC_Bullet"]
                    )
                )

        return elements

    def _format_corporate_classic_references(self, lines: list) -> list:
        """Format references section for Corporate Classic template."""
        elements = []

        entries = []
        current = {"name": "", "title": "", "company": "", "contact": []}

        i = 0
        while i < len(lines):
            line = lines[i]

            if not line:
                if current["name"]:
                    entries.append(current)
                    current = {"name": "", "title": "", "company": "", "contact": []}
                i += 1
                continue

            # Check for "Name | Title | Company" format
            if "|" in line:
                if current["name"]:
                    entries.append(current)
                    current = {"name": "", "title": "", "company": "", "contact": []}
                parts = line.split("|")
                current["name"] = parts[0].strip()
                if len(parts) > 1:
                    current["title"] = parts[1].strip()
                if len(parts) > 2:
                    current["company"] = parts[2].strip()
            elif (
                "@" in line
                or "+" in line
                or line.lower().startswith(("email", "phone", "tel"))
            ):
                current["contact"].append(line)
            elif not current["name"]:
                current["name"] = line
            elif not current["title"]:
                current["title"] = line
            elif not current["company"]:
                current["company"] = line
            else:
                current["contact"].append(line)
            i += 1

        if current["name"]:
            entries.append(current)

        for idx, entry in enumerate(entries):
            if idx > 0:
                elements.append(Spacer(1, 0.1 * inch))

            # Name (bold)
            elements.append(
                Paragraph(self._escape_text(entry["name"]), self.styles["CC_Title"])
            )

            # Title and Company
            subtitle = entry["title"]
            if entry["company"]:
                subtitle += f", {entry['company']}" if subtitle else entry["company"]
            if subtitle:
                elements.append(
                    Paragraph(self._escape_text(subtitle), self.styles["CC_Subtitle"])
                )

            # Contact info
            for contact in entry["contact"]:
                elements.append(
                    Paragraph(self._escape_text(contact), self.styles["CC_BodyText"])
                )

        return elements

    def _format_corporate_classic_generic(self, lines: list) -> list:
        """Format generic section content for Corporate Classic template."""
        elements = []
        for line in lines:
            if not line:
                continue

            if line.startswith(("-", "•", "*", "○", "·")):
                clean = line.lstrip("-•*○·").strip()
                elements.append(
                    Paragraph(f"• {self._escape_text(clean)}", self.styles["CC_Bullet"])
                )
            elif "|" in line:
                parts = line.split("|")
                title = parts[0].strip()
                subtitle = parts[1].strip() if len(parts) > 1 else ""
                elements.append(
                    Paragraph(self._escape_text(title), self.styles["CC_Title"])
                )
                if subtitle:
                    elements.append(
                        Paragraph(
                            self._escape_text(subtitle), self.styles["CC_Subtitle"]
                        )
                    )
            else:
                elements.append(
                    Paragraph(self._escape_text(line), self.styles["CC_BodyText"])
                )

        return elements

    def _add_corporate_classic_footer(
        self, canvas_obj: canvas.Canvas, doc: SimpleDocTemplate
    ):
        """
        Add footer to Corporate Classic template pages.

        Args:
            canvas_obj: ReportLab canvas object
            doc: Document object
        """
        canvas_obj.saveState()

        page_num = canvas_obj.getPageNumber()
        text = f"Page {page_num}"

        canvas_obj.setFont("Times-Roman", 9)
        canvas_obj.setFillColor(colors.black)
        canvas_obj.drawCentredString(self.PAGE_WIDTH / 2, 0.4 * inch, text)

        canvas_obj.restoreState()

    def _is_section_header(self, line: str) -> bool:
        """
        Determine if a line is a section header using SMART WHITELIST detection.

        Based on UserProfile model structure, only recognizes legitimate CV sections.
        This prevents false positives like "- GPA: 3.8/4.0" being treated as headers.

        Args:
            line: Text line to check

        Returns:
            True if line is a legitimate section header
        """
        if not line:
            return False

        line_stripped = line.strip()

        # Lines starting with bullets are NEVER headers
        if line_stripped.startswith(("-", "•", "*", "+")):
            return False

        # Headers must be reasonably short (max 5 words)
        word_count = len(line_stripped.split())
        if word_count > 5:
            return False

        # Don't treat lines ending with sentence punctuation as headers
        if line_stripped.endswith((".", ",", ";", "!", "?", "-")):
            return False

        # Normalize line for comparison (lowercase, remove colon, strip)
        line_normalized = line_stripped.lower().strip(":").strip()

        # Check against our VALID_CV_HEADERS whitelist
        # Only exact matches or very close matches are considered headers
        return line_normalized in self.VALID_CV_HEADERS

    def _create_divider_line(self) -> Table:
        """
        Create a horizontal divider line.

        Returns:
            Table object representing a divider line
        """
        divider = Table(
            [[""]], colWidths=[self.PAGE_WIDTH - self.MARGIN_LEFT - self.MARGIN_RIGHT]
        )
        divider.setStyle(
            TableStyle(
                [
                    ("LINEABOVE", (0, 0), (-1, 0), 1, self.DIVIDER_COLOR),
                    ("TOPPADDING", (0, 0), (-1, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ]
            )
        )
        return divider

    def _escape_text(self, text: str) -> str:
        """
        Escape special characters for ReportLab XML parsing and normalize dashes.

        Args:
            text: Raw text to escape

        Returns:
            Escaped text safe for Paragraph rendering
        """
        if not text:
            return ""

        # Replace long dashes (em dash, en dash) with regular hyphen
        text = text.replace("—", "-")  # Em dash
        text = text.replace("–", "-")  # En dash

        # Escape XML special characters
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")

        return text

    def _add_cv_footer(self, canvas_obj: canvas.Canvas, doc: SimpleDocTemplate):
        """
        Add footer to CV pages with page number only.

        Args:
            canvas_obj: ReportLab canvas object
            doc: Document object
        """
        canvas_obj.saveState()

        # Page number (centered at bottom)
        page_num = canvas_obj.getPageNumber()
        text = f"Page {page_num}"

        canvas_obj.setFont("Times-Roman", 9)
        canvas_obj.setFillColor(self.SECONDARY_COLOR)
        canvas_obj.drawCentredString(self.PAGE_WIDTH / 2, 0.5 * inch, text)

        canvas_obj.restoreState()

    def _add_cover_letter_footer(
        self, canvas_obj: canvas.Canvas, doc: SimpleDocTemplate
    ):
        """
        Add footer to cover letter pages with page number.

        Args:
            canvas_obj: ReportLab canvas object
            doc: Document object
        """
        canvas_obj.saveState()

        # Page number (only for multi-page letters)
        page_num = canvas_obj.getPageNumber()
        if page_num > 1:
            text = f"Page {page_num}"
            canvas_obj.setFont("Helvetica", 9)
            canvas_obj.setFillColor(self.SECONDARY_COLOR)
            canvas_obj.drawCentredString(self.PAGE_WIDTH / 2, 0.5 * inch, text)

        canvas_obj.restoreState()


# Module-level factory function
def get_document_service() -> DocumentService:
    """
    Factory function to get DocumentService instance.
    Used for dependency injection in FastAPI routes.

    Returns:
        DocumentService instance
    """
    return DocumentService()


################################################################################
# TEMPLATE 1: BIZARRE & MODERN
################################################################################

# Sample CV content - structured for Bizarre & Modern template
cv_content = """MARCUS CHEN
Full Stack Developer
marcus.chen@email.com | +44 7700 900123
Portfolio: marcuschen.dev | GitHub: github.com/marcuschen | LinkedIn: linkedin.com/in/marcuschen

PROFESSIONAL SUMMARY

Innovative Full Stack Developer with 6+ years of experience crafting high-performance web applications. Specialized in React, Node.js, and cloud architecture. Passionate about clean code, user experience, and building products that make a difference. Track record of delivering complex projects on time while mentoring junior developers.

EXPERIENCE

Full Stack Developer | Fintech Innovations Ltd
March 2021 - Present

• Architected and built a real-time trading dashboard serving 50,000+ daily active users
• Led migration from legacy PHP system to modern React/Node.js stack, improving performance by 200%
• Implemented WebSocket-based notification system reducing latency from 5s to 50ms
• Mentored 4 junior developers and established coding standards and review processes

Technologies: React, TypeScript, Node.js, PostgreSQL, Redis, AWS

Software Developer | Digital Agency Pro
June 2019 - February 2021

• Developed 15+ client websites and web applications generating over £2M in client revenue
• Built reusable component library reducing development time by 40% across projects
• Integrated third-party APIs including Stripe, Twilio, and various CRM platforms
• Optimized database queries reducing page load times by 65%

Technologies: Vue.js, Laravel, MySQL, Docker, Azure

Junior Developer | StartupXYZ
August 2017 - May 2019

• Developed features for SaaS platform with 10,000+ subscribers
• Implemented automated testing increasing code coverage from 30% to 85%
• Participated in daily standups and bi-weekly sprint planning meetings
• Created technical documentation for API endpoints and internal tools

Technologies: JavaScript, Express.js, MongoDB, AWS Lambda

SKILLS

JavaScript: Expert
TypeScript: Expert
React: Expert
Node.js: Advanced
Python: Advanced
PostgreSQL: Advanced
AWS: Advanced
Docker: Intermediate
Kubernetes: Intermediate
GraphQL: Intermediate

EDUCATION

Business Administration
Yale University - Bachelor of Science
2013

Bachelor of Science in Computer Science
Imperial College London
2017
Upper Second Class Honours (2:1)

CERTIFICATIONS

AWS Certified Developer - Associate
2023

Google Cloud Professional Developer
03/2022 - Present

MongoDB Certified Developer
2021

PROJECTS

Open Source Trading Library
Developed a popular open-source trading algorithm library with 2,500+ GitHub stars and contributions from 50+ developers worldwide.
Technologies: Python, NumPy, Pandas, FastAPI

Real-Time Collaboration Tool
Built a Figma-like collaborative whiteboard application supporting real-time multi-user editing with conflict resolution.
Technologies: React, WebSockets, Canvas API, Redis

LANGUAGES

English: Native
Mandarin: Native
Spanish: Intermediate

INTERESTS

• Contributing to open-source projects
• Writing technical blog posts (10K+ monthly readers)
• Mentoring at local coding bootcamps
• Competitive programming (LeetCode top 5%)

AWARDS AND ACHIEVEMENTS

Employee of the Year | Fintech Innovations Ltd
2023

Outstanding Academic Performance | Imperial College London
2017

Hackathon Winner | London Tech Challenge
2020

VOLUNTEER EXPERIENCE

Technical Mentor | Code Club UK
January 2020 - Present

• Teach programming fundamentals to 20+ students aged 9-13 weekly
• Developed curriculum for Python and web development workshops
• Organized coding competitions and tech talks for young learners

Community Organizer | London Python Meetup
March 2019 - Present

• Coordinate monthly meetups with 200+ attendees
• Invite speakers and manage event logistics
• Built and maintain the community website and registration system

PUBLICATIONS

Scalable Event-Driven Architectures in Finance | London Fintech Summit
2022

Co-authored research paper on implementing microservices architecture in financial trading systems. Presented to audience of 500+ industry professionals.

Modern React Patterns for Enterprise Applications | Tech Blog Series
2021

Five-part technical blog series covering advanced React patterns, performance optimization, and testing strategies. Reached 50,000+ readers across multiple platforms.

PROFESSIONAL MEMBERSHIPS

• Association for Computing Machinery (ACM)
• Python Software Foundation
• London Data Science Society
• IEEE Computer Society

CONFERENCES AND TALKS

• Speaker at ReactConf London 2022: "Building Real-Time Financial Dashboards"
• Panelist at FinTech Innovation Summit 2023: "The Future of Trading Technology"
• Workshop Leader at PyCon UK 2021: "FastAPI for Financial Services"

PATENTS

Real-Time Trading Algorithm Optimization System | GB2598742A
2022

Method and system for optimizing high-frequency trading algorithms using machine learning and real-time market data analysis.

REFERENCES

Sarah Johnson | Engineering Director, Fintech Innovations Ltd
sarah.johnson@fintechinnovations.com | +44 20 7123 4567

David Wilson | CTO, Digital Agency Pro
david.wilson@digitalagencypro.com | +44 20 7890 1234
"""


async def generate_bizarre_modern_cv(output_path: str):
    """Generate a PDF CV using the Bizarre & Modern template."""

    print("Initializing DocumentService...")
    document_service = DocumentService()

    print("Generating PDF with Bizarre & Modern template...")
    pdf_bytes = await document_service.generate_cv_pdf(
        content=cv_content, candidate_name="Marcus Chen", template_name="bizarre_modern"
    )

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write PDF to file
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    print(f"✓ PDF generated successfully: {output_path}")
    return output_path


def main():
    output_file = "outputs/bizarre_modern.pdf"

    print("=" * 80)
    print("GENERATING BIZARRE & MODERN CV SAMPLE")
    print("=" * 80)
    print()
    print("Template: bizarre_modern")
    print("Profile: Marcus Chen - Full Stack Developer")
    print()

    try:
        pdf_path = asyncio.run(generate_bizarre_modern_cv(output_file))

        print()
        print("=" * 80)
        print("PDF GENERATION COMPLETE")
        print("=" * 80)
        print()
        print(f"File: {pdf_path}")
        print(f"Size: {os.path.getsize(pdf_path):,} bytes")
        print()
        print("Template Features:")
        print("  ✓ Orange accent color (#E85D04)")
        print("  ✓ Helvetica font family")
        print("  ✓ Two-column header layout")
        print("  ✓ Uppercase section headers with underlines")
        print("  ✓ Skills in two-column grid")
        print("  ✓ Right-aligned dates")
        print()
        print("Sections Included:")
        print("  ✓ Name and job title")
        print("  ✓ Contact information with icons")
        print("  ✓ Professional summary")
        print("  ✓ Experience (3 positions)")
        print("  ✓ Skills (10 skills with levels)")
        print("  ✓ Education")
        print("  ✓ Certifications")
        print("  ✓ Projects")
        print("  ✓ Languages")
        print("  ✓ Interests")
        print("  ✓ Awards and achievements")
        print("  ✓ Volunteer experience")
        print("  ✓ Publications")
        print("  ✓ Professional memberships")
        print("  ✓ Conferences and talks")
        print("  ✓ Patents")
        print("  ✓ References")
        print()
        print(f"Open the PDF: {os.path.abspath(pdf_path)}")
        print()

    except Exception as e:
        print(f"✗ Error generating PDF: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()


################################################################################
# TEMPLATE 2: UK PROFESSIONAL
################################################################################

async def generate_uk_professional_cv(output_path: str):
    """Generate a PDF CV using the UK Professional template."""

    print("Initializing DocumentService...")
    document_service = DocumentService()

    print("Generating PDF with UK Professional template...")
    pdf_bytes = await document_service.generate_cv_pdf(
        content=cv_content,
        candidate_name="Marcus Chen",
        template_name="uk_professional_template",
    )

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write PDF to file
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    print(f"✓ PDF generated successfully: {output_path}")
    return output_path


def main():
    output_file = "outputs/uk_professional.pdf"

    print("=" * 80)
    print("GENERATING UK PROFESSIONAL CV SAMPLE")
    print("=" * 80)
    print()
    print("Template: uk_professional_template")
    print("Profile: Marcus Chen - Full Stack Developer")
    print()

    try:
        pdf_path = asyncio.run(generate_uk_professional_cv(output_file))

        print()
        print("=" * 80)
        print("PDF GENERATION COMPLETE")
        print("=" * 80)
        print()
        print(f"File: {pdf_path}")
        print(f"Size: {os.path.getsize(pdf_path):,} bytes")
        print()
        print("Template Features:")
        print("  ✓ Times New Roman font family")
        print("  ✓ Professional blue color scheme")
        print("  ✓ Single-column layout")
        print("  ✓ Clean section headers")
        print("  ✓ Traditional UK CV formatting")
        print()
        print("Sections Included:")
        print("  ✓ Name and contact information")
        print("  ✓ Professional summary")
        print("  ✓ Experience (3 positions)")
        print("  ✓ Skills")
        print("  ✓ Education")
        print("  ✓ Certifications")
        print("  ✓ Projects")
        print("  ✓ Languages")
        print("  ✓ Interests")
        print("  ✓ Awards and achievements")
        print("  ✓ Volunteer experience")
        print("  ✓ Publications")
        print("  ✓ Professional memberships")
        print("  ✓ Conferences and talks")
        print("  ✓ Patents")
        print("  ✓ References")
        print()
        print(f"Open the PDF: {os.path.abspath(pdf_path)}")
        print()

    except Exception as e:
        print(f"✗ Error generating PDF: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()


################################################################################
# TEMPLATE 3: CORPORATE CLASSIC
################################################################################

# Comprehensive CV content - ALL sections to test full template capability
cv_content = """ELIZABETH HARTWELL
Senior Financial Analyst
elizabeth.hartwell@email.com | +1 (212) 555-0147
Portfolio: elizabethhartwell.com | LinkedIn: linkedin.com/in/elizabethhartwell

PROFESSIONAL SUMMARY

Distinguished financial analyst with 12+ years of experience in investment banking, portfolio management, and corporate finance. Proven expertise in financial modeling, risk assessment, and strategic advisory for Fortune 500 clients. Adept at leading cross-functional teams and delivering actionable insights that drive multi-million dollar investment decisions. Recognized for exceptional analytical acumen and ability to translate complex financial data into compelling executive presentations.

WORK EXPERIENCE

Senior Financial Analyst | Goldman Sachs & Co. | New York, NY
January 2019 - Present

• Lead financial analysis for $500M+ M&A transactions, providing due diligence and valuation expertise
• Developed proprietary financial models reducing analysis time by 35% while improving accuracy
• Manage team of 6 junior analysts, providing mentorship and performance feedback
• Present quarterly investment recommendations to C-suite executives and board members
• Implemented ESG scoring methodology now used across 200+ portfolio companies

Technologies: Bloomberg Terminal, FactSet, Python, Excel VBA, Tableau

Financial Analyst | Morgan Stanley | New York, NY
June 2015 - December 2018

• Conducted comprehensive financial analysis for IPO offerings totaling $2.5B
• Built DCF, LBO, and comparable company analysis models for 50+ client engagements
• Collaborated with legal and compliance teams to ensure regulatory adherence
• Authored industry research reports distributed to 1,000+ institutional investors
• Achieved 98% accuracy rate in quarterly earnings forecasts

Technologies: Capital IQ, Pitchbook, SQL, R, PowerBI

Junior Analyst | J.P. Morgan Chase | New York, NY
August 2011 - May 2015

• Supported senior analysts in preparing pitch books and client presentations
• Monitored market trends and maintained databases of 500+ public companies
• Assisted in restructuring advisory for clients with $10B+ in combined assets
• Participated in due diligence processes for 25+ acquisitions
• Recognized as "Rising Star" in annual performance reviews (2013, 2014)

Technologies: Excel, PowerPoint, Bloomberg, Reuters

Financial Analyst | Morgan Stanley | New York, NY
June 2015 - December 2018

• Conducted comprehensive financial analysis for IPO offerings totaling $2.5B
• Built DCF, LBO, and comparable company analysis models for 50+ client engagements
• Collaborated with legal and compliance teams to ensure regulatory adherence
• Authored industry research reports distributed to 1,000+ institutional investors
• Achieved 98% accuracy rate in quarterly earnings forecasts

EDUCATION

Master of Business Administration | Harvard Business School | Cambridge, MA
2009 - 2011
Dean's List, Concentration in Finance

Bachelor of Science in Economics | University of Pennsylvania | Philadelphia, PA
2005 - 2009
Magna Cum Laude, Minor in Mathematics

SKILLS

Financial Modeling: Expert
Valuation Analysis: Expert
M&A Advisory: Expert
Risk Management: Advanced
Python Programming: Advanced
SQL/Database: Advanced
Bloomberg Terminal: Expert
Excel/VBA: Expert
Tableau/PowerBI: Advanced
Statistical Analysis: Advanced
Portfolio Management: Expert
Regulatory Compliance: Advanced


CERTIFICATIONS

Chartered Financial Analyst (CFA) | CFA Institute
2015

Financial Risk Manager (FRM) | GARP
2017

Series 7 and 66 Licenses | FINRA
2012

Certified Public Accountant (CPA) | New York State
2014

Bloomberg Market Concepts | Bloomberg
2020




PROJECTS

Algorithmic Trading Strategy Development | Personal Project
2022 - Present

Developed machine learning-based trading algorithms for equity markets with 15% annual returns.
- Implemented sentiment analysis using NLP on financial news feeds
- Built backtesting framework processing 10 years of historical data
- Deployed automated trading system with real-time risk monitoring

Technologies: Python, TensorFlow, AWS, PostgreSQL

Corporate Valuation Dashboard | Goldman Sachs
2021

Led development of interactive dashboard for real-time company valuation analysis.
- Reduced client presentation preparation time by 60%
- Integrated with 5 major financial data providers
- Adopted by 150+ analysts across the organization

Technologies: Python, Dash, SQL, REST APIs

LANGUAGES

English: Native
French: Fluent
Mandarin Chinese: Intermediate
Spanish: Basic

INTERESTS AND HOBBIES

• Classical piano performance and music theory
• Marathon running (completed NYC Marathon 2022, 2023)
• Angel investing in fintech startups
• Board member of local financial literacy nonprofit
• Avid reader of economic history and philosophy

AWARDS AND ACHIEVEMENTS

Top 30 Under 30 in Finance | Forbes
2018

Excellence in Client Service Award | Goldman Sachs
2022

Best Research Paper | CFA Society New York
2020

Phi Beta Kappa Honor Society | University of Pennsylvania
2009

Outstanding MBA Graduate | Harvard Business School
2011

VOLUNTEER EXPERIENCE

Financial Literacy Instructor | Junior Achievement USA | New York, NY
September 2016 - Present

• Teach personal finance and economics to 200+ high school students annually
• Developed curriculum on investing, budgeting, and career planning
• Organized stock market simulation competition for 500+ participants

Board Treasurer | Manhattan Arts Council | New York, NY
January 2020 - Present

• Oversee $3M annual budget and investment portfolio
• Implemented financial controls reducing administrative costs by 20%
• Lead annual audit preparation and grant compliance reporting

PUBLICATIONS

Market Volatility and Institutional Investment Strategies | Journal of Finance
2023

Published peer-reviewed research on institutional investor behavior during market downturns. Cited by 50+ subsequent academic papers.

The Future of ESG Integration in Investment Analysis | Harvard Business Review
2022

Featured article on incorporating environmental, social, and governance factors into traditional financial analysis frameworks.

Quantitative Approaches to Credit Risk Assessment | Risk Management Quarterly
2021

Technical paper presenting novel machine learning methods for predicting corporate default probability.

PROFESSIONAL MEMBERSHIPS

CFA Society New York | Member
2015 - Present

Global Association of Risk Professionals | Member
2017 - Present

Financial Women's Association | Board Member
2020 - Present

American Finance Association | Member
2011 - Present

New York Society of Security Analysts | Member
2012 - Present

CONFERENCES AND TALKS

Keynote Speaker | Fintech Innovation Summit | New York, NY
2023

Presented on "The Intersection of AI and Traditional Financial Analysis" to audience of 1,000+ industry professionals.

Panelist | Women in Finance Leadership Forum | Boston, MA
2022

Discussed strategies for advancing women's leadership in investment banking and asset management.

Workshop Leader | CFA Society Annual Conference | Chicago, IL
2021

Conducted advanced financial modeling workshop attended by 200+ CFA charterholders.

Guest Lecturer | NYU Stern School of Business | New York, NY
2019 - Present

Annual guest lectures on M&A valuation and investment banking careers.

PATENTS

Automated Financial Document Analysis System | US Patent 11,234,567
2022

Novel system for automated extraction and analysis of financial data from unstructured documents using natural language processing and machine learning.

Real-Time Portfolio Risk Assessment Algorithm | US Patent 11,345,678
2023

Proprietary algorithm for continuous portfolio risk monitoring with predictive analytics for market stress scenarios.

REFERENCES

Jonathan Sterling | Managing Director, Goldman Sachs & Co.
jonathan.sterling@gs.com | +1 (212) 555-0198

Dr. Margaret Chen | Professor of Finance, Harvard Business School
mchen@hbs.edu | +1 (617) 555-0234

Robert Fitzgerald | Former CEO, Morgan Stanley Asset Management
rfitzgerald@email.com | +1 (212) 555-0156
"""


async def generate_corporate_classic_cv(output_path: str):
    """Generate a PDF CV using the Corporate Classic template."""

    print("Initializing DocumentService...")
    document_service = DocumentService()

    print("Generating PDF with Corporate Classic template...")
    pdf_bytes = await document_service.generate_cv_pdf(
        content=cv_content,
        candidate_name="Elizabeth Hartwell",
        template_name="corporate_classic",
    )

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write PDF to file
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)

    print(f"✓ PDF generated successfully: {output_path}")
    return output_path


def main():
    output_file = "outputs/corporate_classic.pdf"

    print("=" * 80)
    print("GENERATING CORPORATE CLASSIC CV SAMPLE")
    print("=" * 80)
    print()
    print("Template: corporate_classic")
    print("Profile: Elizabeth Hartwell - Senior Financial Analyst")
    print()

    try:
        pdf_path = asyncio.run(generate_corporate_classic_cv(output_file))

        print()
        print("=" * 80)
        print("PDF GENERATION COMPLETE")
        print("=" * 80)
        print()
        print(f"File: {pdf_path}")
        print(f"Size: {os.path.getsize(pdf_path):,} bytes")
        print()
        print("Template Features:")
        print("  ✓ Serif fonts (Times family)")
        print("  ✓ Monochromatic design (black only)")
        print("  ✓ Stacked name in header")
        print("  ✓ Contact info right-aligned")
        print("  ✓ Section headers with underlines")
        print("  ✓ Italic professional summary")
        print("  ✓ Two-column skills grid")
        print("  ✓ Traditional corporate formatting")
        print()
        print("ALL Sections Included:")
        print("  ✓ Stacked name (first/last)")
        print("  ✓ Job title")
        print("  ✓ Contact information")
        print("  ✓ Professional summary (italic)")
        print("  ✓ Work Experience (3 positions)")
        print("  ✓ Education (2 degrees)")
        print("  ✓ Skills (12 skills in two-column grid)")
        print("  ✓ Certifications (5 certifications)")
        print("  ✓ Projects (2 projects)")
        print("  ✓ Languages (4 languages)")
        print("  ✓ Interests and Hobbies")
        print("  ✓ Awards and Achievements (5 awards)")
        print("  ✓ Volunteer Experience (2 positions)")
        print("  ✓ Publications (3 publications)")
        print("  ✓ Professional Memberships (5 memberships)")
        print("  ✓ Conferences and Talks (4 speaking engagements)")
        print("  ✓ Patents (2 patents)")
        print("  ✓ References (3 references)")
        print()
        print(f"Open the PDF: {os.path.abspath(pdf_path)}")
        print()

    except Exception as e:
        print(f"✗ Error generating PDF: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()


################################################################################
# TEMPLATE 4: MILLENNIAL STYLE
################################################################################

# Comprehensive sample CV content - ALL SECTIONS with 3-5 items each
SAMPLE_CV_CONTENT = """
Ryan Peterson
Business Analyst
+1-202-555-0161 | template@wozber.com
www.wozber.com
New York, NY

PROFESSIONAL SUMMARY

Results-driven Business Analyst with 8+ years of experience in data analytics, business intelligence, and strategic planning. Proven track record of delivering actionable insights that drive revenue growth and operational efficiency. Expert in translating complex data into clear recommendations for executive stakeholders. Passionate about leveraging technology to solve business challenges and optimize processes.

EXPERIENCE

Marketing Business Analyst | Prospect Solutions
01/2015 - Present

• Successfully connected internal sales, marketing as well as design teams and departments with external partners via Trello and Slack integrations, leading to 20% more efficient workflow and effective data tracking and sharing of projects
• Developed successful business models resulting in a revenue increase of 4.4% from 2015 to 2016
• Analyzed and architected business intelligence models to measure ROI. Monitored and reviewed options, risks, and costs of company's $5 million budget
• Worked with multiple data sets to apply qualitative and quantitative customer research techniques and business profitability analysis that lead to exceeding monthly goals by 7% on a continuous basis
• Implemented automated reporting dashboards reducing manual work by 35% across departments

Project Manager | Prospect Solutions
01/2013 - 12/2015

• Solved internal financial business challenges by reducing project's costs by 25% while employing young, but talented, external freelancers without negatively affecting the overall quality of the project
• Managed, lead and coordinated various teams of up to 70 people to perform marketing programs. This included collaboration both with internal and external teams
• Monitored 42 end-to-end marketing and PR projects from conception to successful delivery
• Created comprehensive project documentation and risk assessment frameworks adopted company-wide
• Facilitated cross-functional workshops resulting in 15% improvement in project delivery timelines

Senior Data Analyst | TechVision Corp
06/2010 - 12/2012

• Built predictive analytics models that increased customer retention by 18%
• Developed ETL pipelines processing 2M+ records daily with 99.9% accuracy
• Collaborated with product teams to define KPIs and success metrics for new feature launches
• Presented quarterly business reviews to C-suite executives with data-driven recommendations

Junior Business Analyst | DataFirst Inc
03/2008 - 05/2010

• Supported senior analysts in gathering and documenting business requirements
• Created user acceptance testing plans and coordinated testing cycles
• Maintained business process documentation and workflow diagrams
• Assisted in vendor evaluation and selection for new CRM implementation

EDUCATION

Economics and Political Science
New York University
2012
Bachelor of Science

Master of Business Administration
Columbia Business School
2015
Concentration: Strategic Management

Data Science Certificate
MIT Professional Education
2018
Machine Learning and Statistics

SKILLS

Analytical Skills: Advanced
Data Architecture: Intermediate
Business Intelligence: Advanced
Marketing: Advanced
Organizational Skills: Advanced
Communication: Advanced
Time Management: Expert
Digital Proficiency: Advanced
Perseverance: Advanced
Initiative: Advanced
Flexibility: Advanced
SQL and Python: Advanced
Tableau: Advanced
Power BI: Intermediate
Excel (Advanced): Expert

LANGUAGES

English: Native
Russian: Intermediate
French: Intermediate
Spanish: Basic
German: Basic

CERTIFICATIONS

Google AdWords Search Advanced
2011 - Present

Certified Business Analysis Professional (CBAP)
2016

Tableau Desktop Specialist
2019

AWS Cloud Practitioner
2020

Scrum Master Certification
2021

PROJECTS

Customer Churn Prediction Model
Built machine learning model reducing customer churn by 15% through early intervention strategies.
Technologies: Python, Scikit-learn, Tableau

Marketing Attribution Dashboard
Developed multi-touch attribution system providing visibility into $10M marketing spend ROI.
Technologies: SQL, Power BI, Google Analytics

Process Automation Initiative
Led RPA implementation automating 50+ manual processes, saving 2,000+ work hours annually.
Technologies: UiPath, Python, Azure

Sales Forecasting System
Created predictive sales forecasting improving accuracy from 65% to 89% quarter-over-quarter.
Technologies: Python, TensorFlow, Tableau

PUBLICATIONS

Data-Driven Decision Making in Modern Enterprises | Harvard Business Review
2022

The Future of Business Intelligence | Forbes Technology Council
2021

Optimizing Marketing ROI Through Advanced Analytics | Marketing Week
2020

Building Effective Cross-Functional Data Teams | MIT Sloan Management Review
2019

AWARDS AND ACHIEVEMENTS

Business Analyst of the Year | Prospect Solutions
2019

Innovation Excellence Award | TechVision Corp
2012

Top 40 Under 40 in Analytics | Analytics Magazine
2020

Outstanding Leadership Award | Prospect Solutions
2018

Dean's List | Columbia Business School
2015

PROFESSIONAL MEMBERSHIPS

• International Institute of Business Analysis (IIBA)
• Project Management Institute (PMI)
• American Marketing Association (AMA)
• Data Science Association
• Business Intelligence Professional Association

VOLUNTEER EXPERIENCE

Data Analytics Mentor | Data Science for Social Good
January 2019 - Present

• Mentor aspiring data analysts from underrepresented backgrounds
• Conduct monthly workshops on business analytics fundamentals
• Help mentees prepare for CBAP certification exams
• Support nonprofit organizations with pro-bono analytics projects

Career Coach | NYU Alumni Association
September 2016 - Present

• Advise recent graduates on career planning and job search strategies
• Review resumes and conduct mock interviews for 50+ students annually
• Host quarterly networking events connecting students with industry professionals

CONFERENCES AND TALKS

• Speaker at Strata Data Conference 2022: "Building Scalable Analytics Teams"
• Panelist at Gartner Data & Analytics Summit 2021: "The Future of BI"
• Workshop Leader at PyCon US 2020: "Python for Business Analysts"
• Keynote at Analytics Week NYC 2019: "Data-Driven Decision Making"

PATENTS

Automated Business Process Optimization System | US11,234,567
2022
AI-powered system for identifying and recommending process improvements in enterprise workflows.

Predictive Customer Behavior Analysis Engine | US10,987,654
2020
Machine learning framework for real-time customer behavior prediction and personalization.

REFERENCES

Sarah Johnson | VP of Analytics, Prospect Solutions
sarah.johnson@prospectsolutions.com | +1-202-555-0199

Michael Chen | Director of Business Intelligence, TechVision Corp
m.chen@techvision.com | +1-415-555-0188

Dr. Emily Rodriguez | Professor of Data Science, Columbia Business School
e.rodriguez@columbia.edu | +1-212-555-0177

INTERESTS

• Data visualization and storytelling
• Machine learning and AI applications
• Business strategy and innovation
• Mentoring and coaching young professionals
• Hiking and outdoor photography
"""


async def main():
    """Generate a sample millennial style template CV."""
    print("=" * 70)
    print("GENERATING MILLENNIAL STYLE CV TEMPLATE")
    print("=" * 70)

    service = DocumentService()

    print("\nTemplate: millennial_style")
    print("Layout: Two-column (dark sidebar left, white content right)")
    print("Sidebar: Name, Title, Experience, Education")
    print("Right Column: Contact, Skills, Languages, Certifications, etc.")
    print()

    try:
        # Generate the CV using millennial_style template
        pdf_bytes = await service.generate_cv_pdf(
            content=SAMPLE_CV_CONTENT,
            candidate_name="Ryan Peterson",
            template_name="millennial_style",
        )

        # Save to outputs directory
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "outputs"
        )
        os.makedirs(output_dir, exist_ok=True)

        output_path = os.path.join(output_dir, "millennial_style_sample_cv.pdf")
        with open(output_path, "wb") as f:
            f.write(pdf_bytes)

        print(f"✓ PDF generated successfully!")
        print(f"✓ Size: {len(pdf_bytes):,} bytes")
        print(f"✓ Saved to: {output_path}")
        print()
        print("Template Features:")
        print("  ✓ Dark navy sidebar (#1B3A4B) on left (55%)")
        print("  ✓ White content area on right (45%)")
        print("  ✓ Teal accent color (#4A9B9B) for titles and levels")
        print("  ✓ Letter-spaced section headers (E X P E R I E N C E)")
        print("  ✓ Colored underlines below section headers")
        print("  ✓ Skills/Languages in two-column format")
        print()
        print("Sections in Sidebar (Left):")
        print("  ✓ Name and job title")
        print("  ✓ Professional Summary")
        print("  ✓ Experience (4 positions)")
        print("  ✓ Education (3 entries)")
        print()
        print("Sections in Right Column:")
        print("  ✓ Contact information")
        print("  ✓ Skills (15 skills with levels)")
        print("  ✓ Languages (5 languages)")
        print("  ✓ Certifications (5 certifications)")
        print("  ✓ Projects (4 projects)")
        print("  ✓ Publications (4 publications)")
        print("  ✓ Awards and Achievements (5 awards)")
        print("  ✓ Professional Memberships (5 memberships)")
        print("  ✓ Volunteer Experience (2 roles)")
        print("  ✓ Conferences and Talks (4 talks)")
        print("  ✓ Patents (2 patents)")
        print("  ✓ References (3 references)")
        print("  ✓ Interests (5 interests)")
        print()
        print(f"Open the PDF: {os.path.abspath(output_path)}")

    except Exception as e:
        print(f"✗ Error generating PDF: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

