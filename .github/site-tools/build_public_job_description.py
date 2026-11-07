"""Build the applicant-facing Housing Navigator job description PDF.

Employment terms are derived from the current Google Doc revision dated
2026-10-14. Program duties are aligned with Montana DPHHS HEART Waiver TSS
Policies 605 and 602. Internal acknowledgment and personnel-file mechanics
are intentionally excluded.
"""

from pathlib import Path
from xml.sax.saxutils import escape

import reportlab
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "anchor-support-housing-navigator-tenancy-support-specialist-job-description.pdf"
LOGO = ROOT / "anchor-logo.png"

NAVY = colors.HexColor("#06375d")
DEEP = colors.HexColor("#092c49")
TEAL = colors.HexColor("#168f92")
INK = colors.HexColor("#263847")
MUTED = colors.HexColor("#536777")
PALE = colors.HexColor("#eff7f6")
RULE = colors.HexColor("#d9e4e8")
CORAL = colors.HexColor("#e96956")

FONT_DIR = Path(reportlab.__file__).resolve().parent / "fonts"
pdfmetrics.registerFont(TTFont("Vera", str(FONT_DIR / "Vera.ttf")))
pdfmetrics.registerFont(TTFont("Vera-Bold", str(FONT_DIR / "VeraBd.ttf")))

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(
    name="Brand", fontName="Vera-Bold", fontSize=9.5, leading=12,
    textColor=NAVY, spaceAfter=2,
))
styles.add(ParagraphStyle(
    name="BrandSub", fontName="Vera", fontSize=7.5, leading=9,
    textColor=MUTED,
))
styles.add(ParagraphStyle(
    name="Kicker", fontName="Vera-Bold", fontSize=8, leading=10,
    textColor=TEAL, spaceAfter=5,
))
styles.add(ParagraphStyle(
    name="DocTitle", fontName="Vera-Bold", fontSize=23, leading=26,
    textColor=NAVY, spaceAfter=4,
))
styles.add(ParagraphStyle(
    name="Location", fontName="Vera-Bold", fontSize=10.5, leading=14,
    textColor=TEAL, spaceAfter=7,
))
styles.add(ParagraphStyle(
    name="Intro", fontName="Vera", fontSize=9.2, leading=13.2,
    textColor=INK, spaceAfter=7,
))
styles.add(ParagraphStyle(
    name="Section", fontName="Vera-Bold", fontSize=12.4, leading=15,
    textColor=NAVY, spaceBefore=9, spaceAfter=4, keepWithNext=True,
))
styles.add(ParagraphStyle(
    name="Subhead", fontName="Vera-Bold", fontSize=9.3, leading=12,
    textColor=DEEP, spaceBefore=4, spaceAfter=2, keepWithNext=True,
))
styles.add(ParagraphStyle(
    name="BodySmall", fontName="Vera", fontSize=8.7, leading=12,
    textColor=INK, spaceAfter=4.5,
))
styles.add(ParagraphStyle(
    name="BulletSmall", fontName="Vera", fontSize=8.45, leading=11.5,
    textColor=INK, leftIndent=13, firstLineIndent=-8, bulletIndent=0,
    spaceAfter=2.6,
))
styles.add(ParagraphStyle(
    name="Label", fontName="Vera-Bold", fontSize=7.2, leading=9,
    textColor=MUTED, spaceAfter=2,
))
styles.add(ParagraphStyle(
    name="Value", fontName="Vera-Bold", fontSize=8.4, leading=11.2,
    textColor=INK,
))
styles.add(ParagraphStyle(
    name="Callout", fontName="Vera-Bold", fontSize=9, leading=12.5,
    textColor=NAVY,
))
styles.add(ParagraphStyle(
    name="Footer", fontName="Vera", fontSize=7.2, leading=8.5,
    textColor=MUTED,
))


