# Plotter Studio

Plotter Studio is a browser-based creative coding tool for pen-plotter workflows.  
You describe a sketch in natural language, and it generates:
- Processing (Java) code for plotter-ready output
- p5.js preview code for instant browser rendering
- explanation panels describing how the generated systems work

---

## Project Overview

The repository contains a no-build frontend app and an optional tiny Python proxy:

- `plotter_studio.html`  
  Full version (pipeline mode, debug log, session management, token tracking)
- `plotter_studio_artifact.html`  
  Artifact-focused version (optimized for hosted artifact usage)
- `saia_proxy.py`  
  Local CORS proxy for Academic Cloud (SAIA)

No build system is required: open the HTML file directly in a browser.

---

## Features

- AI-assisted plotter sketch generation from plain-language prompts
- Provider-aware routing across Anthropic, Gemini, and Academic Cloud (SAIA)
- Optional multi-phase generation pipeline:
  - Concept
  - p5.js preview
  - Processing code
  - Explanations
- p5.js live preview with reseed and fullscreen tools
- Auto-fix flow for p5 preview runtime errors
- Export buttons for `.pde`, `.js`, standalone `.html`, and chat/debug logs
- File attachments in prompts (images/text, provider-dependent handling)
- Model picker with key status dots and provider sections
- Local persistence of preferences, keys, and (in full version) saved sessions
- Theme + accent customization

---

## Installation

### 1) Clone repository

```bash
git clone https://github.com/BotAndis/Plotter-Studio.git
cd Plotter-Studio
```

### 2) Open the app

Choose one:
- Open `plotter_studio.html`
- Open `plotter_studio_artifact.html`

You can open either file directly in a browser (double-click or drag into browser).

### 3) Optional: start local SAIA CORS proxy

Use this only if you use Academic Cloud (SAIA) and need browser CORS workaround:

```bash
python saia_proxy.py
```

Then set CORS proxy URL in the app to:

```text
http://localhost:8765/
```

---

## How to use

### Option 1 — Artifact mode (no manual Anthropic key in claude.ai)

Best for quick usage in a Claude artifact environment.

1. Open the artifact edition (`plotter_studio_artifact.html`) in a `claude.ai` artifact environment.
2. Keep default Claude model (or select available model).
3. Enter your prompt in chat and send.
4. Download generated files (`.pde`, `.js`, `.html`) from the response buttons.

Notes:
- In `claude.ai` contexts, Anthropic authentication is automatically handled by the environment.
- Gemini still requires a user API key.
- SAIA requires Academic Cloud key (+ CORS proxy if direct browser requests are blocked).

### Option 2 — API key mode (all providers)

Use this for local standalone browser usage and full provider control.

1. Open `plotter_studio.html` (or artifact file if preferred).
2. Select the target model/provider from model picker.
3. Add API key in key banner and click **Set**.
4. Prompt the assistant and iterate.
5. Export code and explanations.

#### Multiple API key paths (supported)

You can set keys through several paths:

1. **UI key banner (recommended)**  
   Enter key in input and click **Set**.

2. **Provider status dots**  
   Click Anthropic/Gemini/Academic dot to jump key banner to that provider, then save key.

3. **Direct browser localStorage entries**  
   - `plotterStudio_apiKey_anthropic`
   - `plotterStudio_apiKey_gemini`
   - `plotterStudio_apiKey_academic`
   - `plotterStudio_corsProxy` (for SAIA proxy URL)

4. **Legacy key migration path**  
   Older key `plotterStudio_apiKey` is migrated automatically to `plotterStudio_apiKey_anthropic`.

5. **Code-level fallback path (Academic Cloud only)**  
   `ACADEMIC_CLOUD_KEY_DEFAULT` variable in both HTML files can provide a default SAIA key.

> ⚠️ Security warning: localStorage keys and in-file fallback keys are sensitive credentials. Never commit real API keys, never share screenshots exposing keys, and avoid hardcoding keys for production deployments. For production, prefer server-side secrets via environment variables or a dedicated secret manager.

---

## API flow (detailed)

### 1) Provider routing

Model ID decides provider:
- `gemini*` models -> Gemini API
- IDs in Academic model list -> SAIA API
- all others -> Anthropic API

### 2) Endpoints + auth

- **Anthropic**
  - Endpoint: `https://api.anthropic.com/v1/messages`
  - Header: `x-api-key` (when user key is set)
  - Browser direct access flag is added when needed

- **Gemini**
  - Endpoint: `https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent`
  - Header: `x-goog-api-key`

- **Academic Cloud (SAIA, OpenAI-compatible)**
  - Endpoint: `https://chat-ai.academiccloud.de/v1/chat/completions`
  - Header: `Authorization: Bearer <key>`
  - Supports optional proxy prefix through `plotterStudio_corsProxy`

### 3) SAIA CORS behavior

SAIA browser calls may fail due to CORS restrictions. The app supports:
- local proxy (`saia_proxy.py`) -> appends `/v1/chat/completions`
- public proxy style (full URL prepend)

### 4) Generation pipeline

Full version can run a multi-phase chain:
1. Concept generation
2. p5.js preview generation
3. Processing code generation
4. Explanation generation

Fallback: if pipeline is disabled or too small for phase split, app uses single-shot generation.

### 5) Response parsing + rendering

The app parses model output into sections:
- title/description
- `### Processing code`
- `### p5 sketch`
- `### How it works (Processing)`
- `### How it works (p5.js)`

Then it updates UI panels, runs p5 preview, and enables downloads.

---

## Supported providers and typical models

- **Anthropic / Claude**: Sonnet, Opus, Haiku
- **Google Gemini**: Flash, Flash-Lite, Pro variants
- **Academic Cloud (SAIA)**: Qwen, DeepSeek, LLaMA, Mistral, and additional hosted models

Actual list is maintained in model-picker sections in the HTML files.

---

## License

MIT
