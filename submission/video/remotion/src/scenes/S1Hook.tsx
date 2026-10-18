import { AbsoluteFill, CanvasImage, interpolate, staticFile, useCurrentFrame } from "remotion";
import { Corners, Eyebrow, Grid } from "../components/ui";
import { C, F } from "../theme";
import { lineAt, prog, sceneFrames } from "../lib";
import { Words } from "./common";

export const S1Hook: React.FC = () => {
  const frame = useCurrentFrame();
  const l1 = lineAt("s1_hook", 1);
  const dimFirst = prog(frame, l1 - 6, 16);
  const total = sceneFrames("s1_hook");
  return (
    <AbsoluteFill>
      <Grid />
      {/* The real demo shelf, dark and slow: our own photo, not stock footage. */}
      <div style={{ position: "absolute", right: 0, top: 0, width: 900, height: 1080, overflow: "hidden", opacity: 0.32 * prog(frame, 0, 40) }}>
        <CanvasImage
          src={staticFile("img/shelf.jpg")}
          style={{ width: 1430, height: 1080, filter: "grayscale(1) contrast(1.05)", scale: `${interpolate(frame, [0, total], [1.08, 1.0])}`, translate: "-300px 0px" }}
        />
        <div style={{ position: "absolute", inset: 0, background: `linear-gradient(90deg, ${C.bg} 0%, rgba(10,11,12,0.55) 45%, rgba(10,11,12,0.2) 100%)` }} />
      </div>
      <Corners x={1020} y={120} w={780} h={840} o={0.6 * prog(frame, 10, 30)} />
      <div style={{ position: "absolute", left: 120, top: 150, width: 1100 }}>
        <Eyebrow style={{ opacity: prog(frame, 4, 20) }}>[ Retail shelf compliance ]</Eyebrow>
        <div style={{ opacity: 1 - 0.65 * dimFirst }}>
          <Words
            text="Every store has a shelf that is quietly running low."
            start={8}
            style={{ fontFamily: F.display, fontWeight: 600, fontSize: 76, lineHeight: 1.05, letterSpacing: "-0.035em", color: C.tx, marginTop: 40 }}
          />
        </div>
        <Words
          text="Most shelves are still checked by eye."
          start={l1}
          step={3}
          accent={["by", "eye."]}
          accentColor={C.lime}
          style={{ fontFamily: F.display, fontWeight: 600, fontSize: 118, lineHeight: 0.98, letterSpacing: "-0.045em", color: C.tx, marginTop: 70 }}
        />
      </div>
    </AbsoluteFill>
  );
};
