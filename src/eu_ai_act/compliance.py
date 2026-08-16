"""
Compliance logic for the EU AI Act.

Maps obligations to actors and risk tiers, and generates actionable
compliance checklists. Every checklist item cites its source article(s).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from . import data


# --- Obligation catalogue -------------------------------------------------
# Each obligation: id, actor, tier, article ref, title, description, action.
OBLIGATIONS: List[Dict[str, Any]] = [
    # ---- Prohibited practices (all actors) ----
    {
        "id": "proh-1",
        "actor": "all",
        "tier": "prohibited",
        "ref": "Article 5",
        "title": "Do not deploy prohibited AI practices",
        "description": "Subliminal/manipulative techniques, vulnerability exploitation, social scoring, predictive policing based solely on profiling, untargeted facial scraping, emotion inference in workplace/education, biometric categorisation of sensitive attributes, and (subject to strict conditions) real-time remote biometric identification in public spaces.",
        "action": "Screen all AI systems against the Article 5 prohibited list before market placement or use.",
    },
    # ---- AI literacy (all actors) ----
    {
        "id": "lit-1",
        "actor": "all",
        "tier": "all",
        "ref": "Article 4",
        "title": "Ensure AI literacy of staff",
        "description": "Providers and deployers must take measures to ensure a sufficient level of AI literacy of their staff and other persons dealing with AI systems on their behalf.",
        "action": "Implement AI literacy training for all staff involved in developing, deploying or using AI systems.",
    },
    # ---- High-risk: provider obligations ----
    {
        "id": "hr-rm",
        "actor": "provider",
        "tier": "high_risk",
        "ref": "Article 9",
        "title": "Establish a risk management system",
        "description": "Establish, implement, document and maintain a risk management system covering the entire lifecycle of the high-risk AI system.",
        "action": "Document a risk management system with risk identification, analysis, evaluation, and mitigation measures.",
    },
    {
        "id": "hr-data",
        "actor": "provider",
        "tier": "high_risk",
        "ref": "Article 10",
        "title": "Ensure data and data governance",
        "description": "Training, validation and testing data sets must be relevant, sufficiently representative, and free of errors, and must be subject to appropriate data governance and management practices.",
        "action": "Document data governance practices, data provenance, and bias-mitigation measures.",
    },
    {
        "id": "hr-techdoc",
        "actor": "provider",
        "tier": "high_risk",
        "ref": "Article 11 + Annex IV",
        "title": "Prepare technical documentation",
        "description": "Draw up technical documentation demonstrating compliance, in accordance with Annex IV.",
        "action": "Prepare and maintain technical documentation per Annex IV before placing on the market.",
    },
    {
        "id": "hr-logs",
        "actor": "provider",
        "tier": "high_risk",
        "ref": "Article 12",
        "title": "Enable automatic record-keeping",
        "description": "High-risk systems must automatically record events (logs) over their lifetime, enabling traceability.",
        "action": "Implement automatic logging of events for the lifetime of the system.",
    },
    {
        "id": "hr-transp",
        "actor": "provider",
        "tier": "high_risk",
        "ref": "Article 13",
        "title": "Provide transparency and information to deployers",
        "description": "Provide instructions for use and information to deployers to enable compliant use and interpretation of output.",
        "action": "Provide clear instructions for use and deployer-facing information.",
    },
    {
        "id": "hr-oversight",
        "actor": "provider",
        "tier": "high_risk",
        "ref": "Article 14",
        "title": "Enable human oversight",
        "description": "Design high-risk systems so they can be effectively overseen by natural persons during the period they are in use.",
        "action": "Design and document human-oversight measures and controls.",
    },
    {
        "id": "hr-robust",
        "actor": "provider",
        "tier": "high_risk",
        "ref": "Article 15",
        "title": "Ensure accuracy, robustness and cybersecurity",
        "description": "High-risk systems must achieve an appropriate level of accuracy, robustness and cybersecurity throughout their lifecycle.",
        "action": "Document accuracy metrics, robustness testing, and cybersecurity measures.",
    },
    {
        "id": "hr-qms",
        "actor": "provider",
        "tier": "high_risk",
        "ref": "Article 17",
        "title": "Implement a quality management system",
        "description": "Implement a quality management system ensuring compliance, covering design, development, quality, and post-market activities.",
        "action": "Establish and maintain a documented quality management system.",
    },
    {
        "id": "hr-dockeep",
        "actor": "provider",
        "tier": "high_risk",
        "ref": "Article 18",
        "title": "Keep documentation",
        "description": "Keep technical documentation at the disposal of national competent authorities for at least 10 years after placing on the market.",
        "action": "Retain technical documentation for at least 10 years.",
    },
    {
        "id": "hr-correct",
        "actor": "provider",
        "tier": "high_risk",
        "ref": "Article 20",
        "title": "Take corrective actions and inform",
        "description": "If a high-risk system presents a risk, take corrective actions, withdraw/recall it, and inform relevant authorities and deployers.",
        "action": "Establish a corrective-action and duty-of-information process.",
    },
    {
        "id": "hr-coop",
        "actor": "provider",
        "tier": "high_risk",
        "ref": "Article 21",
        "title": "Cooperate with competent authorities",
        "description": "Cooperate with national competent authorities on any corrective action.",
        "action": "Cooperate with authorities on demand.",
    },
    {
        "id": "hr-authrep",
        "actor": "provider",
        "tier": "high_risk",
        "ref": "Article 22",
        "title": "Appoint an authorised representative (non-EU providers)",
        "description": "Providers established outside the EU must appoint an authorised representative established in the Union.",
        "action": "Appoint an EU authorised representative if established outside the EU.",
    },
    {
        "id": "hr-conform",
        "actor": "provider",
        "tier": "high_risk",
        "ref": "Article 43",
        "title": "Undergo conformity assessment",
        "description": "High-risk systems must undergo a conformity assessment procedure before being placed on the market.",
        "action": "Complete the applicable conformity assessment (Annex VI internal control or Annex VII notified-body assessment).",
    },
    {
        "id": "hr-decl",
        "actor": "provider",
        "tier": "high_risk",
        "ref": "Article 47 + Annex V",
        "title": "Draw up EU declaration of conformity",
        "description": "Draw up a written EU declaration of conformity in accordance with Annex V.",
        "action": "Issue and keep an EU declaration of conformity.",
    },
    {
        "id": "hr-ce",
        "actor": "provider",
        "tier": "high_risk",
        "ref": "Article 48",
        "title": "Affix CE marking",
        "description": "Affix the CE marking to high-risk systems that have passed conformity assessment.",
        "action": "Affix CE marking and any other required markings.",
    },
    {
        "id": "hr-reg",
        "actor": "provider",
        "tier": "high_risk",
        "ref": "Article 49 + Annex VIII",
        "title": "Register in the EU database",
        "description": "Register high-risk AI systems in the EU database before placing on the market, with information per Annex VIII.",
        "action": "Register the system in the EU database for high-risk AI systems.",
    },
    {
        "id": "hr-pmm",
        "actor": "provider",
        "tier": "high_risk",
        "ref": "Article 72",
        "title": "Establish post-market monitoring",
        "description": "Establish and document a post-market monitoring system and plan for high-risk systems.",
        "action": "Implement a post-market monitoring plan and system.",
    },
    {
        "id": "hr-incident",
        "actor": "provider",
        "tier": "high_risk",
        "ref": "Article 73",
        "title": "Report serious incidents",
        "description": "Report serious incidents to the market surveillance authorities of the Member States where the incident occurred.",
        "action": "Establish a serious-incident reporting process.",
    },
    # ---- High-risk: importer obligations ----
    {
        "id": "hr-imp",
        "actor": "importer",
        "tier": "high_risk",
        "ref": "Article 23",
        "title": "Verify provider compliance (importers)",
        "description": "Importers must verify that the provider has carried out the conformity assessment, drawn up technical documentation, and affixed CE marking.",
        "action": "Verify provider compliance before placing the system on the market.",
    },
    # ---- High-risk: distributor obligations ----
    {
        "id": "hr-dist",
        "actor": "distributor",
        "tier": "high_risk",
        "ref": "Article 24",
        "title": "Verify compliance (distributors)",
        "description": "Distributors must verify that the system bears the CE marking, is accompanied by the required documentation and instructions, and that the provider/importer have complied.",
        "action": "Verify CE marking, documentation and instructions before making available.",
    },
    # ---- High-risk: deployer obligations ----
    {
        "id": "hr-deploy",
        "actor": "deployer",
        "tier": "high_risk",
        "ref": "Article 26",
        "title": "Use high-risk systems compliantly",
        "description": "Deployers must use high-risk systems in accordance with instructions, ensure human oversight, monitor operation, keep logs, and cooperate with authorities.",
        "action": "Use the system per instructions, assign human oversight, monitor and log operation.",
    },
    {
        "id": "hr-fria",
        "actor": "deployer",
        "tier": "high_risk",
        "ref": "Article 27",
        "title": "Conduct a fundamental rights impact assessment",
        "description": "Public bodies and certain private deployers of high-risk systems must conduct a fundamental rights impact assessment before deployment.",
        "action": "Conduct and document a fundamental rights impact assessment (FRIA).",
    },
    # ---- Limited-risk / transparency ----
    {
        "id": "tr-chatbot",
        "actor": "provider",
        "tier": "limited_risk",
        "ref": "Article 50(1)",
        "title": "Disclose AI interaction (chatbots)",
        "description": "AI systems intended to interact directly with natural persons must inform users they are interacting with an AI system, unless obvious.",
        "action": "Ensure users are informed they are interacting with an AI system.",
    },
    {
        "id": "tr-emotion",
        "actor": "provider",
        "tier": "limited_risk",
        "ref": "Article 50(2)",
        "title": "Disclose emotion recognition / biometric categorisation",
        "description": "Emotion recognition and biometric categorisation systems must inform persons exposed to them.",
        "action": "Inform persons exposed to emotion recognition or biometric categorisation.",
    },
    {
        "id": "tr-deepfake",
        "actor": "provider",
        "tier": "limited_risk",
        "ref": "Article 50(3)",
        "title": "Disclose deepfakes",
        "description": "Deepfakes must be disclosed as artificially generated or manipulated content.",
        "action": "Label deepfake content as artificially generated or manipulated.",
    },
    {
        "id": "tr-public",
        "actor": "provider",
        "tier": "limited_risk",
        "ref": "Article 50(4)",
        "title": "Disclose AI-generated public-interest text",
        "description": "AI-generated text intended to inform the public on matters of public interest must be disclosed as artificially generated.",
        "action": "Disclose AI-generated text on matters of public interest.",
    },
    # ---- GPAI model providers ----
    {
        "id": "gpai-techdoc",
        "actor": "provider",
        "tier": "gpai",
        "ref": "Article 53(1)(a) + Annex XI",
        "title": "Provide technical documentation for GPAI models",
        "description": "Providers of general-purpose AI models must draw up and keep up-to-date technical documentation per Annex XI.",
        "action": "Prepare and maintain technical documentation per Annex XI.",
    },
    {
        "id": "gpai-copyright",
        "actor": "provider",
        "tier": "gpai",
        "ref": "Article 53(1)(c)",
        "title": "Comply with copyright policy",
        "description": "GPAI model providers must put in place a policy to comply with Union copyright law, including opt-outs for text and data mining.",
        "action": "Implement and document a copyright-compliance policy.",
    },
    {
        "id": "gpai-summary",
        "actor": "provider",
        "tier": "gpai",
        "ref": "Article 53(1)(d)",
        "title": "Publish a training-data summary",
        "description": "GPAI model providers must make publicly available a sufficiently detailed summary of the content used for training.",
        "action": "Publish a training-data summary.",
    },
    {
        "id": "gpai-sysrisk",
        "actor": "provider",
        "tier": "gpai_systemic",
        "ref": "Article 55",
        "title": "Manage systemic risk (GPAI with systemic risk)",
        "description": "Providers of GPAI models with systemic risk must perform model evaluation, adversarial testing, mitigate systemic risks, report serious incidents, and ensure cybersecurity.",
        "action": "Implement systemic-risk management: evaluation, adversarial testing, mitigation, incident reporting, cybersecurity.",
    },
]


def obligations_for(
    actor: Optional[str] = None,
    tier: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return obligations filtered by actor and/or risk tier."""
    result = OBLIGATIONS
    if actor:
        key = actor.lower().replace(" ", "_")
        result = [o for o in result if o["actor"] in ("all", key)]
    if tier:
        key = tier.lower().replace(" ", "_")
        result = [o for o in result if o["tier"] in ("all", key)]
    return result


