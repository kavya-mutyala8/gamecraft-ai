// =====================================================================
// SETTINGS: change these when the backend is ready
// =====================================================================
const API_BASE = "http://localhost:5000"; // Shabharish's server
const DEMO_MODE = true; // true = fake data, no backend needed. Set to false for the real API.
const STYLE_BIBLE_FROM_API = true; // false = build the style bible in the browser (if backend has no /style-bible)
const DEMO_MS = 6500; // how long the demo "generation" takes
// =====================================================================
// API the backend needs (all POST, JSON):
//  /style-bible  { concept, style }  -> { palette:[5 hex], paletteNote,
//        line:{title,desc}, shading:{..}, lighting:{..}, camera:{..}, materials:{..} }
//  /generate     { concept, style, style_bible } -> { anchor:"url", assets:[{type,name,size,url} x6] }
//                (order: character, environment, weapon, icon, icon, icon)
//  /regenerate   { concept, style, style_bible, asset_type, asset_name, index } -> { url:"..." }
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
const STYLES = [
  "Pixel art",
  "Hand-drawn",
  "Low-poly 3D",
  "Anime",
  "Dark fantasy",
  "Cartoon",
];
const FOOTERS = [
  "One concept. One world. Every asset belongs.",
  "One concept. One world. Every asset belongs.",
  "Consistency first. Every asset follows your style bible.",
  "Transparent PNGs. Ready to drop into your game.",
];
const BIBLE_CARDS = [
  { key: "line", title: "Line style", icon: "pen" },
  { key: "shading", title: "Shading", icon: "layers" },
  { key: "lighting", title: "Lighting", icon: "sun" },
  { key: "camera", title: "Camera angle", icon: "box" },
  { key: "materials", title: "Materials", icon: "gem" },
];
const GEN_STEPS = [
  { name: "Understanding concept", at: 0 },
  { name: "Building style", at: 22 },
  { name: "Creating anchor", at: 48 },
  { name: "Generating assets", at: 72 },
];
const ASSET_PLAN = [
  { type: "Character", name: "Fernwood ranger", size: 512 },
  { type: "Environment", name: "Elderwood clearing", size: 1024 },
  { type: "Weapon", name: "Thornwood blade", size: 512 },
  { type: "Inventory icon", name: "Mooncap mushroom", size: 256 },
  { type: "Inventory icon", name: "Forest elixir", size: 256 },
  { type: "Inventory icon", name: "Whispering crystal", size: 256 },
];

