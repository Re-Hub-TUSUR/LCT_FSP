---
icon: lucide/book-open
---

# KADRY — documentation

Internal documentation for **KADRY**: how an employer finds a person, how a candidate confirms a grade, and what of that already exists in the code.

## Sections

| Section | What it is |
|---------|------------|
| [Product overview](product/overview.md) | What the platform does and for whom |
| [Page map](product/pages.md) | Screens, primary action, empty states |
| [BRD](business/brd/index.md) | Requirements of the current product |
| [Specification](business/specification.md) | Goals, MVP, extra scope, and non-goals |
| [Actors](actors/personas.md) | Candidate, employer, administrator |
| [Use cases](use-cases/index.md) | Scenarios by role |
| [User flows](user-flows/index.md) | Step-by-step paths with diagrams |
| [Glossary](glossary.md) | Category, bank, invitation, ATS |
| [Engineering](technical/index.md) | How the current monorepo is built |

## The platform in two sentences

The employer looks for a person in the bank and reaches out first. A candidate receives a **category** — specialization plus grade — after a test, not from the resume text. The company sees contacts after the candidate accepts an invitation.

The interface is a Russian **React SPA**. The API is **FastAPI** under `/api/v1`. Data sits in **PostgreSQL**.
