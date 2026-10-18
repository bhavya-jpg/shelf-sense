// Shelf-Sense pitch deck (pptxgenjs, structured: theme + layouts + placeholders + sections).
// Usage: node build_deck.js   -> ShelfSense_Pitch_Deck.pptx
// Every screenshot is from one real inspection on the AMD endpoint (submission/video/stills/), and every
// figure comes from docs/experiments/ or the README. Planned work is labelled as planned.
const path = require("path");
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(
  "/Users/bhavya_/.claude/skills/synced/f86d03ca-c2f5-4c44-bab3-4e9ce86c9fa0_f0df4827-f774-4f0f-85e0-ab9ab74bfd48/pptx/scripts/apply_theme.js"
);

const OUT = path.join(__dirname, "ShelfSense_Pitch_Deck.pptx");
const IMG = (n) => path.join(__dirname, "img", n);

const THEME = {
  name: "Shelf-Sense",
  headFontFace: "Arial",
  bodyFontFace: "Arial",
  colors: {
    dk1: "0A0B0C", lt1: "ECEBE6", dk2: "15181A", lt2: "9DA2A8",
    accent1: "CDFF3F", accent2: "F2B24B", accent3: "FF6B57", accent4: "93B4FF", accent5: "31363A", accent6: "6C7177",
    hlink: "CDFF3F", folHlink: "9DA2A8",
  },
};
const HEX = THEME.colors;
const MONO = "Courier New";

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5 in
pres.title = "Shelf-Sense — pitch deck";
pres.author = "Shelf-Sense";
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
const C = pres.SchemeColor;
// Dark deck: ink is dk1 (text1), paper is lt1 (background1).
const INK = C.text1, PAPER = C.background1, SURFACE = C.text2, MUTED = C.background2;
const LIME = C.accent1, AMBER = C.accent2, RED = C.accent3, LINE = C.accent5, DIM = C.accent6;

const W = 13.333, M = 0.6;

pres.defineSlideMaster({
  title: "COVER",
  background: { color: INK },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 1.95, w: 6.4, h: 1.35, fontSize: 66, bold: true, color: PAPER, valign: "top", align: "left", margin: 0 }, text: "" } },
    { placeholder: { options: { name: "body", type: "body", x: M, y: 3.35, w: 6.2, h: 0.6, fontSize: 24, color: MUTED, valign: "top", align: "left", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: INK },
  margin: [0.6, 0.6, 0.7, 0.6],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.72, w: W - 2 * M, h: 0.75, fontSize: 32, bold: true, color: PAPER, valign: "top", align: "left", margin: 0 }, text: "" } },
    { text: { text: "Shelf-Sense · AMD Developer Hackathon: ACT III", options: { x: M, y: 7.0, w: 7, h: 0.3, fontFace: MONO, fontSize: 10, color: DIM, margin: 0 } } },
  ],
  slideNumber: { x: W - M - 0.6, y: 7.0, w: 0.6, h: 0.3, fontFace: MONO, fontSize: 10, color: DIM, align: "right" },
});

const T = (slide, text, o) => slide.addText(text, { isTextBox: true, margin: 0, fontFace: THEME.bodyFontFace, color: PAPER, valign: "top", ...o });
const eyebrow = (slide, text, y = 0.38) => T(slide, text, { x: M, y, w: 10, h: 0.3, fontFace: MONO, fontSize: 12, color: LIME, charSpacing: 2 });
const box = (slide, o) => slide.addShape(pres.shapes.RECTANGLE, { fill: { color: SURFACE }, line: { color: LINE, width: 1 }, ...o });
const img = (slide, file, o) => {
  slide.addShape(pres.shapes.RECTANGLE, { x: o.x - 0.04, y: o.y - 0.04, w: o.w + 0.08, h: o.h + 0.08, fill: { color: SURFACE }, line: { color: LINE, width: 1 }, objectName: `${o.objectName || file} frame` });
  slide.addImage({ path: IMG(file), ...o });
};

