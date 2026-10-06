"""Demo case data. Generated from frontend/lib/case-data.ts by `npm run export:data` — do not edit."""

DEMO_CLAIM = "CLM-4471902"

CLAIM = {
    "code": "CO-50",
    "text": "The requested service is not medically necessary as defined in the plan.",
    "meta": "Denial letter, page 1 · 14 Sep 2026"
}

ARGS = [
    {
        "id": "a1",
        "tier": "solid",
        "ref": "A1",
        "title": "The plan’s own criteria are met",
        "assert": "Your plan defines medical necessity by the MCG care guidelines in force on the date of service. Your chart meets all four of the criteria it lists.",
        "needs": "Chart notes 12 Mar – 2 Sep 2026 · MCG criteria excerpt, 2026 edition",
        "status": "All evidence on file",
        "ok": True,
        "reply": "They could argue a later edition of the guideline applies.",
        "verdict": "Does not defeat it",
        "why": "The plan names the edition in force on 14 Sep 2026. That edition is attached with its publication date."
    },
    {
        "id": "a2",
        "tier": "solid",
        "ref": "A2",
        "title": "Step therapy was completed",
        "assert": "Two preferred agents were tried and documented as failed, each for fourteen weeks, before this treatment was requested.",
        "needs": "Pharmacy fill history · two physician notes",
        "status": "1 of 2 notes on file",
        "ok": False,
        "reply": "They could say the trials were too short to count.",
        "verdict": "Does not defeat it",
        "why": "Their own step-therapy policy sets the minimum trial at twelve weeks. Both trials ran fourteen."
    },
    {
        "id": "a3",
        "tier": "solid",
        "ref": "A3",
        "title": "Their own clinical policy covers this",
        "assert": "Insurer clinical policy CP-0241 lists this exact indication as covered when prior agents have failed.",
        "needs": "Policy bulletin CP-0241, version effective 1 Jun 2026",
        "status": "All evidence on file",
        "ok": True,
        "reply": "They could say the bulletin was superseded before the date of service.",
        "verdict": "Does not defeat it",
        "why": "The version in force on 14 Sep 2026 is attached, with its revision history page."
    },
    {
        "id": "b1",
        "tier": "add",
        "ref": "B1",
        "title": "A state continuity-of-care mandate",
        "assert": "State law requires continuity of an ongoing course of treatment while a coverage dispute is open.",
        "needs": "State statute text § 38.2-3407.9",
        "status": "Optional — not yet attached",
        "ok": False,
        "reply": "They could say the mandate does not reach self-funded plans.",
        "verdict": "They can knock this one back",
        "why": "Your plan is self-funded, so state insurance mandates may not apply to it. Worth raising as a secondary point, not as a main one."
    },
    {
        "id": "b2",
        "tier": "add",
        "ref": "B2",
        "title": "Interrupting treatment causes documented harm",
        "assert": "Stopping the infusion schedule carries a specific, documented clinical risk within a known timeframe.",
        "needs": "Physician letter, point 4",
        "status": "Requested from Dr. Alvarez",
        "ok": False,
        "reply": "They could say harm is not part of the medical-necessity test.",
        "verdict": "They can knock this one back",
        "why": "Persuasive to a human reviewer, but the plan language does not require them to weigh it. It helps; it does not carry the appeal."
    },
    {
        "id": "c1",
        "tier": "out",
        "ref": "C1",
        "title": "The denial letter was sent late",
        "assert": "The insurer answered outside the window allowed for a post-service claim.",
        "needs": "—",
        "status": "Left out of the letter",
        "ok": False,
        "reply": "—",
        "verdict": "Left out",
        "why": "The letter is dated eleven days after the claim, inside the thirty-day window. The argument does not hold, so it is not in your appeal."
    }
]

CASES = [
    {
        "ins": "Anthem Blue Cross",
        "claim": "CLM-4471902",
        "reason": "Not medically necessary — CO-50",
        "stage": "Internal appeal · drafting",
        "date": "22 Mar 2027",
        "days": 168,
        "total": 180
    },
    {
        "ins": "UnitedHealthcare",
        "claim": "CLM-3390118",
        "reason": "No prior authorisation — CO-197",
        "stage": "Awaiting insurer response",
        "date": "11 Nov 2026",
        "days": 37,
        "total": 60
    },
    {
        "ins": "Cigna",
        "claim": "CLM-7725640",
        "reason": "Step therapy not completed — CO-B7",
        "stage": "External review window open",
        "date": "9 Oct 2026",
        "days": 4,
        "total": 120
    }
]