class PublicJobDoc(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(
            filename,
            pagesize=letter,
            leftMargin=.68 * inch,
            rightMargin=.68 * inch,
            topMargin=.89 * inch,
            bottomMargin=.65 * inch,
            title="Anchor Support Service LLC | Housing Navigator / Tenancy Support Specialist | Public Job Description",
            author="Anchor Support Service LLC",
            subject="Applicant-facing job description based on the current employment source revised October 14, 2026",
        )
        frame = Frame(
            self.leftMargin, self.bottomMargin, self.width, self.height,
            id="content", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0,
        )
        self.addPageTemplates([PageTemplate(id="all", frames=frame, onPage=self.draw_chrome)])

    def draw_chrome(self, canvas, doc):
        canvas.saveState()
        # Use the actual website logo asset with its original aspect ratio.
        logo_size = .53 * inch
        canvas.drawImage(
            str(LOGO), self.leftMargin, letter[1] - .72 * inch,
            width=logo_size, height=logo_size, preserveAspectRatio=True,
            anchor="c", mask="auto",
        )
        canvas.setFont("Vera-Bold", 9.6)
        canvas.setFillColor(NAVY)
        canvas.drawString(self.leftMargin + .66 * inch, letter[1] - .40 * inch, "ANCHOR SUPPORT SERVICE LLC")
        canvas.setFont("Vera", 7.8)
        canvas.setFillColor(MUTED)
        canvas.drawString(self.leftMargin + .66 * inch, letter[1] - .57 * inch, "TENANCY SUPPORT SERVICES  |  MISSOULA, MONTANA")
        canvas.setStrokeColor(TEAL)
        canvas.setLineWidth(1.4)
        canvas.line(self.leftMargin, letter[1] - .82 * inch, letter[0] - self.rightMargin, letter[1] - .82 * inch)

        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(.6)
        canvas.line(self.leftMargin, .49 * inch, letter[0] - self.rightMargin, .49 * inch)
        canvas.setFont("Vera", 7.1)
        canvas.setFillColor(MUTED)
        canvas.drawString(self.leftMargin, .32 * inch, "Anchor Support Service LLC  |  anchorsupportservice.com  |  alex@anchorsupportservice.com")
        canvas.drawRightString(letter[0] - self.rightMargin, .32 * inch, f"Page {doc.page}")
        canvas.restoreState()


def P(text, style="BodySmall"):
    return Paragraph(text, styles[style])


def bullets(items):
    return [Paragraph("• " + escape(item), styles["BulletSmall"]) for item in items]


def section(title, content):
    return [P(escape(title), "Section")] + content


story = [
    Spacer(1, 1),
    P("NOW HIRING  ·  PUBLIC APPLICANT JOB DESCRIPTION", "Kicker"),
    P("Housing Navigator /<br/>Tenancy Support Specialist", "DocTitle"),
    P("Missoula, Montana", "Location"),
    P("Public applicant edition · employment source revised October 14, 2026", "Footer"),
    P(
        "Anchor Support Service LLC is hiring a Housing Navigator / Tenancy Support Specialist to work directly with eligible clients/members experiencing housing instability and related barriers. The role supports people as they identify housing goals, find and apply for housing, address tenancy barriers, and work toward stable housing. This is a practical, community-facing support position with administrative and documentation work as part of the job.",
        "Intro",
    ),
]

facts = [
    [P("EMPLOYMENT", "Label"), P("HOURS", "Label"), P("STARTING RANGE", "Label"), P("PROBATION", "Label")],
    [
        P("W-2 employee<br/>Hourly / non-exempt", "Value"),
        P("Part-time / variable<br/>No guaranteed minimum paid or billable hours", "Value"),
        P("$17.00–$18.00<br/>per hour", "Value"),
        P("Twelve (12) months<br/>from date of hire", "Value"),
    ],
]
facts_table = Table(facts, colWidths=[1.45*inch, 2.06*inch, 1.43*inch, 1.41*inch], hAlign="LEFT")
facts_table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), PALE),
    ("BOX", (0, 0), (-1, -1), .7, RULE),
    ("INNERGRID", (0, 0), (-1, -1), .5, RULE),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ("TOPPADDING", (0, 0), (-1, -1), 7),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
]))
story += [facts_table, Spacer(1, 4)]

story += section("What the work can look like", [
    P(
        "A day may include meeting with a client to complete a housing assessment, researching available rentals, helping complete an application, contacting a property manager with the client’s authorization, gathering housing documents, following up on a waitlist, working through a housing barrier, documenting the service, and planning the next step. Some work is administrative or completed remotely in an approved setting; other work takes place in the community. Activities and hours vary with client needs and assigned work."
    ),
])

story += section("Key responsibilities", bullets([
    "Support assigned tenant screening and housing assessments; identify housing goals, strengths, preferences, needs, and barriers to successful tenancy; assist with individualized housing plans.",
    "Research housing resources; help clients complete applications and gather identification or other housing-related documents; follow vouchers and waitlists; and assist with move-in planning.",
    "Support reasonable-accommodation requests when appropriate, share fair-housing resources, and help clients understand tenant and landlord rights, tenancy expectations, and lease responsibilities. Connect clients with legal or fair-housing resources when needed; this role does not provide legal advice.",
    "With the client’s authorization, communicate with landlords and property managers. Provide practical advocacy and mediation support, help address issues that could lead to eviction, and support housing retention and recertification.",
    "Coordinate with authorized providers, case managers, shelters, benefit programs, and community partners; track follow-ups and deadlines; monitor progress toward housing goals.",
    "Complete accurate and timely service documentation, follow confidentiality and professional-boundary requirements, and follow applicable Medicaid/TSS and company procedures.",
]))

