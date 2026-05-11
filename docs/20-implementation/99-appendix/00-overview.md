---
covers: Operational documentation for local WisprSync setup and configuration.
concepts: [setup, config, operations]
type: overview
---

# Appendix: Overview

The appendix contains operational documentation that supports the implementation but is not part of the core data model. It covers local setup, source discovery, configuration, and repo-local command expectations.

---

## File Tree

```text
99-appendix/
├── 00-overview.md              (this file)
├── 10-setup-workflow.md        Local setup, source discovery, config, commands, and scheduling
└── 20-macos-scheduler-permissions.md
                                macOS LaunchAgent runner and privacy-permission implementation
```

## Child Nodes

### [Setup Workflow](10-setup-workflow.md)

Documents how a local WisprSync repo discovers the Wispr Flow database, writes `.wisprsync/config.json`, and exposes setup/sync commands.

### [macOS Scheduler Permissions](20-macos-scheduler-permissions.md)

Documents how the macOS LaunchAgent runs through a dedicated local runner app
and private Python runtime so privacy access does not need to be granted to a
shared Python interpreter.
