# Firefox Extension Plan: Slang Normalizer

## Goal
Create a Firefox extension that lets a user start a session, select text on a page, and show the normalized meaning of the selected text.

## User Flow
1. User clicks the extension icon.
2. Popup shows a Start button.
3. User clicks Start to enable selection mode.
4. User highlights text on the web page.
5. Extension captures the selected text.
6. Extension sends the text to a local normalizer (or bundled model) and receives the meaning.
7. Extension shows the meaning in a small UI (tooltip, side panel, or popup result view).

## High-Level Architecture
- Popup UI
  - Start button
  - Status text (Ready, Listening, Result)
- Content Script
  - Listens for text selection events
  - Extracts selected text
  - Sends selection to background script
- Background Script
  - Coordinates state (started or stopped)
  - Calls the normalizer
  - Returns normalized meaning to content script
- Normalizer
  - Option A: Local HTTP service (Python model)
  - Option B: Embedded lightweight lookup table

## Suggested Folder Structure
- extension/
  - manifest.json
  - background.js
  - content.js
  - popup.html
  - popup.js
  - popup.css
  - icons/
- slang_normalizer/
  - model.joblib
  - normalize_text.py

## Manifest Permissions (Expected)
- activeTab
- scripting
- storage

## Data Flow
1. Popup sets started=true in storage.
2. Content script checks started state before reacting to selection.
3. On selection, content script sends text to background.
4. Background calls normalizer and returns meaning.
5. Content script renders meaning near selection.

## Normalizer Integration Options
- Option A: Local Service
  - Run a Python service that exposes /normalize
  - Extension calls http://localhost:PORT/normalize
  - Returns JSON: { "normalized": "..." }
- Option B: Inline Lookup
  - Export a JSON map of slang -> normalized
  - Bundle the map with the extension
  - Do not require a local server

## UI Output Options
- Tooltip near selection
- Side panel
- Popup result area

## MVP Steps
1. Build manifest, popup, and content script to detect selections.
2. Implement background coordination and state.
3. Pick integration method (local service or lookup map).
4. Display the normalized meaning in the page.

## Testing Plan
- Test with known dataset entries (English and Filipino).
- Verify that normal text is returned unchanged.
- Verify that the extension only reacts after Start.

## Load in Firefox (Temporary)
1. Open Firefox and go to about:debugging.
2. Click "This Firefox" in the left sidebar.
3. Click "Load Temporary Add-on…".
4. Select the file extension/manifest.json.
5. Click the extension icon, hit Start, then select text on any page.

Notes:
- Temporary add-ons are removed when Firefox restarts.
- If you edit the extension files, click "Reload" in about:debugging to apply changes.

## Run the Model Server (Required)
The extension now calls a local model endpoint at http://localhost:5000/normalize.

The server uses phrase-based normalization from the CSV so normal text stays unchanged
and only slang phrases are rewritten.

Start it in a terminal:
```bash
"/home/siege/Documents/NLP FP/.venv/bin/python" slang_normalizer/serve_model.py \
  --model slang_normalizer/model.joblib \
  --port 5000
```

## Open Questions
- Do you want the normalizer running locally or embedded?
- Should results auto-close or stay until dismissed?
- Should the extension handle multiple selections on a page?
