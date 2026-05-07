# Generative Plotter Studio

A browser-based creative coding assistant for pen plotter art. Describe a sketch in plain language — get runnable Processing Java and p5.js code, a live preview, and export-ready files.

![Dark theme UI with chat, code, and preview panels](https://raw.githubusercontent.com/BotAndis/Plotter-Studio/claude/new-session-p80Ya/plotter_studio.html)

## Features

- **AI-powered sketch generation** — describe your idea, get complete Processing `.pde` and p5.js code
- **Live p5.js preview** — renders the sketch directly in the browser with reseed support
- **Multi-model support** — Claude (Sonnet, Opus, Haiku), Google Gemini (free & paid), and Academic Cloud (SAIA) models
- **Code export** — download `.pde`, `.js`, or a standalone `.html` file
- **Syntax highlighting** — color-coded Processing and p5.js code display
- **Template system** — built-in dMA Creative Coding template or write your own system prompt
- **Session management** — save and restore up to 20 sessions in localStorage
- **Resizable panels** — drag to resize concept, preview, code, and how-it-works panels
- **Light/dark theme** — with customizable accent color
- **Fullscreen preview** — with PNG export
- **Extended thinking** — toggle Claude's chain-of-thought reasoning

## Usage

Open `plotter_studio.html` directly in your browser — no build step, no server required.

1. Enter your API key in the chat panel (Anthropic, Gemini, or Academic Cloud)
2. Select a model from the dropdown
3. Describe your plotter sketch in the chat input
4. Download the generated code or standalone HTML

## Supported Models

| Provider | Models |
|----------|--------|
| **Anthropic** | Claude Sonnet 4.6 ★, Opus 4.7, Haiku 4.5 |
| **Google Gemini** | Gemini 3 Flash ★, 3.1 Pro, 3.1 Flash-Lite, 2.5 Pro/Flash (free & paid) |
| **Academic Cloud (SAIA)** | Qwen3 Coder 30B ★, DeepSeek R1 Distill 70B, LLaMA 3.3 70B, Mistral Large 3 |

Works without an API key inside [claude.ai](https://claude.ai/code) (uses Claude Sonnet 4.6 automatically).

## Creative Lineage

Built on the shoulders of:
- Vera Molnár, Manfred Mohr, Frieder Nake — algorithmic plotter foundations
- [Tyler Hobbs](https://tylerxhobbs.com) — flow fields, parametric density
- [Golan Levin / Drawing With Machines](https://github.com/golanlevin/DrawingWithMachines) — CMU course, Processing-to-SVG pipelines
- [Generative Gestaltung](http://www.generative-gestaltung.de) — parametric grids, noise studies
- [Plotter Files](https://plotterfiles.com), [Turtletoy](https://turtletoy.net), [Generated Space](https://generated.space)

## License

MIT
