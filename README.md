# KokoSpeak

A local text-to-speech application powered by the open-source Kokoro model, with a React interface and a Python backend. Write scripts, blend voices, shape their delivery, and export audio and subtitles from one workspace.

> **Run it on your own machine, privately and for free.** Speech generation runs locally. Internet access is needed for installation and the initial downloads of model weights, voices, and language resources. Once the required files are cached, generation can run offline.

## Preview

<img width="2887" height="3861" alt="thumbnail" src="https://github.com/user-attachments/assets/c5b8b05d-7839-4032-b40e-2d0240817368" />


## Features

- **54 built-in voices across 9 language options:** American and British English, Japanese, Mandarin Chinese, French, Hindi, Italian, Spanish, and Brazilian Portuguese.
- **Weighted voice blending:** Mix up to three voices from the selected language. Weights are normalized before the voice embeddings are combined.
- **Delivery controls:** Adjust speaking speed from 0.50× to 2.00× and pitch from −12 to +12 semitones. Pitch processing compensates for the associated tempo change.
- **Pacing and dialogue:** Set extra gaps between segments and paragraphs, or use script commands to switch speakers and insert explicit pauses.
- **Audio finishing:** Adjust bass, treble, output gain, fades, silence trimming, and peak normalization. Choose clean, small-room echo, or radio-bandpass effects.
- **Voice presets and recipes:** Start with Natural, Narration, Bright, Broadcast, or Soft room. Export your complete voice settings as JSON and import them later.
- **Generation progress and cancellation:** See model preparation separately from completed-segment progress, and request cancellation while a job is queued or running.
- **Batch generation:** Load up to eight `.txt` or `.md` files and generate separate takes sequentially with the current settings.
- **Take history:** Compare the last 12 takes in the current session and restore the script and settings used for each one.
- **Audio preview:** Inspect a waveform, listen with the integrated player, loop playback, enable autoplay for the next take, or change preview playback speed.
- **Timed transcript:** Click a transcript segment to seek to its position in the audio.
- **Audio and subtitle export:** Download WAV, FLAC, OGG, or MP3 audio with a custom filename, plus SRT or VTT subtitles.
- **Text import and export:** Open `.txt` or `.md` scripts and download the editor contents as a text file.
- **Keyboard shortcut:** Press `Ctrl+Enter` or `Cmd+Enter` to generate speech.
- **Responsive interface:** A dark workspace with frosted panels, a floating toolbar, and layouts for different screen sizes.

## Available Languages and Voices

| Language | Female voices | Male voices |
| --- | --- | --- |
| American English | Heart, Alloy, Aoede, Bella, Jessica, Kore, Nicole, Nova, River, Sarah, Sky | Adam, Echo, Eric, Fenrir, Liam, Michael, Onyx, Puck, Santa |
| British English | Alice, Emma, Isabella, Lily | Daniel, Fable, George, Lewis |
| Japanese | Alpha, Gongitsune, Nezumi, Tebukuro | Kumo |
| Mandarin Chinese | Xiaobei, Xiaoni, Xiaoxiao, Xiaoyi | Yunjian, Yunxi, Yunxia, Yunyang |
| French | Siwis | — |
| Hindi | Alpha, Beta | Omega, Psi |
| Italian | Sara | Nicola |
| Spanish | Dora | Alex, Santa |
| Brazilian Portuguese | Dora | Alex, Santa |

Japanese and Mandarin require the optional language dependencies described below.

## Technologies Used

- **React and TypeScript:** Frontend components, state, and typed API requests.
- **Tailwind CSS:** Interface styling and design tokens.
- **Vite:** Frontend development server and production builds.
- **Python, FastAPI, and Uvicorn:** Local API server, request validation, and generation jobs.
- **Kokoro and Misaki:** Speech synthesis and language processing.
- **NumPy and SoundFile:** Audio handling and format conversion.
- **FFmpeg:** Pitch adjustment, EQ, effects, and MP3 encoding.

## Setup and Usage

### Requirements

- **Python 3.11 or 3.12.** The pinned Kokoro 0.9.4 package requires Python below 3.13.
- **Node.js 22.12 or newer.** Node.js 24 is also supported by the project configuration.
- **FFmpeg** for pitch changes, bass/treble adjustments, room/radio effects, and MP3 export. Clean generation with default settings does not require it.

On macOS with Homebrew:

```bash
brew install ffmpeg
```

### 1. Start the Python Backend

From the project root, create and activate a Python 3.12 virtual environment:

```bash
cd server
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

If you already use a Python 3.12 Conda environment, activate it instead of creating a virtual environment, then run the installation and Uvicorn commands from `server/`:

```bash
conda activate kokospeak
```

On Windows, create the environment with `py -3.12 -m venv .venv` and activate it with `.venv\Scripts\activate` in Command Prompt, or `.venv\Scripts\Activate.ps1` in PowerShell.

### 2. Start the React Frontend

Open a second terminal. From the project root:

```bash
cd client
npm install
npm run dev
```

Open **http://127.0.0.1:5173** in your browser. Keep both terminals running during development. The frontend forwards `/api` requests to the Python backend on port 8000.

The interface runs in your browser; it does not open a separate native application window.

### 3. Generate Audio

1. Enter text, open a script, or load the dialogue example.
2. Select a language and voice, or enable the voice mixer.
3. Adjust the delivery and finishing settings.
4. Select **Generate speech** and follow the progress indicator.
5. Preview the result, compare takes, and export audio or subtitles.

For a batch, choose up to eight text files in the editor's batch section and generate them with the current voice settings.

### Optional Language Dependencies

For Japanese and Mandarin, run this from `server/` in your Python environment:

```bash
python -m pip install -r requirements-languages.txt
```

Japanese may also require its dictionary download:

```bash
python -m unidic download
```

If the speech engine cannot locate eSpeak NG, install it for your operating system. On macOS:

```bash
brew install espeak-ng
```

## Dialogue and Pause Commands

Put each command alone on a line. Voice IDs must belong to the selected language. For example, with American English selected:

```text
[voice=af_heart]
Every story begins with a voice.

[pause=1.2]
[voice=am_adam]
And sometimes, a second perspective.
```

- `[voice=...]` changes the speaker. The settings panel shows the base voice ID, and the full catalog is in `server/src/catalog.py`.
- `[pause=...]` adds an explicit pause from 0 to 10 seconds.
- Empty lines create paragraph boundaries.
- Selecting another voice overrides the base blend for that segment. Selecting the base voice returns to its blend when mixing is enabled.

The pacing controls add gaps between planned segments and paragraphs. Natural pauses in the generated speech may remain as well.

## Production Build

Build the frontend from `client/`:

```bash
npm run build
```

Then restart the Python backend from `server/`:

```bash
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

The backend detects `client/dist/` and serves the built interface at **http://127.0.0.1:8000**. The Vite development server is no longer needed for this mode.

## File Structure

```text
kokospeak/
├── client/
│   ├── public/
│   ├── src/
│   │   ├── components/        Editor, voice controls, progress, player, history
│   │   ├── data/              Voice catalog and presets
│   │   ├── hooks/             Studio state and job polling
│   │   ├── lib/               API calls and download helpers
│   │   ├── pages/             Workspace layout
│   │   ├── types/             TypeScript contracts
│   │   ├── App.tsx
│   │   ├── index.css
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── server/
│   ├── src/
│   │   ├── main.py            FastAPI routes and output handling
│   │   ├── engine.py          Kokoro inference and voice blending
│   │   ├── catalog.py         Languages and voice IDs
│   │   ├── models.py          Request and settings validation
│   │   ├── script.py          Script planning and commands
│   │   ├── dsp.py             Audio processing and subtitle generation
│   │   └── jobs.py            Generation queue and cancellation
│   ├── tests/
│   ├── generated/             Created when the backend runs
│   ├── requirements.txt
│   ├── requirements-languages.txt
│   └── requirements-dev.txt
├── assets/
│   └── thumbnail.png
├── DESIGN.md
└── README.md
```

Keep the complete `server/src/` package together. Run the backend through `uvicorn src.main:app`, rather than `python main.py`.

## Notes

- **Local storage:** Generated WAV previews and subtitle metadata remain in `server/generated/` until you remove them. Exported downloads go to the location chosen by your browser.
- **Session history:** Scripts, settings, and recent-take history are held in memory and reset when the page reloads. Download a voice recipe to retain its settings.
- **Cancellation:** Running inference or model downloads may not stop immediately. Cancellation is checked at safe boundaries; completed batch takes are retained.
- **Subtitles:** Timing follows measured audio segments, rather than word-level alignment. Review subtitles before publication.
- **Input limits:** Each script accepts up to 100,000 characters. Long text is split into bounded segments, and sentence splitting is heuristic.
- **Audio controls:** Presets adjust synthesis and audio-processing settings. They do not provide trained emotion conditioning or voice cloning. Preview playback speed changes listening only; it does not alter exports.

## Development Checks

From `server/`, with your Python environment active:

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

From `client/`:

```bash
npm run typecheck
npm run build
```

## Acknowledgments

KokoSpeak uses [Kokoro](https://github.com/hexgrad/kokoro) for speech synthesis. Feature references include [Kokoro Voice Lab](https://github.com/Miceprincipal/Kokoro-Voice-Lab), [Kokoro TTS GUI](https://github.com/Patrick-Ric/kokoro-tts-gui), and [Narrator](https://github.com/MattiaAlessi/Narrator).