// Demo style presets (used in DEMO_MODE, or when STYLE_BIBLE_FROM_API = false)
const PRESETS = {
  "Pixel art": {
    palette: ["#1f4d3a", "#5f9455", "#b7db9b", "#e8b85a", "#9575c2"],
    note: "Forest greens · amber warmth · lavender magic",
    line: [
      "Crisp, stepped pixel edges",
      "Clean silhouettes. No anti-aliasing.",
    ],
    shading: [
      "Soft, two-tone pixel clusters",
      "Simple forms with just enough depth.",
    ],
    lighting: ["Dappled woodland glow", "Warm light from the upper left."],
    camera: ["Three-quarter isometric", "One perspective across your world."],
    materials: [
      "Moss, bark & magic crystal",
      "Natural textures with lavender accents.",
    ],
  },
  "Hand-drawn": {
    palette: ["#2f3a4a", "#7a9e7e", "#f2d6a2", "#d98f6b", "#8fb7c9"],
    note: "Inky blues · soft greens · warm paper",
    line: ["Loose, inked outlines", "Slight wobble. Visible pen strokes."],
    shading: [
      "Cross-hatching & soft washes",
      "Watercolor-like fills inside the lines.",
    ],
    lighting: ["Soft daylight", "Even light with gentle shadows."],
    camera: [
      "Side view, slightly tilted",
      "Storybook framing across your world.",
    ],
    materials: ["Paper, ink & watercolor", "Textured paper grain throughout."],
  },
  "Low-poly 3D": {
    palette: ["#264653", "#2a9d8f", "#e9c46a", "#f4a261", "#e76f51"],
    note: "Deep teal · sunny gold · warm coral",
    line: ["No outlines, faceted edges", "Flat triangles define every shape."],
    shading: ["Flat color per facet", "Hard light steps between faces."],
    lighting: ["Single warm key light", "Strong light from the upper right."],
    camera: [
      "Three-quarter perspective",
      "Slightly elevated view for every asset.",
    ],
    materials: [
      "Matte plastic & stone",
      "Simple surfaces with no fine texture.",
    ],
  },
  Anime: {
    palette: ["#2b2d6e", "#4f7cff", "#ff8fb1", "#ffe28a", "#7be0c3"],
    note: "Night blues · candy pinks · bright accents",
    line: ["Clean, thin ink lines", "Consistent line weight on every asset."],
    shading: ["Cel shading", "Two hard-edged tones plus highlights."],
    lighting: ["Bright, high-contrast light", "Rim light on the edges."],
    camera: ["Front-facing, eye level", "Dynamic but consistent framing."],
    materials: [
      "Cloth, metal & glowing gems",
      "Smooth surfaces with sharp highlights.",
    ],
  },
  "Dark fantasy": {
    palette: ["#14121b", "#3b2f4a", "#7d3c4a", "#b08d57", "#8aa39b"],
    note: "Shadow violets · dried blood · tarnished gold",
    line: ["Rough, heavy outlines", "Worn edges with ink-like texture."],
    shading: ["Deep, painterly shadows", "Strong contrast, murky midtones."],
    lighting: ["Low torchlight glow", "Warm light against cold shadows."],
    camera: ["Slightly low angle", "Makes every asset feel imposing."],
    materials: ["Iron, bone & cracked stone", "Weathered, scratched surfaces."],
  },
  Cartoon: {
    palette: ["#2d2a4a", "#35b57a", "#ffd23f", "#ff6b6b", "#4dabf7"],
    note: "Bright primaries · friendly contrast",
    line: ["Bold, rounded outlines", "Thick lines with smooth curves."],
    shading: [
      "Flat color with a simple shadow",
      "One soft shadow shape per asset.",
    ],
    lighting: ["Bright and cheerful", "Even light from the top."],
    camera: [
      "Front view, slightly above",
      "Friendly proportions across your world.",
    ],
    materials: ["Soft, chunky shapes", "Simple, toy-like surfaces."],
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
const toHex = (c) => (/^#[0-9a-f]{6}$/i.test(c) ? c : "#000000");

// ---------------------------------------------------------------- state
const state = {
  step: 1,
  concept: "",
  style: "Pixel art",
  bible: null,
  editing: new Set(),
  anchor: "",
  assets: [],
  progress: 0,
  error: "",
};
const view = $("#view");
let viewerIndex = -1;

// ---------------------------------------------------------------- data layer
async function api(path, body, timeoutMs = 120000) {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(API_BASE + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: ctrl.signal,
    });
    if (!res.ok) throw new Error(`Server returned ${res.status}`);
    return await res.json();
  } finally {
    clearTimeout(timer);
  }
}

function demoBible(style) {
  const p = PRESETS[style] || PRESETS["Pixel art"];
  const mk = (a) => ({ title: a[0], desc: a[1] });
  return {
    palette: [...p.palette],
    paletteNote: p.note,
    line: mk(p.line),
    shading: mk(p.shading),
    lighting: mk(p.lighting),
    camera: mk(p.camera),
    materials: mk(p.materials),
  };
}

function normalizeBible(d) {
  const base = demoBible(state.style);
  const pick = (k) =>
    d && d[k] && d[k].title
      ? { title: String(d[k].title), desc: String(d[k].desc || "") }
      : base[k];
  return {
    palette:
      Array.isArray(d?.palette) && d.palette.length >= 3
        ? d.palette.slice(0, 5)
        : base.palette,
    paletteNote: d?.paletteNote || base.paletteNote,
    line: pick("line"),
    shading: pick("shading"),
    lighting: pick("lighting"),
    camera: pick("camera"),
    materials: pick("materials"),
  };
}

async function getBible() {
  if (DEMO_MODE) {
    await sleep(700);
    return demoBible(state.style);
  }
  if (!STYLE_BIBLE_FROM_API) return demoBible(state.style);
  return normalizeBible(
    await api(
      "/style-bible",
      { concept: state.concept, style: state.style },
      60000,
    ),
  );
}

function placeholder(label, seed) {
  const c = state.bible.palette;
  const a = c[seed % c.length],
    b = c[(seed + 2) % c.length],
    d = c[(seed + 4) % c.length];
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="512" height="512" viewBox="0 0 512 512">
    <rect x="160" y="96" width="192" height="64" fill="${b}"/>
    <rect x="128" y="160" width="256" height="192" fill="${a}"/>
    <rect x="192" y="352" width="128" height="32" fill="${d}"/>
    <rect x="128" y="160" width="256" height="192" fill="none" stroke="#1d1b3a" stroke-width="8"/>
    <text x="256" y="448" text-anchor="middle" font-family="sans-serif" font-size="30" font-weight="700" fill="#1d1b3a">${esc(label)}</text></svg>`;
  return "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
}

function normalizeAssets(d) {
  const list = Array.isArray(d) ? d : d.assets || d.images;
  if (!Array.isArray(list) || list.length === 0)
    throw new Error("No images in the response");
  const assets = list.slice(0, ASSET_PLAN.length).map((x, i) => {
    const o = typeof x === "string" ? { url: x } : x;
    return {
      type: o.type || ASSET_PLAN[i].type,
      name: o.name || ASSET_PLAN[i].name,
      size: o.size || ASSET_PLAN[i].size,
      url: o.url || o.image,
      loading: false,
    };
  });
  return { anchor: d.anchor || d.style_anchor || assets[0].url, assets };
}

async function getAssets() {
  if (DEMO_MODE) {
    await sleep(DEMO_MS);
    return {
      anchor: placeholder("Style anchor", 1),
      assets: ASSET_PLAN.map((a, i) => ({
        ...a,
        url: placeholder(a.name, i),
        loading: false,
      })),
    };
  }
  return normalizeAssets(
    await api(
      "/generate",
      { concept: state.concept, style: state.style, style_bible: state.bible },
      180000,
    ),
  );
}

async function getOneAsset(i) {
  const a = state.assets[i];
  if (DEMO_MODE) {
    await sleep(900);
    return placeholder(a.name, i + Math.floor(Math.random() * 5) + 1);
  }
  const d = await api(
    "/regenerate",
    {
      concept: state.concept,
      style: state.style,
      style_bible: state.bible,
      asset_type: a.type,
      asset_name: a.name,
      index: i,
    },
    120000,
  );
  const url = d.url || d.image || (d.images && d.images[0]);
  if (!url) throw new Error("No image in the response");
  return url;
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
    <p class="note">${icon("box", 22)} Your starter pack: 1 character · 1 environment · 1 weapon · 3 inventory icons</p>`;
}

function bibleCard(c) {
  const d = state.bible[c.key];
  const ed = state.editing.has(c.key);
  return `<article class="card">
    <div class="card-h"><h3>${icon(c.icon)} ${c.title}</h3>
      <button type="button" class="iconbtn" data-action="edit" data-key="${c.key}" aria-label="${ed ? "Save" : "Edit"} ${c.title}">${icon(ed ? "check" : "pencil")}</button></div>
    ${
      ed
        ? `<input class="ed" data-f="${c.key}-title" value="${esc(d.title)}" aria-label="${c.title} summary">
         <textarea class="ed" data-f="${c.key}-desc" rows="2" aria-label="${c.title} details">${esc(d.desc)}</textarea>`
        : `<p class="b">${esc(d.title)}</p><p class="m">${esc(d.desc)}</p>`
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

function viewGenerating() {
  return `
    ${head("A little magic. A matching world.", "We’re turning your art direction into an asset pack.", '<span class="stepno">STEP 03 / 04</span>')}
    <section class="panel run" aria-live="polite">
      <div>
        <div class="run-h"><strong>Style anchor</strong><small>CREATING…</small></div>
        <div class="frame"><div class="skeleton"></div></div>
        <p class="cap">The visual north star for your entire pack.</p>
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

function paintProgress() {
  const p = Math.round(state.progress);
  const pct = $("#pct");
  if (!pct) return;
  pct.textContent = p + "%";
  $("#bar").style.width = p + "%";
  $("#eta").textContent =
    p >= 100
      ? "Done!"
      : `About ${Math.max(5, Math.round((100 - p) * (DEMO_MODE ? DEMO_MS / 100000 : 0.6)))} seconds remaining`;
  $("#steps").innerHTML = stepsHtml();
}

function assetCard(a, i) {
  const body = a.loading
    ? `<div class="frame loading"><span class="empty">Regenerating…</span></div>`
    : `<div class="frame"><img src="${esc(a.url)}" alt="${esc(a.name)}" data-preview="${i}"></div>`;
  return `<article class="asset">
    <p class="type">${esc(a.type)}</p><p class="name">${esc(a.name)}</p>
    ${body}
    <div class="meta"><span>${a.size ? `${a.size} × ${a.size}` : ""}</span><span>PNG · Transparent</span></div>
    <div class="btns">
      <button type="button" class="btn" data-action="preview" data-i="${i}" ${a.loading ? "disabled" : ""}>Preview</button>
      <button type="button" class="btn" data-action="regen" data-i="${i}" ${a.loading ? "disabled" : ""}>Regenerate</button>
      <button type="button" class="btn btn-yellow" data-action="download" data-i="${i}" ${a.loading ? "disabled" : ""}>Download</button>
    </div></article>`;
}

function viewPack() {
  const n = state.assets.length;
  return `
    ${head("Your world, ready to play.", `${n} assets. One world. Made to belong together.`, `<span class="ready">${icon("circleCheck", 18)} ${n} / ${n} READY</span>`)}
    <section class="anchor">
      <div class="thumb"><img src="${esc(state.anchor)}" alt="Style anchor"></div>
      <div class="info"><strong>Style anchor</strong><span>${esc(shortText(state.concept, 40))}</span>
        <small>${esc(state.style)} · ${esc(state.bible.camera.title)}</small></div>
      <div class="pal"><small>YOUR PALETTE</small>${swatchesSm()}</div>
    </section>
    <div class="grid">${state.assets.map(assetCard).join("")}</div>
    ${state.error ? `<p class="error" role="alert">${esc(state.error)}</p>` : ""}
    <div class="pack-actions">
      <button type="button" class="btn btn-yellow btn-wide" data-action="zip">${icon("download")} Download all as ZIP</button>
      <button type="button" class="btn btn-wide btn-plain" data-action="restart">${icon("refresh")} Start over</button>
    </div>`;
}

function render() {
  renderStepper();
  view.innerHTML = [viewConcept, viewBible, viewGenerating, viewPack][
    state.step - 1
  ]();
  $("#foot-left").textContent = FOOTERS[state.step - 1];
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
      state.bible.palette = [
        ...view.querySelectorAll('[data-f="palette"]'),
      ].map((el) => el.value);
    } else {
      const t = view.querySelector(`[data-f="${k}-title"]`),
        d = view.querySelector(`[data-f="${k}-desc"]`);
      if (t && d)
        state.bible[k] = {
          title: t.value.trim() || state.bible[k].title,
          desc: d.value.trim(),
        };
    }
  });
}