// ---------------------------------------------------------------- 1 Cover
pres.addSection({ title: "Shelf-Sense" });
{
  const s = pres.addSlide({ masterName: "COVER", sectionTitle: "Shelf-Sense" });
  eyebrow(s, "[ AMD DEVELOPER HACKATHON: ACT III · REINVENT COMMERCE ]", 0.6);
  s.addText("Shelf-Sense", { placeholder: "title" });
  s.addText("AI-powered retail shelf intelligence", { placeholder: "body" });
  T(s, "Photograph a shelf. Get per-product counts, a compliance verdict, an estimated margin at risk and a restocking list. The model counts; code decides.", { x: M, y: 4.25, w: 5.9, h: 1.2, fontSize: 16, color: MUTED, lineSpacingMultiple: 1.2 });
  T(s, "Gemma-4-31B-IT · AMD Developer Cloud Token Factory", { x: M, y: 6.55, w: 6.3, h: 0.3, fontFace: MONO, fontSize: 11, color: LIME });
  img(s, "verdict.png", { x: 6.95, y: 1.55, w: 5.78, h: 5.78 * 575 / 1136, objectName: "real result screenshot" });
  T(s, "Real result from the app: one inspection on the AMD endpoint", { x: 6.95, y: 4.65, w: 5.78, h: 0.3, fontFace: MONO, fontSize: 10, color: DIM });
  s.addNotes("Shelf-Sense turns one ordinary shelf photograph into a preliminary compliance report. The screenshot is a real result from the app: one call to Gemma-4-31B-IT on AMD Developer Cloud's Token Factory. The money figure is labelled unverified from the first slide on; we'll explain why.");
}

// ---------------------------------------------------------------- 2 Problem
pres.addSection({ title: "Problem and solution" });
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Problem and solution" });
  eyebrow(s, "[01] THE PROBLEM");
  s.addText("Shelves are still checked by eye", { placeholder: "title" });
  T(s, "Missing facings quietly cost margin. Manual shelf walks are slow and inconsistent, and small stores can’t justify dedicated shelf-scanning hardware.", { x: M, y: 1.55, w: 8.6, h: 0.7, fontSize: 16, color: MUTED });
  const cards = [
    ["MANUAL", "Every count is a person with a clipboard", "Checking a bay means walking it, counting facings and writing them down."],
    ["INFREQUENT", "Gaps sit unnoticed between walks", "A missing facing can stay missing until the next scheduled check."],
    ["INCONSISTENT", "Two people, two different counts", "Half-hidden boxes and variants are judged differently each time."],
    ["UNPRICED", "Nobody knows what the gap costs", "Without a number attached, restocking competes with everything else."],
  ];
  const cw = (W - 2 * M - 3 * 0.2) / 4;
  cards.forEach(([tag, h, p], i) => {
    const x = M + i * (cw + 0.2), y = 2.65;
    box(s, { x, y, w: cw, h: 3.95, objectName: `${tag} card` });
    T(s, `[0${i + 1}] ${tag}`, { x: x + 0.25, y: y + 0.25, w: cw - 0.5, h: 0.3, fontFace: MONO, fontSize: 11, color: LIME });
    T(s, `0${i + 1}`, { x: x + 0.25, y: y + 0.65, w: cw - 0.5, h: 0.9, fontSize: 54, bold: true, color: LINE });
    T(s, h, { x: x + 0.25, y: y + 1.6, w: cw - 0.5, h: 1.2, fontSize: 18, bold: true, color: PAPER });
    T(s, p, { x: x + 0.25, y: y + 2.85, w: cw - 0.5, h: 1.0, fontSize: 14, color: MUTED });
  });
  s.addNotes("Shelf audits today are manual: a person counts facings against a planned layout. That's slow, infrequent and inconsistent, and the gap rarely has a cost attached. We're not quoting industry statistics here; these are the operational frictions Shelf-Sense targets.");
}