FACTS = [
    {
        "id": "f1",
        "k": "Claim number",
        "v": "CLM-4471902",
        "conf": "high",
        "span": "page 1, line 4",
        "quote": "Claim number: CLM-4471902.",
        "st": "confirmed"
    },
    {
        "id": "f2",
        "k": "Date of denial",
        "v": "14 September 2026",
        "conf": "high",
        "span": "page 1, header",
        "quote": "Date of notice: September 14, 2026.",
        "st": "confirmed"
    },
    {
        "id": "f3",
        "k": "Reason code",
        "v": "CO-50",
        "conf": "high",
        "span": "page 1, line 9",
        "quote": "Reason code CO-50.",
        "st": "confirmed"
    },
    {
        "id": "f4",
        "k": "Stated reason",
        "v": "Not medically necessary as defined in the plan",
        "conf": "high",
        "span": "page 1, line 9–11",
        "quote": "The requested service is not medically necessary as defined in the plan. Reason code CO-50.",
        "st": "confirmed"
    },
    {
        "id": "f5",
        "k": "Service denied",
        "v": "Infliximab infusion — J1745",
        "conf": "high",
        "span": "page 1, line 6",
        "quote": "Service requested: infliximab infusion, HCPCS J1745.",
        "st": "confirmed"
    },
    {
        "id": "f6",
        "k": "Plan type",
        "v": "Employer-sponsored, self-funded (ERISA)",
        "conf": "medium",
        "span": "page 2, line 2",
        "quote": "Your coverage is provided through a self-funded group health plan sponsored by your employer.",
        "st": "confirmed"
    },
    {
        "id": "f7",
        "k": "Policy section cited",
        "v": "7.4(b)",
        "conf": "low",
        "span": "page 2, line 14",
        "quote": "Plan provision 7.4(b) excludes services that are investigational.",
        "st": "pending"
    },
    {
        "id": "f8",
        "k": "Appeal address",
        "v": "P.O. Box 60007, Los Angeles CA 90060",
        "conf": "medium",
        "span": "page 3, line 3",
        "quote": "Send written appeals to: Appeals Unit, P.O. Box 60007, Los Angeles, CA 90060.",
        "st": "pending"
    }
]

ROAD_STEPS = [
    {
        "n": "01",
        "title": "Internal appeal",
        "who": "You file",
        "date": "22 Mar 2027",
        "days": 168,
        "total": 180,
        "current": True,
        "need": "Written appeal, physician letter, supporting records",
        "rule": "29 C.F.R. § 2560.503-1(h)(3)(i)",
        "calc": "Your plan allows 180 days from the date of the adverse determination. The determination is dated 14 Sep 2026, so day 180 falls on 22 Mar 2027. Day one is the day after the letter date.",
        "quote": "A claimant shall have at least 180 days following receipt of a notification of an adverse benefit determination within which to appeal the determination."
    },
    {
        "n": "02",
        "title": "Insurer responds",
        "who": "They answer",
        "date": "within 30 days",
        "days": 30,
        "total": 30,
        "current": False,
        "need": "Nothing from you. We log the date they received it.",
        "rule": "29 C.F.R. § 2560.503-1(i)(2)(iii)",
        "calc": "For a post-service claim the plan has 60 days; for a pre-service claim, 30. Yours is pre-service, so 30 days from the date they receive the appeal.",
        "quote": "The plan administrator shall notify the claimant of the benefit determination on review within a reasonable period of time appropriate to the medical circumstances."
    },
    {
        "n": "03",
        "title": "External review",
        "who": "You request",
        "date": "4 months after a final denial",
        "days": 120,
        "total": 120,
        "current": False,
        "need": "Request form, the final denial, the same evidence file",
        "rule": "45 C.F.R. § 147.137(b)(2)",
        "calc": "The window opens the day the internal appeal is finally denied and runs four months. It does not start until that happens.",
        "quote": "A request for external review must be filed within four months after the date of receipt of a notice of an adverse benefit determination or final internal adverse benefit determination."
    },
    {
        "n": "04",
        "title": "Independent decision",
        "who": "Reviewer decides",
        "date": "within 45 days",
        "days": 45,
        "total": 45,
        "current": False,
        "need": "Nothing from you. The decision binds the insurer.",
        "rule": "45 C.F.R. § 147.137(c)(2)(xi)",
        "calc": "The independent review organisation has 45 days from the date it accepts the request. An expedited track exists if your doctor certifies urgency.",
        "quote": "The assigned independent review organization must provide written notice of the final external review decision within 45 days after it receives the request for external review."
    }
]