// ---------------------------------------------------------------- actions
async function makeBible(btn) {
  const text = state.concept.trim();
  if (!text) {
    state.error =
      "Enter a game concept first, like “a sci-fi game on a space station”.";
    render();
    $("#concept").focus();
    return;
  }
  state.error = "";
  state.concept = text;
  btn.disabled = true;
  btn.innerHTML = `${icon("loader")} Building your style…`;
  try {
    state.bible = await getBible();
    state.editing.clear();
    go(2);
  } catch (err) {
    state.error =
      err.name === "AbortError"
        ? "That took too long. Try again in a moment."
        : `Couldn’t build the style bible (${err.message}). Check that the backend is running, then try again.`;
    render();
  }
}

async function regenBible(btn) {
  state.error = "";
  btn.disabled = true;
  btn.innerHTML = `${icon("loader")} Regenerating…`;
  try {
    state.bible = await getBible();
    state.editing.clear();
    render();
  } catch (err) {
    state.error = `Couldn’t regenerate the style (${err.message}).`;
    render();
  }
}

async function startGenerate() {
  collectEdits();
  state.editing.clear();
  state.error = "";
  state.progress = 0;
  go(3);
  const total = DEMO_MODE ? DEMO_MS : 60000;
  const t0 = performance.now();
  const timer = setInterval(() => {
    state.progress = Math.min(92, ((performance.now() - t0) / total) * 92);
    paintProgress();
  }, 250);
  paintProgress();
  try {
    const r = await getAssets();
    clearInterval(timer);
    state.progress = 100;
    paintProgress();
    await sleep(600);
    state.anchor = r.anchor;
    state.assets = r.assets;
    go(4);
  } catch (err) {
    clearInterval(timer);
    state.error =
      err.name === "AbortError"
        ? "Generation took too long. Try again in a moment."
        : `Couldn’t generate assets (${err.message}). Check that the backend is running, then try again.`;
    go(2);
  }
}

