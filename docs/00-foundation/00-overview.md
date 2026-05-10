---
covers: Foundation documentation for why WisprSync exists and what data ownership problem it addresses.
concepts: [foundation, backstory, data-ownership]
type: overview
---

# Foundation

The foundation layer captures the motivation for WisprSync: local data ownership for Wispr Flow transcript history. It is the place for project backstory and framing, separate from system design and implementation details.

---

## File Tree

```text
00-foundation/
├── 00-overview.md              (this file)
├── 10-backstory.md             Project origin, discovery process, and ownership motivation
├── 20-principles.md            Data ownership and local-first export principles
└── 30-boundaries.md            Non-affiliation, safety, and scope boundaries
```

## Child Nodes

### [Backstory](10-backstory.md)

Explains why WisprSync exists, how the local data was discovered, and why the project focuses on making already-local transcript data accessible and portable.

### [Principles](20-principles.md)

Captures the core product principles: data ownership, local-first export, transparent formats, explicit sync, and safe defaults.

### [Boundaries](30-boundaries.md)

Defines what WisprSync is not: not affiliated with Wispr Flow, not a restore tool, not a raw app backup, not automatic publishing, and not a permanent Wispr Flow schema contract.
