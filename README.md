# Generative Plotter Studio

Plotter Studio is a browser-first AI creative coding studio for plotter workflows.
It generates **Processing (Java)** and **p5.js** sketches from natural-language prompts.

---

## 1) Simple Guide (Install + Use)

This section is for quick start without technical internals.

### What you need

- A modern browser
- At least one API key (Anthropic, Gemini, or Academic Cloud SAIA)
- Optional: Python 3 if you want to run the local SAIA CORS proxy

### Installation

1. Clone:

```bash
git clone https://github.com/BotAndis/Plotter-Studio.git
cd Plotter-Studio
```

2. Open one file directly in your browser:

- `plotter_studio.html` (full version)
- `plotter_studio_artifact.html` (artifact-focused version)

No npm, no build step, no bundler.

### Direct Claude artifact access

You can open the public artifact directly here:

https://claude.ai/public/artifacts/9be3b773-3073-400b-a249-96ee83578ad3

⚠️ Note: via this direct public artifact link, API-based features do not work.

### Optional: SAIA proxy (only if CORS blocks browser requests)

```bash
python saia_proxy.py
```

Then set CORS Proxy URL inside the app to:

```text
http://localhost:8765/
```

### Simple usage flow

1. Open app.
2. Pick a model in the model selector.
3. Enter API key in key area, click **Set**.
4. Write prompt and send.
5. Preview generated p5 sketch.
6. Switch tabs to review Processing/p5 code and explanations.
7. Download output (`.pde`, `.js`, `.html`, preview `.png`).

### Where keys are stored

Keys and preferences are stored in browser `localStorage` (client-side).
Do **not** share browser profile exports or screenshots with visible keys.

---

## 2) Technical Guide (Detailed)

This section explains API calls, pipeline behavior, history, debug logs, settings, state handling, and auto-fix.

### 2.1 Architecture

- Single-file vanilla JS app (`plotter_studio.html` / `plotter_studio_artifact.html`)
- No build system
- p5.js loaded via CDN
- Optional tiny Python proxy: `saia_proxy.py`
- Heavy UI + logic in-browser (state, rendering, request dispatch, exports)

### 2.2 Provider routing and request dispatch

Provider is chosen by model ID:

- Gemini models → Gemini API
- Academic models → SAIA (OpenAI-compatible) API
- Otherwise → Anthropic Messages API

Core phase dispatcher:

- `callPhase()` decides provider and dispatches to:
  - `callPhaseAcademic(...)`
  - `callPhaseAnthropic(...)`
  - `callPhaseGemini(...)`

### 2.3 API endpoints, auth, and request shape

#### Anthropic

- Endpoint: `https://api.anthropic.com/v1/messages`
- Headers:
  - `anthropic-version: 2023-06-01`
  - `x-api-key: <key>` (if set)
  - `anthropic-dangerous-direct-browser-access: true` (browser direct mode)
- Body includes `model`, `system`, `messages`, `max_tokens` (+ optional `thinking`)

#### Gemini

- Endpoint: `https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent`
- Header: `x-goog-api-key`
- Body includes:
  - `systemInstruction`
  - `contents[]`
  - `generationConfig`
- Anthropic-shaped history is converted into Gemini `contents` format

#### Academic Cloud (SAIA)

- Base endpoint: `https://chat-ai.academiccloud.de/v1/chat/completions`
- Header: `Authorization: Bearer <key>`
- Body is OpenAI-compatible (`model`, `messages`, `temperature`, `max_tokens`)
- If proxy is configured:
  - localhost proxy mode appends `/v1/chat/completions`
  - non-local proxy prepends full SAIA URL

### 2.4 Multi-phase pipeline internals

Pipeline mode splits one generation into focused phases:

1. `concept`
2. `p5`
3. `pde`
4. `explain`

Important behavior:

- `PIPELINE_ENABLED` controls this mode.
- If disabled (or too few selected outputs), app falls back to single-shot generation.
- Concept phase carries follow-up context via `chatHistory`.
- p5/pde phases can use existing generated code (`stored.p5code` / `stored.pdecode`) with **modify-not-rewrite** prompts.

