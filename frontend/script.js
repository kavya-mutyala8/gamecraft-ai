// =====================================================================
// SETTINGS: change these if needed
// =====================================================================
const API_ORIGIN = "http://localhost:8000"; // where Shabharish's backend runs
const API_BASE = API_ORIGIN + "/api/v1";
const DEMO_MODE = false; // true = fake data, no backend needed (good for a quick UI check)
const ENGINE = "universal"; // export layout: universal | godot | unity | unreal
const DEMO_MS = 6500; // how long the demo "generation" takes
// =====================================================================
// Backend flow (gamecraft-backend):
//   POST /analyze        -> project + art bible + 4 blueprints
//   POST /generate/batch -> job; then GET /jobs/{id} until completed/partial/failed
//   POST /assets/{id}/regenerate
//   GET  /projects/{id}/export?engine=...  -> ZIP with manifest.json
// =====================================================================

const ICONS = {
  sparkles:
    '<path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/><path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/>',
  arrow: '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
  refresh:
    '<path d="M21 12a9 9 0 1 1-9-9c2.52 0 4.93 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/>',
  pencil:
    '<path d="M17 3a2.85 2.83 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5Z"/><path d="m15 5 4 4"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  circleCheck: '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
  loader:
    '<path d="M12 2v4"/><path d="m16.2 7.8 2.9-2.9"/><path d="M18 12h4"/><path d="m16.2 16.2 2.9 2.9"/><path d="M12 18v4"/><path d="m4.9 19.1 2.9-2.9"/><path d="M2 12h4"/><path d="m4.9 4.9 2.9 2.9"/>',
  dashed:
    '<path d="M10.1 2.182a10 10 0 0 1 3.8 0"/><path d="M13.9 21.818a10 10 0 0 1-3.8 0"/><path d="M17.609 3.721a10 10 0 0 1 2.69 2.7"/><path d="M2.182 13.9a10 10 0 0 1 0-3.8"/><path d="M20.279 17.609a10 10 0 0 1-2.7 2.69"/><path d="M21.818 10.1a10 10 0 0 1 0 3.8"/><path d="M3.721 6.391a10 10 0 0 1 2.7-2.69"/><path d="M6.391 20.279a10 10 0 0 1-2.69-2.7"/>',
  pen: '<path d="m12 19 7-7 3 3-7 7-3-3z"/><path d="m18 13-1.5-7.5L2 2l3.5 14.5L13 18l5-5z"/><path d="m2 2 7.586 7.586"/><circle cx="11" cy="11" r="2"/>',
  layers:
    '<path d="m12.83 2.18a2 2 0 0 0-1.66 0L2.6 6.08a1 1 0 0 0 0 1.83l8.58 3.91a2 2 0 0 0 1.66 0l8.58-3.9a1 1 0 0 0 0-1.83Z"/><path d="m22 17.65-9.17 4.16a2 2 0 0 1-1.66 0L2 17.65"/><path d="m22 12.65-9.17 4.16a2 2 0 0 1-1.66 0L2 12.65"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>',
  box: '<path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z"/><path d="m3.3 7 8.7 5 8.7-5"/><path d="M12 22V12"/>',
  gem: '<path d="M6 3h12l4 6-10 13L2 9Z"/><path d="M11 3 8 9l4 13 4-13-3-6"/><path d="M2 9h20"/>',
  download:
    '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/>',
};