// ---------------------------------------------------------------- 3 Solution
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Problem and solution" });
  eyebrow(s, "[02] THE SOLUTION");
  s.addText("One photo in, a preliminary compliance report out", { placeholder: "title" });
  const steps = ["Choose a shelf specification", "Add a shelf photograph", "Run one inspection"];
  steps.forEach((t, i) => {
    const y = 1.85 + i * 0.62;
    s.addShape(pres.shapes.LINE, { x: M, y, w: 5.3, h: 0, line: { color: LINE, width: 1 } });
    T(s, `[0${i + 1}]`, { x: M, y: y + 0.16, w: 0.7, h: 0.35, fontFace: MONO, fontSize: 13, color: LIME });
    T(s, t, { x: M + 0.75, y: y + 0.12, w: 4.6, h: 0.4, fontSize: 19, bold: true });
  });
  s.addShape(pres.shapes.LINE, { x: M, y: 1.85 + 3 * 0.62, w: 5.3, h: 0, line: { color: LINE, width: 1 } });
  T(s, "WHAT COMES BACK", { x: M, y: 4.0, w: 5.3, h: 0.3, fontFace: MONO, fontSize: 11, color: DIM, charSpacing: 2 });
  T(s, [
    { text: "Per-product status and shelf-by-shelf counts", options: { bullet: true, breakLine: true } },
    { text: "Discrepancies against the expected inventory", options: { bullet: true, breakLine: true } },
    { text: "Estimated Margin at Risk (Unverified), computed in code", options: { bullet: true, breakLine: true } },
    { text: "A restocking note, labelled with who wrote it", options: { bullet: true } },
  ], { x: M, y: 4.35, w: 5.4, h: 1.9, fontSize: 15, color: PAPER, paraSpaceAfter: 6 });
  img(s, "landing.png", { x: 6.45, y: 1.85, w: 6.28, h: 6.28 * 1080 / 1920, objectName: "landing page screenshot" });
  T(s, "The live web app: landing page, dashboard and method pages", { x: 6.45, y: 5.5, w: 6.28, h: 0.3, fontFace: MONO, fontSize: 10, color: DIM });
  s.addNotes("The user picks a shelf specification, adds a photo and runs one inspection. A vision model counts each product shelf by shelf; plain Python turns those counts into the verdict, the estimated margin at risk and a restocking list. The result is preliminary by design.");
}

// ---------------------------------------------------------------- 4 Product demonstration
pres.addSection({ title: "Product" });
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Product" });
  eyebrow(s, "[03] PRODUCT DEMONSTRATION");
  s.addText("A real inspection, end to end", { placeholder: "title" });
  const chips = ["Specification", "Shelf image", "Inference on AMD", "Results", "Action note"];
  const chipW = 2.25;
  chips.forEach((t, i) => {
    const x = M + i * (chipW + 0.21);
    s.addShape(pres.shapes.RECTANGLE, { x, y: 1.6, w: chipW, h: 0.46, fill: { color: i === 2 ? LIME : SURFACE }, line: { color: i === 2 ? LIME : LINE, width: 1 }, objectName: `step ${t}` });
    T(s, `${i + 1}  ${t}`, { x: x + 0.15, y: 1.6, w: chipW - 0.3, h: 0.46, fontFace: MONO, fontSize: 12, color: i === 2 ? INK : PAPER, valign: "middle" });
  });
  const y = 2.45, h = 3.75;
  img(s, "photo_panel.png", { x: M, y, w: h * 495 / 570, h, objectName: "photo panel" });
  const tw = 4.75;
  img(s, "table.png", { x: 4.1, y, w: tw, h: tw * 640 / 1120, objectName: "results table" });
  const aw = 3.55;
  img(s, "actions.png", { x: 9.18, y, w: aw, h: aw * 730 / 1120, objectName: "action note" });
  T(s, "compliant.png, a self-taken photo of a 4-shelf cereal bay", { x: M, y: y + h + 0.15, w: 3.3, h: 0.5, fontFace: MONO, fontSize: 10, color: DIM });
  T(s, "Per-shelf counts against expected; Koko Krunch 7 of 8 flagged", { x: 4.1, y: y + tw * 640 / 1120 + 0.15, w: tw, h: 0.5, fontFace: MONO, fontSize: 10, color: DIM });
  T(s, "AMD-worded note; names, counts and figures inserted by code", { x: 9.18, y: y + aw * 730 / 1120 + 0.15, w: aw, h: 0.5, fontFace: MONO, fontSize: 10, color: DIM });
  s.addNotes("These three screenshots are from one real run: 13.2 seconds of inspection on the AMD endpoint. The model reported Koko Krunch as 7 of 8 boxes, so the shelf came back non-compliant with an estimated $1.00 at risk, labelled unverified. The action note was worded by Gemma, but every number in it was inserted by code.");
}

