# Concept: Auto-Generated, Interactive Audio for Vector Sketches

> Status: design proposal — not yet implemented.
> Scope: an opt-in mode where generating a Plotter (vector) sketch also produces a matching audio patch that is (a) harmonic and well-mixed by construction, (b) **interactively coupled** to the sketch's sliders so changing a visual parameter changes the sound live, and (c) steered by a pre-generation mood preset.

---

## 1. Goal

When the user generates a vector sketch, optionally auto-generate an Audio Studio patch that:

1. **Matches the sketch** — its concept/mood (and its tunable parameters) drive the sound.
2. **Sounds good by construction** — consonant *and* properly mixed (gain-staged, click-free, no aliasing/DC mud), never random noise — even though the generated DSP stays simple.
3. **Is interactive** — the sketch's sliders (e.g. *more lines*, *bigger curves*) are mirrored into the audio engine and **coupled live**: drag a slider → both the drawing and the sound respond in real time.
4. **Is preset-driven** — before generating, the user picks one of 4 moods (*Dreamy*, *Energetic/Electric*, *Dark*, *Organic*), or *Auto* (keyword-detected).

Opt-in, because it adds a second generation pass per sketch.

---

## 2. Prior art / research

Two bodies of knowledge apply: **sonification / generative visual music** (how to map art→sound) and **music production / DSP** (how to make it sound *professional*, not just correct).

### Mapping (art → sound)
- **Parameter mapping** is the core technique: translate numeric/visual features into musical parameters (pitch, tempo, amplitude, timbre). Dominant, well-understood.
- **Visual-feature → sound**: documented for artworks — lightness, color diversity, density and style modulate tempo/pitch; warm vs cool palettes map to mode/brightness.
- **Harmony by constraint**: keep output consonant by restricting pitch to a **scale** (pentatonic = safe), using simple **chords/drones**, quantizing rhythm to the beat. Curation (shrinking the space) beats cleverness.

### Production / DSP (this is what makes it not sound amateur)
- **Gain staging & headroom**: never hit 0 dBFS; leave 3–6 dB headroom (peak ≈ −6…−3 dBFS ≈ ~0.5–0.7 linear). A good synth start point is ~60% of max. Don't use the clamp/limiter as a mixer.
- **Clicks**: any note on/off without a short fade (2–10 ms attack/release from/to 0) produces audible clicks. Envelopes are mandatory.
- **DC offset**: waveforms must stay centered on 0; offset steals headroom and causes pops. High-pass / DC-block the master.
- **Aliasing**: naive saw/square alias badly — at 44.1 kHz, fundamentals above ~1.3 kHz fold harsh metallic partials back down. Use sine/triangle for high notes, additive synthesis, or band-limited (PolyBLEP) oscillators; lowpass bright tones.
- **Frequency balance / masking**: layers stacked in the same range muddy each other. Spread them across registers (sub/low, mid, air); high-pass the bed below ~60 Hz (inaudible rumble wastes headroom); carve space per layer.

