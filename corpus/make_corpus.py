"""Generates the demo corpus.

Design intent (PRD §10, "corpus too small to show believable multi-intent
retrieval"): 18 documents about corporate event planning, travel and
reimbursement, with deliberate overlap and two planted contradictions so the
Trust Gauntlet (PRD §2.1 D) has something real to catch.

Run: python -m corpus.make_corpus
"""
from __future__ import annotations

from pathlib import Path

DOCS: dict[str, str] = {}

DOCS["Doc_01"] = """# Venue Directory — Pune Region

## Capacity and Layout
The Pune region has four approved venues. Orchid Hall seats 30 people in
boardroom layout and 45 in theatre layout, making it the default choice for
mid-size offsites. Riverside Studio seats 18 people and is intended for
workshops rather than presentations. Sahyadri Conference Centre seats 120 in
theatre layout and 60 in banquet rounds. The Baner Annexe seats 25 and has no
dedicated catering kitchen.

## Booking Windows
Orchid Hall and Riverside Studio accept bookings up to 90 days in advance.
Sahyadri Conference Centre requires a minimum of 14 days notice for any booking
involving more than 50 attendees. The Baner Annexe can be booked same-day
subject to availability, which makes it the usual fallback when a primary venue
falls through.

## Equipment Included
All four venues include a projector, two wireless microphones and whiteboards in
the base rate. Video conferencing hardware is included at Orchid Hall and
Sahyadri only; the other two venues charge 4000 rupees per day for a portable
VC kit.
"""

DOCS["Doc_02"] = """# Venue Directory — Bangalore Region

## Capacity and Layout
Indiranagar Loft seats 35 people in boardroom layout. Whitefield Pavilion seats
200 in theatre layout and is the only venue in the Bangalore region licensed for
external guests. Koramangala Studio seats 20 and is workshop-oriented.

## Booking Windows
Whitefield Pavilion requires 21 days notice for external-guest events because of
the visitor security screening process. Indiranagar Loft and Koramangala Studio
accept bookings up to 60 days ahead with a 7 day minimum notice.

## Regional Rate Differences
Bangalore venue rates run roughly 15 percent higher than equivalent Pune venues.
Budget approvals should account for this difference when a team compares regions
for the same headcount.
"""

DOCS["Doc_03"] = """# Cancellation Policy — Standard Events

## Notice Tiers
Cancellations made more than 14 days before the event date incur no charge.
Cancellations between 7 and 14 days before the event incur 25 percent of the
venue fee. Cancellations inside 7 days incur 50 percent of the venue fee.
Cancellations inside 48 hours incur the full venue fee.

## Who Can Cancel
A cancellation inside the 7 day window must be authorised by the event owner's
reporting manager. A cancellation inside 48 hours must be authorised by a
senior director, because the full fee is charged to the department cost centre.

## Rescheduling Instead of Cancelling
Moving an event to a new date more than 14 days away is treated as a reschedule,
not a cancellation, and carries no fee. Only one free reschedule is permitted
per booking; a second date change is charged at the applicable cancellation
tier.
"""

DOCS["Doc_04"] = """# Cancellation Policy — Catered Events

## Catering Lock-In
Catering headcount locks 72 hours before the event. After lock-in the catering
charge is payable in full regardless of actual attendance, because ingredients
are ordered against the locked number.

## Interaction With the Standard Policy
The catered-event supplement applies on top of the standard venue cancellation
tiers in the events policy. A cancellation 5 days out therefore incurs 25
percent of the venue fee and nothing for catering, because catering had not yet
locked.

## Exception for Venue-Caused Cancellation
If the venue cancels, no fee of any kind applies and catering is refunded in
full, including within the 72 hour lock-in window.
"""

DOCS["Doc_05"] = """# Catering Options and Dietary Accommodation

## Standard Menus
Three standard menus are available: North Indian vegetarian, South Indian
vegetarian, and a mixed non-vegetarian menu. All three include tea, coffee and
two snack services across a full day.

## Dietary Accommodation
Jain, vegan and gluten-free requirements are accommodated at no extra cost when
flagged at least 72 hours before the event, which aligns with the catering
headcount lock-in. Requests made after lock-in are handled on a best-effort
basis and may not be met.

## Per-Head Costs
The vegetarian menus are charged at 650 rupees per head per day. The
non-vegetarian menu is 850 rupees per head per day. A minimum charge of 15
heads applies regardless of actual headcount.
"""

