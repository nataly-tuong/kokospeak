# KokoSpeak Studio backend

Use Python 3.11 or 3.12. From this folder:

```bash
python -m pip install -r requirements.txt
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

The full `src/` package is required. FastAPI receives jobs, a bounded single worker runs Kokoro, and React polls actual progress. Model downloads are lazy. ffmpeg is used for pitch/EQ/effects and MP3. No NiceGUI or desktop-window dependency is used.

Run core tests without downloading Kokoro weights:

```bash
python -m unittest discover -s tests -p test_core.py -v
```

For HTTP and export tests, install `requirements-dev.txt` and run the entire test suite. See the project README for controls, scripting, optional language dependencies, batch generation, and limitations.