Sources:
- [Sonification of Visual Artworks — guidelines](https://www.researchgate.net/publication/334861462_Preliminary_Guidelines_on_the_Sonification_of_Visual_Artworks_Linking_Music_Sonification_Visual_Arts)
- [From Visual Art to Music (adapts to painting style)](https://www.tandfonline.com/doi/abs/10.1080/10447318.2022.2091210)
- [Cycling '74 — Algorithmic Composition primer](https://cycling74.com/tutorials/algorithmic-composition-an-introduction-for-the-curious-terrified-or-perplexed-beginner)
- [Tonic Audio — Generative Music](https://blog.tonicaudio.com/generative-music/)
- [Audient — Beginner's Guide to Headroom](https://audient.com/tutorial/the-beginners-guide-to-headroom/)
- [Sound on Sound — Gain Staging](https://www.soundonsound.com/techniques/gain-staging-your-daw-software)
- [DC Offset: The Case of the Missing Headroom](https://www.harmonycentral.com/articles/uncategorized/dc-offset-the-case-of-the-missing-headroom-r31/)
- [Practical Music Production — EQ Frequency Guide](https://www.practical-music-production.com/eq-frequency-guide/)
- [PolyBLEP band-limited oscillator (anti-aliasing)](https://christianfloisand.wordpress.com/2014/09/03/custom-pure-data-external-polyblep-sawtooth-oscillator/)

---

## 3. Where does the audio come from? Three approaches

| | Source | Coupling to sketch | Effort | Risk |
|---|---|---|---|---|
| **A. Concept/keyword-driven** | sketch title + concept + prompt | thematic | low — reuses everything | matches the *theme*, not the drawing |
| **B. Geometry/feature-driven** | measured sketch features | structural | high | mapping needs tuning |
| **C. Hybrid (recommended)** | concept text **+ the sketch's param manifest** (see §5) | thematic + parametric | medium | — |

**Recommendation: C, lightweight.** Reuse the whole audio pipeline (approach A) for the *character*, and additionally hand the audio generator the sketch's **parameter manifest** so the sliders become musically meaningful and coupled. That covers "interactive" without full geometry analysis. True geometry sonification (B) stays a later option.

---

## 4. "Sounds good" = two enforced layers

Quality is **enforced in code + prompt**, not left to the model. Layer 1 keeps it *in key*; layer 2 keeps it *well-mixed*.

### 4.1 Harmony layer (consonance)
1. **Scale quantization** — every pitch is a scale *degree*, snapped to a scale. Default minor pentatonic = can't sound wrong.
2. **Locked root + mode per preset** — melody and bed share them → always in key.
3. **Harmonic bed** — a sustained root+fifth drone / slow triad under the melody → instant fullness.
4. **Rhythm quantized to `beat`** — gate events on beat fractions (engine already passes `beat`).

### 4.2 Production layer (mix quality)
5. **Gain budget** — sum voices, scale so master peak ≈ 0.6–0.7, *then* soft-clip as safety (not as mixer).
6. **Anti-click envelopes** — every note uses a 2–10 ms attack/release.
7. **DC block + register split** — keep output centered; bed low, melody mid, sparkle high; high-pass sub-rumble.
8. **Anti-aliasing** — sine/triangle or additive for high notes; band-limit saw/square; lowpass bright voices (the existing Tone one-pole helps).

### Proposed sandbox helpers (extend the `compileAudioDsp` preamble)
Today the sandbox injects `TAU`, `note(n)` (MIDI→Hz), `clamp(v)`. Add scale + production helpers, and **expose `SR` (sample rate)** so anti-aliasing math is possible:

```javascript
// ── pitch / harmony ──
var SCALES = {
  majPent:[0,2,4,7,9], minPent:[0,3,5,7,10],
  major:[0,2,4,5,7,9,11], minor:[0,2,3,5,7,8,10],
  dorian:[0,2,3,5,7,9,10], phrygian:[0,1,3,5,7,8,10], lydian:[0,2,4,6,7,9,11]
};
function scaleNote(deg, rootMidi, id){
  var s = SCALES[id] || SCALES.minPent, n = s.length;
  var o = Math.floor(deg/n), i = ((deg%n)+n)%n;
  return rootMidi + o*12 + s[i];
}
function scaleHz(deg, rootMidi, id){ return note(scaleNote(deg, rootMidi, id)); }
function chordHz(deg, rootMidi, id){ return [0,2,4].map(function(d){return scaleHz(deg+d, rootMidi, id);}); }

// ── production ──
// AR envelope over a note of `len` beats starting at `start` (anti-click). -> 0..1
function env(beat, start, len, atk, rel){
  var b = beat - start; if (b < 0 || b > len) return 0;
  if (b < atk) return b/atk;
  if (b > len-rel) return Math.max(0,(len-b)/rel);
  return 1;
}
// equal-power-ish mixer: sum then normalize, leaving headroom
function mix(){ var s=0,i; for(i=0;i<arguments.length;i++) s+=arguments[i]; return s/Math.max(1,arguments.length); }
// band-limited saw via PolyBLEP (needs SR). phase 0..1, f = Hz
function saw(phase, f){ var dt=f/SR, x=2*phase-1;
  if(phase<dt){var t=phase/dt; x-=t+t-t*t-1;}
  else if(phase>1-dt){var t=(phase-1)/dt; x-=t*t+t+t+1;}
  return x; }
```

With these, generated DSP stays simple yet is in-key, click-free, and gain-managed:
```javascript
function dsp(t, beat, p){
  var root = 57;                               // A3
  var step = Math.floor(beat) % 8;
  var melHz = scaleHz(step, root, 'minPent');
  var mel = Math.sin(TAU*melHz*t) * env(beat, Math.floor(beat), 0.9, 0.01, 0.2);
  var c = chordHz(0, root, 'minPent');         // root triad bed, low + quiet
  var bed = mix(Math.sin(TAU*c[0]*t), Math.sin(TAU*c[1]*t), Math.sin(TAU*c[2]*t)) * 0.5;
  return clamp(mix(mel*0.9, bed*0.6) * 0.7);   // ~0.7 peak budget
}
```

- **DC block** is stateful, so add it **engine-side** (one-pole high-pass in the `onaudioprocess` loop, like the existing `lpf` Tone filter), not in the per-sample `dsp`.
- **Mirror every new helper** into `buildStandaloneAudioHtml()`'s inline `compile()` preamble, or downloaded patches break.

### Prompt-side rules (auto mode)
Append to the audio system prompt: *"Pitches MUST come from `scaleHz(deg, root, scale)`. Wrap every note in `env(...)`. Mix with `mix(...)` and keep master peak ≤ ~0.7. Bed low, melody mid. Prefer sine/triangle; use `saw()` (band-limited) only for bright mid voices. Never hardcode frequencies."*

---

## 5. Interactive parameter coupling (vector sliders ↔ audio)

**The core of the "interactive" ask.** Goal: the sketch's sliders and the audio's sliders are the *same* sliders — moving one changes both the drawing and the sound, live.

### Why it needs a contract change
- **Audio is already live-coupled**: `dsp(t, beat, p)` reads `audioEngine.paramVals` *every sample*, and the slider `input` handler writes there — so audio reacts instantly with **no recompile**. 
- **Plotter sliders are opaque**: when *Allow Parameter Sliders* is on, the p5 phase is told to `p.createSlider()` *inside the generated sketch* with arbitrary names/handlers ([`plotter_studio.html:2133`](../plotter_studio.html)). The host doesn't know they exist, so it can't route them to audio.

To couple, both sides must agree on a **shared parameter manifest + bus**.

### The design: one manifest, one bus, two consumers
1. **Manifest.** In coupled mode, the plotter generation emits a structured param list (alongside the code):
   ```json
   [ {"name":"lineCount","label":"Lines","min":10,"max":400,"value":120,"step":1,"role":"count"},
     {"name":"curveSize","label":"Curve size","min":0,"max":1,"value":0.4,"step":0.01,"role":"size"} ]
   ```
   `role` is a semantic tag (`count | size | density | speed | complexity | …`) that drives the musical mapping.
2. **Bus.** The host renders **one** unified slider panel that writes to a shared live object `PARAMS` (the visual twin of audio's `paramVals`).
3. **Consumer A — p5.** The p5 phase is instructed (coupled mode only) to **read tunable values from `PARAMS[name]`** instead of `createSlider`. On slider change the host triggers the sketch's redraw (same as today's `.input()→redraw` pattern, just host-driven).
4. **Consumer B — audio.** The same manifest is handed to the audio phase, which declares matching `params` (identical names) and uses them per the mapping table below. Because audio reads `p` live, it needs **no recompile** on change.
5. Result: drag *Lines* → `PARAMS.lineCount` updates → p5 redraws with more lines **and** `dsp` reads the new value → more note density. One gesture, both media.

### Mapping contract (visual role → musical target)
| role (visual) | musical target |
|---|---|
| `count` (lines, points) | note density / rhythmic subdivision / voice count |
| `size` / `scale` (curve size) | filter cutoff, vibrato/LFO depth, note length |
| `density` | event rate, reverb/space amount |
| `speed` / `motion` | LFO rate, tempo feel, arpeggio rate |
| `complexity` / `chaos` | detune, timbre richness, ornament probability |
| `hue` / `palette` | mode brightness (major↔minor lean) |

The audio system prompt is given the manifest + this table so each declared slider does something *musically sensible and audible*.

> **Decision (locked):** use the **shared bus**, not the DOM-bridge. Coupling is the headline feature, so it gets the robust contract. (Bridge fallback — keep p5's `createSlider`, match sliders by manifest order/label after `runP5`, fan values into `PARAMS` — is noted only as an emergency escape hatch; it is brittle and not the plan.)

---

## 6. Mood presets — pre-generation selector + Auto

The app already has an `AUDIO_PRESETS` map (key → prompt string), `audioState.preset`, and an `audio-preset` dropdown via `onAudioPresetChange()` — today a preset only pre-fills the chat input. Extend into musical presets and surface a **pre-generation mood selector** (a small segmented control / dropdown shown near the generate controls).

Starter set — **4 moods + Auto** (locked):

```javascript
var AUDIO_MOODS = {
  dreamy:    { label:'Dreamy',
               match:['calm','soft','ambient','ocean','mist','dream','gentle','drift','slow','ethereal'],
               root:57, scale:'majPent', bpm:[60,80],  density:0.25, drive:5,  tone:65,
               hint:'warm ambient pad, sparse bell tones, slow evolving, lots of space/reverb feel' },
  energetic: { label:'Energetic / Electric',
               match:['fast','energetic','electric','vibrant','burst','pulse','rapid','neon','dance','bright'],
               root:60, scale:'minPent', bpm:[120,150], density:0.8, drive:25, tone:90,
               hint:'driving arpeggio, punchy bass on the beat, bright band-limited saw lead' },
  dark:      { label:'Dark',
               match:['dark','dramatic','heavy','shadow','deep','ominous','void','noir','brooding'],
               root:50, scale:'phrygian', bpm:[70,95],  density:0.4, drive:35, tone:45,
               hint:'low brooding drone, minor melody, restrained, filtered' },
  organic:   { label:'Organic',
               match:['organic','flow','nature','growth','branch','wave','flora','curve','bloom','leaf'],
               root:55, scale:'lydian', bpm:[80,100], density:0.45, drive:8, tone:75,
               hint:'flowing, bright lydian, gently shifting overtones, soft pluck' }
};
var AUDIO_MOOD_DEFAULT = 'dreamy'; // also the Auto fallback
```

- **Pre-gen pick**: the chosen mood is locked before generation and fixes root/scale/bpm/FX + prompt character.
- **Auto**: if the user leaves it on *Auto*, run the keyword matcher over `title + desc + prompt` and pick the best of the 3 (fallback = default). Explicit pick always overrides Auto.

```javascript
function pickAudioMood(text){
  text = (text||'').toLowerCase();
  var best = AUDIO_MOOD_DEFAULT, bestScore = 0;
  Object.keys(AUDIO_MOODS).forEach(function(k){
    var sc = AUDIO_MOODS[k].match.reduce(function(a,w){ return a + (text.indexOf(w)>-1?1:0); }, 0);
    if (sc > bestScore){ bestScore = sc; best = k; }
  });
  return best;
}
```

---

## 7. Integration into existing code

All in [`plotter_studio.html`](../plotter_studio.html). Additive where possible; one real contract change (the p5 param bus, §5).

1. **Settings toggle** — checkbox `opt-audio-auto` next to `opt-pipeline`, class `.sp-cb` (auto-persist); wire into `getSettings()` / `applySettings()`.
2. **Pre-gen mood selector** — small control near generate; store in `audioState.preset` (reuse the field). `Auto` + the 3 moods.
3. **Hook after plotter gen** — after `generatePipeline()` / `callClaude()` resolves and `stored` is populated:
   ```javascript
   if (getSettings().audioAuto) autoGenerateAudioFromPlot(stored, task, manifest);
   ```
4. **Refactor `generateAudio()`** → extract pipeline body into `runAudioPipeline({prompt, bpm, mood, manifest, autoplay})`; the chat flow and auto flow share it.
5. **`autoGenerateAudioFromPlot(stored, userPrompt, manifest)`** — resolve mood (pick or Auto), set bpm/FX from mood, build prompt from `mood.hint + concept + manifest + mapping table`, run `runAudioPipeline(..., autoplay:false)`.
6. **Param bus (§5)** — introduce shared `PARAMS`; render one unified slider panel; coupled-mode p5 prompt reads `PARAMS[name]`; `runP5` / `runP5_FS` inject `PARAMS` + redraw-on-change; audio `params` reuse the same names (live, no recompile).
7. **Sandbox helpers (§4)** — extend `compileAudioDsp` preamble (scale + production + `SR`); **mirror into `buildStandaloneAudioHtml`**; add engine-side DC-block in `onaudioprocess`.
8. **Audio system prompt** — add §4 quality rules + §5 mapping table; inject the mood's concrete root/scale/bpm/density and the manifest.
9. **Failure isolation** — wrap auto-audio in try/catch; never block or break the vector result; cancel in-flight auto-audio if a new plotter gen starts.

---

## 8. Cost, UX, determinism

- **Cost (locked: lite).** Auto-audio runs in **lite mode** — code phase + auto-fix only, skipping the separate concept and explain phases (~1–2 API calls instead of ~4). The harmony/production rules live in the prompt regardless, so lite still sounds good, and the compile-check/fix loop is kept so broken DSP still self-heals. Full multi-phase stays available for manual Audio Studio generation.
- **Live + muted (locked).** Because the patch is **live music being modulated by the sliders**, the engine **auto-starts playing** on generation but behind a **mute toggle that defaults to ON**. So the patch is already running; the moment the user unmutes, slider moves are audible immediately. Needs a new mute control in the audio transport (master gain → 0 while muted; the existing Play/Stop and Volume stay). Do not auto-switch tabs.
- **Determinism**: seed bpm / random choices from a hash of `stored.title` so the same sketch reproduces the same audio. Optional.
- **UX**: show "Auto-generating audio from sketch…" in the Audio panel; surface the chosen mood name.

---

## 9. Build order

**Interactive coupling is a v1 requirement, not a later phase.** v1 ships the full loop; build it in this dependency order so each step is testable:

**v1 (core deliverable)**
1. **Foundation** — `opt-audio-auto` toggle, pre-gen 4-mood selector + Auto (`AUDIO_MOODS`, `pickAudioMood`), `autoGenerateAudioFromPlot`, lite pipeline (code + auto-fix).
2. **Quality layer (§4)** — scale + production helpers in the sandbox (mirror into the standalone export), engine-side DC-block, harmony/production rules in the audio prompt.
3. **Live + mute** — auto-start the engine on generation behind a mute toggle defaulting to ON.
4. **Interactive coupling (§5, headline)** — shared `PARAMS` bus + param manifest; coupled-mode p5 reads `PARAMS[name]` and redraws on change; audio declares matching `params` (live, no recompile); one slider drives both media.

**Later enhancements**
5. Determinism (seed from title hash) + richer LLM mapping hints (brightness/motion).
6. Geometry sonification (approach B) — optional canvas/feature extraction for a "literal" mode.

---

## 10. Decisions (locked)

1. **Interactive coupling is core to v1** — not deferred. Sliders that change the p5 preview must also modulate the audio live.
2. **Shared `PARAMS` bus** (§5), not the DOM-bridge — the robust contract, since coupling is the headline feature.
3. **4 moods + Auto**: Dreamy / Energetic-Electric / Dark / Organic.
4. **Lite cost mode** for auto-gen (code + auto-fix; concept & explain skipped). Full stays available for manual generation.
5. **Live + muted**: the patch auto-plays on generation but starts behind a mute toggle that defaults ON; unmuting reveals the live, slider-modulated sound.

### Still to confirm before coding
- **Where the mood selector + auto-toggle live** in the UI (settings panel vs near the generate button).
- **Determinism** (§8): seed audio from the sketch title so the same sketch reproduces the same patch — yes/no.
- **Mute scope**: a dedicated audio mute, or reuse Volume=0 as "muted"? (Recommend a dedicated toggle so Volume keeps its value.)
