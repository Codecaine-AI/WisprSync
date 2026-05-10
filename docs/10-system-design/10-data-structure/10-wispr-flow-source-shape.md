---
covers: The local Wispr Flow source data shape that WisprSync reads from SQLite.
concepts: [wispr-flow, sqlite, history, dictionary]
---

# Wispr Flow Source Shape

Wispr Flow stores the local transcript corpus in a SQLite database. WisprSync treats that database as a read-only source and builds its canonical export from the `History` and `Dictionary` tables.

---

## Source Database

The main source database is usually:

```text
~/Library/Application Support/Wispr Flow/flow.sqlite
```

The primary table is `History`, keyed by:

```text
transcriptEntityId
```

Each `History` row represents one dictation or transcript event, plus surrounding app context and any available media.

## History Field Groups

Important `History` fields group into these concepts:

| Concept | Source fields |
| --- | --- |
| Identity | `transcriptEntityId` |
| Time | `timestamp`, `timezoneOffsetMinutes` |
| Transcript text | `asrText`, `formattedText`, `editedText`, `pastedText`, `defaultAsrText`, `fallbackAsrText`, `defaultFormattedText`, `fallbackFormattedText` |
| Status | `status`, `editedTextStatus`, `needsUploading`, `shareType`, `isArchived` |
| App context | `app`, `url`, `additionalContext`, `textboxContents`, `appVersion`, `platform`, `transcriptOrigin` |
| Language and device | `language`, `detectedLanguage`, `micDevice`, `conversationId` |
| Statistics | `duration`, `speechDuration`, `numWords` |
| Quality and edits | `e2eLatency`, `clientNetworkLatency`, `averageLogProb`, `formattingDivergenceScore`, `fallbackAsrDivergenceScore`, `fallbackFormattingDivergenceScore`, `usedFallbackAsr`, `usedFallbackFormatting`, `calledExternalAsr`, `userEditMetaData`, `numWordsCorrected`, `numDictionaryReplacements`, `hasRevertedAI` |
| Media | `audio`, `screenshot`, `opusChunks` |

## Source Media

Known source media:

```text
audio       WAV, PCM signed 16-bit, mono, 16000 Hz
screenshot  PNG
opusChunks  internal Opus packet JSON
```

WisprSync exports `audio` and `screenshot` as portable files when present. `opusChunks` is intentionally excluded from the canonical export because the inspected rows that include it also include normal WAV audio, and the WAV artifact is the stable downstream format.

## Dictionary Data

Wispr Flow also has a `Dictionary` table. WisprSync treats dictionary rows as current vocabulary/snippet state, not as transcript events.

Important dictionary fields include:

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

Dictionary rows are exported separately from `History` records.
