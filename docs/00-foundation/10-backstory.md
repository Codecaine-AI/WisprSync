---
covers: The project origin story for WisprSync and the local data ownership problem it addresses.
concepts: [backstory, data-export, ownership]
---

# Backstory

WisprSync started from a simple data access problem.

I use Wispr Flow heavily and wanted a full export of my transcript history and audio so I could analyze it, back it up, and keep it accessible outside the product.

I reached out to support and asked for a full data export.

The answer was: 

"I've recorded your feature request for the product team. In the meantime, the only option is manually copying transcripts from your History or downloading individual audio files."

This was not a feasible option given my over 600K words transcribed.

At first, that seemed annoying but understandable.
    - If all historical transcripts and audio lived only in Wispr Flow's cloud systems
    - A full export feature could involve real product work and costs 
      - Egress, permissions, packaging, retries, support, etc.

Then I looked more closely at the local app.

Wispr Flow has local history behavior for features such as transcript retries and normal app operation.

I asked Codex to inspect the local machine and find out whether the transcript data was actually present there.

It was.

The local Wispr Flow data included a SQLite database containing:
- Transcript history
  - Formatted text
  - Raw ASR text
  - Edited and pasted text
  - App context
  - Timestamps
  - Audio of transcript
  - Screenshots with transcript
- Dictionary data

Everything I needed and more was already on **MY** machine

That changed the shape of the problem and pissed me off.

- If the data is already stored locally, then the product clearly has an easy path to help users export it
  - They do not expose this knowledge anywhere
  - When I reached out to support directly, I was told a full export was not possible
  - With one Codex prompt, the local data was discoverable and exportable
- Instead, the "only option" is one-by-one export
  - That makes it extremely hard to export your data and transition to another provider.
  - To me, that is clearly anti-competitive lock-in, or at minimum a product choice that does not actually care about the user experience of data ownership.
  - It feels like feigning data access while making real data access unnecessarily difficult.
- Users do not have clear ownership of data that already exists on their own device.
  - That is fucked.

If the data is already on your machine, you should be able to inspect it, back it up, analyze it, and move it into whatever workflow you prefer.

The missing piece was not access to a remote export API, but a clear local exporter that writes the data into a folder you control.

WisprSync is that exporter.

It reads the local Wispr Flow database, extracts the transcript records and related artifacts, and writes them into a documented data folder with metadata, transcript text files, media files, indexes, a manifest, and run reports.
