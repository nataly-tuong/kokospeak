# KokoSpeak

A local text-to-speech application powered by the open-source Kokoro model. Write scripts, blend voices, shape their delivery, and export audio and subtitles through a React interface backed by Python.

> **Private, local, and free to run.** Speech generation happens on your computer. Installation and the first downloads of model weights, voices, and language resources require internet access. Once the required files are cached, generation can run offline.

## Preview

![KokoSpeak Thumbnail](https://github.com/user-attachments/assets/b38a9d08-274f-4280-88b8-a6c0e041a914)

https://github.com/user-attachments/assets/d404b889-975e-4d2a-a451-1e12f1f087ba

## Installation

Download and extract the complete project into a writable folder. The automatic installer selects Python 3.12, prepares an isolated environment, installs dependencies and FFmpeg, builds the interface, and opens KokoSpeak in your browser.

Your existing Python or Conda environment can stay active. The installer manages its own environment and frontend build tools.

### macOS and Linux

Open a terminal in the extracted project folder and run:

```bash
bash install.sh
```

On macOS, you can also double-click **Start KokoSpeak.command**. If Finder does not open it, use the terminal command above.

### Windows

Double-click **Start KokoSpeak.cmd**, or run this from the project folder in PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

The execution-policy option applies only to that process; it does not change your saved system policy.

### First Run and Later Launches

The first setup downloads dependencies and may take several minutes. It obtains Python 3.12 through uv and downloads Node.js 24 LTS locally when the frontend needs building. FFmpeg is supplied through its Python package on supported platforms. Source/configuration fingerprints let later launches reuse completed setup.

Use the same installer command or Start file for later launches. On macOS/Linux, you can also run:

```bash
bash start.sh
```

The launcher starts one local server and opens the built interface in your default browser. It normally uses port 8000 and selects another free loopback port if necessary. Keep the terminal open for source launches. Use **Quit KokoSpeak** in the toolbar, or press `Ctrl+C` in the terminal, to stop a launcher-managed session. Closing the browser tab alone does not stop the server.

### Setup Options

| Purpose                                          | macOS/Linux                       | Windows launcher                        |
| ------------------------------------------------ | --------------------------------- | --------------------------------------- |
| Add Japanese and Mandarin resources              | `bash install.sh --all-languages` | `".\Start KokoSpeak.cmd" -AllLanguages` |
| Reinstall dependencies and rebuild the interface | `bash install.sh --repair`        | `".\Start KokoSpeak.cmd" -Repair`       |
| Install without launching                        | `bash install.sh --no-launch`     | `".\Start KokoSpeak.cmd" -NoLaunch`     |

The Windows launcher commands above work in Command Prompt. In PowerShell, prefix a quoted launcher path with `&`, for example:

```powershell
& ".\Start KokoSpeak.cmd" -Repair
```

If a download times out, rerun the installer to retry. Use the repair option if packages or build files are damaged. Setup output is saved in `.runtime/setup.log`.

See [INSTALL.md](INSTALL.md) for troubleshooting, runtime locations, and distribution details.

## Features

- **54 built-in voices across 9 language options.** Choose American or British English, Japanese, Mandarin Chinese, French, Hindi, Italian, Spanish, or Brazilian Portuguese.
- **Weighted voice mixing.** Blend up to three voices from the selected language, with normalized embedding weights.
- **Speed and pitch controls.** Set speaking speed from 0.50× to 2.00× and pitch from −12 to +12 semitones, with tempo compensation during pitch processing.
- **Pacing and dialogue.** Adjust extra segment and paragraph gaps, switch speakers within a script, and insert explicit pauses.
- **Audio finishing.** Control bass, treble, output gain, fades, edge-silence trimming, and peak normalization. Choose clean, small-room echo, or radio-bandpass effects.
- **Presets and reusable recipes.** Start with Natural, Narration, Bright, Broadcast, or Soft room. Save complete voice settings as JSON and import them later.
- **Progress and cancellation.** See preparation status and actual completed-segment progress. Cancel queued work or request cancellation of a running job.
- **Batch generation.** Process up to eight `.txt` or `.md` files sequentially with the current voice settings.
- **Take comparison.** Replay the last 12 takes in the current session and restore the exact script and settings behind each one.
- **Audio preview.** Inspect a waveform, listen with the integrated player, loop playback, enable autoplay for the next take, and adjust preview speed.
- **Timed transcript and subtitles.** Click transcript segments to seek, then download SRT or VTT captions.
- **Multiple audio formats.** Export WAV, FLAC, OGG, or MP3 with a custom filename.
- **Text import and export.** Open `.txt` or `.md` scripts and download the editor contents as a text file.
- **Keyboard shortcut.** Press `Ctrl+Enter` or `Cmd+Enter` to generate speech.
- **Responsive workspace.** Frosted panels, a floating toolbar, and layouts that adapt to different screen sizes.

## Available Languages and Voices

| Language             | Female voices                                                              | Male voices                                                |
| -------------------- | -------------------------------------------------------------------------- | ---------------------------------------------------------- |
| American English     | Heart, Alloy, Aoede, Bella, Jessica, Kore, Nicole, Nova, River, Sarah, Sky | Adam, Echo, Eric, Fenrir, Liam, Michael, Onyx, Puck, Santa |
| British English      | Alice, Emma, Isabella, Lily                                                | Daniel, Fable, George, Lewis                               |
| Japanese             | Alpha, Gongitsune, Nezumi, Tebukuro                                        | Kumo                                                       |
| Mandarin Chinese     | Xiaobei, Xiaoni, Xiaoxiao, Xiaoyi                                          | Yunjian, Yunxi, Yunxia, Yunyang                            |
| French               | Siwis                                                                      | —                                                          |
| Hindi                | Alpha, Beta                                                                | Omega, Psi                                                 |
| Italian              | Sara                                                                       | Nicola                                                     |
| Spanish              | Dora                                                                       | Alex, Santa                                                |
| Brazilian Portuguese | Dora                                                                       | Alex, Santa                                                |

Japanese and Mandarin require the optional language setup. Model, voice, and dictionary downloads can still occur when you first use an uncached resource.

## Using KokoSpeak

1. Write or open a script, or load the dialogue example.
2. Select a language and base voice. Enable the mixer to create a blend.
3. Adjust the delivery and audio-finishing settings.
4. Select **Generate speech** and follow the progress indicator.
5. Listen, compare takes, and export audio or subtitles.

For a batch, select up to eight files in the editor's batch section and generate them with the current settings. Each file produces a separate take.

### Dialogue and Pause Commands

Place commands alone on a line. Voice IDs must belong to the selected language. With American English selected:

```text
[voice=af_heart]
Every story begins with a voice.

[pause=1.2]
[voice=am_adam]
And sometimes, a second perspective.
```

- `[voice=...]` changes the speaker. The settings panel shows your base voice ID; the complete catalog is in `server/src/catalog.py`.
- `[pause=...]` inserts an explicit pause from 0 to 10 seconds.
- Empty lines create paragraph boundaries.
- Switching to another voice overrides the base blend for that segment. Selecting the base voice returns to its blend when mixing is enabled.

Pacing settings add gaps between planned segments and paragraphs. Natural pauses in the speech may remain in addition to these gaps.

### History, Files, and Offline Use

Scripts, settings, and the 12-take history live in session memory and reset when you reload the page. Download a voice recipe to retain its settings.

Source launches save generated WAV previews and subtitle metadata in `server/generated/`. Packaged applications use the operating system's writable KokoSpeak application-data folder. Exported downloads go to the location selected by your browser.

Complete setup and cache the languages/voices you need before working offline. Cancellation is checked at safe boundaries, so a model download or active inference chunk may not stop immediately. Completed batch takes are retained.

Subtitles follow measured processed-segment durations, rather than word-level alignment. Review captions before publication. Preview playback-speed changes affect listening only; they do not change the exported audio.

## Technologies Used

| Component                   | Technology                                                 |
| --------------------------- | ---------------------------------------------------------- |
| Interface                   | React, TypeScript, Tailwind CSS, Vite                      |
| Local backend               | Python, FastAPI, Uvicorn                                   |
| Speech synthesis            | Kokoro 0.9.4 and Misaki                                    |
| Audio processing            | NumPy, SoundFile, FFmpeg                                   |
| Automatic setup             | uv, isolated Python environment, local Node.js build tools |
| Desktop build configuration | PyInstaller and a manual GitHub Actions workflow           |

## Development

Automatic installation is intended for running the application. For frontend/backend development, use separate processes.

<details>
<summary>Manual developer setup</summary>

Use Python 3.11 or 3.12 and Node.js 22.12+ or 24. From the project root, start the backend:

```bash
cd server
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m uvicorn src.main:app --host 127.0.0.1 --port 8000
```

An existing Python 3.12 Conda environment can be used instead of creating `.venv`. On Windows, use `py -3.12 -m venv .venv` and activate it with `.venv\Scripts\activate` in Command Prompt or `.venv\Scripts\Activate.ps1` in PowerShell.

In another terminal, from the project root:

```bash
cd client
npm install
npm run dev
```

Open **http://127.0.0.1:5173**. Vite forwards `/api` requests to Python. Stop a manually started backend in its terminal.

For optional Japanese/Mandarin resources, run these in the backend environment from `server/`:

```bash
python -m pip install -r requirements-languages.txt
python -m unidic download
```

The requirements include `imageio-ffmpeg`. If your platform cannot use its binary, install a system FFmpeg executable or set `KOKOSPEAK_FFMPEG_PATH`. eSpeak NG may also need a system installation if its loader cannot locate it.

</details>

### Checks

From `server/`, with its Python environment active:

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

From `client/`:

```bash
npm run typecheck
npm run build
```

After building the frontend, restart the Python backend to serve `client/dist/` at **http://127.0.0.1:8000** without the Vite development server.

## Building a Desktop Release

Build configuration is included for downloadable app bundles. From the project root, in a Python 3.11/3.12 build environment with Node.js available:

```bash
python scripts/build_desktop.py
```

The script installs build dependencies, builds the frontend, and creates a native archive under `release/`.

| Build host | Archive contents                                                   |
| ---------- | ------------------------------------------------------------------ |
| macOS      | `KokoSpeak.app`                                                    |
| Windows    | `KokoSpeak` folder containing `KokoSpeak.exe` and its dependencies |
| Linux      | Native `KokoSpeak` executable folder                               |

Build on each target operating system and architecture. Keep the complete Windows/Linux output folder together. Bundled applications still open the interface in the user's browser.

The repository also includes a manually triggered **Build desktop bundles** GitHub Actions workflow. Desktop configuration is provided; compiled, signed installers are not included in the source download. Signing, notarization, and clean-machine release testing remain separate distribution steps. See [INSTALL.md](INSTALL.md) for the full process.

## File Structure

```text
kokospeak/
├── client/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   ├── data/
│   │   ├── hooks/
│   │   ├── lib/
│   │   ├── pages/
│   │   ├── types/
│   │   ├── App.tsx
│   │   ├── index.css
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── server/
│   ├── src/
│   │   ├── main.py
│   │   ├── engine.py
│   │   ├── catalog.py
│   │   ├── models.py
│   │   ├── script.py
│   │   ├── dsp.py
│   │   ├── jobs.py
│   │   └── runtime.py
│   ├── tests/
│   ├── generated/
│   └── requirements*.txt
├── scripts/
│   ├── setup.py
│   └── build_desktop.py
├── packaging/
├── .github/workflows/build-desktop.yml
├── assets/thumbnail.png
├── install.sh
├── install.ps1
├── start.sh
├── Start KokoSpeak.command
├── Start KokoSpeak.cmd
├── launch.py
├── INSTALL.md
└── README.md
```

The complete `server/src/` package is required. `generated/` and `.runtime/` are created as needed; `.runtime/` contains managed setup files and is excluded from source control.

## Acknowledgments

KokoSpeak uses [Kokoro](https://github.com/hexgrad/kokoro) for speech synthesis. Feature references include [Kokoro Voice Lab](https://github.com/Miceprincipal/Kokoro-Voice-Lab), [Kokoro TTS GUI](https://github.com/Patrick-Ric/kokoro-tts-gui), and [Narrator](https://github.com/MattiaAlessi/Narrator).
