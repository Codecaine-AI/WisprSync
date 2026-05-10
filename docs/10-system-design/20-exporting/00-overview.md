---
covers: The exporting design section for folder export and future extension ideas.
concepts: [exporting, folder-export, targets]
type: overview
---

# Exporting

Exporting writes the canonical WisprSync data tree to a folder the user specifies. If the user wants cloud sync, they can choose a folder already managed by Dropbox, iCloud Drive, Google Drive, OneDrive, or another sync tool.

---

## File Tree

```text
20-exporting/
├── 00-overview.md                  (this file)
├── 10-folder-export.md             Write the export to a specified local folder
└── 30-export-targets.md            Extension model for future remote targets
```

## Export Modes

### [Folder Export](10-folder-export.md)

The base mode writes to a user-specified folder. This is the default and should remain the lowest-friction path. For easy cloud backup, the recommended output folder can live inside a normal cloud-synced directory such as Dropbox, iCloud Drive, Google Drive, or OneDrive.

### [Export Targets](30-export-targets.md)

Future targets, such as GitHub, S3, webhooks, or another remote store, are not implemented today. If they are added later, they should plug in after folder export without changing the source reading or canonical data shape.