async function regenAsset(i) {
  state.error = "";
  state.assets[i].loading = true;
  render();
  try {
    state.assets[i].url = await getOneAsset(i);
  } catch (err) {
    state.error = `Couldn’t regenerate “${state.assets[i].name}” (${err.message}).`;
  }
  state.assets[i].loading = false;
  render();
}

async function saveFile(url, baseName) {
  const blob = await (await fetch(url)).blob();
  const ext = blob.type.includes("svg") ? "svg" : "png";
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${baseName}.${ext}`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
}

async function downloadAsset(i) {
  const a = state.assets[i];
  if (!a) return;
  try {
    await saveFile(a.url, `gamecraft-${slug(a.name)}`);
  } catch {
    window.open(a.url, "_blank");
  } // fallback if the image host blocks fetch
}

async function downloadZip(btn) {
  if (typeof JSZip === "undefined") {
    state.error =
      "ZIP tool didn’t load. Check your internet connection and refresh.";
    render();
    return;
  }
  btn.disabled = true;
  btn.innerHTML = `${icon("loader")} Packing…`;
  const zip = new JSZip();
  const files = [
    { name: "style-anchor", url: state.anchor },
    ...state.assets.map((a) => ({ name: slug(a.name), url: a.url })),
  ];
  const manifest = {
    concept: state.concept,
    style: state.style,
    style_bible: state.bible,
    assets: [],
  };
  for (const f of files) {
    try {
      const blob = await (await fetch(f.url)).blob();
      const file = `${f.name}.${blob.type.includes("svg") ? "svg" : "png"}`;
      zip.file(file, blob);
      manifest.assets.push({ name: f.name, file });
    } catch {
      /* skip files that can't be fetched */
    }
  }
  zip.file("manifest.json", JSON.stringify(manifest, null, 2));
  const out = await zip.generateAsync({ type: "blob" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(out);
  a.download = "gamecraft-asset-pack.zip";
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  render();
}

function openViewer(i) {
  const a = state.assets[i];
  if (!a) return;
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
