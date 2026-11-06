from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import BaseDocTemplate, Frame, PageTemplate, Paragraph, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "assets" / "anchor-support-housing-navigator-tenancy-support-specialist-job-description.pdf"
NAVY = colors.HexColor("#00335f")
DEEP = colors.HexColor("#082b49")
TEAL = colors.HexColor("#168c90")
INK = colors.HexColor("#243746")
MUTED = colors.HexColor("#536675")
PALE = colors.HexColor("#edf7f6")
RULE = colors.HexColor("#dbe5eb")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="Brand", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=10, leading=13, textColor=NAVY, spaceAfter=3))
styles.add(ParagraphStyle(name="DocTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=25, leading=29, alignment=TA_LEFT, textColor=NAVY, spaceAfter=7))
styles.add(ParagraphStyle(name="Subtitle", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=11, leading=15, textColor=TEAL, spaceAfter=10))
styles.add(ParagraphStyle(name="Intro", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.4, leading=14, textColor=INK, spaceAfter=8))
styles.add(ParagraphStyle(name="Section", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=16, textColor=NAVY, spaceBefore=11, spaceAfter=5, keepWithNext=True))
styles.add(ParagraphStyle(name="BodySmall", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.8, leading=12.4, textColor=INK, spaceAfter=5))
styles.add(ParagraphStyle(name="BulletSmall", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.6, leading=11.8, textColor=INK, leftIndent=12, firstLineIndent=-8, bulletIndent=0, spaceAfter=3))
styles.add(ParagraphStyle(name="Label", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=7.6, leading=10, textColor=MUTED))
styles.add(ParagraphStyle(name="Value", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=8.3, leading=11.5, textColor=INK))
styles.add(ParagraphStyle(name="Callout", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=9, leading=13, textColor=NAVY))
styles.add(ParagraphStyle(name="Footer", parent=styles["Normal"], fontName="Helvetica", fontSize=7.5, leading=9, textColor=MUTED))

class PublicJobDoc(BaseDocTemplate):
    def __init__(self, filename):
        super().__init__(filename, pagesize=letter, rightMargin=.66*inch, leftMargin=.66*inch, topMargin=.72*inch, bottomMargin=.62*inch, title="Housing Navigator / Tenancy Support Specialist - Public Job Description", author="Anchor Support Service LLC", subject="Applicant-facing job description revised October 14, 2026")
        first = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="first", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        later = Frame(self.leftMargin, self.bottomMargin, self.width, self.height, id="later", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
        self.addPageTemplates([
            PageTemplate(id="first", frames=first, onPage=self.draw_chrome, autoNextPageTemplate="later"),
            PageTemplate(id="later", frames=later, onPage=self.draw_chrome, autoNextPageTemplate="later"),
        ])

    def draw_chrome(self, canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(TEAL)
        canvas.setLineWidth(2)
        canvas.line(self.leftMargin, letter[1] - .49*inch, letter[0] - self.rightMargin, letter[1] - .49*inch)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(NAVY)
        canvas.drawString(self.leftMargin, letter[1] - .38*inch, "ANCHOR SUPPORT SERVICE LLC")
        canvas.setStrokeColor(RULE)
        canvas.setLineWidth(.6)
        canvas.line(self.leftMargin, .46*inch, letter[0] - self.rightMargin, .46*inch)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(self.leftMargin, .31*inch, "Housing Navigator / Tenancy Support Specialist | Public Job Description")
        canvas.drawRightString(letter[0] - self.rightMargin, .31*inch, f"Page {doc.page}")
        canvas.restoreState()

def P(text, style="BodySmall"):
    return Paragraph(text, styles[style])

def bullets(items):
    return [Paragraph("- " + escape(item), styles["BulletSmall"]) for item in items]

def section(title, content):
    return [P(escape(title), "Section")] + content

story = [Spacer(1, 5), P("HOUSING NAVIGATOR / TENANCY SUPPORT SPECIALIST", "DocTitle"), P("Public Job Description | Revised October 14, 2026", "Subtitle"), P("Anchor Support Service LLC is hiring a part-time, variable-hour Housing Navigator / Tenancy Support Specialist in Missoula, Montana. This W-2 role supports eligible clients/members with housing-related planning and tenancy support. Work is client- and assignment-driven.", "Intro")]

facts = [
    [P("LOCATION", "Label"), P("EMPLOYMENT", "Label"), P("SCHEDULE", "Label")],
    [P("Missoula, Montana", "Value"), P("W-2 employee<br/>Hourly / non-exempt", "Value"), P("Part-time / variable hours<br/>No guaranteed minimum paid or billable hours", "Value")],
]
t = Table(facts, colWidths=[1.85*inch, 2.15*inch, 2.75*inch], hAlign="LEFT")
t.setStyle(TableStyle([
    ("BACKGROUND", (0,0), (-1,-1), PALE), ("BOX", (0,0), (-1,-1), .7, RULE),
    ("INNERGRID", (0,0), (-1,-1), .5, RULE), ("VALIGN", (0,0), (-1,-1), "TOP"),
    ("LEFTPADDING", (0,0), (-1,-1), 9), ("RIGHTPADDING", (0,0), (-1,-1), 9),
    ("TOPPADDING", (0,0), (-1,-1), 8), ("BOTTOMPADDING", (0,0), (-1,-1), 8),
]))
story += [t, Spacer(1, 6)]

story += section("Position purpose", [P("The role helps eligible clients/members acquire, maintain, or stabilize safe and reliable housing through housing assessment and planning, housing searches and applications, document gathering, voucher or waitlist follow-up, landlord/property communication, reasonable-accommodation support where appropriate, move-in planning, tenant education, housing stabilization and retention, recertification support, follow-up, and coordination with approved community partners.")])

story += section("Key responsibilities", bullets([
    "Assist with client intake, Referral to TSS forms, referral-status tracking, and required consent or release documents as assigned; identify housing goals, barriers, strengths, preferences, and next steps; assist with housing assessments and Housing Plans.",
    "Support housing searches and applications, document gathering, voucher/waitlist follow-up, landlord/property communication, move-in planning, and connection to resources.",
    "Provide tenant education and appropriate housing-retention, stabilization, recertification, monitoring, and follow-up support.",
    "Coordinate with landlords, property managers, shelters, case managers, providers, benefit programs, and other approved contacts when authorized and appropriate.",
    "Complete accurate, timely service logs/progress notes; track follow-up dates and report documentation, safety, eligibility, authorization, or billing concerns promptly.",
    "Keep activities within the authorized role, client/member Housing Plan or housing need, company policies, and applicable Medicaid/TSS requirements."
]))

story += section("Minimum qualifications", [P("Applicants must meet one of these pathways:")] + bullets([
    "Associate degree in human services, social services, public health, or a related field from an accredited college or university; or",
    "High school diploma, GED, or HiSET plus at least one year of relevant work experience as determined by Anchor Support Service LLC."
]) + [P("Relevant experience may include housing navigation, case-management support, social services, peer support, community outreach, property management, behavioral-health support, substance-use service support, homeless services, reentry services, benefits navigation, tenancy support, or other related experience.")])

story += section("Preferred qualifications", bullets([
    "Experience supporting people experiencing homelessness, housing instability, behavioral-health or substance-use recovery needs, reentry barriers, disabilities, or other housing-related barriers.",
    "Experience with housing applications, vouchers, leases, landlords/property managers, tenant education, fair-housing concepts, or housing retention.",
    "Clear, objective, timely, and accurate service-note writing; respectful communication with clients/members, landlords, providers, referral sources, and community partners.",
    "Ability to use approved business technology and protect confidential information.",
    "Reliable transportation or ability to attend community-based appointments when assigned and appropriate."
]))

story += section("Schedule, compensation, and probation", [
    P("Hours depend on client/member appointments, authorized service needs, available assignments, staffing, and company operational needs. Cancellations, no-shows, rescheduling, eligibility or authorization changes, and lack of allowable service need may change available hours. There is no guaranteed minimum number of paid or billable hours, fixed schedule, or guaranteed employment duration."),
    P("Probationary starting range: $17.00-$18.00 per hour, based on documented relevant experience, education/training, qualifications, and other lawful job-related factors. The probationary period is twelve (12) months from date of hire."),
    P("Successful completion of probation includes a performance and compensation review. The current post-probation target range is generally $18.00-$20.00 per hour, depending on performance, demonstrated competency, responsibilities, current business conditions, and company approval. A pay increase is not automatic or guaranteed; any approved wage change will be confirmed in writing before it takes effect."),
])

story += section("Documentation, timekeeping, and compliance", bullets([
    "Document services actually provided and actual time only, accurately and promptly. Notes should capture client/member identity from the authoritative record; service date; actual start/end times and total minutes; service category/type and delivery method; summary; participation/response when applicable; progress toward housing goals; follow-up; staff identity/attestation; and completion date.",
    "Record all compensable work time accurately, including assigned documentation, training, meetings, and other work. Paid work time and Medicaid-billable time are different; billing is limited to allowable services actually provided and documented.",
    "Confirm or document Medicaid eligibility and authorization status as assigned. Do not perform off-the-clock work or create, inflate, estimate, or extend billable service time. Flag unclear eligibility, authorization, billing, diagnosis, or documentation for review.",
    "Protect client/member and business information, use approved systems and communication methods, and maintain professional boundaries. Follow assigned safety, confidentiality, documentation, timekeeping, and company requirements. The role may be subject to supervision, documentation/billing review, coaching, retraining, and performance review.",
    "Meal periods are unpaid only when the employee is fully relieved of duties for the entire period and applicable law permits. Work performed during a meal period must be recorded; authorized rest breaks of 20 minutes or less are paid work time under applicable wage-and-hour rules."
]))

story += section("Professional expectations, safety, and work environment", [
    P("Communicate respectfully, plainly, and professionally; keep work communication service-related; follow through on assignments; attend confirmed appointments or promptly report conflicts; and report errors, compliance concerns, incidents, and safety concerns. Use good judgment in community settings, leave unsafe situations when safe to do so, and contact emergency services for immediate danger or a medical emergency. Staff are not expected to place themselves in unsafe situations."),
    P("Work may occur by phone, text, email, video, in the community, at a public location, client/member residence, agency office, landlord/property office, approved remote setting, or another approved setting. The position may require approved technology and travel to community locations when assigned. Required training may cover company policies, confidentiality, safety, professional boundaries, TSS workflow, documentation, and timekeeping/billing."),
    P("This role provides housing-related navigation, education, document gathering, coordination, and follow-up. Unless separately licensed, credentialed, and authorized, the role does not provide legal or medical advice, therapy, substance-use treatment, financial advising, property-management services, Medicaid eligibility determinations, or final authorization/billing decisions. Transportation alone is not the purpose of the role.")
])

story += section("Fair employment and employment relationship", [
    P("Anchor Support Service LLC is committed to fair and lawful employment practices. Employment and work-assignment decisions are made without unlawful discrimination, harassment, or retaliation."),
    P("This description summarizes the general nature of the position and does not promise guaranteed hours, guaranteed billable work, a fixed schedule, a specific pay increase, or continued employment. Duties, schedules, expectations, and assignments may change based on business and client/member needs, Medicaid requirements, staffing, safety, and company operations. The employment relationship is governed by applicable Montana and federal law and the company’s current written policies.")
])

story += section("How to apply", [P("Email a resume and a short letter of interest explaining your interest in the position to <link href='mailto:info@anchorsupportservice.com' color='#00335f'>info@anchorsupportservice.com</link>. Suggested subject: <b>Housing Navigator Application - [Applicant Name]</b>.", "Callout"), P("Please do not send Social Security numbers, date of birth, Medicaid information, medical information, criminal-history information, driver's-license numbers, bank information, or other sensitive personal information by ordinary email.")])

OUT.parent.mkdir(parents=True, exist_ok=True)
doc = PublicJobDoc(str(OUT))
doc.build(story)
print(f"Created {OUT} ({OUT.stat().st_size} bytes)")
