# Unmatched photos

`missing.png` and `misplaced.png` are self-taken shelf photos. They show different shelves from `data/demo/compliant.png`, and no spec or hand-counted ground truth exists for them yet. They're kept here, outside `data/demo/`, so the app doesn't offer them as demo buttons. Inspecting them against `specs/nestle_cereal_bay.json` would give meaningless results.

To use one as a demo:
1. Write a matching spec in `specs/`.
2. Write a `<name>.truth.json` ground truth.
3. Move the photo back into `data/demo/`.
