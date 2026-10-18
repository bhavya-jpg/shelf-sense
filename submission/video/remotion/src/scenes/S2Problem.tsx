import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { Eyebrow, Grid } from "../components/ui";
import { C, F } from "../theme";
import { lineAt, prog, rise } from "../lib";

const ICONS: Record<string, string[]> = {
  manual: ["M22 14h44v60H22z", "M32 30h24M32 40h24M32 50h14", "M36 8h16v10H36z"],
  infrequent: ["M44 14a30 30 0 1 0 0.1 0", "M44 24v20l13 8", "M14 44h6M68 44h6M44 14v6M44 68v6"],
  inconsistent: ["M12 22h28v44H12z", "M48 22h28v44H48z", "M20 36h12M20 46h12M56 36h12M56 46h6", "M40 44h8"],
  unpriced: ["M14 66h60M22 66V40M38 66V28M54 66V48M70 66V20", "M54 35a5 5 0 1 0 0.1 0"],
};

const Icon: React.FC<{ name: string; t: number }> = ({ name, t }) => (
  <svg viewBox="0 0 88 88" width={120} height={120} fill="none">
    {ICONS[name].map((d, i) => (
      <path key={i} d={d} stroke={i === ICONS[name].length - 1 ? C.lime : C.dim} strokeWidth={1.4} pathLength={1}
        strokeDasharray={1} strokeDashoffset={1 - Math.min(1, Math.max(0, t * 1.4 - i * 0.12))} />
    ))}
  </svg>
);

const CARDS = [
  { tag: "Manual", icon: "manual", h: "Every count is a person with a clipboard.", line: 0 },
  { tag: "Infrequent", icon: "infrequent", h: "Gaps sit unnoticed between walks.", line: 1 },
  { tag: "Inconsistent", icon: "inconsistent", h: "Two people, two different counts.", line: 1, delay: 40 },
  { tag: "Unpriced", icon: "unpriced", h: "Nobody knows what the gap costs.", line: 2 },
];

export const S2Problem: React.FC = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Grid reveal={false} />
      <div style={{ position: "absolute", left: 120, top: 110, ...rise(frame, 0) }}>
        <Eyebrow>[01] The problem</Eyebrow>
        <div style={{ fontFamily: F.display, fontWeight: 600, fontSize: 86, letterSpacing: "-0.04em", lineHeight: 1, color: C.tx, marginTop: 22 }}>
          Shelves are still <span style={{ color: C.dim }}>checked by eye.</span>
        </div>
      </div>
      <div style={{ position: "absolute", left: 120, right: 120, top: 380, display: "grid", gridTemplateColumns: "repeat(4, 1fr)", border: `1.5px solid ${C.line}`, borderRadius: 8, background: C.s1 }}>
        {CARDS.map((c, i) => {
          const start = lineAt("s2_problem", c.line) + (c.delay ?? 0);
          const t = prog(frame, start, 30);
          const lit = interpolate(frame, [start, start + 20], [0.25, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          return (
            <div key={c.tag} style={{ padding: "34px 32px 40px", borderLeft: i ? `1.5px solid ${C.line}` : "none", minHeight: 440, display: "flex", flexDirection: "column", gap: 26, opacity: lit }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontFamily: F.mono, fontSize: 18, letterSpacing: "0.1em", textTransform: "uppercase", color: C.mu }}>
                <span>{c.tag}</span><span>[0{i + 1}]</span>
              </div>
              <Icon name={c.icon} t={t} />
              <div style={{ marginTop: "auto", fontFamily: F.display, fontWeight: 600, fontSize: 36, lineHeight: 1.15, letterSpacing: "-0.02em", color: C.tx, ...rise(frame, start + 8, 20, 18) }}>
                {c.h}
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
