---
observed_on: 2026-05-02
last_verified_on: 2026-05-10
platform: macOS
observed_app_bundle: /Applications/Wispr Flow.app
observed_app_version: 1.5.257
status: observed-reference
---

# Wispr Flow Local Storage Reference

This reference records where Wispr Flow local data has been observed on macOS and what structure WisprSync expects to find. Treat it as a dated observation, not a permanent contract. If Wispr Flow changes its app storage layout or SQLite schema, update this file and then update source discovery/export code to match.

## Observed App Version

Last verified local app bundle:

```text
/Applications/Wispr Flow.app
```

Observed bundle version on 2026-05-10:

```text
CFBundleShortVersionString  1.5.257
CFBundleVersion             1.5.257
```

This matters because Wispr Flow may change local storage paths or schema across app versions. When refreshing this reference, record both the date and the installed app version.

## Current Verification Snapshot

Last verified on 2026-05-10:

```text
active database   ~/Library/Application Support/Wispr Flow/flow.sqlite
History rows      16,864
History range     2024-09-04 14:34:52 UTC through 2026-05-10 18:14:38 UTC
```

Top observed `History.appVersion` values are historical row-level app versions, not necessarily the currently installed app version:

```text
1.0.66   1,406 rows
1.2.128    780 rows
1.5.113    731 rows
1.4.154    720 rows
1.2.145    534 rows
```

## Likely Storage Locations

Observed primary database candidates:

```text
~/Library/Application Support/Wispr Flow/flow.sqlite
~/Library/Application Support/Flow/flow.sqlite
```

Observed related app support folders:

```text
~/Library/Application Support/Wispr Flow
~/Library/Application Support/Flow
~/Library/Application Support/com.electron.wispr-flow.accessibility-mac-app
```

Observed log folder:

```text
~/Library/Logs/Wispr Flow
```

The primary WisprSync source is the SQLite database, not the full application support folder.

## Important Files Near The Database

The active app data folder may include:

```text
flow.sqlite
flow.sqlite-wal
flow.sqlite-shm
config.json
session.json
backups/
Cache/
Code Cache/
Cookies
Local Storage/
Session Storage/
sentry/
```

WisprSync should read from `flow.sqlite` through a safe read-only connection or SQLite backup. It should not export cookies, sessions, cache folders, telemetry folders, or raw Electron app state.

## Observed SQLite Tables

Observed tables include:

```text
CalendarEvents
Dictionary
FlowLensHistory
History
Links
MeetingVersions
Meetings
NoteImages
NoteVersions
Notes
Polish
RemoteNotifications
SequelizeMeta
```

`History` is the primary transcript table. `Dictionary` is exported as separate current-state vocabulary/snippet data. Other tables may exist but are not part of the initial canonical transcript export unless a future design explicitly includes them.

## Observed History Fields

Important observed `History` fields include:

```text
transcriptEntityId
asrText
formattedText
editedText
timestamp
audio
screenshot
additionalContext
status
app
url
duration
speechDuration
numWords
textboxContents
appVersion
editedTextStatus
language
detectedLanguage
micDevice
conversationId
pastedText
defaultAsrText
fallbackAsrText
defaultFormattedText
fallbackFormattedText
userEditMetaData
opusChunks
transcriptOrigin
platform
timezoneOffsetMinutes
needsUploading
shareType
isArchived
```

Observed source media:

```text
audio       WAV, PCM signed 16-bit, mono, 16000 Hz
screenshot  PNG
opusChunks  internal Opus packet JSON
```

WisprSync exports normal WAV audio and PNG screenshots when present and configured. It does not export `opusChunks` as a first-class artifact by default.

## Observed Dictionary Fields

Important observed `Dictionary` fields include:

```text
id
phrase
replacement
teamDictionaryId
lastUsed
frequencyUsed
remoteFrequencyUsed
manualEntry
createdAt
modifiedAt
isDeleted
source
observedSource
isSnippet
isStarred
```

Dictionary export is separate from transcript records because dictionary rows are vocabulary/snippet state, not transcript events.

## How To Re-Discover If This Changes

Use read-only inspection commands. Do not modify the Wispr Flow database.

Follow the self-healing refresh workflow in `.codex/skills/wisprsync/SKILL.md`.
The workflow is preferred over a fixed script because the point is to inspect the current machine, notice drift, and update this reference when Wispr Flow changes.

Search likely app data locations:

```sh
ls -la ~/Library/Application\ Support | rg -i 'wispr|flow|whisper'
ls -la ~/Library/Containers | rg -i 'wispr|flow|whisper'
mdfind 'kMDItemDisplayName == "*Wispr*"cd || kMDItemDisplayName == "*wispr*"cd || kMDItemDisplayName == "*Flow*"cd'
```

Inspect a candidate database:

```sh
sqlite3 -readonly "$DB" '.tables'
sqlite3 -readonly "$DB" 'select count(*) from History;'
sqlite3 -readonly "$DB" 'select min(timestamp), max(timestamp), count(*) from History;'
sqlite3 -readonly "$DB" 'pragma table_info(History);'
sqlite3 -readonly "$DB" 'pragma table_info(Dictionary);'
sqlite3 -readonly "$DB" \
  "select appVersion, count(*) from History where appVersion is not null and appVersion != '' group by appVersion order by count(*) desc limit 20;"
sqlite3 -readonly "$DB" \
  'select name, type, sql from sqlite_master where type in ("table","index") order by type,name;'
```

If a copied or live database reports locking issues, immutable read mode can help for inspection:

```sh
sqlite3 "file:$DB?mode=ro&immutable=1" 'select count(*) from History;'
```

For actual export from the live app database, prefer SQLite backup APIs over direct filesystem copies.

## Update Checklist

When Wispr Flow storage changes:

1. Update the `observed_on` date in this file.
2. Update `last_verified_on`.
3. Update the observed app bundle path and app version.
4. Update likely database paths and related folders.
5. Update observed table and field lists.
6. Update `docs/10-system-design/10-data-structure/10-wispr-flow-source-shape.md` if source concepts changed.
7. Update source discovery code and tests.
8. Run setup/export/validation against the new observed structure.
