import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Badge, Eyebrow, Frame, Grid } from "../components/ui";
import { C, F } from "../theme";
import { lineAt, prog, rise } from "../lib";
import { Pan } from "./common";

const W = 1008, H = 640;

export const S5Results: React.FC = () => {
  const frame = useCurrentFrame();
  const l1 = lineAt("s5_results", 1);
  const l2 = lineAt("s5_results", 2);
  const swap = interpolate(frame, [l1 - 6, l1 + 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const row = (label: string, value: React.ReactNode, at: number) => (
    <div style={{ padding: "22px 0", borderBottom: `1.5px solid ${C.line}`, ...rise(frame, at, 18, 14) }}>
      <div style={{ fontFamily: F.mono, fontSize: 18, letterSpacing: "0.1em", textTransform: "uppercase", color: C.mu }}>{label}</div>
      <div style={{ fontFamily: F.display, fontWeight: 600, fontSize: 40, letterSpacing: "-0.02em", color: C.tx, marginTop: 8 }}>{value}</div>
    </div>
  );
  return (
    <AbsoluteFill>
      <Grid reveal={false} />
      <div style={{ position: "absolute", left: 120, top: 110, width: 560 }}>
        <Eyebrow style={rise(frame, 0)}>[04] The result</Eyebrow>
        <div style={{ fontFamily: F.display, fontWeight: 600, fontSize: 64, letterSpacing: "-0.04em", lineHeight: 1, color: C.tx, marginTop: 20, ...rise(frame, 4) }}>
          Counted shelf by shelf. <span style={{ color: C.dim }}>Decided in code.</span>
        </div>
        <div style={{ marginTop: 36, borderTop: `1.5px solid ${C.line}` }}>
          {row("Koko Krunch · per shelf", <span style={{ fontFamily: F.mono, fontSize: 36 }}>2 / <span style={{ color: C.amber }}>1</span> / 2 / 2</span>, 14)}
          {row("Discrepancy", <span>7 of 8 · <span style={{ color: C.amber }}>partial</span></span>, l1)}
          {row("Estimated margin at risk", <span>$1.00 <span style={{ fontFamily: F.mono, fontSize: 20, color: C.mu }}>computed in code</span></span>, l1 + 18)}
        </div>
        <div style={{ marginTop: 28, ...rise(frame, l2) }}>
          <Badge kind="warn" size={20}>Unverified · AI-estimated counts</Badge>
          <div style={{ fontFamily: F.mono, fontSize: 19, color: C.dim, marginTop: 14 }}>Demo margins: $1.00 per unit (assumption)</div>
        </div>
      </div>
      <Frame label="inspect · result" right="real screenshot, same run" style={{ left: 760, top: 150, width: W + 32, height: H + 68, opacity: prog(frame, 6, 20) }}>
        <div style={{ position: "absolute", inset: 0, opacity: 1 - swap }}>
          <Pan src="img/inspect_table.png" w={W} h={H} regions={[{ x: 740, y: 420, w: 1090, h: 430 }]} at={[0]} />
        </div>
        <div style={{ position: "absolute", inset: 0, opacity: swap }}>
          <Pan src="img/inspect_verdict.png" w={W} h={H} regions={[{ x: 740, y: 200, w: 1090, h: 420 }, { x: 740, y: 340, w: 1090, h: 420 }]} at={[0, l2]} />
        </div>
      </Frame>
    </AbsoluteFill>
  );
};
