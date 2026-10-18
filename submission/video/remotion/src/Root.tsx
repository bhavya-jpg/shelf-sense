import { Composition } from "remotion";
import { ShelfSense } from "./ShelfSense";
import { FPS, totalFrames } from "./lib";

export const RemotionRoot: React.FC = () => (
  <Composition id="ShelfSense" component={ShelfSense} durationInFrames={totalFrames()} fps={FPS} width={1920} height={1080} />
);
