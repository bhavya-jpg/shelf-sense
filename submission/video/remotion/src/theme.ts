import { loadFont as loadInter } from "@remotion/google-fonts/Inter";
import { loadFont as loadInterTight } from "@remotion/google-fonts/InterTight";
import { loadFont as loadMono } from "@remotion/google-fonts/JetBrainsMono";

/** The Shelf-Sense UI tokens (app/ui.py), so the film and the product look like one thing. */
export const C = {
  bg: "#0A0B0C",
  s1: "#101214",
  s2: "#15181A",
  s3: "#1B1F22",
  line: "#23272A",
  line2: "#31363A",
  tx: "#ECEBE6",
  mu: "#9DA2A8",
  dim: "#6C7177",
  lime: "#CDFF3F",
  amber: "#F2B24B",
  red: "#FF6B57",
  blue: "#93B4FF",
};

export const F = {
  display: loadInterTight("normal", { weights: ["500", "600", "700"], subsets: ["latin"] }).fontFamily,
  sans: loadInter("normal", { weights: ["400", "500", "600"], subsets: ["latin"] }).fontFamily,
  mono: loadMono("normal", { weights: ["400", "500"], subsets: ["latin"] }).fontFamily,
};
