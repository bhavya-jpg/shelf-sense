import React from "react";
import { CanvasImage, interpolate, staticFile, useCurrentFrame } from "remotion";
import { EASE_IO } from "../lib";

export type Region = { x: number; y: number; w: number; h: number };

/**
 * A "camera" over a real 1920x1080 screenshot: shows `regions[i]` from frame `at[i]`, easing between them.
 * Nothing is drawn on the screenshot; it is panned and scaled only.
 */
export const Pan: React.FC<{ src: string; w: number; h: number; regions: Region[]; at: number[]; dur?: number }> = ({
  src, w, h, regions, at, dur = 26,
}) => {
  const frame = useCurrentFrame();
  let r = regions[0];
  for (let i = 1; i < regions.length; i++) {
    const t = interpolate(frame, [at[i], at[i] + dur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: EASE_IO });
    const a = r;
    const b = regions[i];
    r = { x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t, w: a.w + (b.w - a.w) * t, h: a.h + (b.h - a.h) * t };
  }
  const scale = Math.min(w / r.w, h / r.h);
  const ox = (w - r.w * scale) / 2 - r.x * scale;
  const oy = (h - r.h * scale) / 2 - r.y * scale;
  return (
    <div style={{ position: "absolute", left: 0, top: 0, width: 1920, height: 1080, transformOrigin: "0 0", translate: `${ox}px ${oy}px`, scale: `${scale}` }}>
      <CanvasImage src={staticFile(src)} style={{ width: 1920, height: 1080 }} />
    </div>
  );
};

export const Words: React.FC<{ text: string; start: number; step?: number; style?: React.CSSProperties; accent?: string[]; accentColor?: string }> = ({
  text, start, step = 3, style, accent = [], accentColor,
}) => {
  const frame = useCurrentFrame();
  return (
    <div style={style}>
      {text.split(" ").map((w, i) => {
        const p = interpolate(frame, [start + i * step, start + i * step + 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
        return (
          <span key={i} style={{ display: "inline-block", opacity: p, translate: `0px ${(1 - p) * 18}px`, marginRight: "0.24em", color: accent.includes(w) ? accentColor : undefined }}>
            {w}
          </span>
        );
      })}
    </div>
  );
};
