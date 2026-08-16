# Compliance Checklist

This is a step-by-step guide to achieving compliance with the EU AI Act. It is organised by actor. Use the CLI to generate an interactive checklist:

```bash
eu-ai-act checklist provider
eu-ai-act checklist deployer
eu-ai-act checklist importer
eu-ai-act checklist distributor
```

---

## Step 0 — Determine your role and risk tier

Before anything else, establish:

1. **Who are you?** Provider, deployer, importer, distributor, authorised representative, or a combination?
2. **What risk tier is your AI system?** Prohibited, high-risk, limited-risk, or minimal-risk?

Use the heuristic classifier for a first pass:

```bash
eu-ai-act classify "describe your AI system here"
```

> **Important:** The classifier is a decision-support aid. A formal legal assessment under Article 6 (and, for products, the Annex I legislation) is required for definitive classification.

---

## Provider checklist (high-risk systems)

| # | Obligation | Ref |
|---|---|---|
| 1 | Screen against prohibited practices (Art 5) | Art 5 |
| 2 | Ensure AI literacy of staff | Art 4 |
| 3 | Establish a risk management system | Art 9 |
| 4 | Ensure data and data governance | Art 10 |
| 5 | Prepare technical documentation | Art 11 + Annex IV |
| 6 | Enable automatic record-keeping (logs) | Art 12 |
| 7 | Provide transparency and information to deployers | Art 13 |
| 8 | Enable human oversight | Art 14 |
| 9 | Ensure accuracy, robustness, cybersecurity | Art 15 |
| 10 | Implement a quality management system | Art 17 |
| 11 | Keep documentation (10 years) | Art 18 |
| 12 | Take corrective actions and inform | Art 20 |
| 13 | Cooperate with competent authorities | Art 21 |
| 14 | Appoint authorised representative (non-EU) | Art 22 |
| 15 | Undergo conformity assessment | Art 43 |
| 16 | Draw up EU declaration of conformity | Art 47 + Annex V |
| 17 | Affix CE marking | Art 48 |
| 18 | Register in the EU database | Art 49 + Annex VIII |
| 19 | Establish post-market monitoring | Art 72 |
| 20 | Report serious incidents | Art 73 |

---

## Deployer checklist (high-risk systems)

| # | Obligation | Ref |
|---|---|---|
| 1 | Use high-risk systems in accordance with instructions | Art 26 |
| 2 | Ensure human oversight | Art 26 |
| 3 | Monitor operation and keep logs | Art 26 |
| 4 | Cooperate with authorities | Art 26 |
| 5 | Conduct a fundamental rights impact assessment (public bodies / certain private deployers) | Art 27 |
| 6 | Ensure AI literacy of staff | Art 4 |

---

## Importer checklist

| # | Obligation | Ref |
|---|---|---|
| 1 | Verify provider compliance | Art 23 |
| 2 | Ensure conformity assessment done | Art 23 |
| 3 | Keep copies of documentation | Art 23 |
| 4 | Cooperate with authorities | Art 23 |

---

## Distributor checklist

| # | Obligation | Ref |
|---|---|---|
| 1 | Verify CE marking | Art 24 |
| 2 | Verify documentation and instructions | Art 24 |
| 3 | Cooperate with authorities | Art 24 |
| 4 | Take corrective action if non-compliant | Art 24 |

---

## GPAI model provider checklist

| # | Obligation | Ref |
|---|---|---|
| 1 | Provide technical documentation | Art 53(1)(a) + Annex XI |
| 2 | Comply with copyright policy | Art 53(1)(c) |
| 3 | Publish a training-data summary | Art 53(1)(d) |
| 4 | (If systemic risk) Manage systemic risk: evaluation, adversarial testing, mitigation, incident reporting, cybersecurity | Art 55 |

---

## Transparency obligations (all relevant actors)

| # | Obligation | Ref |
|---|---|---|
| 1 | Disclose AI interaction (chatbots) | Art 50(1) |
| 2 | Disclose emotion recognition / biometric categorisation | Art 50(2) |
| 3 | Disclose deepfakes | Art 50(3) |
| 4 | Disclose AI-generated public-interest text | Art 50(4) |

---

## Timeline of obligations

| Date | What applies |
|---|---|
| 2 Feb 2025 | Prohibited practices (Art 5), general provisions, definitions |
| 2 Aug 2025 | Notified bodies, GPAI models, governance, confidentiality |
| 2 Aug 2026 | Full application (all remaining provisions) |
| 2 Aug 2027 | Art 6(1) high-risk classification for Annex I product safety components |

See [timeline.md](timeline.md) for details.
