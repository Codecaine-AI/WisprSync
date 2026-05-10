---
covers: The project origin story for WisprSync and the local data ownership problem it addresses.
concepts: [backstory, data-export, ownership]
---

# Backstory

WisprSync started from a simple data access problem.

I use Wispr Flow heavily and wanted a full export of my transcript history and audio so I could analyze it, back it up, and keep it accessible outside the product.

I reached out and asked for a full data export.

The answer was that there was no bulk export option.

The available path was to export transcripts and audio one at a time, and the request was noted as a feature request.
    - This was not a feasible option given my over 600K words transcribed

At first, that seemed annoying but understandable.
    - If all historical transcripts and audio lived only in Wispr Flow's cloud systems, a full export feature could involve real product work: 
      - Egress, permissions, packaging, retries, support, etc.

Then I looked more closely at the local app.

Wispr Flow has local history behavior for features such as transcript retries and normal app operation.

I asked Codex to inspect the local machine and find out whether the transcript data was actually present there.

It was.

The local Wispr Flow data included a SQLite database with transcript history, formatted text, raw ASR text, edited and pasted text, app context, timestamps, dictionary data, and some audio and screenshot blobs.

That changed the shape of the problem.

The data needed for a personal export was already on the device.

This pissed me off.

- If the data is already stored locally, then the product clearly has an easy path to help users export it.
  - They could tell users where the local data is and how to access it if they don't want to build a button
  - They do not expose that path anywhere obvious.
  - The location and structure are not documented on their support pages.
  - When I reached out to support directly, I was told a full export was not possible.
  - With one Codex prompt, the local data was discoverable.
- Instead, the product exposes one-by-one export while the practical full-export data remains hidden in local storage.
  - That makes it extremely hard to export your data and transition to another provider.
  - To me, that is clearly anti-competitive lock-in, or at minimum a product choice that does not actually care about the user experience of data ownership.
  - It feels like feigning data access while making real data access unnecessarily difficult.
- Users do not have clear ownership of data that already exists on their own device.
  - That is fucked.

The missing piece was not access to a remote export API, but a clear local exporter that writes the data into a folder you control.

WisprSync is that exporter.

It reads the local Wispr Flow database, extracts the transcript records and related artifacts, and writes them into a documented data folder with metadata, transcript text files, media files, indexes, a manifest, and run reports.

The point is data ownership.

If the data is already on your machine, you should be able to inspect it, back it up, analyze it, and move it into whatever workflow you prefer.
