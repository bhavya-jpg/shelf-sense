import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Badge, Eyebrow, Frame, Grid } from "../components/ui";
import { C, F } from "../theme";
import { lineAt, prog, rise } from "../lib";
import { Pan } from "./common";

export const S6Actions: React.FC = () => {
  const frame = useCurrentFrame();
  const l1 = lineAt("s6_actions", 1);
  return (
    <AbsoluteFill>
      <Grid reveal={false} />
      <Frame label="inspect · recommended actions" right="real screenshot" style={{ left: 120, top: 130, width: 1040, height: 720, opacity: prog(frame, 0, 18) }}>
        <Pan src="img/inspect_actions.png" w={1008} h={652} regions={[{ x: 740, y: 160, w: 1090, h: 520 }, { x: 740, y: 300, w: 1090, h: 520 }]} at={[0, l1]} dur={60} />
      </Frame>
      <div style={{ position: "absolute", left: 1240, top: 150, width: 560 }}>
        <Eyebrow style={rise(frame, 4)}>[05] Actions</Eyebrow>
        <div style={{ fontFamily: F.display, fontWeight: 600, fontSize: 64, letterSpacing: "-0.04em", lineHeight: 1.02, color: C.tx, marginTop: 20, ...rise(frame, 8) }}>
          A restocking list, <span style={{ color: C.dim }}>labelled with who wrote it.</span>
        </div>
        <div style={{ marginTop: 40, display: "flex", flexDirection: "column", gap: 22 }}>
          <div style={rise(frame, l1)}><Badge kind="ok">AMD-worded · Gemma-4-31B-IT</Badge></div>
          <div style={{ fontFamily: F.sans, fontSize: 28, lineHeight: 1.5, color: C.mu, ...rise(frame, l1 + 14) }}>
            Every product name, count and dollar figure is <span style={{ color: C.tx }}>inserted by code</span>. If the wording fails validation, a deterministic template is used, and labelled as one.
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
