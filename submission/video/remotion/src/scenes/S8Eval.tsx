import { AbsoluteFill, CanvasImage, interpolate, staticFile, useCurrentFrame } from "remotion";
import { Badge, Eyebrow, Grid } from "../components/ui";
import { C, F } from "../theme";
import { lineAt, prog, rise } from "../lib";

// The half-hidden dark Koko Krunch box on shelf 2, located by hand in data/demo/compliant.png (1354x1024).
const BOX = { x: 138, y: 330, w: 56, h: 167 };
const CROP = { x: 40, y: 290, w: 560, h: 240 };
const VIEW_W = 900;
const S = VIEW_W / CROP.w;

export const S8Eval: React.FC = () => {
  const frame = useCurrentFrame();
  const [l0, l1, l2, l3] = [0, 1, 2, 3].map((i) => lineAt("s8_eval", i));
  const n = Math.round(interpolate(frame, [l1 + 10, l1 + 40], [8, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const cell = (v: string, hit: boolean) => (
    <span style={{ display: "inline-block", minWidth: 64, textAlign: "center", padding: "8px 0", border: `1.5px solid ${hit ? C.red : C.line2}`, color: hit ? C.red : C.tx, background: hit ? "rgba(255,107,87,0.08)" : "transparent", borderRadius: 3 }}>{v}</span>
  );
  return (
    <AbsoluteFill>
      <Grid reveal={false} />
      <div style={{ position: "absolute", left: 120, top: 100, width: 760 }}>
        <Eyebrow style={rise(frame, l0)}>[07] Evaluation · measured, not asserted</Eyebrow>
        <div style={{ fontFamily: F.display, fontWeight: 600, fontSize: 56, letterSpacing: "-0.035em", lineHeight: 1.05, color: C.tx, marginTop: 20, ...rise(frame, l0 + 4) }}>
          A shelf we counted by hand.
        </div>
        <div style={{ fontFamily: F.mono, fontSize: 22, color: C.mu, marginTop: 14, ...rise(frame, l0 + 14) }}>Stars 16 · Koko Krunch 8 · Milo 4 · Trix 4</div>
        <div style={{ marginTop: 50, ...rise(frame, l1) }}>
          <div style={{ fontFamily: F.display, fontWeight: 600, fontSize: 200, lineHeight: 0.85, letterSpacing: "-0.06em", color: C.tx }}>
            8 <span style={{ color: C.dim, fontSize: 110 }}>→</span> <span style={{ color: C.lime }}>{n}</span>
          </div>
          <div style={{ fontFamily: F.sans, fontSize: 28, color: C.mu, marginTop: 18 }}>boxes of counting error, after the shelf-by-shelf prompt</div>
        </div>
        <div style={{ marginTop: 56, ...rise(frame, l3) }}>
          <Badge kind="warn" size={21}>Estimated Margin at Risk (Unverified)</Badge>
          <div style={{ fontFamily: F.sans, fontSize: 26, color: C.mu, marginTop: 16, lineHeight: 1.45 }}>Per-shelf counts are shown, so a person can check the model in seconds.</div>
        </div>
      </div>
      {/* Right: the real photo, shelf 2, with the box the model misses (ground truth, marked by hand). */}
      <div style={{ position: "absolute", left: 900, top: 150, width: VIEW_W, opacity: prog(frame, l2 - 10, 20) }}>
        <div style={{ position: "relative", width: VIEW_W, height: CROP.h * S, overflow: "hidden", borderRadius: 8, border: `1.5px solid ${C.line2}` }}>
          <CanvasImage src={staticFile("img/shelf.jpg")} style={{ position: "absolute", width: 1354 * S, height: 1024 * S, left: -CROP.x * S, top: -CROP.y * S }} />
          <div style={{ position: "absolute", left: (BOX.x - CROP.x) * S, top: (BOX.y - CROP.y) * S, width: BOX.w * S, height: BOX.h * S, border: `3px solid ${C.red}`, borderRadius: 4, opacity: prog(frame, l2 + 20, 14) }} />
        </div>
        <div style={{ display: "flex", justifyContent: "space-between", fontFamily: F.mono, fontSize: 19, color: C.mu, marginTop: 12 }}>
          <span>data/demo/compliant.png · shelf 2</span><span style={{ color: C.red, opacity: prog(frame, l2 + 20, 14) }}>half-hidden box · hand-marked</span>
        </div>
        <div style={{ marginTop: 34, fontFamily: F.mono, fontSize: 26, color: C.tx, display: "grid", gridTemplateColumns: "230px 1fr", rowGap: 16, alignItems: "center", ...rise(frame, l2 + 36) }}>
          <span style={{ color: C.mu, fontSize: 20, letterSpacing: "0.08em", textTransform: "uppercase" }}>Hand count</span>
          <span style={{ display: "flex", gap: 10 }}>{cell("2", false)}{cell("2", false)}{cell("2", false)}{cell("2", false)}<span style={{ marginLeft: 14 }}>= 8</span></span>
          <span style={{ color: C.mu, fontSize: 20, letterSpacing: "0.08em", textTransform: "uppercase" }}>Model</span>
          <span style={{ display: "flex", gap: 10 }}>{cell("2", false)}{cell("1", true)}{cell("2", false)}{cell("2", false)}<span style={{ marginLeft: 14 }}>= 7 · <span style={{ color: C.red }}>100% confident</span></span></span>
        </div>
      </div>
    </AbsoluteFill>
  );
};
