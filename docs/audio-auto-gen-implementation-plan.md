# Implementation Plan — Auto-Generated, Interactive Audio for Vector Sketches

> **STATUS: IMPLEMENTED** (all steps landed in `plotter_studio.html`, +246/−37 lines, JS syntax-checked via `node --check`). Steps 1–8 below are done. Not yet run end-to-end in a browser — that needs a live API key; see "How to test" at the bottom.

> Companion to [audio-auto-gen-concept.md](audio-auto-gen-concept.md). This is the 1:1 build plan: exact files, functions, line anchors (as of current `plotter_studio.html`), the code to insert, the exact prompt text, and the music-theory / DSP grounding for each decision.

## How to test (manual, needs an API key)
1. Open `plotter_studio.html`, open ⚙ settings, enable **Auto-generate matching audio** (Pipeline must stay on for slider coupling). Pick an **Audio** mood next to the prompt box (or leave Auto).
2. Generate a plotter sketch (e.g. *"dense flow field of curved lines"*). After the sketch renders, the veil shows *"♪ Auto-generating audio…"* and a slider panel appears under the preview.
3. The audio engine auto-starts but is **muted** — click **🔇/🔈** or **Play** to hear it.
4. Drag a slider (e.g. *Lines*): the drawing redraws **and** the sound changes live (no regen). That is the coupling.
5. Regressions to confirm unaffected: manual Audio Studio generation + Play still makes sound; downloaded `.html` audio still plays.

Known minor gaps: coupling needs Pipeline ON (single-shot has no manifest); standalone export omits the DC-block (helpers are mirrored); manual audio-mood choice is not persisted across reload (defaults to Auto).

---

> Single file: everything lives in [`plotter_studio.html`](../plotter_studio.html). ES5 style (`var`, no arrow fns in injected DSP), p5 instance mode. Line numbers shift as edits land — anchor by **function name + nearby string**, not the raw number.

---

## 0. Anchor map (current line numbers)

| What | Function / id | Line | Touched in step |
|---|---|---|---|
| Plotter send / generate trigger | `send()` | 5212 | 7 |
| Result → `stored` + preview | `renderAll(r)` | 5144 | 5, 7 |
| Response parser | `parseResponse(text)` | 2972 | 5 |
| p5 runner (eval + p5 instance) | `runP5(fnStr,seed)` | 5174 | 5 |
| Per-phase prompt builder | `getDefaultPhasePrompt(phase,s)` | 2121 | 4, 5 |
| Audio system prompt default | `DEFAULT_AUDIO_SYSTEM_PROMPT` | 2106 | 4 |
| Audio pipeline | `generateAudio()` | 4383 | 6 |
| DSP compile + sandbox preamble | `compileAudioDsp(code)` | 4320 | 2 |
| Standalone export compile | `buildStandaloneAudioHtml()` | 4361 | 2 |
| Audio engine playback loop | `playAudio()` / `onaudioprocess` | 4462 / 4487 | 3, 5 |
| Custom slider renderer | `renderCustomSliders(params)` | 4257 | 5 |
| Settings read / write | `getSettings()` / `applySettings(s)` | 4999 / 5008 | 1 |
| Existing preset map | `AUDIO_PRESETS` | 4159 | 1 |
| Preset change handler | `onAudioPresetChange()` | 4228 | 1 |
| Settings panel checkbox row | `#opt-sliders` (HTML) | 1503 | 1 |
| Audio transport buttons (HTML) | `#audio-play-btn` row | 1196 | 3 |
| Plotter input row (HTML) | `#cinrow` | 1445 | 1 |

---

## 1. Music-theory & digital-audio foundation (why each rule exists)

Every "make it sound good" rule below maps to a concrete code action in steps 2–6. Sources at the end of the concept doc.

