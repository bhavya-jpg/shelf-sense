import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Eyebrow, Grid } from "../components/ui";
import { C, F } from "../theme";
import { lineAt, prog, rise } from "../lib";

const NEXT = ["Better counting under occlusion", "Human verification of uncertain findings", "Evaluation on many more shelves"];

export const S10Close: React.FC = () => {
  const frame = useCurrentFrame();
  const l1 = lineAt("s10_close", 1);
  const out = prog(frame, l1 - 8, 16);
  return (
    <AbsoluteFill>
      <Grid reveal={false} />
      <div style={{ position: "absolute", left: 120, top: 130, width: 1680, opacity: 1 - out }}>
        <Eyebrow style={rise(frame, 0)}>[09] Next · planned, not built</Eyebrow>
        <div style={{ marginTop: 40, borderTop: `1.5px solid ${C.line}` }}>
          {NEXT.map((n, i) => (
            <div key={n} style={{ display: "flex", gap: 34, alignItems: "baseline", padding: "30px 0", borderBottom: `1.5px solid ${C.line}`, ...rise(frame, 8 + i * 22, 20, 14) }}>
              <span style={{ fontFamily: F.mono, fontSize: 22, color: C.lime }}>[0{i + 1}]</span>
              <span style={{ fontFamily: F.display, fontWeight: 600, fontSize: 64, letterSpacing: "-0.035em", color: C.tx }}>{n}</span>
            </div>
          ))}
        </div>
      </div>
      <div style={{ position: "absolute", left: 110, top: 250, opacity: out }}>
        <div style={{ fontFamily: F.display, fontWeight: 600, fontSize: 250, letterSpacing: "-0.065em", lineHeight: 0.84, color: C.tx, translate: `0px ${(1 - out) * 30}px` }}>
          Shelf<span style={{ color: C.lime }}>-</span>Sense
        </div>
        <div style={{ fontFamily: F.display, fontWeight: 500, fontSize: 52, letterSpacing: "-0.02em", color: C.mu, marginTop: 44, ...rise(frame, l1 + 10) }}>
          AMD-hosted vision. Decisions in code. <span style={{ color: C.tx }}>Honest about its limits.</span>
        </div>
        <div style={{ fontFamily: F.mono, fontSize: 26, color: C.lime, marginTop: 60, ...rise(frame, l1 + 30) }}>github.com/bhavya-jpg/shelf-sense</div>
      </div>
      <div style={{ position: "absolute", left: 120, right: 120, bottom: 12, display: "flex", justifyContent: "space-between", fontFamily: F.mono, fontSize: 17, color: C.dim, letterSpacing: "0.04em", opacity: out }}>
        <span>Narration: synthetic voice (Chatterbox, Resemble AI). Footage: the real app and real AMD inference; the wait is sped up.</span>
        <span>AMD Developer Hackathon: ACT III</span>
      </div>
    </AbsoluteFill>
  );
};
