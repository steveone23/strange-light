# Drawing the Sea

Indonesian batik makers lean out of their boats and draw on the ocean itself with canting wax pens. Wherever the hot wax touches, the living sea turns into finished batik cloth, and a fishing boat sails from real water onto the pattern.

## How it was made

The final image was generated with `openai/gpt-image-2.6-sunburst` from the `batiksea4` prompt in `tools/prompts.json` (`tools/generate.py`), served through the Orbio gateway, which is OpenRouter-compatible. It was chosen because it beat the previous version on three proxy judge models, then was fitted to the contest limits with `tools/fit.py`. `main.py` copies the committed `entry.png` to `/output/entry.png`.