// ---------------------------------------------------------------- 5 Architecture
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Product" });
  eyebrow(s, "[04] TECHNICAL ARCHITECTURE");
  s.addText("One Python process, one model call", { placeholder: "title" });
  const nodes = [
    ["CODE", "Streamlit app", "Spec, photo, results UI; three pages"],
    ["CODE", "Inspection + prompt", "EXIF-rotate, resize to 1024 px; spec as text"],
    ["MODEL", "AMD Token Factory", "Gemma-4-31B-IT returns per-shelf counts (JSON)"],
    ["CODE", "Validation", "Pydantic schema, one retry, review flags"],
    ["CODE", "Financial calculation", "Verdict and margin estimate, Decimal maths"],
    ["CODE + MODEL", "Action note", "Template; AMD may reword; numbers from code"],
  ];
  const nw = (W - 2 * M - 5 * 0.22) / 6;
  nodes.forEach(([k, h, p], i) => {
    const x = M + i * (nw + 0.22), y = 1.9, model = k === "MODEL";
    s.addShape(pres.shapes.RECTANGLE, { x, y, w: nw, h: 2.75, fill: { color: model ? LIME : SURFACE, transparency: model ? 88 : 0 }, line: { color: model ? LIME : LINE, width: model ? 1.5 : 1 }, objectName: `${h} node` });
    T(s, k, { x: x + 0.15, y: y + 0.18, w: nw - 0.3, h: 0.3, fontFace: MONO, fontSize: 10, color: model ? LIME : DIM });
    T(s, h, { x: x + 0.15, y: y + 0.65, w: nw - 0.3, h: 0.75, fontSize: 16, bold: true });
    T(s, p, { x: x + 0.15, y: y + 1.45, w: nw - 0.3, h: 1.2, fontSize: 14, color: MUTED });
    if (i < nodes.length - 1) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + nw + 0.03, y: y + 1.27, w: 0.16, h: 0.2, fill: { color: DIM }, line: { color: DIM, width: 0 }, objectName: `arrow ${i + 1}` });
  });
  T(s, [
    { text: "Model output: ", options: { bold: true, color: LIME } },
    { text: "per-product, per-shelf counts and optional wording.  ", options: { color: PAPER } },
    { text: "Code: ", options: { bold: true, color: PAPER } },
    { text: "validation, statuses, the verdict, every dollar figure, and the checks on any AI wording.", options: { color: MUTED } },
  ], { x: M, y: 5.05, w: W - 2 * M, h: 0.7, fontSize: 15 });
  T(s, "Single Docker container on Render · no database · no other model provider · 195 offline tests", { x: M, y: 6.0, w: W - 2 * M, h: 0.35, fontFace: MONO, fontSize: 11, color: DIM });
  s.addNotes("Everything runs in one Python process. The photo and the spec go to the AMD endpoint in a single call; Gemma returns structured counts. Pydantic validates them, invented items are dropped, and unreliable or contradictory counts go to review. The verdict and the money are computed in code; the model never sets a status or a number.");
}

