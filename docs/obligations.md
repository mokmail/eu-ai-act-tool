# Obligations by Actor

The EU AI Act assigns obligations to different **actors** in the AI value chain. This document maps each actor to its obligations, with legal citations. Use the CLI to explore interactively:

```bash
eu-ai-act actor provider
eu-ai-act actor deployer
eu-ai-act actor importer
eu-ai-act actor distributor
eu-ai-act actor authorised_representative
eu-ai-act actor operator
```

---

## Provider

**Definition (Article 3(3)):** A natural or legal person, public authority, agency or other body that develops an AI system or a general-purpose AI model, or that has one developed, and places it on the market or puts it into service under its own name or trademark, whether for payment or free of charge.

**Key obligations:**

| Ref | Obligation |
|---|---|
| Art 16 | Ensure high-risk systems comply with requirements (Arts 9–15); quality management system; technical documentation; logs; corrective actions; cooperation |
| Art 22 | Appoint an authorised representative (if established outside the EU) |
| Art 43 | Undergo conformity assessment |
| Art 47 | Draw up EU declaration of conformity |
| Art 48 | Affix CE marking |
| Art 49 | Register high-risk systems in the EU database |
| Art 50 | Comply with transparency obligations |
| Art 53 | GPAI providers: technical documentation, copyright policy, training-data summary |
| Art 55 | GPAI systemic-risk providers: model evaluation, adversarial testing, risk mitigation, incident reporting, cybersecurity |

---

## Deployer

**Definition (Article 3(4)):** A natural or legal person, public authority, agency or other body using an AI system under its authority, except where used in the course of a personal non-professional activity.

**Key obligations:**

| Ref | Obligation |
|---|---|
| Art 26 | Use high-risk systems in accordance with instructions; ensure human oversight; monitor operation; keep logs; cooperate with authorities |
| Art 27 | Conduct a fundamental rights impact assessment (public bodies and certain private deployers of high-risk systems) |
| Art 50 | Comply with transparency obligations |
| Art 4 | Ensure AI literacy of staff |

---

## Importer

**Definition (Article 3(6)):** A natural or legal person established in the Union that places on the market or puts into service an AI system or GPAI model bearing the name or trademark of a person established outside the Union.

**Key obligations:**

| Ref | Obligation |
|---|---|
| Art 23 | Verify provider compliance; ensure conformity assessment done; keep copies of documentation; cooperate with authorities |

---

## Distributor

**Definition (Article 3(7)):** A natural or legal person in the supply chain, other than the provider or importer, that makes an AI system or GPAI model available on the Union market.

**Key obligations:**

| Ref | Obligation |
|---|---|
| Art 24 | Verify CE marking, documentation, instructions; cooperate with authorities; take corrective action if non-compliant |

---

## Authorised Representative

**Definition (Article 3(5)):** A natural or legal person established in the Union who has received a written mandate from a provider to act on its behalf regarding specified tasks.

**Key obligations:**

| Ref | Obligation |
|---|---|
| Art 22 | Act on behalf of non-EU providers; keep documentation; cooperate with authorities |

---

## Operator (umbrella term)

**Definition (Article 3(8)):** A provider, deployer, importer, distributor, or authorised representative.

**Key obligations:**

| Ref | Obligation |
|---|---|
| Art 99 | Subject to penalties for non-compliance |

---

## Responsibilities along the value chain

**Article 25** governs responsibilities along the AI value chain. Key points:

- A distributor, importer, deployer, or other third party is treated as a **provider** if they place the AI system on the market or put it into service under their own name or trademark, or substantially modify an existing high-risk system.
- This means the "provider" label can shift along the chain depending on who modifies or rebrands the system.

---

## Penalties for non-compliance

| Ref | Violation | Fine |
|---|---|---|
| Art 99(3) | Prohibited practices (Art 5) | Up to EUR 35M or 7% of worldwide turnover |
| Art 99(4) | Provider/AR/importer/distributor/deployer/notified-body/transparency obligations | Up to EUR 15M or 3% of worldwide turnover |
| Art 99(5) | Incorrect/misleading information to authorities | Up to EUR 7.5M or 1% of worldwide turnover |
| Art 99(6) | SMEs/start-ups | Fines may be capped at the lower amount |
| Art 100 | Union institutions/bodies/agencies | Fines set by the Commission |
| Art 101 | GPAI providers (Art 53/55) or failure to comply with Commission requests | Up to EUR 15M or 3% of worldwide turnover (imposed by Commission) |
