import { Video } from "@remotion/media";
import { AbsoluteFill, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Badge, Eyebrow, Frame, Grid } from "../components/ui";
import { C, F } from "../theme";
import { CAPTURE, EDIT, prog } from "../lib";

/** One callout chip, shown from frame `at` (times come from the capture's own event marks). */
const Chip: React.FC<{ at: number; k: string; v: string; y: number }> = ({ at, k, v, y }) => {
  const frame = useCurrentFrame();
  const p = prog(frame, at, 16);
  return (
    <div style={{ position: "absolute", right: 70, top: y, opacity: p, translate: `${(1 - p) * 24}px 0px`, display: "flex", flexDirection: "column", gap: 6, alignItems: "flex-end" }}>
      <span style={{ fontFamily: F.mono, fontSize: 17, letterSpacing: "0.1em", textTransform: "uppercase", color: C.dim }}>{k}</span>
      <span style={{ fontFamily: F.mono, fontSize: 22, color: C.tx, background: "rgba(10,11,12,0.86)", border: `1px solid ${C.line2}`, padding: "8px 12px", borderRadius: 3 }}>{v}</span>
    </div>
  );
};

export const S4Demo: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const e = EDIT.inspect;
  const m = (e as unknown as { marks: Record<string, number> }).marks;
  const fast = frame >= e.fastFrom && frame < e.fastTo;
  const r = CAPTURE.clips.inspect.result_text;
  return (
    <AbsoluteFill>
      <Grid reveal={false} />
      <div style={{ position: "absolute", left: 120, top: 46 }}>
        <Eyebrow>[03] The real application · real AMD inference</Eyebrow>
      </div>
      <Frame label="inspect" right={`${r.run_meta.split("\n")[0]}`} style={{ left: 120, top: 92, width: 1440, height: 860 }}>
        <Video src={staticFile("footage/inspect-edit.mp4")} premountFor={fps} muted objectFit="cover" style={{ position: "absolute", width: "100%", height: "100%" }} />
        {fast ? (
          <div style={{ position: "absolute", left: 24, bottom: 24, opacity: prog(frame, e.fastFrom, 8) }}>
            <Badge kind="warn" size={20}>Sped up {e.speedup.toFixed(1)}× · real wait {e.realWaitS.toFixed(1)} s</Badge>
          </div>
        ) : null}
      </Frame>
      <Chip at={m.spec} k="Specification" v="nestle_cereal_bay" y={150} />
      <Chip at={m.photo} k="Photo" v="compliant.png · self-taken" y={250} />
      <Chip at={m.run} k="Inference" v="Gemma-4-31B-IT · AMD" y={350} />
      <Chip at={m.result} k="Real result" v={r.run_meta.split("\n")[0].split(" · ")[1] + " inspection"} y={450} />
    </AbsoluteFill>
  );
};