### 2.5 Follow-up context and history logic

`chatHistory` accumulates conversation context used for follow-up quality.

- History trimming keeps recent turns (`MAX_HISTORY_TURNS`) and inserts a summary marker when old turns are trimmed.
- In pipeline mode, after all phases complete, combined output is pushed to history.
- In legacy single-shot mode, user/assistant turns are also appended per call.

### 2.6 Auto-fix runtime error loop

When p5 preview execution fails:

- `runP5()` captures runtime/init error
- If auto-fix setting is enabled (`AUTOFIX_ENABLED`):
  - app builds a focused fix prompt containing error + original code
  - app calls `callPhase('p5', fixPrompt, ...)`
  - corrected sketch is re-run

This exists both in pipeline flow and single-shot flow.

### 2.7 Debug system (behind-the-scenes transparency)

Debug overlay: `#dbg-overlay`.

- Open via ⚙ button
- Close via:
  - ✕ button
  - Escape key
  - clicking overlay background
- Logs include generation grouping, phase labels, directions (request/response), and metadata (provider/model/usage)

This is the main developer-facing trace view for request/response internals.

### 2.8 Token tracking and usage

Session token counters are tracked in-memory:

- `sessionTokens.input`
- `sessionTokens.output`
- `sessionTokens.requests`

Counters are updated from provider usage fields where available.

### 2.9 State model: preferences vs session data

#### `saveState()` (preferences only)

`saveState()` persists only user preferences in `plotterStudio_prefs`, such as:

- selected model
- settings toggles
- selected template
- custom template content

It intentionally does **not** persist full session/chat/code data.

#### `saveCurrentSession()` (full session snapshot)

`saveCurrentSession()` stores full session data in `plotterStudio_sessions` and exports a `.txt` session file.
Stored data includes:

- `chatHistory`
- generated code/explanations (`stored` object)
- model + settings
- template state
- token totals

### 2.10 Development settings and generation controls

Settings control what is generated and how:

- Output toggles (Processing, p5, explanation blocks)
- UI-control requirements (text toggle, line label toggle, reseed, sliders)
- Pipeline mode toggle
- Auto-fix toggle

These toggles alter prompt construction (`buildSysPrompt` / `buildPhasePrompt`) and downstream runtime behavior.

### 2.11 Response parsing and panel rendering

Model responses are parsed into named sections:

- `### Processing code`
- `### p5 sketch`
- `### How it works (Processing)`
- `### How it works (p5.js)`

Parsed content updates:

- code tabs
- explanation panels
- p5 live preview
- download actions

### 2.12 Particle background system

The app includes a dedicated particle animation IIFE:

- raw canvas 2D rendering
- faux 3D perspective projection
- mouse gravity interaction

This runs independently of generation pipeline logic.

---

## 3) Full vs Artifact Version (Detailed Difference)

`plotter_studio_artifact.html` is a stripped-down sibling, **not** a replacement for `plotter_studio.html`.

### What stays

- Full UI (dark theme, particle animation, layout)
- Model picker + API key input + proxy URL
- Single prompt → single generation (legacy single-shot path)
- p5.js live preview with reseed, sliders, fullscreen, download (SVG/PNG)
- Processing code panel + download
- Explanation panels
- dMA template system
- localStorage for API key + basic prefs (try/catch, graceful failure)

### What gets cut

- ❌ Pipeline mode + concept/pde/explain phases
- ❌ Chat history accumulation + follow-up context
- ❌ Session save/load panel
- ❌ Debug overlay (⚙ and full logging)
- ❌ Auto-fix toggle
- ❌ Export (chat history, debug log) buttons
- ❌ Token tracking
- ❌ Session name input

### Result

- Roughly half the code size
- One prompt = one fresh generation
- No state between runs

---

## 4) Security Notes

- API keys are secrets.
- Never commit keys.
- Never share screenshots exposing keys.
- Prefer server-side secret handling for production deployments.

---

## 5) Repository Files

- `plotter_studio.html` — full feature app
- `plotter_studio_artifact.html` — artifact-focused variant
- `saia_proxy.py` — optional local SAIA CORS proxy

---

## License

MIT
