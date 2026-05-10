---
covers: The data structure section for Wispr Flow source data and WisprSync output data.
concepts: [data-structure, source-shape, output-shape]
type: overview
---

# Data Structure

WisprSync's data model is easiest to understand in two stages: the shape Wispr Flow stores locally, and the shape WisprSync exports for ownership, search, validation, and analysis. This section keeps those shapes separate so source facts do not blur into output contracts.

---

## File Tree

```text
10-data-structure/
├── 00-overview.md                    (this file)
├── 10-wispr-flow-source-shape.md     Source SQLite tables, History fields, media, and Dictionary data
└── 20-wisprsync-output-shape.md      Canonical record shape, output tree, indexes, manifest, and placement rules
```

## Child Nodes

### [Wispr Flow Source Shape](10-wispr-flow-source-shape.md)

Documents what Wispr Flow stores locally: the primary SQLite database, `History` table, field groups, source media, and dictionary data.

### [WisprSync Output Shape](20-wisprsync-output-shape.md)

Documents what WisprSync exports: canonical records, `metadata.json`, transcript/media files, `data/` layout, JSONL indexes, manifest, run reports, and placement rules.