### Pitch & harmony
- **Equal temperament** — the sandbox already ships `note(n) = 440·2^((n−69)/12)` (MIDI→Hz, A4=440 at MIDI 69). All pitch math builds on this.
- **Consonance** — simplest frequency ratios sound most stable: octave 2:1, perfect fifth 3:2, fourth 4:3. A root+fifth **drone** is maximally consonant → our harmonic "bed".
- **Scales as semitone sets** — restricting pitches to a scale removes wrong notes. **Pentatonic (5 notes, no semitone clashes)** is the safe default; minor/dorian/phrygian/lydian give mood without dissonance. Encoded as `SCALES` (step 2).
- **Mode ↔ mood** — major/lydian = bright, minor/phrygian = dark. Each preset locks a root + scale so melody and bed are always in key.

### Rhythm
- **Beat quantization** — the engine passes `beat = t·BPM/60`. Gating events on `floor(beat)` / fractions keeps rhythm on a grid (`env(beat,…)` in step 2). No free-running mush.

### Production / DSP hygiene (this is what separates "amateur" from "mixed")
- **Anti-click envelopes** — a note that jumps from 0→amp→0 instantly clicks. A 2–10 ms attack/release ramp from/to 0 removes it. → `env()` helper, mandatory in prompt.
- **Gain staging & headroom** — never reach 0 dBFS. Sum N voices, **normalize**, target master peak ≈ 0.6–0.7 linear (~−3 to −4 dBFS). Use `tanh` soft-clip only as a *safety* net, not as the mixer. → `mix()` helper + peak budget in prompt.
- **DC offset** — a waveform not centered on 0 steals headroom and pops on edits. Remove with a one-pole high-pass on the master. → engine-side DC-block (step 3).
- **Aliasing** — Nyquist = SR/2. A naive saw/square has infinite harmonics; above a ~1.3 kHz fundamental at 44.1 kHz they fold back as harsh, inharmonic tones. Fixes: prefer **sine/triangle** for high pitches, use **additive** synthesis, or a **band-limited (PolyBLEP) saw** (`saw()` helper, step 2). Lowpass bright voices (existing Tone filter helps).
- **Frequency balance / masking** — layers stacked in one band turn to mud. Spread by register: high-pass sub-rumble <60 Hz (inaudible, wastes headroom), bed low, melody mid (~200 Hz–2 kHz), sparkle/air (2–5 kHz). → register guidance in prompt + presets.

---

## 2. Sandbox quality helpers (harmony + production)

**Goal:** generated DSP stays *simple* yet is in-key, click-free, gain-managed, alias-aware.

### 2a. Extend the `compileAudioDsp` preamble — `compileAudioDsp(code)` @ 4320

Current preamble (4337-4343) injects `TAU`, `note(n)`, `clamp(v)`. Replace that `src` head with the block below. Note `SR` is resolved from the live context if present, else 44100 (the probe at compile time has no context; `playAudio` recompiles with the real rate):

```javascript
var SR = (audioEngine && audioEngine.ctx && audioEngine.ctx.sampleRate) || 44100;
var src = '"use strict";\n' +
  'var TAU=Math.PI*2;\n' +
  'var SR=' + SR + ';\n' +
  'function note(n){return 440*Math.pow(2,(n-69)/12);}\n' +
  'function clamp(v){return Math.max(-1,Math.min(1,v));}\n' +
  // ── harmony ──
  'var SCALES={majPent:[0,2,4,7,9],minPent:[0,3,5,7,10],major:[0,2,4,5,7,9,11],' +
    'minor:[0,2,3,5,7,8,10],dorian:[0,2,3,5,7,9,10],phrygian:[0,1,3,5,7,8,10],lydian:[0,2,4,6,7,9,11]};\n' +
  'function scaleNote(d,r,id){var s=SCALES[id]||SCALES.minPent,n=s.length;' +
    'var o=Math.floor(d/n),i=((d%n)+n)%n;return r+o*12+s[i];}\n' +
  'function scaleHz(d,r,id){return note(scaleNote(d,r,id));}\n' +
  'function chordHz(d,r,id){return [0,2,4].map(function(x){return scaleHz(d+x,r,id);});}\n' +
  // ── production ──
  'function env(beat,start,len,atk,rel){var b=beat-start;if(b<0||b>len)return 0;' +
    'if(b<atk)return b/atk;if(b>len-rel)return Math.max(0,(len-b)/rel);return 1;}\n' +
  'function mix(){var s=0,i;for(i=0;i<arguments.length;i++)s+=arguments[i];return s/Math.max(1,arguments.length);}\n' +
  'function saw(ph,f){var dt=f/SR,x=2*ph-1,t;if(ph<dt){t=ph/dt;x-=t+t-t*t-1;}' +
    'else if(ph>1-dt){t=(ph-1)/dt;x-=t*t+t+t+1;}return x;}\n' +
  code + '\n' +
  'if(typeof dsp!=="function") throw new Error("Audio code must define a function named dsp(t, beat)");\n' +
  'return { dsp: dsp, params: (typeof params!=="undefined" && Array.isArray(params)) ? params : [] };';
```

