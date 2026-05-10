---
covers: The entry point for WisprSync documentation, organized into foundation, design, and implementation layers.
concepts: [documentation, foundation, design, implementation]
type: overview
---

# WisprSync Documentation

WisprSync documentation is organized into foundation, system design, and implementation layers. The foundation layer explains why the project exists, the design layer explains the data and export model, and the implementation layer explains how the current repo code produces and validates that structure.

---

## File Tree

```text
docs/
├── 00-overview.md              (this file)
├── 00-foundation/              Project motivation and ownership framing
├── 10-system-design/           Design-level data contracts and sync behavior
└── 20-implementation/          Code-specific exporter, validation, and setup docs
```

## Layers

### [Foundation](00-foundation/00-overview.md)

The foundation layer explains the project origin and data ownership motivation. Start here to understand the backstory before reading the data model.

### [System Design](10-system-design/00-overview.md)

The design layer describes the data model independent of Python modules. Start here to understand what Wispr Flow provides, what WisprSync treats as the canonical record, and how records are laid out under `data/`.

### [Implementation](20-implementation/00-overview.md)

The implementation layer maps the design onto the current repository. Read it when changing setup, source discovery, export, record writing, index generation, or validation behavior.
