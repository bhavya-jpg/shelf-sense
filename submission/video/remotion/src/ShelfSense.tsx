import { Audio } from "@remotion/media";
import { TransitionSeries, linearTiming } from "@remotion/transitions";
import { fade } from "@remotion/transitions/fade";
import { AbsoluteFill, staticFile, useVideoConfig } from "remotion";
import { Captions } from "./components/ui";
import { SceneId, TRANSITION, sceneFrames } from "./lib";
import { S1Hook } from "./scenes/S1Hook";
import { S2Problem } from "./scenes/S2Problem";
import { S3Solution } from "./scenes/S3Solution";
import { S4Demo } from "./scenes/S4Demo";
import { S5Results } from "./scenes/S5Results";
import { S6Actions } from "./scenes/S6Actions";
import { S7Arch } from "./scenes/S7Arch";
import { S8Eval } from "./scenes/S8Eval";
import { S9Amd } from "./scenes/S9Amd";
import { S10Close } from "./scenes/S10Close";

/** Narration (Chatterbox) and its captions travel inside each scene, so re-timing a scene moves both. */
const Voiced: React.FC<{ id: SceneId; children: React.ReactNode }> = ({ id, children }) => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill>
      {children}
      <Audio src={staticFile(`vo/${id}.wav`)} premountFor={fps} />
      <Captions id={id} />
    </AbsoluteFill>
  );
};

const cut = <TransitionSeries.Transition presentation={fade()} timing={linearTiming({ durationInFrames: TRANSITION })} />;

/**
 * Shelf-Sense in about two and a half minutes: the problem, the product, a real inspection on AMD,
 * how it is built, what we measured, and what comes next. Each scene is as long as its narration.
 */
export const ShelfSense: React.FC = () => {
  const { fps } = useVideoConfig();
  return (
    <TransitionSeries>
      <TransitionSeries.Sequence name="1 Hook" durationInFrames={sceneFrames("s1_hook")} premountFor={fps}>
        <Voiced id="s1_hook"><S1Hook /></Voiced>
      </TransitionSeries.Sequence>
      {cut}
      <TransitionSeries.Sequence name="2 Problem" durationInFrames={sceneFrames("s2_problem")} premountFor={fps}>
        <Voiced id="s2_problem"><S2Problem /></Voiced>
      </TransitionSeries.Sequence>
      {cut}
      <TransitionSeries.Sequence name="3 Solution" durationInFrames={sceneFrames("s3_solution")} premountFor={fps}>
        <Voiced id="s3_solution"><S3Solution /></Voiced>
      </TransitionSeries.Sequence>
      {cut}
      <TransitionSeries.Sequence name="4 Real demo" durationInFrames={sceneFrames("s4_demo")} premountFor={fps}>
        <Voiced id="s4_demo"><S4Demo /></Voiced>
      </TransitionSeries.Sequence>
      {cut}
      <TransitionSeries.Sequence name="5 Results" durationInFrames={sceneFrames("s5_results")} premountFor={fps}>
        <Voiced id="s5_results"><S5Results /></Voiced>
      </TransitionSeries.Sequence>
      {cut}
      <TransitionSeries.Sequence name="6 Actions" durationInFrames={sceneFrames("s6_actions")} premountFor={fps}>
        <Voiced id="s6_actions"><S6Actions /></Voiced>
      </TransitionSeries.Sequence>
      {cut}
      <TransitionSeries.Sequence name="7 Architecture" durationInFrames={sceneFrames("s7_arch")} premountFor={fps}>
        <Voiced id="s7_arch"><S7Arch /></Voiced>
      </TransitionSeries.Sequence>
      {cut}
      <TransitionSeries.Sequence name="8 Evaluation" durationInFrames={sceneFrames("s8_eval")} premountFor={fps}>
        <Voiced id="s8_eval"><S8Eval /></Voiced>
      </TransitionSeries.Sequence>
      {cut}
      <TransitionSeries.Sequence name="9 AMD" durationInFrames={sceneFrames("s9_amd")} premountFor={fps}>
        <Voiced id="s9_amd"><S9Amd /></Voiced>
      </TransitionSeries.Sequence>
      {cut}
      <TransitionSeries.Sequence name="10 Close" durationInFrames={sceneFrames("s10_close")} premountFor={fps}>
        <Voiced id="s10_close"><S10Close /></Voiced>
      </TransitionSeries.Sequence>
    </TransitionSeries>
  );
};