The banned-API scan (4327-4336) is unchanged and still runs first — these helpers add no new capabilities.

### 2b. Mirror helpers into the standalone export — `buildStandaloneAudioHtml()` @ 4361

The download path compiles with its own inline preamble (line 4372). Update that string so downloaded patches keep working — add `SR` (from the exported ctx), `SCALES`, `scaleNote/scaleHz/chordHz`, `env`, `mix`, `saw` exactly as above. In that file `SR` is available as `ctx.sampleRate` at play time:

```javascript
// inside compile(): build src with
'"use strict";var TAU=Math.PI*2;var SR=ctx.sampleRate;' +
'function note(n){return 440*Math.pow(2,(n-69)/12);}function clamp(v){return Math.max(-1,Math.min(1,v));}' +
'var SCALES={…same…};function scaleNote(…){…}function scaleHz(…){…}function chordHz(…){…}' +
'function env(…){…}function mix(){…}function saw(…){…}' + code + '…'
```

> **Test gate:** generate a patch → download `.html` → it must still play. Both compile sites must match or the export breaks (this is the #1 regression risk).

---

## 3. Engine: DC-block + mute

### 3a. State — `audioEngine` object (search `audioEngine = {`)
Add fields: `muted: true`, and DC-block state `dcXL:0, dcYL:0, dcXR:0, dcYR:0`. Reset `dcXL=dcYL=dcXR=dcYR=0` in `playAudio()` next to the existing `lpfL=0; lpfR=0;` (≈4483).

### 3b. Per-sample chain — `onaudioprocess` in `playAudio()` @ 4487
After the existing Drive→Tone→Volume FX and before `L[i]=…; R[i]=…`, insert a one-pole high-pass DC-block, then the mute gate. One-pole HPF: `y = x − x₁ + R·y₁`, `R≈0.995` (~35 Hz corner — removes DC, keeps bass):

```javascript
// DC block (one-pole high-pass) — removes offset, recovers headroom
var R = 0.995;
var hpL = l - audioEngine.dcXL + R * audioEngine.dcYL; audioEngine.dcXL = l; audioEngine.dcYL = hpL; l = hpL;
var hpR = r - audioEngine.dcXR + R * audioEngine.dcYR; audioEngine.dcXR = r; audioEngine.dcYR = hpR; r = hpR;
// final safety clamp (already present)
l = Math.max(-1, Math.min(1, l)); r = Math.max(-1, Math.min(1, r));
if (audioEngine.muted) { l = 0; r = 0; }   // live but silent until unmuted
```

Mute gates **after** the chain so the engine keeps running (live music) — unmuting is instant, no recompile, no restart. (Optional: mirror the DC-block into the standalone export loop too.)

### 3c. Mute UI — transport row HTML @ 1196
Add a mute button next to Play/Stop:

```html
<button class="ibtn" id="audio-mute-btn" aria-pressed="true">🔇 Muted</button>
```

Wire it near the other audio listeners (≈4609):

```javascript
function setMute(on){
  audioEngine.muted = !!on;
  var b = G('audio-mute-btn');
  if (b){ b.textContent = on ? '🔇 Muted' : '🔈 Live'; b.setAttribute('aria-pressed', on?'true':'false'); }
}
G('audio-mute-btn').addEventListener('click', function(){ setMute(!audioEngine.muted); });
```

Default ON: initialize `audioEngine.muted = true` and call `setMute(true)` at startup.

---

## 4. Audio prompt: harmony/production rules + helper docs

### 4a. System prompt — `DEFAULT_AUDIO_SYSTEM_PROMPT` @ 2106
Append (helpers are now globally available, so document them for *all* audio generation — manual benefits too):

```
 Helper functions are in scope: note(midi)->Hz, scaleHz(degree,rootMidi,scaleId)->Hz, chordHz(degree,rootMidi,scaleId)->[Hz,Hz,Hz], env(beat,startBeat,lenBeats,atkBeats,relBeats)->0..1, mix(...voices)->normalized sum, saw(phase01,freqHz)->band-limited saw, clamp(v), SR (sample rate), TAU. Scale ids: majPent,minPent,major,minor,dorian,phrygian,lydian. Production rules: derive pitches from scaleHz/note (do not hardcode frequencies); wrap notes in env() to avoid clicks; combine layers with mix() and keep the master peak near 0.7; prefer sine/triangle for high notes and saw() (band-limited) for bright mid voices to avoid aliasing; put the bass/bed low and the melody in the mids.
```

### 4b. Auto-mode hard rules
These are injected by the auto builder (step 6), *not* the system prompt, so manual generation stays flexible. The builder appends the locked mood values + the §5 mapping table + this directive:

```
HARD CONSTRAINTS (auto mode): root = <midi>, scale = "<id>", target BPM = <n>.
Pitches MUST come from scaleHz(deg, <root>, "<id>"). Add a quiet root chord bed via chordHz(0, <root>, "<id>"). Every note uses env(). Master peak <= 0.7.
Declare `var params` using EXACTLY these names (no others) and make each audibly change the sound per the mapping: <manifest names + roles>.
```

---

## 5. Param manifest + shared `PARAMS` bus (interactive coupling — headline)

**Model:** one manifest (declared by the plotter sketch) → one slider panel → one shared values object read live by **both** the p5 sketch and the DSP. Moving a slider updates `PARAMS`; the host calls `p5inst.redraw()` (visual) while `dsp` reads the new value next sample (audio). No recompile, no two-source drift.

### 5a. Global bus — near other top-level vars (e.g. by `var stored` @ 1903)
```javascript
var PARAMS = {};   // shared live param values: visual twin of audioEngine.paramVals
```

### 5b. Coupled p5 contract — `getDefaultPhasePrompt('p5', s)` @ 2128
When `s.audioAuto` is on, **replace** the p5 control rules so the sketch (a) declares a manifest and (b) reads values from `PARAMS` and draws in `p.draw` (so `redraw()` works), instead of `createSlider`:

```javascript
if (phase === 'p5') {
  if (s.audioAuto) {
    return "OUTPUT: Return exactly two sections:\n" +
      "### Params\n```json\n[{\"name\":\"lineCount\",\"label\":\"Lines\",\"min\":10,\"max\":400,\"value\":120,\"step\":1,\"role\":\"count\"}]\n```\n" +
      "### p5 sketch\n```p5instance\nfunction(p){ ... }\n```\n\n" +
      "PARAMS CONTRACT (mandatory):\n" +
      "- Declare 2-4 tunable params in ### Params. Allowed roles: count, size, density, speed, complexity, hue.\n" +
      "- Inside the sketch, read each value as PARAMS.<name> (a global object the host updates live). Do NOT call p.createSlider — the host renders the sliders.\n" +
      "- Do the drawing inside p.draw (reading PARAMS there) and call p.noLoop() at the end of p.setup, so the host can re-render with p.redraw() when a value changes.\n" +
      "Canvas 540x383. White bg. noFill. Black strokes. let seed = <number>; at top. randomSeed(seed)/noiseSeed(seed) in setup.\n" +
      "CRITICAL: no DOM access; all p5 calls use the p. prefix. ONLY the two sections above.";
  }
  // …existing non-coupled branch (createSlider etc.) unchanged…
}
```

Rationale for "draw in `p.draw` + `noLoop`": the current template draws once in `setup` via `drawSketch()`, so `redraw()` (which re-runs `draw`) would do nothing. Moving the draw into `p.draw` makes host-driven re-render work for static plotter art.

### 5c. Parse the manifest — `parseResponse(text)` @ 2972
Add `params:[]` to the result and parse a `### Params` JSON block (safely; never throw):

```javascript
r.params = [];
var pm = text.match(/###\s*Params\s*```(?:json)?\s*([\s\S]*?)```/i);
if (pm){ try { var arr = JSON.parse(pm[1].trim()); if (Array.isArray(arr)) r.params = arr; } catch(e){} }
```
Also add `'### Params'` to the section-stop lists so it doesn't bleed into `desc`/code (add to the `secs` index set and the `between(...)` stop arrays).

Carry it through: in `generatePipeline` (p5 phase, ≈2520 where `stored.p5code = result.p5code`) set `result.params = p5Parsed.params`; `callClaude` already returns the parsed object — ensure the caller keeps `r.params`.

### 5d. Unified slider panel + shared values — new `renderCoupledParams(manifest)`
Place the host panel in the preview column (search `id="p5w"`; add a sibling):
```html
<div id="plot-params" class="plot-params"></div>
```
Renderer (mirrors `renderCustomSliders` but writes the shared bus and redraws p5):
```javascript
function renderCoupledParams(manifest){
  var host = G('plot-params'); if (!host) return;
  host.innerHTML = '';
  PARAMS = {};
  audioEngine.paramVals = PARAMS;          // SHARED reference — dsp reads the same object
  audioEngine.coupled = true;
  (manifest||[]).forEach(function(pm){
    if (!pm || pm.name == null) return;
    var name=String(pm.name), min=Number(pm.min), max=Number(pm.max);
    if(!isFinite(min))min=0; if(!isFinite(max)||max<=min)max=min+1;
    var def=Number(pm.value); if(!isFinite(def))def=(min+max)/2;
    var step=Number(pm.step); if(!isFinite(step)||step<=0)step=(max-min)/100;
    PARAMS[name]=def;
    var row=document.createElement('div'); row.className='audio-slider-row';
    var lab=document.createElement('label'); lab.textContent=String(pm.label||name);
    var inp=document.createElement('input'); inp.type='range'; inp.min=min; inp.max=max; inp.step=step; inp.value=def;
    var out=document.createElement('span'); out.className='audio-slider-val'; out.textContent=fmtParam(def);
    inp.addEventListener('input',function(){
      var v=parseFloat(inp.value); if(!isFinite(v))v=def;
      PARAMS[name]=v; out.textContent=fmtParam(v);
      if (p5inst && typeof p5inst.redraw==='function') p5inst.redraw();  // visual updates; audio is live
    });
    row.appendChild(lab); row.appendChild(inp); row.appendChild(out); host.appendChild(row);
  });
}
```

### 5e. Don't let `playAudio` wipe the shared bus — `playAudio()` @ 4467
`playAudio` calls `renderCustomSliders(compiledPatch.params)` which resets `paramVals={}`. Guard it:
```javascript
if (audioEngine.coupled) { renderCoupledParams(stored.params); }
else { renderCustomSliders(compiledPatch.params); }
```
(Reset `audioEngine.coupled=false` in `generateAudio()`'s manual path and on session reset.)

---

## 6. `autoGenerateAudioFromPlot` + refactor to `runAudioPipeline`

### 6a. Extract a reusable pipeline — refactor `generateAudio()` @ 4383
Move the body into `runAudioPipeline(opts)` where `opts = { prompt, bpm, mood, manifest, autoplay, lite }`. `generateAudio()` becomes the chat wrapper:
```javascript
async function generateAudio(){
  if (typeof endAudioCodeEdit === 'function') endAudioCodeEdit();
  var prompt=(audioState.prompt||'').trim();
  if(!prompt){ setAudioStatus('Describe a sound in the Audio Assistant chat first.', true); return; }
  audioEngine.coupled=false;
  return runAudioPipeline({ prompt:prompt, bpm:getAudioBpm(), lite:false, autoplay:false });
}
```
`runAudioPipeline` keeps the existing concept→code→syntax-fix→explain flow, but when `lite` is true it **skips the audioconcept and audioexp phases** and runs only: build prompt → `audio` phase → `compileAudioDsp` → one fix retry on failure. The compile-check/fix stays in both modes (self-healing).

### 6b. `autoGenerateAudioFromPlot(stored, userPrompt, manifest)` — new
```javascript
function hashStr(s){ var h=0,i; s=String(s); for(i=0;i<s.length;i++){h=(h*31+s.charCodeAt(i))|0;} return Math.abs(h); }

async function autoGenerateAudioFromPlot(stored, userPrompt, manifest){
  var text = ((stored.title||'')+' '+(stored.desc||'')+' '+(userPrompt||'')).toLowerCase();
  var sel = G('audio-mood') ? G('audio-mood').value : 'auto';
  var moodKey = (sel && sel!=='auto') ? sel : pickAudioMood(text);
  var mood = AUDIO_MOODS[moodKey] || AUDIO_MOODS[AUDIO_MOOD_DEFAULT];
  // determinism: stable BPM within the mood range from the title hash
  var span = mood.bpm[1]-mood.bpm[0];
  var bpm = mood.bpm[0] + (span>0 ? hashStr(stored.title||'x')%(span+1) : 0);
  audioState.preset = moodKey;
  G('audio-bpm').value = bpm;
  G('audio-drive').value = mood.drive; G('audio-tone').value = mood.tone; syncAudioControls();
  audioEngine.coupled = true;

  var names = (manifest||[]).map(function(m){return m.name+' ('+(m.role||'param')+')';}).join(', ') || '(none)';
  var prompt =
    mood.hint + '\n\nInspired by this sketch concept:\n### ' + (stored.title||'') + '\n' + (stored.desc||'') +
    '\n\n' + AUTO_MAPPING_TABLE +                       // the §5 role→musical-target table as text
    '\n\nHARD CONSTRAINTS: root=' + mood.root + ', scale="' + mood.scale + '", BPM=' + bpm +
    '. Pitches via scaleHz(deg,' + mood.root + ',"' + mood.scale + '"). Quiet bed via chordHz(0,' + mood.root + ',"' + mood.scale + '").' +
    ' Wrap notes in env(); master peak <= 0.7.' +
    ' Declare var params using EXACTLY these names and map each per the table: ' + names + '.';

  audioState.prompt = prompt;
  setMute(true);                                        // live but silent
  await runAudioPipeline({ prompt:prompt, bpm:bpm, mood:mood, manifest:manifest, lite:true, autoplay:true });
  renderCoupledParams(manifest);                        // one panel drives p5 + audio
}
```
`autoplay:true` starts the engine (so coupling is immediately felt on unmute); `setMute(true)` keeps it silent until the user opts in.

---

## 7. Hook into the plotter flow — `send()` @ 5212

After the single-shot auto-fix block (≈5258, right before the "Verify model" note at 5260), add the trigger. `r.params` comes from the manifest parse (step 5c):

```javascript
if (getSettings().audioAuto) {
  G('veil-detail').textContent = '♪ Auto-generating audio from sketch…';
  try { await autoGenerateAudioFromPlot(stored, text, r.params || []); }
  catch (audioErr) { console.error('Auto-audio failed:', audioErr); setAudioStatus('Auto-audio failed: ' + audioErr.message, true); }
}
```
Failure isolation: the vector result is already rendered (`renderAll` ran at 5242); auto-audio is wrapped so it can never break the sketch. If a new `send()` starts while audio is in flight, the existing generation guard (`G('csend').disabled`) plus `endAudioCodeEdit()` cover cancellation; add an `audioEngine` in-flight flag if needed.

---

## 8. Settings, presets, persistence

### 8a. Toggle — settings panel HTML @ 1503 (next to `#opt-sliders`)
```html
<label class="sp-row"><input type="checkbox" class="sp-cb" id="opt-audio-auto"><span class="sp-label">Auto-generate matching audio</span></label>
```
`getSettings()` @ 4999 → add `audioAuto: G('opt-audio-auto').checked`. `applySettings()` @ 5008 → add `if(s.audioAuto!==undefined) G('opt-audio-auto').checked=s.audioAuto;`. The `.sp-cb` change listener (5022) already persists.

### 8b. Mood selector — plotter input row HTML @ 1445 (`#cinrow`), shown when audioAuto on
```html
<select id="audio-mood" title="Audio mood for auto-generated sound">
  <option value="auto">Audio: Auto</option>
  <option value="dreamy">Dreamy</option>
  <option value="energetic">Energetic / Electric</option>
  <option value="dark">Dark</option>
  <option value="organic">Organic</option>
</select>
```

### 8c. Mood data + matcher — near `AUDIO_PRESETS` @ 4159
Add the `AUDIO_MOODS` map, `AUDIO_MOOD_DEFAULT`, `pickAudioMood(text)`, and `AUTO_MAPPING_TABLE` (the role→target table as a prompt string) exactly as in concept §5–§6.

### 8d. Persistence
Session snapshot already stores `audioState` and `audio-preset`. Add `stored.params` and the current `PARAMS` values to the snapshot (search `preset: G('audio-preset').value` @ 4923) so a reloaded session restores the coupled sliders. On load, if `stored.params.length`, call `renderCoupledParams(stored.params)`.

---

## 9. Build order & manual test checklist

Build in dependency order (each line testable in isolation):

1. **Step 2** sandbox helpers → generate a normal audio patch manually; confirm it still compiles & plays, and `.html` export still plays.
2. **Step 3** DC-block + mute → Play; confirm mute toggle silences/restores instantly with the engine still running.
3. **Step 8a/8c** toggle + mood data → settings persist across reload.
4. **Step 4** prompt rules → manual audio sounds in-key / click-free.
5. **Step 5** manifest + bus → enable audioAuto, generate a sketch; confirm `### Params` parses, one slider panel appears, dragging redraws p5.
6. **Step 6 + 7** auto pipeline + hook → full loop: generate sketch → audio auto-generates (lite), engine live+muted → unmute → drag a slider → **both** the drawing and the sound change.

No automated test harness exists (single-file app). Verify in-browser; watch the debug overlay for phase/provider and the console for DSP/compile errors.

---

## 10. Risk register

| Risk | Mitigation |
|---|---|
| Export breaks (helpers only in live sandbox) | Step 2b — mirror helpers into `buildStandaloneAudioHtml`; test gate in §9.1. |
| `playAudio` wipes shared bus | Step 5e guard on `audioEngine.coupled`. |
| Coupled p5 `redraw()` no-ops | Step 5b contract forces draw in `p.draw` + `noLoop`. |
| Aliasing on bright leads | `saw()` band-limited helper + prompt rule (sine/triangle high). |
| LLM ignores param names → bus mismatch | Auto prompt: "EXACTLY these names, no others"; compile probe + fix loop catches breakage; unmatched names simply read `undefined`→guard with defaults in DSP prompt. |
| Cost doubling | Lite mode (code+fix only) is the auto default; full stays manual. |
| Auto-audio error breaks sketch | Step 7 try/catch; sketch already rendered before audio runs. |

---

## 11. Open confirmations (small, from concept §10)
- **Mood selector placement**: planned in `#cinrow` (near generate). Move to settings panel if preferred.
- **Determinism**: planned ON (BPM seeded from title hash). Drop `hashStr` use for random-in-range if you'd rather it vary.
- **Mute scope**: dedicated `#audio-mute-btn` (Volume keeps its value). 
