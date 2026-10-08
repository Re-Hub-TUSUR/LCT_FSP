---
icon: lucide/server
---

# Engineering

This section describes the current monorepo. If the code disagrees with the [BRD](../business/brd/index.md), the requirement stays in the product, and the code fact is on [implementation status](implementation-status.md).

Developer sources this site does not replace:

- `docs/ARCHITECTURE.md` — layers and import rules. Its API status table is stale and is not copied here.
- `docs/FSP_INTEGRATION.md` — the FSP ID contract.
- `docs/ATS_INTEGRATION.md` — the ATS connector.
- `docs/ADMIN.md` — admin tabs.

| Page | About |
|------|--------|
| [Architecture](architecture.md) | Two deployment units and the layers |
| [API](api.md) | The `/api/v1` prefix and the modules |
| [Data model](data-model.md) | Tables that exist in the code |
| [Local start](local-start.md) | How to run the project |
| [FSP ID](fsp-id.md) | Linking to the registry |
| [ATS](ats.md) | Polling an external ATS with our filters |
| [Implementation status](implementation-status.md) | Done, partial, absent |
