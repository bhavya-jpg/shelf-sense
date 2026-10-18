import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame } from "remotion";
import { C, F } from "../theme";
import { SceneId, VO, prog } from "../lib";

/** Faint 88px grid, like the app's page background; lines draw in at the start of a scene. */
export const Grid: React.FC<{ reveal?: boolean }> = ({ reveal = true }) => {
  const frame = useCurrentFrame();
  const o = reveal ? prog(frame, 0, 40) : 1;
  return (
    <AbsoluteFill
      style={{
        backgroundColor: C.bg,
        backgroundImage: `linear-gradient(rgba(255,255,255,${0.028 * o}) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,${0.028 * o}) 1px, transparent 1px)`,
        backgroundSize: "88px 88px",
      }}
    />
  );
};

export const Eyebrow: React.FC<{ children: React.ReactNode; color?: string; style?: React.CSSProperties }> = ({
  children, color = C.lime, style,
}) => (
  <div style={{ fontFamily: F.mono, fontSize: 22, letterSpacing: "0.14em", textTransform: "uppercase", color, ...style }}>
    {children}
  </div>
);

/** Corner marks + coordinate labels, the "measured" motif from the landing page. */
export const Corners: React.FC<{ x: number; y: number; w: number; h: number; color?: string; o?: number }> = ({
  x, y, w, h, color = C.mu, o = 1,
}) => {
  const s = 18;
  const base: React.CSSProperties = { position: "absolute", width: s, height: s, borderColor: color, borderStyle: "solid", opacity: o };
  return (
    <>
      <div style={{ ...base, left: x - 1, top: y - 1, borderWidth: "2px 0 0 2px" }} />
      <div style={{ ...base, left: x + w - s + 1, top: y - 1, borderWidth: "2px 2px 0 0" }} />
      <div style={{ ...base, left: x - 1, top: y + h - s + 1, borderWidth: "0 0 2px 2px" }} />
      <div style={{ ...base, left: x + w - s + 1, top: y + h - s + 1, borderWidth: "0 2px 2px 0" }} />
    </>
  );
};

/** Browser-like frame around real product footage or screenshots. */
export const Frame: React.FC<{
  label: string; right?: string; style?: React.CSSProperties; children: React.ReactNode;
}> = ({ label, right, style, children }) => (
  <div
    style={{
      position: "absolute", background: `linear-gradient(180deg, ${C.s2}, ${C.s1})`, border: `1.5px solid ${C.line2}`,
      borderRadius: 12, padding: 16, boxShadow: "0 40px 120px rgba(0,0,0,0.55)", ...style,
    }}
  >
    <div style={{ display: "flex", justifyContent: "space-between", fontFamily: F.mono, fontSize: 17, color: C.dim, padding: "0 4px 14px", letterSpacing: "0.04em" }}>
      <span><span style={{ color: C.mu }}>shelf-sense</span> / {label}</span>
      <span>{right}</span>
    </div>
    <div style={{ position: "relative", overflow: "hidden", borderRadius: 6, border: `1px solid ${C.line}`, width: "100%", height: "calc(100% - 36px)" }}>
      {children}
    </div>
  </div>
);

/** Burned-in caption for the current narration line of a scene (timings from Chatterbox, src/data/vo.json). */
export const Captions: React.FC<{ id: SceneId; bottom?: number }> = ({ id, bottom = 54 }) => {
  const frame = useCurrentFrame();
  const t = frame / 30;
  const line = VO[id].lines.find((l) => t >= l.start - 0.05 && t <= l.end + 0.25);
  if (!line) return null;
  const o = interpolate(t, [line.start - 0.05, line.start + 0.15, line.end + 0.1, line.end + 0.25], [0, 1, 1, 0], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp",
  });
  return (
    <div style={{ position: "absolute", left: 0, right: 0, bottom, display: "flex", justifyContent: "center", opacity: o }}>
      <div
        style={{
          maxWidth: 1340, padding: "12px 24px", background: "rgba(10,11,12,0.82)", border: `1px solid ${C.line}`, borderRadius: 6,
          fontFamily: F.sans, fontSize: 32, lineHeight: 1.35, color: C.tx, textAlign: "center",
        }}
      >
        {line.text}
      </div>
    </div>
  );
};

export const Badge: React.FC<{ kind: "ok" | "warn" | "bad" | "info"; children: React.ReactNode; size?: number }> = ({
  kind, children, size = 20,
}) => {
  const col = { ok: C.lime, warn: C.amber, bad: C.red, info: C.blue }[kind];
  return (
    <span
      style={{
        display: "inline-flex", alignItems: "center", gap: 10, fontFamily: F.mono, fontSize: size, letterSpacing: "0.07em",
        textTransform: "uppercase", color: col, border: `1.5px solid ${col}66`, background: `${col}14`, padding: "6px 12px", borderRadius: 3,
      }}
    >
      <span style={{ width: size * 0.4, height: size * 0.4, borderRadius: "50%", background: col }} />
      {children}
    </span>
  );
};