const STEP_NAMES = ["Concept", "Style bible", "Generating", "Asset pack"];
// label shown in the UI -> id the backend expects
const STYLE_IDS = {
  "Pixel art": "pixel_art",
  "Hand-painted": "hand_painted_fantasy",
  "Low-poly 3D": "low_poly_3d",
  "Retro anime": "retro_anime",
  "Dark gothic": "dark_gothic",
  "Sci-fi vector": "sci_fi_vector",
};
const STYLES = Object.keys(STYLE_IDS);
const CAT_LABEL = {
  character: "Character",
  environment: "Environment",
  weapon: "Weapon",
  icon: "Inventory icon",
};
const CAT_ORDER = ["character", "environment", "weapon", "icon"];
const FOOTERS = [
  "One concept. One world. Every asset belongs.",
  "One concept. One world. Every asset belongs.",
  "Every asset follows your art bible.",
  "Your pack includes a manifest.json for your game engine.",
];
const BIBLE_CARDS = [
  { key: "theme", title: "Theme", icon: "sparkles" },
  { key: "lighting", title: "Lighting & atmosphere", icon: "sun" },
  { key: "shape", title: "Shape language", icon: "pen" },
  { key: "keywords", title: "Style keywords", icon: "gem" },
  { key: "style", title: "Art style", icon: "layers", readonly: true },
];
const GEN_STEPS = [
  { name: "Understanding concept", at: 0 },
  { name: "Locking the style", at: 10 },
  { name: "Generating assets", at: 20 },
  { name: "Packing your results", at: 96 },
];

