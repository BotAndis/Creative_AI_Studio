# Generative Plotter Studio

## About

Plotter Studio is a browser-based vibe coding tool for Experimental drawing and generative art. Designed to create pen-plotter svgs, designed to generate editable creative code for Processing and p5.js sketches with live preview support, customizable Prompt presets, Multi-phase pipeline with debug tooling. Usable with API or as an embedded AI Artifact.

---

## Quick Feature Overview

- Single-file browser app
- No build system
- Live p5.js preview
- Processing code generation
- Optional explanation panels
- Multiple provider support
- Proxy support for SAIA
- Downloadable generated outputs
- Multi-phase pipeline with debug tooling

---

## Demo Artifact:
https://claude.ai/public/artifacts/50c651e4-8f2b-423d-9ff4-f8f5df0fc706

---

## Run Locally with Your Own API Key

You open the HTML file locally in your browser and use your own provider key.

Supported providers include:

- Anthropic [How to get a Anthropic API key](docs/anthropic-api-key.md)
- Google Gemini [How to get a Gemini API key](docs/gemini-api-key.md)
- Academic Cloud SAIA [How to get a Academic Cloud API key](https://docs.hpc.gwdg.de/services/ai-services/saia/index.html)
- LUHKI2 API KEY ??? [Maybe comming soon, I doubt it]

This is the best option if you want control over model choice, local edits, custom prompts, proxy settings, or future modifications. Gemini supports API-key-based integration through Google AI Studio, and Anthropic supports its Messages API for direct app integration.

---

## Quick Start

### What you need

- A modern browser
- At least one supported API key:
  - Anthropic
  - Google Gemini
  - Academic Cloud SAIA
- Optional: Python 3 if you want to run the local SAIA CORS proxy (must for Academic Cloud SAIA)

### Installation

Clone the repository:

```bash
git clone [https://github.com/BotAndis/Plotter-Studio.git](https://github.com/BotAndis/Plotter-Studio.git)
cd Plotter-Studio
```

Then open this file directly in your browser:

- `plotter_studio.html`

There is no npm setup, build step, or bundler.

### Local use flow

1. Open the app in your browser.
2. Choose a model from the model selector.
3. Paste your API key into the key field and click **Set**.
4. Enter a prompt describing the plotter sketch you want.
5. Send the prompt.
6. Review the live preview.
7. Switch between generated Processing code, p5.js code, and explanation panels.
8. Download the outputs you want, such as `.pde`, `.js`, `.html`, or preview `.png`.

### Optional SAIA proxy

If browser CORS blocks requests to SAIA, run the local proxy:

```bash
python saia_proxy.py
```

Then set the proxy URL inside the app to:

```text
http://localhost:8765/
```

### Where keys are stored

Keys and preferences are stored client-side in browser storage according to the app design.

Do **not** share:

- screenshots with visible keys
- exported browser profiles
- synced browser data you do not trust
- raw localStorage dumps

---

## Supported Providers

Plotter Studio can route requests to different providers depending on the selected model.

### Anthropic

Anthropic requests use the Messages API at:

```text
[https://api.anthropic.com/v1/messages](https://api.anthropic.com/v1/messages)
```

Anthropic documents the Messages API as the main multi-turn interface for Claude model calls.

### Gemini

Gemini requests use Google's `generateContent` API pattern. Google documents API key usage through Google AI Studio and explicit key-based authentication for Gemini API requests.

### Academic Cloud SAIA

SAIA is handled through an OpenAI-compatible chat-completions flow in this project, optionally through the included local proxy if direct browser requests run into CORS problems.

---

## Project Information

- **Project type:** Single-file web app (vanilla HTML/CSS/JavaScript)
- **Main app file:** `plotter_studio.html`
- **Optional local helper:** `saia_proxy.py` (Python proxy for SAIA/CORS)
- **Runtime requirements:** Modern browser, and Python 3 only if using the local proxy
- **License:** MIT

---

## Technical Guide

This section explains how the app is structured internally.

### Architecture

- Single-file vanilla JavaScript app
- No build system
- p5.js loaded through CDN
- Optional Python proxy: `saia_proxy.py`
- Most state, rendering, request dispatch, and exports happen in the browser

Main files:

- `plotter_studio.html`
- `saia_proxy.py`

---

### Provider Routing and Request Dispatch

Provider selection is based on the chosen model ID:

- Gemini models → Gemini API
- Academic models → SAIA
- Other supported models → Anthropic Messages API

Core dispatcher:

- `callPhase()`

Provider-specific handlers:

- `callPhaseAcademic(...)`
- `callPhaseAnthropic(...)`
- `callPhaseGemini(...)`

This lets one UI talk to multiple backends without changing the frontend workflow.

---

### API Endpoints and Auth

#### Anthropic

Endpoint:

```text
[https://api.anthropic.com/v1/messages](https://api.anthropic.com/v1/messages)
```

Typical headers:

- `anthropic-version: 2023-06-01`
- `x-api-key: <key>`
- browser-direct mode may also include a special direct-browser header depending on implementation strategy

Typical request body includes:

- `model`
- `system`
- `messages`
- `max_tokens`
- optional `thinking`

Anthropic’s Messages API is the documented structure for Claude conversations.

#### Gemini

Endpoint pattern:

```text
https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent
```

Auth:

- `x-goog-api-key: <key>` or equivalent documented key-based usage

Typical request body includes:

- `contents[]`
- `systemInstruction`
- `generationConfig`

Google documents Gemini API key management in Google AI Studio and explicit key-based integration patterns.

#### Academic Cloud SAIA

Base endpoint:

```text
[https://chat-ai.academiccloud.de/v1/chat/completions](https://chat-ai.academiccloud.de/v1/chat/completions)
```

Auth:

- `Authorization: Bearer <key>`

Body is OpenAI-compatible:

- `model`
- `messages`
- `temperature`
- `max_tokens`

If proxy is configured:

- localhost proxy mode appends `/v1/chat/completions`
- non-local proxy mode can prepend the full SAIA URL

---

### Multi-Phase Pipeline

The full app can split one generation into focused phases:

1. `concept`
2. `p5`
3. `pde`
4. `explain`

Important behavior:

- `PIPELINE_ENABLED` controls this mode
- If disabled, the app falls back to a single-shot generation path
- Follow-up context is carried through `chatHistory`
- p5 and Processing phases can reuse previous code with modify-not-rewrite prompts

This helps produce cleaner results than forcing concept, preview, Processing, and explanation into one raw response.

---

### Follow-Up Context and History

`chatHistory` accumulates prior turns so follow-up prompts can modify the current sketch instead of restarting from zero.

Behavior includes:

- trimming older turns with `MAX_HISTORY_TURNS`
- adding summary markers when earlier context is compressed
- appending combined output back into history in pipeline mode
- preserving iterative quality for prompts like:
  - “make it denser”
  - “add a Voronoi layer”
  - “reduce pen lifts”
  - “make it more architectural”

---

### Auto-Fix Runtime Loop

When p5 preview execution fails:

- `runP5()` captures the runtime or init error
- if `AUTOFIX_ENABLED` is active:
  - the app builds a focused repair prompt
  - includes the error and original code
  - calls `callPhase('p5', ...)`
  - retries the corrected sketch

This exists to make preview iteration less fragile during experimentation.

---

### Debug Overlay

The debug overlay is the main internal trace panel for development.

It can show:

- request grouping
- phase labels
- request/response direction
- provider metadata
- model metadata
- usage and token-related info where available

Typical interactions:

- open via the ⚙ button
- close with the ✕ button
- close with Escape
- close by clicking outside the panel

---

### Token Tracking

Session-level counters are tracked in memory:

- `sessionTokens.input`
- `sessionTokens.output`
- `sessionTokens.requests`

Where providers expose usage fields, those values are folded into the session totals.

---

### State Model

#### Preferences

`saveState()` stores only user preferences in `plotterStudio_prefs`, such as:

- selected model
- settings toggles
- selected template
- custom template text

It intentionally does **not** store full working session content.

#### Full session snapshots

`saveCurrentSession()` stores richer session data in `plotterStudio_sessions` and can export a `.txt` session file.

Stored session data may include:

- `chatHistory`
- generated code
- explanations
- current model
- settings
- template state
- token totals

This separation keeps preferences lightweight while still allowing richer session saving when needed.

---

### Settings and Generation Controls

The app includes settings that change prompt construction and runtime behavior.

Examples:

- output toggles for Processing, p5, and explanation blocks
- text-toggle requirements
- line-label toggle
- reseed requirement
- slider/UI control requirements
- pipeline mode toggle
- auto-fix toggle

These settings affect prompt construction through functions such as:

- `buildSysPrompt(...)`
- `buildPhasePrompt(...)`

They also affect what gets rendered and downloaded later.

---

### Response Parsing and Rendering

Model responses are parsed into named sections such as:

- `### Processing code`
- `### p5 sketch`
- `### How it works (Processing)`
- `### How it works (p5.js)`

Parsed sections update:

- code tabs
- explanation panels
- p5 live preview
- download actions

This structured parsing is what makes one response usable across multiple panels.

---

### Particle Background System

The interface also includes a separate particle animation layer.

Characteristics:

- raw canvas 2D rendering
- faux 3D projection
- mouse interaction
- independent from generation pipeline logic

This system is visual only and does not affect provider calls or code generation.

---

## Note on Artifact HTML

`plotter_studio_artifact.html` is not part of the recommended workflow.  
Use `plotter_studio.html` as the primary app file.

---

## Security Notes

- API keys are secrets
- never commit them
- never share screenshots with visible keys
- prefer server-side secret handling for public production deployments
- browser-direct key usage is fine for local testing, but less safe than a backend proxy

Google explicitly documents API-key-based Gemini integration, while also noting that hardcoding keys should only be temporary.

---

## Repository Files

- `plotter_studio.html` — full feature app
- `saia_proxy.py` — optional local SAIA CORS proxy

---

## License

Plotter-Studio: A specialized tool for designing and managing pen plotter artwork.
Copyright (C) 2026 BotAndis

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
