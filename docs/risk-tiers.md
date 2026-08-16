# Risk Tiers

The EU AI Act regulates AI through a **risk-based framework**. The level of regulatory burden scales with the risk an AI system poses to health, safety, and fundamental rights. There are four tiers.

---

## 1. Prohibited AI practices (unacceptable risk)

**Legal basis:** Article 5 · **Applies from:** 2 February 2025
**Penalty:** Up to EUR 35,000,000 or 7% of total worldwide annual turnover, whichever is higher (Article 99(3))

These practices are banned outright. They are considered to pose an unacceptable risk to fundamental rights and safety.

| Ref | Practice | Exceptions |
|---|---|---|
| Art 5(1)(a) | **Subliminal / manipulative / deceptive techniques** that materially distort behaviour and cause significant harm | None |
| Art 5(1)(b) | **Exploitation of vulnerabilities** (age, disability, social/economic situation) causing significant harm | None |
| Art 5(1)(c) | **Social scoring** — evaluation/classification based on social behaviour or predicted characteristics leading to detrimental treatment | None |
| Art 5(1)(d) | **Predictive policing** based solely on profiling or personality traits | AI supporting human assessment of criminal involvement based on objective, verifiable facts |
| Art 5(1)(e) | **Untargeted scraping of facial images** from the internet or CCTV to build facial recognition databases | None |
| Art 5(1)(f) | **Emotion inference** in workplace and education | Medical or safety reasons |
| Art 5(1)(g) | **Biometric categorisation** inferring sensitive attributes (race, politics, religion, sexual orientation, etc.) | Labelling/filtering of lawfully acquired biometric datasets; law-enforcement categorisation per Union law |
| Art 5(1)(h) | **Real-time remote biometric identification (RBI)** in publicly accessible spaces for law enforcement | Strictly limited objectives + prior judicial/administrative authorisation (Art 5(2)-(6)) |

> **Note on Art 5(1)(h):** Real-time RBI is not an absolute ban — it is a *highly restricted* use subject to strict necessity, listed objectives (search for missing persons; prevention of imminent threats/terrorist attacks; prosecution of listed serious crimes in Annex II), and prior authorisation.

---

## 2. High-risk AI systems

**Legal basis:** Articles 6, 7, 9–27, Annexes I, III
**Applies from:** 2 August 2026 (Article 6(1) and corresponding obligations from 2 August 2027)

High-risk systems carry the most extensive obligations. A system is high-risk if it falls into one of two categories:

### Category A — Safety components of regulated products (Article 6(1) + Annex I)

AI systems that are safety components of products (or are themselves products) covered by Union harmonisation legislation listed in **Annex I**, and that are required to undergo third-party conformity assessment under that legislation.

### Category B — Annex III areas (Article 6(2) + Annex III)

AI systems falling within the **8 areas** of Annex III, **unless** they do not pose a significant risk of harm, do not materially influence decision-making, and are not used for profiling (Article 6(3)).

| Area | Ref | Description |
|---|---|---|
| 1 | Annex III, point 1 | **Biometrics** — identification, categorisation, emotion recognition (verification systems excepted) |
| 2 | Annex III, point 2 | **Critical infrastructure** — safety components of digital, road, water, gas, heating, electricity |
| 3 | Annex III, point 3 | **Education & vocational training** — access, admission, learning evaluation, test monitoring |
| 4 | Annex III, point 4 | **Employment & workers** — recruitment, promotion, termination, task allocation, performance monitoring |
| 5 | Annex III, point 5 | **Essential services & benefits** — eligibility, creditworthiness (except small consumer credit), emergency dispatch |
| 6 | Annex III, point 6 | **Law enforcement** — risk assessment, polygraphs, evidence reliability, re-offending risk, profiling |
| 7 | Annex III, point 7 | **Migration, asylum & border control** — polygraphs, security/risk assessment, asylum applications, border surveillance |
| 8 | Annex III, point 8 | **Justice & democratic processes** — judicial assistance, election/voting influence |

### High-risk obligations (summary)

Providers of high-risk systems must comply with Articles 9–27, including:

- Risk management system (Art 9)
- Data and data governance (Art 10)
- Technical documentation (Art 11 + Annex IV)
- Record-keeping / automatic logs (Art 12)
- Transparency to deployers (Art 13)
- Human oversight (Art 14)
- Accuracy, robustness, cybersecurity (Art 15)
- Quality management system (Art 17)
- Conformity assessment (Art 43), EU declaration of conformity (Art 47), CE marking (Art 48)
- Registration in the EU database (Art 49)
- Post-market monitoring (Art 72) and serious-incident reporting (Art 73)

Deployers of high-risk systems must comply with Articles 26–27 (compliant use, human oversight, fundamental rights impact assessment).

---

## 3. Limited-risk / transparency obligations

**Legal basis:** Article 50 · **Applies from:** 2 August 2026

Certain AI systems carry specific transparency obligations even though they are not high-risk:

| Ref | Obligation |
|---|---|
| Art 50(1) | AI systems interacting directly with persons must inform users they are interacting with an AI system (unless obvious) |
| Art 50(2) | Emotion recognition / biometric categorisation systems must inform persons exposed to them |
| Art 50(3) | Deepfakes must be disclosed as artificially generated or manipulated |
| Art 50(4) | AI-generated text informing the public on matters of public interest must be disclosed as artificially generated |

---

## 4. Minimal-risk AI systems

**Legal basis:** Article 95 (voluntary) · **Applies from:** N/A (voluntary)

All other AI systems. There are no mandatory obligations, but the Act encourages voluntary application of the high-risk requirements through **codes of conduct** (Article 95).

---

## General-purpose AI (GPAI) models

**Legal basis:** Chapter V (Articles 51–56) · **Applies from:** 2 August 2025

GPAI models (e.g. large foundation models) are regulated separately:

- **All GPAI providers** (Art 53): technical documentation (Annex XI), copyright policy, training-data summary.
- **GPAI with systemic risk** (Art 55): model evaluation, adversarial testing, systemic-risk mitigation, serious-incident reporting, cybersecurity.
- **Systemic-risk threshold** (Art 51): presumed when training compute exceeds **10^25 FLOPs**.
- **Penalty** (Art 101): up to EUR 15,000,000 or 3% of total worldwide annual turnover, imposed by the Commission.

---

## Quick classification aid

Use the CLI's heuristic classifier for a first-pass indication:

```bash
eu-ai-act classify "facial recognition for recruitment"
# → LIKELY HIGH-RISK (matches Annex III areas 1 and 4)
```

> The classifier is a decision-support aid based on Annex III keywords. A formal legal assessment under Article 6 is required for definitive classification.
