# Creative AI Studio

> A browser-based, single-file vibe-coding workbench for experimental drawing **and** experimental sound.

Creative AI Studio is a multi-workspace generative-art tool you open in your browser. It currently ships two workspaces:

- **Plotter Studio** — generates Processing (`.pde`) and p5.js sketches aimed at pen plotters and SVG output, with a live preview, multi-phase pipeline, and editable code.
- **Audio Studio** — generates compact realtime Web Audio DSP patches with live transport, hardcoded FX sliders, and AI-declared custom sliders, also fully editable.

Both share a single chat assistant (mode-aware), a single API-key surface, a multi-provider model router, customizable prompt templates, an inspiration panel with curated references, and live theme controls.

---

## Demo Artifact

A standalone Plotter-only build is available as a Claude artifact:
https://claude.ai/public/artifacts/169074ca-d958-45a8-b4da-fbecc1c51e4c

Use the local (API-Version) file for the full feature set.

---

## Quick Feature Overview

- Two workspaces in one file: **Plotter Studio** + **Audio Studio**
- Live p5.js preview, Processing code generation, realtime Web Audio playback
- **Vector export** — download the generated drawing as plotter-ready `.svg` or `.pdf` (true vector paths, not raster), alongside `.png` / `.html` / `.pde` / `.js`
- **Editable code panels** with chat-history sync — your edits feed back into the next AI request
- Multi-phase pipeline for both workspaces (concept → code → fix → explain)
- Mode-aware chat ("Plotter Assistant" / "Audio Assistant") with separate histories, shared model + key
- Mode-aware prompt-template editor with per-phase override
- AI-declared **custom sliders** for audio patches (`params` declaration in generated DSP)
- Hardcoded audio FX chain (Volume / Tone / Drive) applied post-DSP — always works regardless of generated code
- Inspiration panel with two tabs (**Plotter** + **Audio**) of curated references
- Light / dark theme, accent-color picker, text-color picker, **S / M / L letter-size**, dark theme defaults to white text, light theme defaults to dark text
- Multi-provider routing: **Anthropic**, **Google Gemini**, **Academic Cloud SAIA** (incl. optional CORS proxy), **OpenRouter** (one key, every provider)
- Auto-fix loop for both p5 runtime errors and audio compile errors
- Session save / load, debug overlay, per-phase model selection

---

## Run Locally with Your Own API Key

Open `plotter_studio.html` directly in a modern browser, paste an API key, pick a model, send a prompt.

Supported providers:

- **Anthropic** — [How to get an Anthropic API key](docs/anthropic-api-key.md)
- **Google Gemini** — [How to get a Gemini API key](docs/gemini-api-key.md)
- **Academic Cloud SAIA** — [How to get an Academic Cloud API key](https://docs.hpc.gwdg.de/services/ai-services/saia/index.html)
- **OpenRouter** — [Get an OpenRouter API key](https://openrouter.ai/settings/keys) (one key routes to Anthropic, OpenAI, Google, xAI, DeepSeek, Qwen and more — includes free-tier models, no CORS proxy needed)

This is the best path if you want full control over model choice, local edits, custom prompts, proxy settings, or future modifications.

---

## Quick Start

### What you need

- A modern browser
- At least one supported API key
- Optional: Python 3 if you want to run the local SAIA CORS proxy (required for Academic Cloud SAIA in some browsers)

### Installation

```bash
git clone https://github.com/BotAndis/Creative_AI_Studio.git
cd Creative_AI_Studio
```

Then open `plotter_studio.html` directly in your browser. There is no npm setup, build step, or bundler.

### Plotter Studio flow

1. Switch to the **Plotter Studio** nav tab.
2. Choose a model and paste an API key.
3. Enter a prompt describing the plotter sketch you want.
4. Send the prompt — concept, p5.js sketch, Processing code, and explanations populate automatically.
5. Switch between the Processing and p5.js code tabs, or hit **✎ Edit** to modify code in-place.
6. Save edits — your changes flow into the next request and the p5 preview re-runs.
7. Download `.pde`, `.js`, `.html`, a `.png` of the preview, or a plotter-ready **vector `.svg` / `.pdf`** of the drawing.

### Audio Studio flow

1. Switch to the **Audio Studio** nav tab.
2. Open the chat popup ("Audio Assistant") and describe a sound (e.g. *"warm ambient drone, 60 BPM"*).
3. Send — concept, DSP code, custom sliders, and explanation populate.
4. **Play** / **Stop** transport sits at the top of the Controls panel.
5. Use Volume / Tone / Drive sliders for always-on FX; tweak any AI-declared custom sliders for patch-specific parameters.
6. **✎ Edit** the DSP code, save — patch recompiles, sliders refresh, playback restarts if live.
7. Send another chat message to refine — the AI builds on your current code (and any edits) instead of restarting.
8. Download as `.js` or a self-contained `.html` player.

### Optional SAIA proxy

If browser CORS blocks requests to SAIA, run the local proxy:

```bash
python saia_proxy.py
```

Then set the proxy URL inside the app to:

```text
http://localhost:8765/
```
---

## Supported Providers

### Anthropic

Messages API: `https://api.anthropic.com/v1/messages`

### Gemini

`generateContent` API pattern. Documented through Google AI Studio with explicit key-based auth.

### Academic Cloud SAIA

OpenAI-compatible `chat-completions` flow, with an optional bundled Python CORS proxy.
The in-app model list mirrors the live SAIA catalogue (`/v1/models`); a stale saved model
falls back to the default automatically. Transient 429/5xx responses (model cold-start)
are retried with backoff both in the browser and in the proxy. Setting the key runs an
automatic connection test that lists the live models.

### OpenRouter

OpenAI-compatible `chat-completions` flow via `https://openrouter.ai/api/v1`.
Browser-direct (CORS-enabled) — no proxy required. Supports image attachments as
data-URI `image_url` blocks. Model ids are vendor-prefixed (`anthropic/claude-sonnet-5`,
`openai/gpt-5.5`, `deepseek/deepseek-v4-flash`, …); `:free` variants are rate-limited free-tier models.

---

## Project Information

- **Project type:** Single-file web app (vanilla HTML / CSS / JavaScript)
- **Main app file:** `plotter_studio.html`
- **Optional local helper:** `saia_proxy.py`
- **Runtime requirements:** Modern browser; Python 3 only if using the local proxy
- **License:** GPL-3.0

---

## Technical Guide

### Architecture

- Single-file vanilla JavaScript app
- No build system
- p5.js loaded through CDN (used for Plotter previews and the inspiration animation)
- Web Audio API (`AudioContext` + `ScriptProcessorNode`) for the audio engine
- Optional Python proxy: `saia_proxy.py`
- Most state, rendering, request dispatch, FX chain, particle backgrounds, and exports happen in the browser

Main files:

- `plotter_studio.html`
- `saia_proxy.py`

---

### Provider Routing and Request Dispatch

Provider selection is based on the chosen model ID:

- Vendor-prefixed models (`vendor/model`) → OpenRouter
- Gemini models → Gemini API
- Academic models → SAIA
- Other supported models → Anthropic Messages API

Core dispatcher: `callPhase()`

Provider-specific handlers:

- `callPhaseAcademic(...)`
- `callPhaseOpenRouter(...)`
- `callPhaseAnthropic(...)`
- `callPhaseGemini(...)`

One UI talks to multiple backends without changing the workflow.

---

### Multi-Phase Pipelines

**Plotter:** `concept` → `p5` → (auto-fix) → `pde` → (auto-fix) → `explain`

**Audio:** `audioconcept` → `audio` → (compile check / auto-fix) → `audioexp`

Key behaviour:

- `PIPELINE_ENABLED` controls the plotter pipeline; falls back to single-shot if disabled
- Follow-up context is carried through `chatHistory`
- p5 and Processing phases reuse the previous code via *MODIFY-existing* prompts
- The audio pipeline likewise reuses `audioState.code` once it exists, so a follow-up like *"make the bass deeper"* modifies the current patch rather than starting fresh

---

### Code Editing & History Sync

Both workspaces ship inline editing of generated code:

- `✎ Edit` swaps the read-only code display for a `<textarea>`
- `✓ Save` writes back to the authoritative store (`stored.p5code` / `stored.pdecode` for plotter, `audioState.code` for audio)
- `✕` discards edits
- Plotter saves also patch the most-recent assistant entry in `chatHistory` so the next concept-phase prompt sees the edited code
- Plotter p5 saves auto-re-run the sketch; audio saves auto-recompile the patch, refresh custom sliders, and restart playback if live
- Editing is blocked while a generation is in flight; starting a new generation cancels any open edit

This makes the loop *"AI generates → I tweak → AI builds on my tweaks"* close cleanly.

---

### Audio Engine

- `compileAudioDsp(code)` wraps user/AI code in a safe sandbox and returns `{ dsp, params }`
- DSP contract: `function dsp(t, beat, p)` — returns a sample in `[-1, 1]` (mono) or `[L, R]` (stereo); `p` holds live slider values
- Patches may declare `var params = [{name, label, min, max, value, step}, …]` to expose **AI-generated custom sliders** in the Patch Controls section
- Hardcoded FX chain runs *after* the generated code, so Volume / Tone / Drive always work:
  - Drive → `tanh(x * (1 + drive * 6))` saturation
  - Tone → one-pole low-pass filter
  - Volume → final gain
- Security blocklist strips comments first so DSP vocabulary (e.g. "Hann *window*") does not false-trigger; bans DOM / network / timers / dynamic `import()`

---

### Auto-Fix Loops

**p5 preview** — `runP5()` catches runtime / init errors, builds a focused repair prompt, retries.

**Audio compile** — `compileAudioDsp()` failures trigger a single targeted fix-prompt with the original code and the exact error.

---

### Prompt Templates and Mode-Aware Editing

The template editor swaps section sets based on the active assistant:

- **Studio** sections: Template Prompt (`base`), System Prompt, Concept Phase, p5.js Phase, Processing Phase, Explain Phase
- **Audio** sections: Audio System Prompt, Audio Concept Phase, Audio Code Phase, Audio Explanation Phase

Plotter prompts and audio prompts are stored independently in `promptTemplates`; the `adoptStringMap` helper makes prompt-key persistence forward-compatible.

The toolbar dropdowns mirror this split:

- Plotter: **dMA Creative Coding** / Edit Prompt Templates… / Custom + Prompt Templates…
- Audio: **Audio Base** / Edit Audio Prompts… / Custom Audio Prompts…

---

### Inspiration Panel

Two-tab curated reference page:

- **Plotter** — Drawing With Machines, Plotter Files, Turtletoy, Generated Space, Generative Art (erdavids), Generative Gestaltung
- **Audio** — DittyToy, MDN Web Audio, Gibber, Sonic Pi, Flok, Tone.js, SuperCollider, Orca, CCRMA/JOS DSP textbook

The background animation (p5 flow field + morphing form) is theme-aware: dark canvas with subtle amber strokes in dark mode, light cream canvas with deeper amber/cool/charcoal strokes in light mode.

---

### Theme + Text Controls

- Light / dark theme toggle on the top bar
- Accent-color picker (8 presets + custom)
- Text-color picker (6 presets + custom)
- **S / M / L letter-size** selector applies to chat bubbles, code display, how-it-works panels, inspiration card descriptions, and input
- Theme toggle auto-resets text color to the theme default (white in dark, near-black in light); manual picks persist across refreshes

---

### Token Tracking and Debug Overlay

Session-level counters track input/output tokens and request count.
The debug overlay shows request grouping, phase labels, request/response direction, provider + model metadata, and usage where available.

---

### State Model

- **Preferences** — `plotterStudio_prefs` stores model, settings, templates, accent, text color, text size, audio-template selection
- **Sessions** — `plotterStudio_sessions` stores full session snapshots (`chatHistory`, generated code, explanations, audio state, template state, tokens) plus optional `.txt` export

---

### Response Parsing and Rendering

Model responses are parsed into named sections:

- `### Processing code`
- `### p5 sketch`
- `### How it works (Processing)`
- `### How it works (p5.js)`

Audio responses are parsed via `parseAudioResponse()` into `{ code, explain }`.

---

### Vector Export (SVG / PDF)

The live preview draws to a raster `<canvas>`, which is useless for a pen plotter.
To export true vectors, the current p5 sketch is **re-run through the
[`p5.js-svg`](https://github.com/zenozeng/p5.js-svg) renderer** so every
`line`/`rect`/`ellipse`/`vertex` becomes a real SVG path:

- `renderCurrentSketchToSVG()` transforms `createCanvas(w, h)` → `createCanvas(w, h, p.SVG)`
  and runs the sketch in a **hidden, same-origin iframe with its own pinned p5 1.6.0**
  (p5.js-svg's renderer is broken against the app's p5 1.9.0 — it drops shapes /
  throws in `RendererSVG.resize`). The main app's p5 stays 1.9.0 and untouched.
- `.svg` download = the serialized vector document.
- `.pdf` download wraps that SVG via [`svg2pdf.js`](https://github.com/yWorks/svg2pdf.js) +
  [`jsPDF`](https://github.com/parallax/jsPDF) — still vector. If a sketch can't be
  re-rendered to SVG (e.g. WEBGL), PDF falls back to a raster embed of the canvas.
- All three export libraries load lazily from CDN on first use, so a user who never
  exports pays nothing.

Buttons live on the preview action bar, the fullscreen bar, and the
generation-complete chat message.

---

### Particle Background Systems

- **Plotter concept panel** — slow rotating "seeds" with hair strands, mouse-reactive
- **Audio concept panel** — concentric sound-wave ripples + central pulsing sine, mouse-spawns ripples
- **Preview panel idle** — 3-D particle cloud (or musical-note cloud on the audio side)
- **Inspiration overlay** — p5 flow field + morphing form, theme-aware colours

All four are independent of generation pipelines.

---

## Security Notes

- API keys are secrets
- never commit them
- never share screenshots with visible keys
- prefer server-side secret handling for public production deployments
- browser-direct key usage is fine for local testing, but less safe than a backend proxy

---

## Repository Files

- `plotter_studio.html` — the full app (Plotter Studio + Audio Studio + Inspiration)
- `saia_proxy.py` — optional local SAIA CORS proxy
- `docs/` — provider key setup guides

---

## License

Creative AI Studio: a multi-workspace tool for designing and managing generative pen-plotter artwork and realtime audio patches.
Copyright (C) 2026 BotAndis

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.
