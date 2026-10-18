import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Eyebrow, Grid } from "../components/ui";
import { C, F } from "../theme";
import { lineAt, prog, rise } from "../lib";

const NODES = [
  { h: "Photo + spec", p: "EXIF-rotated, resized to ≤1024 px. Spec sent as text, no prices.", kind: "code", line: 1 },
  { h: "AMD Token Factory", p: "Gemma-4-31B-IT counts each product, shelf by shelf.", kind: "model", line: 1, d: 16 },
  { h: "Validation", p: "Schema check, one retry; unreliable counts go to review.", kind: "code", line: 2 },
  { h: "Calculator", p: "Verdict and margin estimate in plain Python.", kind: "code", line: 3 },
  { h: "Action note", p: "Template; AMD may reword. Numbers come from code.", kind: "code", line: 3, d: 18 },
];

export const S7Arch: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Grid reveal={false} />
      <div style={{ position: "absolute", left: 120, top: 110, ...rise(frame, 0) }}>
        <Eyebrow>[06] Architecture</Eyebrow>
        <div style={{ fontFamily: F.display, fontWeight: 600, fontSize: 84, letterSpacing: "-0.04em", lineHeight: 1, color: C.tx, marginTop: 22 }}>
          One Python process. <span style={{ color: C.dim }}>One model call.</span>
        </div>
      </div>
      <div style={{ position: "absolute", left: 120, right: 120, top: 400, display: "flex", alignItems: "stretch", gap: 0 }}>
        {NODES.map((n, i) => {
          const at = lineAt("s7_arch", n.line) + (n.d ?? 0);
          const p = prog(frame, at, 20);
          const model = n.kind === "model";
          return (
            <div key={n.h} style={{ display: "flex", alignItems: "center", flex: 1 }}>
              <div style={{ flex: 1, minHeight: 300, padding: "28px 26px", border: `1.5px solid ${model ? C.lime : C.line2}`, background: model ? "rgba(205,255,63,0.08)" : C.s1, borderRadius: 6, opacity: 0.18 + 0.82 * p, translate: `0px ${(1 - p) * 20}px` }}>
                <div style={{ fontFamily: F.mono, fontSize: 18, color: model ? C.lime : C.mu, letterSpacing: "0.08em" }}>[0{i + 1}] {model ? "MODEL" : "CODE"}</div>
                <div style={{ fontFamily: F.display, fontWeight: 600, fontSize: 34, letterSpacing: "-0.02em", color: C.tx, margin: "34px 0 12px" }}>{n.h}</div>
                <div style={{ fontFamily: F.sans, fontSize: 22, lineHeight: 1.45, color: C.mu }}>{n.p}</div>
              </div>
              {i < NODES.length - 1 ? (
                <div style={{ width: 34, height: 2, background: C.line2, position: "relative" }}>
                  <div style={{ position: "absolute", inset: 0, background: C.lime, scale: `${prog(frame, at + 10, 16)} 1`, transformOrigin: "0 50%" }} />
                </div>
              ) : null}
            </div>
          );
        })}
      </div>
      <div style={{ position: "absolute", left: 120, top: 760, display: "flex", gap: 40, fontFamily: F.mono, fontSize: 21, color: C.mu, letterSpacing: "0.05em", ...rise(frame, lineAt("s7_arch", 3) + 30) }}>
        <span><span style={{ color: C.lime }}>■</span> model output</span>
        <span><span style={{ color: C.tx }}>□</span> code: validation, verdict, money, wording checks</span>
        <span style={{ color: C.dim }}>Streamlit · Python · Pydantic · Docker</span>
      </div>
    </AbsoluteFill>
  );
};
