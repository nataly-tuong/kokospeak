# KokoSpeak third-party components

The desktop build includes third-party Python packages, their metadata, and package data. Preserve the bundled license and notice files when distributing the app. This document is an index, not a replacement for their license terms.

- Python: https://www.python.org/psf/license/
- Kokoro: https://github.com/hexgrad/kokoro
- Kokoro model weights: https://huggingface.co/hexgrad/Kokoro-82M
- Misaki: https://github.com/hexgrad/misaki
- PyTorch: https://github.com/pytorch/pytorch/blob/main/LICENSE
- spaCy and its language model: https://github.com/explosion/spaCy and https://github.com/explosion/spacy-models
- FFmpeg wrapper and bundled binaries: https://github.com/imageio/imageio-ffmpeg
- FFmpeg: https://ffmpeg.org/legal.html
- FastAPI: https://github.com/fastapi/fastapi
- Uvicorn: https://github.com/encode/uvicorn
- React: https://github.com/facebook/react
- DM Sans and Geist font packages: https://fontsource.org/

FFmpeg license details depend on the binary shipped in the selected imageio-ffmpeg wheel. Keep that wheel's included notices and record its resolved version in the release build environment. Optional language resources have their own package/model notices.

Feature references: https://github.com/Miceprincipal/Kokoro-Voice-Lab, https://github.com/Patrick-Ric/kokoro-tts-gui, and https://github.com/MattiaAlessi/Narrator.