DOCS["Doc_06"] = """# Catering at Specific Venues

## Orchid Hall
Orchid Hall has an in-house kitchen and supports all three standard menus plus
all dietary accommodations.

## Riverside Studio
Riverside Studio has no kitchen. Catering is delivered from an external partner,
which means the dietary accommodation window extends to 96 hours rather than 72.

## The Baner Annexe
The Baner Annexe has no catering capability at all. Teams booking this venue
arrange catering independently and claim it as a reimbursable expense under the
events expense category.

## Whitefield Pavilion
Whitefield Pavilion supports full catering but charges a 10 percent service
levy on the catering total, which is not charged at any Pune venue.
"""

DOCS["Doc_07"] = """# Expense Reimbursement — Standard Rules

## Eligible Categories
Travel, accommodation, per-diem meals and event-related expenses are
reimbursable. Personal entertainment, alcohol and fines are not reimbursable
under any circumstance.

## Submission Deadline
Claims must be submitted within 30 days of the expense date. The standard
reimbursement rule still applies to event-related claims: original receipts are
required for any single item above 2000 rupees.

## Approval Chain
Claims up to 25000 rupees are approved by the reporting manager. Claims above
25000 rupees require finance partner review in addition to manager approval.
"""

DOCS["Doc_08"] = """# Expense Reimbursement — Late and Exceptional Claims

## Late Submission
A claim submitted between 30 and 60 days after the expense date requires a
written justification and reporting-manager approval. A claim submitted more
than 60 days after the expense date requires senior director approval and is
approved only in exceptional circumstances.

## The Late-Booking Exception
Where a venue or travel booking was made inside the normal notice window because
of a business-critical need, the resulting premium is reimbursable under the
late-booking exception. The late-booking exception requires senior director
approval and a note recording the business reason.

## Documentation
Exceptional claims require the original receipt regardless of amount, so the
2000 rupee receipt threshold does not apply to them.
"""

DOCS["Doc_09"] = """# Travel Booking Policy — Domestic

## Booking Channel
All domestic travel is booked through the corporate travel desk. Self-booked
travel is reimbursable only where the travel desk was unavailable and the
traveller records that fact in the claim.

## Advance Purchase
Domestic flights should be booked at least 14 days in advance. Bookings inside
14 days require reporting-manager approval and are flagged for the quarterly
travel cost review.

## Class of Travel
Economy class is standard for all domestic flights regardless of grade. Rail
travel is booked in AC 2-tier or below.
"""

DOCS["Doc_10"] = """# Travel Booking Policy — International

## Booking Channel and Notice
International travel is booked through the corporate travel desk with a minimum
of 21 days notice. Bookings inside 21 days require senior director approval,
which is a stricter bar than the domestic 14 day rule.

## Class of Travel
Economy class is standard for flights under six hours. Premium economy is
permitted for flights over six hours. Business class requires senior director
approval and is not available on the basis of grade alone.

## Visa and Documentation
Visa costs, travel insurance and mandatory vaccinations are reimbursable and are
claimed under the travel category rather than the events category.
"""

DOCS["Doc_11"] = """# Per-Diem Rates

## Domestic Rates
The domestic per-diem is 1800 rupees per day in metro cities and 1200 rupees per
day elsewhere. Pune and Bangalore are both classified as metro cities for
per-diem purposes.

## International Rates
The international per-diem is set per country and published quarterly by
finance. Per-diem is not payable for any day on which the employer provides all
three meals, which is typical on a fully catered offsite day.

## Receipts
Per-diem does not require receipts. Actual-cost meal claims are an alternative
to per-diem and do require receipts, but the two cannot be mixed on a single
trip.
"""

