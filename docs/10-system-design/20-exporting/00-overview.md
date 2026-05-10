---
covers: The exporting design section for folder export, optional GitHub sync, and future export targets.
concepts: [exporting, folder-export, git-sync, targets]
type: overview
---

# Exporting

Exporting starts with the simplest useful behavior: write the canonical WisprSync data tree to a folder the user specifies. Other sync options should wrap that folder export instead of changing the core record, index, manifest, and run-report structure.

---

## File Tree

```text
20-exporting/
├── 00-overview.md                  (this file)
├── 10-folder-export.md             Write the export to a specified local folder
├── 20-github-git-export.md         Optional Git/GitHub sync layered on top of folder export
└── 30-export-targets.md            Extension model for future remote targets
```

## Export Modes

### [Folder Export](10-folder-export.md)

The base mode writes to a user-specified folder. This is the default and should remain the lowest-friction path. For easy cloud backup, the recommended output folder can live inside a normal cloud-synced directory such as Dropbox, iCloud Drive, Google Drive, or OneDrive.

### [GitHub Git Export](20-github-git-export.md)

The Git/GitHub mode treats GitHub as the cloud sync layer. It should be a separate layer that commits and pushes the folder export, not a replacement for the folder export.

### [Export Targets](30-export-targets.md)

Future targets, such as S3 or another remote store, should plug in after the folder export contract is clear. The source reading and canonical data shape should stay shared.