// ---------------------------------------------------------------- 6 Evaluation and limitations
pres.addSection({ title: "Evidence and value" });
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Evidence and value" });
  eyebrow(s, "[05] EVALUATION AND LIMITATIONS");
  s.addText("Measured on a real shelf, reported as measured", { placeholder: "title" });
  const head = (t) => ({ text: t, options: { bold: true, color: DIM, fontFace: MONO, fontSize: 10, fill: { color: SURFACE } } });
  const cell = (t, o = {}) => ({ text: t, options: { color: PAPER, fontSize: 12, ...o } });
  const rows = [
    [head("EXPERIMENT"), head("CHANGE"), head("EXACT"), head("ERROR"), head("SHELF RIGHT")],
    [cell("Baseline"), cell("First prompt"), cell("1 / 4"), cell("8 boxes"), cell("0 of 2")],
    [cell("1 · production", { bold: true, color: LIME }), cell("Shelf-by-shelf prompt"), cell("3 / 4"), cell("1 box"), cell("0 of 3")],
    [cell("2"), cell("1536 px instead of 1024"), cell("3 / 4"), cell("1 box"), cell("0 of 6")],
    [cell("3"), cell("MiniCPM-V instead of Gemma"), cell("3 / 4"), cell("1 box"), cell("0 of 2")],
    [cell("4"), cell("Per-shelf crops (by hand)"), cell("2–3 / 4"), cell("2–3"), cell("3 of 3")],
  ];
  s.addTable(rows, { x: M, y: 1.6, w: 7.1, colW: [1.45, 2.55, 0.95, 1.0, 1.15], border: { type: "solid", color: HEX.accent5, pt: 0.75 }, fill: { color: HEX.dk1 }, rowH: 0.36, margin: [0.04, 0.08, 0.04, 0.08], fontFace: THEME.bodyFontFace });
  img(s, "shelf2_marked.png", { x: 8.05, y: 1.6, w: 4.68, h: 4.68 * 480 / 1120, objectName: "shelf 2 with hidden box marked" });
  T(s, "Shelf 2 of the real photo. Hand count: 2 Koko Krunch. Model: 1, at 100% confidence. Box outlined by hand.", { x: 8.05, y: 3.75, w: 4.68, h: 0.55, fontFace: MONO, fontSize: 10, color: DIM });
  const blocks = [
    ["MEASURED", LIME, "Production misses one half-hidden box in all 9 recorded runs, so the full shelf is reported short."],
    ["EXPERIMENTAL", AMBER, "Per-shelf crops fixed the verdict (3 of 3) but overcounted neighbours. Not adopted."],
    ["DEMO ASSUMPTIONS", AMBER, "$1.00 per-unit margins. One self-taken photo: a case study, not a benchmark."],
    ["FUTURE", DIM, "Occlusion-aware counting, human verification, many more shelves."],
  ];
  const bw = (W - 2 * M - 3 * 0.2) / 4;
  blocks.forEach(([k, col, p], i) => {
    const x = M + i * (bw + 0.2), y = 4.55;
    box(s, { x, y, w: bw, h: 2.05, objectName: `${k} block` });
    T(s, k, { x: x + 0.2, y: y + 0.2, w: bw - 0.4, h: 0.3, fontFace: MONO, fontSize: 11, color: col });
    T(s, p, { x: x + 0.2, y: y + 0.6, w: bw - 0.4, h: 1.35, fontSize: 14, color: PAPER });
  });
  s.addNotes("Ground truth was counted by hand: 16 Stars, 8 Koko Krunch, 4 Milo, 4 Trix. A shelf-by-shelf prompt cut the error from 8 boxes to 1. Higher resolution and a second model didn't fix the last, half-hidden box. Per-shelf cropping did, but it overcounted neighbours and used hand-placed crops, so it isn't in production. That's why every dollar figure is labelled unverified.");
}

