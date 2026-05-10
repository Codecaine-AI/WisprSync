---
covers: System design documentation for WisprSync data structure and synchronization behavior.
concepts: [data-model, export, sync]
type: overview
---

# System Design

The system design layer documents WisprSync as a data model and export process, not as a Python package. It defines the source shape in Wispr Flow, the normalized record shape used by WisprSync, and the file tree contracts that downstream tools can depend on.

---

## File Tree

```text
10-system-design/
├── 00-overview.md              (this file)
├── 10-data-structure/          Wispr Flow source shape and WisprSync output shape
└── 20-exporting/               Folder export and future export target ideas
```

## Design Scope

### What This Layer Owns

- The canonical meaning of a transcript record.
- The mapping from Wispr Flow source fields into portable data concepts.
- The exported `data/` layout and the guarantees made by that layout.
- Sync behavior around identity, updates, missing source rows, and collisions.

### What This Layer Does Not Own

- Python module boundaries.
- CLI argument parsing.
- Local setup mechanics.
- Validation implementation details.

## Child Nodes

### [Data Structure](10-data-structure/00-overview.md)

Explains the source and output data shapes as separate design documents: what exists in Wispr Flow, and what WisprSync exports.

### [Exporting](20-exporting/00-overview.md)

Explains the default folder export and how future targets could be layered without changing the canonical data shape.
