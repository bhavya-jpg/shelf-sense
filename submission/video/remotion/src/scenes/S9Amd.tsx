import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Eyebrow } from "../components/ui";
import { C, F } from "../theme";
import { lineAt, prog, rise } from "../lib";

const SPECS: [string, string][] = [
  ["Model", "Gemma-4-31B-IT, vision input"],
  ["Endpoint", "AMD Developer Cloud · Token Factory (OpenAI-compatible)"],
  ["Calls", "1 vision call per inspection + 1 text call for wording"],
  ["Latency", "18.2 s median · 11.7–45.8 s · 9 recorded runs"],
  ["Not claimed", "We call a hosted service: no GPU or serving-stack claims"],
];

export const S9Amd: React.FC = () => {
  const frame = useCurrentFrame();
  const l1 = lineAt("s9_amd", 1);
  const w = prog(frame, 0, 26);
  return (
    <AbsoluteFill style={{ background: C.bg }}>
      <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: 860 * w, background: C.lime, overflow: "hidden" }}>
        <div style={{ position: "absolute", left: 120, top: 130, width: 640 }}>
          <Eyebrow color={C.bg} style={rise(frame, 10)}>[08] Inference</Eyebrow>
          <div style={{ fontFamily: F.display, fontWeight: 600, fontSize: 100, letterSpacing: "-0.045em", lineHeight: 0.96, color: C.bg, marginTop: 40, ...rise(frame, 14) }}>
            Every inspection runs on AMD.
          </div>
        </div>
        <div style={{ position: "absolute", left: 120, bottom: 300, width: 620, fontFamily: F.sans, fontSize: 30, lineHeight: 1.45, color: "#1E2410", ...rise(frame, l1) }}>
          For a store manager: a fast second opinion on where to look, and roughly what is at stake.
        </div>
      </div>
      <div style={{ position: "absolute", left: 940, right: 120, top: 190, borderTop: `1.5px solid ${C.line}` }}>
        {SPECS.map(([k, v], i) => (
          <div key={k} style={{ display: "grid", gridTemplateColumns: "220px 1fr", padding: "26px 0", borderBottom: `1.5px solid ${C.line}`, ...rise(frame, 16 + i * 10, 18, 12) }}>
            <span style={{ fontFamily: F.mono, fontSize: 19, letterSpacing: "0.1em", textTransform: "uppercase", color: C.dim, paddingTop: 6 }}>{k}</span>
            <span style={{ fontFamily: F.sans, fontSize: 29, color: k === "Not claimed" ? C.mu : C.tx }}>{v}</span>
          </div>
        ))}
      </div>
    </AbsoluteFill>
  );
};