def checklist(
    actor: str,
    tier: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Generate a compliance checklist for a given actor (and optional tier).

    Returns a list of checklist items, each with a checkbox, obligation title,
    description, action, and legal reference.
    """
    items = []
    for o in obligations_for(actor=actor, tier=tier):
        items.append(
            {
                "done": False,
                "id": o["id"],
                "title": o["title"],
                "description": o["description"],
                "action": o["action"],
                "ref": o["ref"],
            }
        )
    return items


def classify_high_risk(description: str) -> Dict[str, Any]:
    """
    Heuristic classification of whether an AI system is likely high-risk.

    This is a decision-support aid based on Annex III areas and Article 6.
    It is NOT a substitute for a formal legal assessment.
    """
    text = description.lower()
    areas = data.risk_tiers()[1]["annex_iii_areas"]
    matches = []
    keywords = {
        1: ["biometric", "facial recognition", "emotion recognition", "biometric categorisation"],
        2: ["critical infrastructure", "safety component", "electricity", "water", "gas", "heating", "road", "traffic"],
        3: ["education", "admission", "learning outcome", "student", "exam", "vocational"],
        4: ["recruitment", "hiring", "employee", "worker", "performance", "promotion", "termination"],
        5: ["credit", "loan", "essential service", "benefit", "emergency", "social security", "insurance"],
        6: ["law enforcement", "police", "criminal", "offence", "re-offending", "polygraph"],
        7: ["migration", "asylum", "border", "refugee", "immigration"],
        8: ["judicial", "court", "justice", "election", "referendum", "voting"],
    }
    for area_num, kws in keywords.items():
        if any(k in text for k in kws):
            area = next(a for a in areas if a["area"] == area_num)
            matches.append(area)
    likely = len(matches) > 0
    return {
        "likely_high_risk": likely,
        "matched_annex_iii_areas": matches,
        "disclaimer": "Heuristic classification based on Annex III keywords. A formal legal assessment under Article 6 is required for definitive classification.",
        "ref": "Article 6, Annex III",
    }