DOCS["Doc_12"] = """# Event Approval Workflow

## Threshold for Approval
Any event with a total budget above 150000 rupees requires finance partner
sign-off before the venue is confirmed. Events below that threshold are approved
by the reporting manager alone.

## Headcount Triggers
An event with more than 50 attendees requires a facilities safety review
regardless of budget. An event with external attendees requires security
screening regardless of headcount.

## Standing Reimbursement Rule
The standard reimbursement rule still applies to all event spend: the event
owner remains responsible for submitting claims within 30 days, and approval
under this workflow does not substitute for expense approval.
"""

DOCS["Doc_13"] = """# Offsite Planning Checklist

## Four Weeks Out
Confirm headcount, shortlist two venues in the target region, and confirm budget
against the approval threshold.

## Two Weeks Out
Confirm the venue booking, raise travel requests through the travel desk, and
circulate the agenda. This is also the last point at which a cancellation is
free under the standard policy.

## Seventy-Two Hours Out
Lock the catering headcount and confirm dietary accommodations. After this point
catering is payable in full.

## Day Of
Collect receipts for any independently arranged catering or transport, since
these are claimed under the events expense category.
"""

DOCS["Doc_14"] = """# Accommodation Policy

## Room Standard
Standard accommodation is a single occupancy room in a mid-tier business hotel.
Shared rooms are never required.

## Rate Caps
The nightly rate cap is 6500 rupees in metro cities and 4500 rupees elsewhere.
Rates above the cap require reporting-manager approval and a note explaining why
a compliant option was unavailable.

## Offsite Accommodation
Where an offsite venue includes accommodation, the venue rate supersedes the
nightly cap and no separate approval is needed, provided the bundled rate was
part of the approved event budget.
"""

DOCS["Doc_15"] = """# Vendor and Venue Payment Terms

## Payment Schedule
Venues are paid 30 percent on confirmation and the balance within 15 days of the
event. Catering partners are paid in full within 30 days of the event.

## Advance Refunds
The 30 percent confirmation advance is refundable only where the cancellation
falls in the no-charge tier, meaning more than 14 days before the event.

## Purchase Orders
Any vendor engagement above 50000 rupees requires a purchase order raised before
the service date. Retrospective purchase orders are not accepted.
"""

DOCS["Doc_16"] = """# Accessibility Requirements

## Venue Accessibility
All approved venues must have step-free access to the main hall and an
accessible restroom. Orchid Hall, Sahyadri Conference Centre and Whitefield
Pavilion meet this standard in full.

## Partial Compliance
Riverside Studio has step-free access but no accessible restroom on the same
floor. The Baner Annexe has three steps at the entrance and is not step-free.
Teams with accessibility requirements should not book either venue without
confirming arrangements.

## Requesting Support
Sign-language interpretation and live captioning can be arranged with 10
working days notice and are charged to the event budget.
"""

DOCS["Doc_17"] = """# Data and Recording Guidelines

## Recording Sessions
Recording a session requires the consent of everyone present. Consent is
recorded in the event notes rather than collected individually.

## Retention
Recordings of internal events are retained for 90 days and then deleted.
Recordings involving external attendees are retained for 30 days only.

## Sharing
Recordings are shared through the internal video platform. They are never
attached to email or uploaded to external services.
"""

DOCS["Doc_18"] = """# Frequently Asked Questions

## Can I book a venue before budget approval?
You can hold a provisional booking, but the venue is not confirmed and the 30
percent advance is not paid until budget approval clears. A provisional hold
does not start the cancellation clock.

## What happens if attendance drops after catering locks?
The locked catering headcount is charged in full. There is no partial refund for
reduced attendance after the 72 hour lock-in.

## Does the free reschedule apply to catering?
A reschedule more than 14 days out carries no venue fee, and since catering has
not locked at that point, no catering charge applies either.

## Who approves a same-day venue change?
A same-day change is treated as a cancellation inside 48 hours plus a new
booking, so it needs senior director approval for the cancelled booking.
"""


def write_corpus(target: Path | None = None) -> list[Path]:
    directory = Path(target or Path(__file__).resolve().parent / "docs")
    directory.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for doc_id, body in DOCS.items():
        path = directory / f"{doc_id}.md"
        path.write_text(body.strip() + "\n", encoding="utf-8")
        written.append(path)
    return written


if __name__ == "__main__":
    paths = write_corpus()
    print(f"Wrote {len(paths)} documents to {paths[0].parent}")