// ---------------------------------------------------------------- 7 AMD integration and value
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Evidence and value" });
  eyebrow(s, "[06] AMD INTEGRATION AND VALUE");
  s.addText("Every inspection runs on AMD", { placeholder: "title" });
  const stats = [
    ["18.2 s", "median inspection on the shared endpoint (9 recorded runs, 11.7–45.8 s)"],
    ["1", "vision call per inspection, plus 1 text call to word the actions"],
    ["24", "experiment records kept with the model’s raw replies"],
  ];
  stats.forEach(([v, k], i) => {
    const y = 1.75 + i * 1.5;
    T(s, v, { x: M, y, w: 3.0, h: 1.0, fontSize: 54, bold: true, color: i === 0 ? LIME : PAPER });
    T(s, k, { x: 3.7, y: y + 0.2, w: 3.0, h: 0.9, fontSize: 14, color: MUTED });
  });
  const specs = [
    ["MODEL", "Gemma-4-31B-IT, vision input"],
    ["ENDPOINT", "AMD Developer Cloud Token Factory, OpenAI-compatible chat completions"],
    ["EVIDENCE", "First raw HTTP 200 and every experiment reply kept in the repository"],
    ["NOT CLAIMED", "We call a hosted service: no GPU, vLLM or ROCm claims"],
  ];
  specs.forEach(([k, v], i) => {
    const y = 1.75 + i * 0.78;
    s.addShape(pres.shapes.LINE, { x: 7.1, y, w: 5.63, h: 0, line: { color: LINE, width: 1 } });
    T(s, k, { x: 7.1, y: y + 0.18, w: 1.6, h: 0.3, fontFace: MONO, fontSize: 10, color: DIM });
    T(s, v, { x: 8.75, y: y + 0.14, w: 3.98, h: 0.6, fontSize: 14, color: k === "NOT CLAIMED" ? MUTED : PAPER });
  });
  s.addShape(pres.shapes.RECTANGLE, { x: 7.1, y: 5.15, w: 5.63, h: 1.45, fill: { color: LIME }, line: { color: LIME, width: 1 }, objectName: "value statement" });
  T(s, "Intended value: a fast, photo-based second opinion for store staff on where to look and roughly what is at stake, without shelf-scanning hardware.", { x: 7.35, y: 5.32, w: 5.15, h: 1.15, fontSize: 15, bold: true, color: INK });
  s.addNotes("The integration is real and simple: each inspection is an HTTPS call to the Token Factory endpoint with Gemma-4-31B-IT, and the measured median is 18.2 seconds. We kept the first raw response and every experiment reply. We don't claim which serving software or GPU runs behind the hosted service. The value is intended, not measured in a store yet.");
}

// ---------------------------------------------------------------- 8 Roadmap and closing
pres.addSection({ title: "Close" });
{
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: "Close" });
  eyebrow(s, "[07] ROADMAP · PLANNED, NOT BUILT");
  s.addText("What comes next", { placeholder: "title" });
  const next = [
    "Better product counting under occlusion",
    "Human verification of uncertain findings",
    "Evaluation on diverse shelf images",
    "Reliability testing in a real store",
  ];
  next.forEach((t, i) => {
    const y = 1.8 + i * 0.8;
    s.addShape(pres.shapes.LINE, { x: M, y, w: 6.2, h: 0, line: { color: LINE, width: 1 } });
    T(s, `[0${i + 1}]`, { x: M, y: y + 0.24, w: 0.7, h: 0.35, fontFace: MONO, fontSize: 13, color: LIME });
    T(s, t, { x: M + 0.75, y: y + 0.18, w: 5.4, h: 0.45, fontSize: 19, bold: true });
  });
  s.addShape(pres.shapes.LINE, { x: M, y: 1.8 + 4 * 0.8, w: 6.2, h: 0, line: { color: LINE, width: 1 } });
  T(s, "Shelf-Sense", { x: 7.3, y: 2.0, w: 5.4, h: 1.0, fontSize: 54, bold: true });
  T(s, "AMD-hosted vision. Decisions in code. Honest about its limits.", { x: 7.3, y: 3.1, w: 5.3, h: 0.9, fontSize: 19, color: MUTED });
  T(s, "github.com/bhavya-jpg/shelf-sense", { x: 7.3, y: 4.35, w: 5.4, h: 0.4, fontFace: MONO, fontSize: 14, color: LIME, hyperlink: { url: "https://github.com/bhavya-jpg/shelf-sense" } });
  T(s, "MIT licence · ACT III · Reinvent Commerce", { x: 7.3, y: 4.85, w: 5.4, h: 0.35, fontFace: MONO, fontSize: 10, color: DIM });
  s.addNotes("Next steps follow directly from what we measured: better counting under occlusion, a step where a person verifies uncertain findings, evaluation on many more shelves, and real operational testing. None of that is built yet. Shelf-Sense today is AMD-hosted vision with decisions in code, and it's honest about its limits.");
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT);
})();
