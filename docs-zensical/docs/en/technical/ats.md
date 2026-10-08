---
icon: lucide/cable
---

# ATS

The full contract is `docs/ATS_INTEGRATION.md`. This page is the short loop.

An employer connects an ATS and polls it. Applications are screened with our filters: required skills, the salary band, and the city. The result is a score, a decision, and reasons. A tag, a note, and the score are written back to the ATS.

The platform's candidate bank does not change because of this flow. An external person does not become a KADRY user.

The provider now is `ATS_MODE=mock`: three demo applications inside the API. The `fixture` mode reads JSON with different field names and passes the same protocol. A live ATS with API documentation is one new adapter in `backend/app/integrations/ats/`, and the pipeline stays as it is.

Polling walks a cursor stored on the company connection. The same event does not queue a second screening. The cabinet page is «ATS».
