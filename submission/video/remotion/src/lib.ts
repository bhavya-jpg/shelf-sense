import { Easing, interpolate } from "remotion";
import voJson from "./data/vo.json";
import capJson from "./data/capture.json";
import editJson from "./data/edit.json";

export const FPS = 30;
export const TRANSITION = 14; // frames of cross-fade between scenes
const HOLD = 0.5; // seconds a scene stays after its last word
const END_HOLD = 3.2; // the close stays long enough to read the credits line

export const EASE = Easing.bezier(0.2, 0.7, 0.2, 1);
export const EASE_IO = Easing.bezier(0.65, 0, 0.35, 1);

export const prog = (frame: number, start: number, dur = 18, easing = EASE): number =>
  interpolate(frame, [start, start + dur], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing });

/** Fade up into place. */
export const rise = (frame: number, start: number, dur = 20, dist = 32) => ({
  opacity: prog(frame, start, dur),
  translate: `0px ${(1 - prog(frame, start, dur)) * dist}px`,
});

export type SceneId = keyof typeof voJson;
type Line = { text: string; start: number; end: number };
export const VO = voJson as Record<SceneId, { seconds: number; lines: Line[] }>;
export const CAPTURE = capJson;
export const EDIT = editJson as { inspect: { frames: number; speedup: number; realWaitS: number; fastFrom: number; fastTo: number } };

export const SCENES: SceneId[] = [
  "s1_hook", "s2_problem", "s3_solution", "s4_demo", "s5_results",
  "s6_actions", "s7_arch", "s8_eval", "s9_amd", "s10_close",
];

export const sceneFrames = (id: SceneId) => Math.ceil((VO[id].seconds + (id === "s10_close" ? END_HOLD : HOLD)) * FPS);
export const totalFrames = () => SCENES.reduce((s, id) => s + sceneFrames(id), 0) - TRANSITION * (SCENES.length - 1);
/** Frame at which narration line `i` of a scene starts (or ends). */
export const lineAt = (id: SceneId, i: number, edge: "start" | "end" = "start") =>
  Math.round(VO[id].lines[Math.min(i, VO[id].lines.length - 1)][edge] * FPS);
/** Absolute start frame of each scene in the cut (scenes overlap by TRANSITION). */
export const sceneStart = (id: SceneId) => {
  let f = 0;
  for (const s of SCENES) {
    if (s === id) return f;
    f += sceneFrames(s) - TRANSITION;
  }
  return f;
};