EVIDENCE = [
    {
        "id": "e1",
        "t": "Chart notes, 12 Mar – 2 Sep 2026",
        "why": "A1",
        "how": "Request from the treating clinic. Ask for the full visit notes, not the summary.",
        "st": "have"
    },
    {
        "id": "e2",
        "t": "MCG criteria excerpt, 2026 edition",
        "why": "A1",
        "how": "We pulled the four criteria your plan names. Check the edition date matches.",
        "st": "have"
    },
    {
        "id": "e3",
        "t": "Pharmacy fill history",
        "why": "A2",
        "how": "Your pharmacy can print 24 months on request, usually same day.",
        "st": "have"
    },
    {
        "id": "e4",
        "t": "Physician note — adalimumab trial",
        "why": "A2",
        "how": "From Dr. Alvarez. Must show start date, dose and why it was stopped.",
        "st": "have"
    },
    {
        "id": "e5",
        "t": "Physician note — etanercept trial",
        "why": "A2",
        "how": "Call the office and ask for the 14-week follow-up note specifically.",
        "st": "missing"
    },
    {
        "id": "e6",
        "t": "Insurer clinical policy CP-0241",
        "why": "A3",
        "how": "We have the version in force on 14 Sep 2026, with its revision page.",
        "st": "have"
    },
    {
        "id": "e7",
        "t": "Physician letter of medical necessity",
        "why": "A1 A2 B2",
        "how": "Use the template below. Four points, in the doctor’s own words, on letterhead.",
        "st": "progress"
    },
    {
        "id": "e8",
        "t": "State statute § 38.2-3407.9 text",
        "why": "B1",
        "how": "Optional. Only strengthens a secondary argument.",
        "st": "optional"
    }
]

LETTER_PARAS = [
    {
        "id": "p1",
        "ref": None,
        "text": "I am appealing the denial of coverage for infliximab infusion therapy, HCPCS code J1745, under claim CLM-4471902. The denial is dated 14 September 2026 and gives reason code CO-50, stating that the service is not medically necessary as defined in the plan. This letter sets out why that conclusion does not hold under the plan’s own terms."
    },
    {
        "id": "p2",
        "ref": "A1",
        "text": "Section 4.2 of the plan defines medical necessity by reference to the MCG care guidelines in force on the date of service. The relevant guideline lists four criteria. The enclosed chart notes, covering 12 March to 2 September 2026, document that all four are met, and the guideline excerpt enclosed is the edition in force on 14 September 2026."
    },
    {
        "id": "p3",
        "ref": "A2",
        "text": "The plan’s step-therapy requirement has been satisfied. Two preferred agents were tried before this request: adalimumab from 3 January to 10 April 2026, and etanercept from 24 April to 31 July 2026. Each trial ran fourteen weeks. The plan’s own policy sets the minimum trial at twelve. The enclosed pharmacy fill history and physician notes document both."
    },
    {
        "id": "p4",
        "ref": "A3",
        "text": "Your own clinical policy CP-0241, in the version effective 1 June 2026 and enclosed here with its revision page, lists this indication as covered where prior agents have failed. The facts above place this request within that policy as it stood on the date of service."
    },
    {
        "id": "p5",
        "ref": "B1",
        "text": "Separately, and as a secondary point, state law requires continuity of an ongoing course of treatment while a coverage dispute is open. I recognise that this requirement may not reach a self-funded plan, and I raise it as additional context rather than as a basis for reversal."
    },
    {
        "id": "p6",
        "ref": None,
        "text": "I am asking you to reverse the denial and authorise the requested course of treatment. Enclosed are the chart notes, the pharmacy fill history, two physician notes, the clinical policy with its revision page, and a letter of medical necessity from the treating physician. I would be grateful for your decision within the thirty days allowed."
    }
]