// Demo-only data (used when DEMO_MODE = true)
const DEMO_ASSETS = [
  { category: "character", name: "Fernwood ranger" },
  { category: "environment", name: "Elderwood clearing" },
  { category: "weapon", name: "Thornwood blade" },
  { category: "icon", name: "Mooncap mushroom" },
];
const PRESETS = {
  "Pixel art": {
    palette: ["#1f4d3a", "#5f9455", "#b7db9b", "#e8b85a", "#9575c2"],
    note: "Forest greens · amber warmth · lavender magic",
    lighting: "Dappled woodland glow. Warm light from the upper left.",
    shape: "Crisp, stepped pixel edges. Clean silhouettes, no anti-aliasing.",
    keywords: "pixel clusters, moss, bark, magic crystal",
  },
  "Hand-painted": {
    palette: ["#2f3a4a", "#7a9e7e", "#f2d6a2", "#d98f6b", "#8fb7c9"],
    note: "Inky blues · soft greens · warm paper",
    lighting: "Soft daylight with gentle shadows.",
    shape: "Loose, painterly outlines with visible brush strokes.",
    keywords: "watercolor, paper grain, storybook",
  },
  "Low-poly 3D": {
    palette: ["#264653", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51"],
    note: "Deep teal · sunny gold · warm coral",
    lighting: "Single warm key light from the upper right.",
    shape: "Faceted flat triangles, no outlines.",
    keywords: "flat shading, matte plastic, stone",
  },
  "Retro anime": {
    palette: ["#2b2d6e", "#4f7cff", "#ff8fb1", "#ffe28a", "#7be0c3"],
    note: "Night blues · candy pinks · bright accents",
    lighting: "Bright, high-contrast light with rim highlights.",
    shape: "Clean ink outlines with cel shading.",
    keywords: "cel shading, film grain, glowing gems",
  },
  "Dark gothic": {
    palette: ["#14121b", "#3b2f4a", "#7d3c4a", "#b08d57", "#8aa39b"],
    note: "Shadow violets · dried blood · tarnished gold",
    lighting: "Low torchlight glow against cold shadows.",
    shape: "Rough, heavy outlines with ornate detail.",
    keywords: "iron, bone, cracked stone",
  },
  "Sci-fi vector": {
    palette: ["#0f172a", "#22d3ee", "#e879f9", "#f8fafc", "#facc15"],
    note: "Deep space · neon cyan · plasma magenta",
    lighting: "Cool ambient light with neon accents.",
    shape: "Sharp geometric shapes, flat colors.",
    keywords: "neon, hull panels, holograms",
  },
};

// ---------------------------------------------------------------- helpers
const $ = (s, r = document) => r.querySelector(s);
const esc = (s) =>
  String(s ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const icon = (name, size = 20) =>
  `<svg class="ic" width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name]}</svg>`;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const slug = (s) =>
  String(s)
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "") || "asset";
const shortText = (t, n = 34) =>
  t.length > n ? t.slice(0, n - 1).trimEnd() + "…" : t;
function toHex(c) {
  c = String(c || "");
  if (/^#[0-9a-f]{6}$/i.test(c)) return c;
  if (/^#[0-9a-f]{3}$/i.test(c))
    return (
      "#" +
      c
        .slice(1)
        .split("")
        .map((x) => x + x)
        .join("")
    );
  return "#000000";
}
function deriveTitle(text) {
  const words = text
    .replace(/[^\w\s'-]/g, " ")
    .split(/\s+/)
    .filter(Boolean);
  while (words.length > 2 && /^(a|an|the)$/i.test(words[0])) words.shift();
  const t = words
    .slice(0, 4)
    .map((w) => w[0].toUpperCase() + w.slice(1))
    .join(" ");
  return t.length >= 2 ? t : "My Game";
}

// ---------------------------------------------------------------- state
const state = {
  step: 1,
  concept: "",
  style: "Pixel art",
  project: null, // what /analyze returned (project_id, art_bible, blueprints)
  bible: null, // what the style bible screen shows and edits
  dirty: false, // true if the user edited the bible
  editing: new Set(),
  assets: [],
  progress: 0,
  jobInfo: null,
  live: "",
  error: "",
};
const view = $("#view");
let viewerIndex = -1;

// ---------------------------------------------------------------- API layer
async function api(path, { method = "POST", body, timeoutMs = 120000 } = {}) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  let res;
  try {
    res = await fetch(API_BASE + path, {
      method,
      headers: body ? { "Content-Type": "application/json" } : {},
      body: body ? JSON.stringify(body) : undefined,
      signal: ctrl.signal,
    });
  } catch (e) {
    if (e.name === "AbortError")
      throw new Error("The server took too long to respond.");
    throw new Error(`Can't reach the backend at ${API_ORIGIN}. Is it running?`);
  } finally {
    clearTimeout(timer);
  }
  if (!res.ok) {
    let msg = `Server returned ${res.status}`;
    try {
      const j = await res.json();
      if (j.error) {
        msg = j.error.message || msg;
        if (Array.isArray(j.error.details))
          msg +=
            " (" +
            j.error.details.map((d) => `${d.field}: ${d.message}`).join("; ") +
            ")";
      }
    } catch {
      /* body wasn't JSON */
    }
    throw new Error(msg);
  }
  return res.json();
}

function fromArtBible(ab) {
  const pal = ab.palette.slice(0, 5);
  return {
    palette: pal.map((p) => p.hex),
    paletteNote: pal.map((p) => p.name).join(" · "),
    theme: { text: ab.theme_summary },
    lighting: { text: ab.lighting_atmosphere },
    shape: { text: ab.silhouette_guidelines },
    keywords: { text: ab.style_keywords.join(", ") },
    style: { text: state.style },
  };
}

function demoBible() {
  const p = PRESETS[state.style] || PRESETS["Pixel art"];
  return {
    palette: [...p.palette],
    paletteNote: p.note,
    theme: { text: shortText(state.concept, 120) },
    lighting: { text: p.lighting },
    shape: { text: p.shape },
    keywords: { text: p.keywords },
    style: { text: state.style },
  };
}

async function analyze() {
  if (DEMO_MODE) {
    await sleep(700);
    state.project = { project_id: "demo", blueprints: [] };
    return demoBible();
  }
  const res = await api("/analyze", {
    body: {
      title: deriveTitle(state.concept),
      genre: "Video game",
      synopsis: state.concept,
      art_style: STYLE_IDS[state.style],
    },
  });
  state.project = res;
  return fromArtBible(res.art_bible);
}

function placeholder(label, seed) {
  const c = state.bible.palette;
  const a = c[seed % c.length],
    b = c[(seed + 2) % c.length],
    d = c[(seed + 4) % c.length];
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
    <rect x="160" y="96" width="192" height="64" fill="${b}"/><rect x="128" y="160" width="256" height="192" fill="${a}"/>
    <rect x="192" y="352" width="128" height="32" fill="${d}"/>
    <rect x="128" y="160" width="256" height="192" fill="none" stroke="#1d1b3a" stroke-width="8"/>
    <text x="256" y="448" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="700" fill="#1d1b3a">${esc(label)}</text></svg>`;
  return "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
}

function toUiAsset(a, v = 0) {
  return {
    id: a.id,
    type: CAT_LABEL[a.category] || a.category,
    order: CAT_ORDER.indexOf(a.category),
    name: a.name,
    ratio: a.aspect_ratio || "",
    status: a.status,
    url: a.image_url ? API_ORIGIN + a.image_url + (v ? `?v=${v}` : "") : "",
    error: (a.error && a.error.message) || "",
    loading: false,
    v,
  };
}

// If the user edited the style bible, send the edits to the backend as extra instructions in each prompt.
function buildBlueprints() {
  if (!state.dirty || !state.project.blueprints) return null;
  const b = state.bible;
  const rules =
    `Art direction (follow strictly): palette ${b.palette.join(", ")}. Lighting: ${b.lighting.text}. Shape language: ${b.shape.text}. Keywords: ${b.keywords.text}.`.slice(
      0,
      700,
    );
  return state.project.blueprints.map((bp) => ({
    ...bp,
    prompt: bp.prompt.slice(0, 1499 - rules.length) + " " + rules,
  }));
}

async function generateReal() {
  const body = { project_id: state.project.project_id };
  const bps = buildBlueprints();
  if (bps) body.blueprints = bps;
  let job = await api("/generate/batch", { body });
  const t0 = Date.now();
  for (;;) {
    state.jobInfo = { done: job.completed + job.failed, total: job.total };
    state.progress = job.total
      ? 20 + 76 * (state.jobInfo.done / job.total)
      : 20;
    const first = job.assets.find(
      (a) => a.status === "completed" && a.image_url,
    );
    if (first) state.live = API_ORIGIN + first.image_url;
    paintProgress();
    if (["completed", "partial", "failed"].includes(job.status)) break;
    if (Date.now() - t0 > 5 * 60 * 1000)
      throw new Error("Generation is taking too long. Try again.");
    await sleep(1500);
    job = await api(`/jobs/${job.job_id}`, { method: "GET", timeoutMs: 30000 });
  }
  const assets = job.assets
    .map((a) => toUiAsset(a))
    .sort((a, b) => a.order - b.order);
  if (!assets.some((a) => a.status === "completed")) {
    const err = job.assets.find((a) => a.error);
    throw new Error(err ? err.error.message : "No images were generated.");
  }
  return assets;
}

async function generateDemo() {
  await sleep(DEMO_MS);
  return DEMO_ASSETS.map((a, i) => ({
    id: "demo-" + i,
    type: CAT_LABEL[a.category],
    order: i,
    name: a.name,
    ratio: "1:1",
    status: "completed",
    url: placeholder(a.name, i),
    error: "",
    loading: false,
    v: 0,
  }));
}

async function regenerateOne(i) {
  const a = state.assets[i];
  if (DEMO_MODE) {
    await sleep(900);
    a.url = placeholder(a.name, i + Math.floor(Math.random() * 5) + 1);
    return;
  }
  const out = await api(`/assets/${a.id}/regenerate`, {
    body: {},
    timeoutMs: 120000,
  });
  if (out.status !== "completed")
    throw new Error((out.error && out.error.message) || "Regeneration failed.");
  state.assets[i] = { ...toUiAsset(out, Date.now()), order: a.order }; // ?v= makes the browser load the new image
}

// ---------------------------------------------------------------- views
function renderStepper() {
  $("#stepper").innerHTML = STEP_NAMES.map((name, idx) => {
    const n = idx + 1;
    const cls =
      n < state.step ? "done" : n === state.step ? "active" : "pending";
    const label =
      cls === "done" ? `${icon("check", 14)} ${name}` : `<b>0${n}</b> ${name}`;
    const canGo = cls === "done" && n < 3 && state.step !== 3;
    return `<button type="button" class="step ${cls}" ${canGo ? `data-go="${n}"` : 'tabindex="-1"'} ${cls === "active" ? 'aria-current="step"' : ""}>${label}</button>`;
  }).join("");
}

function head(title, sub, right) {
  return `<div class="head"><div><h2 tabindex="-1">${title}</h2><p>${sub}</p></div>${right}</div>`;
}

function viewConcept() {
  return `
    ${head("A whole game world starts here.", "Tell us what you’re making. We’ll take care of the art direction.", '<span class="stepno">STEP 01 / 04</span>')}
    <section class="panel">
      <label for="concept" class="title">Your game concept</label>
      <textarea id="concept" class="concept" maxlength="300" placeholder="A fantasy game set in an enchanted forest">${esc(state.concept)}</textarea>
      <div class="hint"><span>A setting, a mood, a hero. One sentence is all you need.</span><span id="count">${state.concept.length}/300</span></div>
      <fieldset>
        <legend class="title">Art style</legend>
        <div class="chips">${STYLES.map(
          (s) =>
            `<label><input type="radio" name="style" value="${esc(s)}" ${s === state.style ? "checked" : ""}><span>${esc(s)}</span></label>`,
        ).join("")}</div>
      </fieldset>
      <button type="button" class="btn btn-yellow btn-wide" data-action="make-bible">${icon("sparkles")} Generate assets</button>
      ${state.error ? `<p class="error" role="alert">${esc(state.error)}</p>` : ""}
    </section>
    <p class="note">${icon("box", 22)} Your starter pack: 1 character · 1 environment · 1 weapon · 1 inventory icon</p>`;
}

function bibleCard(c) {
  const d = state.bible[c.key];
  const ed = state.editing.has(c.key);
  const btn = c.readonly
    ? ""
    : `<button type="button" class="iconbtn" data-action="edit" data-key="${c.key}" aria-label="${ed ? "Save" : "Edit"} ${c.title}">${icon(ed ? "check" : "pencil")}</button>`;
  return `<article class="card">
    <div class="card-h"><h3>${icon(c.icon)} ${c.title}</h3>${btn}</div>
    ${
      ed
        ? `<textarea class="ed" data-f="${c.key}-text" rows="4" aria-label="${c.title}">${esc(d.text)}</textarea>`
        : `<p class="b">${esc(d.text)}</p>`
    }
  </article>`;
}

function viewBible() {
  const b = state.bible;
  const ed = state.editing.has("palette");
  return `
    ${head("Review your art direction", "The rules that make every asset feel like it belongs.", '<span class="stepno">STEP 02 / 04</span>')}
    <div class="banner">${icon("sparkles")}<span>${esc(shortText(state.concept, 90))}</span><small>${esc(state.style)}</small></div>
    <div class="bible">
      <article class="card">
        <div class="card-h"><h3>Palette</h3>
          <button type="button" class="iconbtn" data-action="edit" data-key="palette" aria-label="${ed ? "Save" : "Edit"} palette">${icon(ed ? "check" : "pencil")}</button></div>
        <div class="swatches">${b.palette
          .map((c, i) =>
            ed
              ? `<input type="color" data-f="palette" value="${toHex(c)}" aria-label="Color ${i + 1}">`
              : `<div class="sw" style="background:${esc(c)}" title="${esc(c)}"></div>`,
          )
          .join("")}</div>
        <p class="m" style="margin-top:14px">${esc(b.paletteNote)}</p>
      </article>
      ${BIBLE_CARDS.map(bibleCard).join("")}
    </div>
    ${state.error ? `<p class="error" role="alert">${esc(state.error)}</p>` : ""}
    <div class="actions">
      <button type="button" class="btn btn-yellow btn-wide" data-action="continue">${icon("arrow")} Looks good, continue</button>
      <button type="button" class="btn btn-wide btn-plain" data-action="regen-bible">${icon("refresh")} Regenerate style</button>
    </div>`;
}

function stepsHtml() {
  const p = state.progress;
  let active = 0;
  GEN_STEPS.forEach((s, i) => {
    if (p >= s.at) active = i;
  });
  return GEN_STEPS.map((s, i) => {
    const done = p >= 100 || i < active;
    const cls = done ? "done" : i === active ? "active" : "pending";
    const ic =
      cls === "done" ? "circleCheck" : cls === "active" ? "loader" : "dashed";
    return `<div class="srow ${cls}">${icon(ic)}<span>${s.name}</span></div>`;
  }).join("");
}

function swatchesSm() {
  return `<div class="swatches sm">${state.bible.palette.map((c) => `<div class="sw-sm" style="background:${esc(c)}"></div>`).join("")}</div>`;
}

function liveHtml() {
  return state.live
    ? `<img src="${esc(state.live)}" alt="First finished asset">`
    : `<div class="skeleton"></div>`;
}

function viewGenerating() {
  return `
    ${head("A little magic. A matching world.", "We’re turning your art direction into an asset pack.", '<span class="stepno">STEP 03 / 04</span>')}
    <section class="panel run" aria-live="polite">
      <div>
        <div class="run-h"><strong>Live preview</strong><small>CREATING…</small></div>
        <div class="frame" id="live">${liveHtml()}</div>
        <p class="cap">The first finished asset shows up here.</p>
      </div>
      <div>
        <div class="pct"><span>Crafting your world</span><span id="pct">0%</span></div>
        <div class="bar"><i id="bar" style="width:0%"></i></div>
        <p class="eta" id="eta"></p>
        <div class="steps" id="steps">${stepsHtml()}</div>
        ${swatchesSm()}
        <p class="cap">${esc(state.style)} · ${esc(shortText(state.concept, 30))}</p>
      </div>
    </section>`;
}

let lastLive = "";
function paintProgress() {
  const pct = $("#pct");
  if (!pct) return;
  const p = Math.round(state.progress);
  pct.textContent = p + "%";
  $("#bar").style.width = p + "%";
  let eta;
  if (p >= 100) eta = "Done!";
  else if (DEMO_MODE)
    eta = `About ${Math.max(5, Math.round((100 - p) * (DEMO_MS / 100000)))} seconds remaining`;
  else if (state.jobInfo)
    eta = `${state.jobInfo.done} of ${state.jobInfo.total} assets ready`;
  else eta = "Starting…";
  $("#eta").textContent = eta;
  $("#steps").innerHTML = stepsHtml();
  if (state.live && state.live !== lastLive) {
    lastLive = state.live;
    $("#live").innerHTML = liveHtml();
  }
}

function assetCard(a, i) {
  const failed = a.status === "failed";
  let body;
  if (a.loading)
    body = `<div class="frame loading"><span class="empty">Regenerating…</span></div>`;
  else if (failed || !a.url)
    body = `<div class="frame"><span class="fail">Couldn’t generate this one.${a.error ? " " + esc(a.error) : ""} Try Regenerate.</span></div>`;
  else
    body = `<div class="frame"><img src="${esc(a.url)}" alt="${esc(a.name)}" data-preview="${i}"></div>`;
  const noImg = a.loading || failed || !a.url;
  return `<article class="asset">
    <p class="type">${esc(a.type)}</p><p class="name">${esc(a.name)}</p>
    ${body}
    <div class="meta"><span>${esc(a.ratio)}</span><span>Generated image</span></div>
    <div class="btns">
      <button type="button" class="btn" data-action="preview" data-i="${i}" ${noImg ? "disabled" : ""}>Preview</button>
      <button type="button" class="btn" data-action="regen" data-i="${i}" ${a.loading ? "disabled" : ""}>Regenerate</button>
      <button type="button" class="btn btn-yellow" data-action="download" data-i="${i}" ${noImg ? "disabled" : ""}>Download</button>
    </div></article>`;
}

function viewPack() {
  const n = state.assets.length;
  const ok = state.assets.filter((a) => a.status === "completed").length;
  const thumb = (state.assets.find((a) => a.url) || {}).url || "";
  return `
    ${head("Your world, ready to play.", `${n} assets. One world. Made to belong together.`, `<span class="ready">${icon("circleCheck", 18)} ${ok} / ${n} READY</span>`)}
    <section class="anchor">
      <div class="thumb">${thumb ? `<img src="${esc(thumb)}" alt="">` : ""}</div>
      <div class="info"><strong>Art bible</strong><span>${esc(shortText(state.concept, 40))}</span>
        <small>${esc(state.style)}</small></div>
      <div class="pal"><small>YOUR PALETTE</small>${swatchesSm()}</div>
    </section>
    <div class="grid">${state.assets.map(assetCard).join("")}</div>
    ${state.error ? `<p class="error" role="alert">${esc(state.error)}</p>` : ""}
    <div class="pack-actions">
      <button type="button" class="btn btn-yellow btn-wide" data-action="zip">${icon("download")} Download pack (ZIP + manifest)</button>
      <button type="button" class="btn btn-wide btn-plain" data-action="restart">${icon("refresh")} Start over</button>
    </div>`;
}

function render() {
  renderStepper();
  view.innerHTML = [viewConcept, viewBible, viewGenerating, viewPack][
    state.step - 1
  ]();
  $("#foot-left").textContent = FOOTERS[state.step - 1];
  lastLive = state.live;
}

function go(n) {
  state.step = n;
  render();
  window.scrollTo({ top: 0 });
  const h = $("h2", view);
  if (h) h.focus({ preventScroll: true });
}

// ---------------------------------------------------------------- style bible editing
function collectEdits() {
  state.editing.forEach((k) => {
    if (k === "palette") {
      const vals = [...view.querySelectorAll('[data-f="palette"]')].map(
        (el) => el.value,
      );
      if (
        vals.length &&
        vals.join() !== state.bible.palette.map(toHex).join()
      ) {
        state.bible.palette = vals;
        state.dirty = true;
      }
    } else {
      const t = view.querySelector(`[data-f="${k}-text"]`);
      if (t && t.value.trim() && t.value.trim() !== state.bible[k].text) {
        state.bible[k].text = t.value.trim();
        state.dirty = true;
      }
    }
  });
}

// ---------------------------------------------------------------- actions
async function makeBible(btn) {
  const text = state.concept.trim();
  if (text.length < 10) {
    state.error =
      "Add a bit more detail (at least 10 characters), like “a sci-fi game on a space station”.";
    render();
    $("#concept").focus();
    return;
  }
  state.error = "";
  state.concept = text;
  btn.disabled = true;
  btn.innerHTML = `${icon("loader")} Building your style…`;
  try {
    state.bible = await analyze();
    state.dirty = false;
    state.editing.clear();
    go(2);
  } catch (err) {
    state.error = `Couldn’t build the style: ${err.message}`;
    render();
  }
}

async function regenBible(btn) {
  state.error = "";
  btn.disabled = true;
  btn.innerHTML = `${icon("loader")} Regenerating…`;
  try {
    state.bible = await analyze();
    state.dirty = false;
    state.editing.clear();
    render();
  } catch (err) {
    state.error = `Couldn’t regenerate the style: ${err.message}`;
    render();
  }
}

async function startGenerate() {
  collectEdits();
  state.editing.clear();
  state.error = "";
  state.progress = 0;
  state.jobInfo = null;
  state.live = "";
  go(3);
  let timer = null;
  try {
    let assets;
    if (DEMO_MODE) {
      const t0 = performance.now();
      timer = setInterval(() => {
        state.progress = Math.min(
          92,
          ((performance.now() - t0) / DEMO_MS) * 92,
        );
        paintProgress();
      }, 250);
      paintProgress();
      assets = await generateDemo();
    } else {
      state.progress = 10;
      paintProgress();
      assets = await generateReal();
    }
    if (timer) clearInterval(timer);
    state.progress = 100;
    paintProgress();
    await sleep(600);
    state.assets = assets;
    go(4);
  } catch (err) {
    if (timer) clearInterval(timer);
    state.error = `Couldn’t generate assets: ${err.message}`;
    go(2);
  }
}

async function regenAsset(i) {
  state.error = "";
  state.assets[i].loading = true;
  render();
  try {
    await regenerateOne(i);
  } catch (err) {
    state.error = `Couldn’t regenerate “${state.assets[i].name}”: ${err.message}`;
  }
  state.assets[i].loading = false;
  render();
}

function extFor(blob) {
  const t = (blob.type || "").split("/")[1] || "png";
  return t.replace("svg+xml", "svg").replace("jpeg", "jpg");
}
function saveBlob(blob, filename) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

async function downloadAsset(i) {
  const a = state.assets[i];
  if (!a || !a.url) return;
  try {
    const blob = await (await fetch(a.url)).blob();
    saveBlob(blob, `gamecraft-${slug(a.name)}.${extFor(blob)}`);
  } catch {
    window.open(a.url, "_blank");
  } // fallback if the browser blocks the download
}

async function downloadZip(btn) {
  if (DEMO_MODE) {
    state.error = "ZIP export needs the real backend. Set DEMO_MODE = false.";
    render();
    return;
  }
  btn.disabled = true;
  btn.innerHTML = `${icon("loader")} Packing…`;
  try {
    const res = await fetch(
      `${API_BASE}/projects/${state.project.project_id}/export?engine=${ENGINE}`,
    );
    if (!res.ok) {
      let msg = `Server returned ${res.status}`;
      try {
        msg = (await res.json()).error.message || msg;
      } catch {
        /* not JSON */
      }
      throw new Error(msg);
    }
    const cd = res.headers.get("Content-Disposition") || "";
    const m = /filename="?([^";]+)"?/.exec(cd);
    saveBlob(await res.blob(), m ? m[1] : "gamecraft-asset-pack.zip");
    state.error = "";
  } catch (err) {
    state.error = `Couldn’t export the pack: ${err.message}`;
  }
  render();
}

function openViewer(i) {
  const a = state.assets[i];
  if (!a || !a.url) return;
  viewerIndex = i;
  $("#viewer-img").src = a.url;
  $("#viewer-img").alt = a.name;
  $("#viewer-title").textContent = a.name;
  $("#viewer").showModal();
}

// ---------------------------------------------------------------- events
document.addEventListener("click", (e) => {
  const goBtn = e.target.closest("[data-go]");
  if (goBtn) {
    collectEdits();
    state.error = "";
    go(+goBtn.dataset.go);
    return;
  }
  const img = e.target.closest("img[data-preview]");
  if (img) {
    openViewer(+img.dataset.preview);
    return;
  }
  const el = e.target.closest("[data-action]");
  if (!el) return;
  const i = +el.dataset.i;
  switch (el.dataset.action) {
    case "make-bible":
      makeBible(el);
      break;
    case "regen-bible":
      regenBible(el);
      break;
    case "continue":
      startGenerate();
      break;
    case "edit": {
      collectEdits();
      const k = el.dataset.key;
      state.editing.has(k) ? state.editing.delete(k) : state.editing.add(k);
      render();
      break;
    }
    case "preview":
      openViewer(i);
      break;
    case "download":
      downloadAsset(i);
      break;
    case "regen":
      regenAsset(i);
      break;
    case "zip":
      downloadZip(el);
      break;
    case "restart":
      state.assets = [];
      state.bible = null;
      state.project = null;
      state.error = "";
      go(1);
      break;
  }
});

document.addEventListener("input", (e) => {
  if (e.target.id === "concept") {
    state.concept = e.target.value;
    $("#count").textContent = `${state.concept.length}/300`;
  }
});
document.addEventListener("change", (e) => {
  if (e.target.name === "style") state.style = e.target.value;
});

$("#viewer-close").addEventListener("click", () => $("#viewer").close());
$("#viewer-download").addEventListener("click", () =>
  downloadAsset(viewerIndex),
);
$("#viewer").addEventListener("click", (e) => {
  if (e.target === $("#viewer")) $("#viewer").close();
});

render();
