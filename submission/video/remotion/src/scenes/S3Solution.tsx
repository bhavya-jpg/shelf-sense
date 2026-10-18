import { Video } from "@remotion/media";
import { AbsoluteFill, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Eyebrow, Frame, Grid } from "../components/ui";
import { C, F } from "../theme";
import { CAPTURE, lineAt, prog, rise } from "../lib";

const STEPS = ["Choose a shelf specification", "Add a shelf photograph", "Run one inspection"];

export const S3Solution: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const l1 = lineAt("s3_solution", 1);
  const l2 = lineAt("s3_solution", 2);
  return (
    <AbsoluteFill>
      <Grid reveal={false} />
      <div style={{ position: "absolute", left: 120, top: 120, width: 680 }}>
        <Eyebrow style={rise(frame, 0)}>[02] The solution</Eyebrow>
        <div style={{ fontFamily: F.display, fontWeight: 600, fontSize: 132, letterSpacing: "-0.06em", lineHeight: 0.9, color: C.tx, marginTop: 30, ...rise(frame, 6, 24) }}>
          Shelf<span style={{ color: C.lime }}>-</span>Sense
        </div>
        <div style={{ fontFamily: F.sans, fontSize: 32, lineHeight: 1.45, color: C.mu, marginTop: 30, ...rise(frame, 18) }}>
          One shelf photograph in. A <span style={{ color: C.tx }}>preliminary compliance report</span> out.
        </div>
        <div style={{ marginTop: 48, borderTop: `1.5px solid ${C.line}` }}>
          {STEPS.map((s, i) => (
            <div key={s} style={{ display: "flex", gap: 26, alignItems: "baseline", padding: "20px 0", borderBottom: `1.5px solid ${C.line}`, ...rise(frame, l1 + i * 12, 18, 14) }}>
              <span style={{ fontFamily: F.mono, fontSize: 20, color: C.lime }}>[0{i + 1}]</span>
              <span style={{ fontFamily: F.display, fontSize: 36, fontWeight: 600, letterSpacing: "-0.02em", color: C.tx }}>{s}</span>
            </div>
          ))}
        </div>
        <div style={{ display: "flex", gap: 18, marginTop: 40, ...rise(frame, l2 + 4) }}>
          <span style={{ fontFamily: F.mono, fontSize: 22, letterSpacing: "0.06em", textTransform: "uppercase", color: C.bg, background: C.lime, padding: "12px 18px", borderRadius: 3 }}>Model counts</span>
          <span style={{ fontFamily: F.mono, fontSize: 22, letterSpacing: "0.06em", textTransform: "uppercase", color: C.tx, border: `1.5px solid ${C.line2}`, padding: "12px 18px", borderRadius: 3 }}>Code decides</span>
        </div>
      </div>
      {/* Real footage: the landing page, scrolled in the capture. */}
      <Frame label="home" right="real capture" style={{ left: 880, top: 150, width: 920, height: 556, opacity: prog(frame, 10, 24), translate: `0px ${(1 - prog(frame, 10, 24)) * 30}px` }}>
        <Video src={staticFile("footage/landing.mp4")} trimBefore={Math.round(CAPTURE.clips.landing.loaded * fps)} premountFor={fps} muted
          objectFit="cover" style={{ position: "absolute", width: "100%", height: "100%" }} />
      </Frame>
    </AbsoluteFill>
  );
};