story += section("Minimum qualifications", [
    P("Applicants must meet one of these two pathways:")
] + bullets([
    "Associate degree in human services, social services, public health, or a related field from an accredited college or university; or",
    "High school diploma, GED, or HiSET plus at least one year of relevant work experience as determined by Anchor Support Service LLC.",
]) + [
    P("Relevant experience may include housing navigation, case-management support, social services, peer support, community outreach, property management, behavioral-health support, substance-use support services, homeless services, reentry services, benefits navigation, tenancy support, or other related experience.")
])

story += [PageBreak()]

story += section("Preferred qualifications", bullets([
    "Experience supporting people experiencing homelessness or housing instability, including behavioral-health, recovery, disability, reentry, or other housing barriers.",
    "Experience with housing applications, vouchers, waitlists, leases, landlords/property managers, tenant education, fair-housing concepts, or housing retention.",
    "Clear, objective, accurate writing; respectful communication; organization and follow-through; and the ability to work independently while seeking guidance when needed.",
    "Comfort using computers and approved client-management technology and protecting confidential information.",
    "Reliable transportation or the ability to attend community-based appointments when assigned and appropriate.",
]))

story += section("Schedule, compensation, and probation", [
    P("This is a W-2 employee position classified as hourly / non-exempt and part-time / variable hours. Available hours depend on assigned clients, caseload, appointments, authorized service needs, available assignments, staffing, and company operations. Cancellations, no-shows, rescheduling, or changes in allowable service needs may change available hours. There is no guaranteed minimum paid hours or billable hours, and there is no fixed schedule."),
    P("<b>Probationary starting range: $17.00–$18.00 per hour,</b> based on documented relevant experience, education/training, qualifications, and other lawful job-related factors. The introductory/probationary period is twelve (12) months from date of hire."),
    P("Successful completion of probation includes a compensation review. The post-probation target range is generally <b>$18.00–$20.00 per hour</b>, depending on performance, demonstrated competency, responsibilities, current business conditions, and company approval. A pay increase is not automatic or guaranteed."),
])

story += section("Documentation and responsible practice", bullets([
    "Complete accurate and timely service notes for client contacts. Notes should describe the service, actual time, client participation when applicable, progress toward housing goals, and follow-up or next steps.",
    "Record all work time accurately, including assigned documentation and other work. Paid work time and Medicaid-billable time are different; Medicaid billing is limited to allowable services actually provided and documented.",
    "Confirm or document Medicaid eligibility and authorization status only as assigned. The employee does not independently determine Medicaid eligibility or make final authorization decisions.",
    "Protect confidential information, use approved systems and communication methods, maintain professional boundaries, and follow company safety and TSS requirements. Staff are not expected to place themselves in unsafe situations.",
]))

story += [PageBreak()]

story += section("Work setting and role boundaries", [
    P("Services may take place by phone, email, video, in a community or public location, an appropriate client residence, an agency or partner location, a landlord/property office, or another approved remote setting. The position may require travel to community appointments when assigned and appropriate. It is not fully remote or office-only."),
    P("This role provides housing-related navigation, education, document-gathering, coordination, and follow-up. It is not a clinical therapist, property-management, or transportation-only role. Unless separately licensed, credentialed, and authorized, the employee does not provide legal or medical advice, therapy, substance-use treatment, financial advising, or property-management services, and does not make final Medicaid eligibility, authorization, or billing decisions."),
])

story += section("Who may be a good fit", [
    P("This position may be a good fit for someone who is organized, dependable, and comfortable working directly with people facing significant housing barriers; can communicate professionally with clients, landlords, and community partners; follows through on next steps; and understands that accurate documentation is a regular part of client work."),
])

story += section("Equal employment", [
    P("Anchor Support Service LLC is committed to fair and lawful employment practices. Employment and work-assignment decisions are made without unlawful discrimination, harassment, or retaliation."),
    P("This description summarizes the general nature of the position. It does not promise a fixed schedule, guaranteed hours or billable work, a specific pay increase, or continued employment. Duties, schedules, expectations, and assignments may change with business and client/member needs, Medicaid requirements, staffing, safety, and company operations. Employment is governed by applicable Montana and federal law and the company’s current written policies."),
])

apply_block = [
    P("How to apply", "Section"),
    P("Interested in joining Anchor Support Service? Email your résumé and a brief introduction to:", "BodySmall"),
    P("<link href='mailto:alex@anchorsupportservice.com' color='#06375d'><b>alex@anchorsupportservice.com</b></link>", "Callout"),
    P("To request the complete job description, please email the same address.", "BodySmall"),
    P("Suggested subject: <b>Housing Navigator - Resume</b>", "BodySmall"),
    P("Please do not email Social Security numbers, dates of birth, medical information, or other unnecessary sensitive personal information.", "BodySmall"),
]
story.append(KeepTogether(apply_block))

OUT.parent.mkdir(parents=True, exist_ok=True)
doc = PublicJobDoc(str(OUT))
doc.build(story)
print(f"Created {OUT} ({OUT.stat().st_size} bytes)")
