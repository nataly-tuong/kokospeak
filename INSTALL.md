# Installing and distributing KokoSpeak

## One-command setup from the source download

Extract the complete project into a writable folder. On macOS or Linux, open a terminal in that folder and run:

```bash
bash install.sh
```

Alternatively, macOS users can double-click `Start KokoSpeak.command`. If your downloaded copy does not open through Finder, run the terminal command above.

On Windows, double-click `Start KokoSpeak.cmd`, or run this in PowerShell from the project folder:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\install.ps1
```

The execution-policy option applies to that PowerShell process; the installer does not change your machine's saved policy.

### What happens

1. Find uv, or download its official installer into the project. A private uv installation does not modify your shell profiles.
2. Select/download Python 3.12 and create `.runtime/python312` as an isolated environment.
3. Install the backend dependencies with extended HTTP timeouts and retries. The `imageio-ffmpeg` platform wheel supplies FFmpeg where supported.
4. Download a private Node.js 24 LTS distribution if the interface needs building. Verify its SHA-256 checksum against Node's HTTPS release checksum file.
5. Install the frontend packages and create `client/dist`.
6. Start one local Python server and open the built interface in your default browser.

No administrator privileges or global Node/Python installation are requested. uv's managed Python downloads and package cache can use uv's normal per-user cache/data locations. First setup needs internet and enough disk space for Python, PyTorch, model assets, and build tools.

Successful dependency setup and frontend builds are recorded so later runs can skip them. Failed downloads/builds do not mark the unfinished step as successful. Source/configuration changes trigger an interface rebuild; requirement changes trigger dependency installation. The manifests are not full dependency lockfiles.

The source archive is not a prebuilt desktop application: it still downloads and installs dependencies on the first run. A packaged desktop release is the no-development-tools option described below.

### Later launches

Use the same command or Start file. Or, on macOS/Linux:

```bash
bash start.sh
```

Keep the terminal window open for a source launch. Use **Quit KokoSpeak** in the toolbar to stop the launcher-managed server, or press Ctrl+C in its terminal. A manually started Uvicorn development server has no Quit button and should be stopped in its terminal. Closing a browser tab alone does not stop Python.

The launcher prefers `127.0.0.1:8000`. If it is already occupied by another process, it binds a free loopback port and opens the correct address. When its recorded instance is already running, it reopens that instance. The application stays local; the launcher does not bind to your LAN interface.

### Options

| macOS/Linux | Windows | Purpose |
| --- | --- | --- |
| `bash install.sh --repair` | `install.ps1 -Repair` | Reinstall requirements and rebuild the client |
| `bash install.sh --no-launch` | `install.ps1 -NoLaunch` | Prepare files without starting the app |
| `bash install.sh --all-languages` | `install.ps1 -AllLanguages` | Add Japanese/Mandarin dependencies and the Japanese dictionary |

Run Windows commands through the PowerShell invocation shown above, or pass those flags to the `.cmd` launcher. The English and eSpeak-backed languages are the default setup; Japanese/Mandarin add downloads and setup time. Once optional languages have been installed, subsequent ordinary setup runs retain them.

### Files and troubleshooting

- `.runtime/setup.log`: setup command output.
- `.runtime/python312`: the private Python environment.
- `.runtime/node`: the private frontend build tools.
- `.runtime/installed.json`: completed dependency setup fingerprint.
- `client/dist`: the built browser interface.
- `server/generated`: source-mode generated audio and caption metadata.

Launcher logs are written to the per-user KokoSpeak application-data folder. On macOS this is `~/Library/Application Support/KokoSpeak/launcher.log`; on Windows it is `%LOCALAPPDATA%\KokoSpeak\launcher.log`; on Linux it is under the XDG data directory or `~/.local/share/kokospeak/launcher.log`.

If a download times out, run the same installer again. Use `--repair`/`-Repair` after a corrupted dependency or a failed launch caused by missing packages. If your platform has no FFmpeg wheel, install a system FFmpeg executable or set `KOKOSPEAK_FFMPEG_PATH` to it and restart. The setup script stops rather than continuing after a failed required step.

For offline launches, complete setup and generate once with every language/voice you need while online. Uncached model, voice, or dictionary files can still require downloads later.

## Building a downloadable app

The project includes PyInstaller configuration and a manual GitHub Actions workflow. A successful native build bundles Python, dependencies, FFmpeg, and the built React interface; its users do not install Python, Node.js, or Conda. Model/voice downloads remain lazy.

These are build instructions and configuration, not already-tested signed release binaries.

### Build on your own computer

Use a Python 3.11/3.12 build environment and Node.js 22.12+ or 24. From the project root:

```bash
python scripts/build_desktop.py
```

The script installs `server/requirements-build.txt`, builds the React client, invokes `packaging/KokoSpeak.spec`, and creates an archive under `release/`.

If build dependencies are already installed:

```bash
python scripts/build_desktop.py --skip-install
```

| Build host | Output |
| --- | --- |
| macOS | A ZIP containing `KokoSpeak.app` |
| Windows | A ZIP containing the `KokoSpeak` folder and `KokoSpeak.exe` |
| Linux | A ZIP containing the native `KokoSpeak` folder/executable |

The entire Windows/Linux folder is required; the executable is not standalone outside it. On macOS, extract the app, move it to Applications, and open it. It starts the local server and opens your browser rather than embedding a native webview. Use the toolbar's Quit button to stop it.

Build separately on each operating system and architecture you intend to support. An Apple Silicon build is not an Intel Mac build. The manual workflow builds for the architectures supplied by its selected GitHub runners; it does not promise every architecture.

### Use GitHub Actions

Commit the project to your repository, including `.github/workflows/build-desktop.yml`. In the Actions tab, manually run **Build desktop bundles**. Each successful job uploads its archive and resolved Python dependency list as workflow artifacts. The workflow does not publish a GitHub Release automatically.

Before distributing a build, launch it on a clean machine and exercise first-run model downloads, synthesis, voice mixing, effects, cancellation, audio/subtitle export, and Quit. Test Japanese/Mandarin separately if you add those optional packages to the build environment.

The supplied workflow does not configure macOS Developer ID signing/notarization or Windows code signing. Those require your own distribution credentials and remain release work. There is no generated DMG/MSI installer in this project; the current output is a zipped app/folder bundle.

### Bundled data and caches

Frozen applications never save generated audio inside their app bundle. Defaults are:

- macOS: `~/Library/Application Support/KokoSpeak/generated`
- Windows: `%LOCALAPPDATA%\KokoSpeak\generated`
- Linux: `$XDG_DATA_HOME/kokospeak/generated` or `~/.local/share/kokospeak/generated`

You can override the parent data directory with `KOKOSPEAK_DATA_DIR`. The frozen launcher sets a default Hugging Face cache under its application-data folder unless `HF_HOME` is already configured. Keep third-party package/model license files and `packaging/THIRD_PARTY_NOTICES.md` with your distribution.

## Verification completed here

Offline tests cover installer fingerprints, reusing a private Python environment, Node target selection, checksum rejection, archive traversal/symlink rejection, frozen data paths, FFmpeg fallback, loopback port selection, and existing-instance detection. The existing core audio tests also run against the modified runtime lookup.

This environment cannot download the complete application dependencies, build the React bundle, run the full HTTP suite, or compile/test native macOS and Windows binaries. First-run network installation, PowerShell execution, PyInstaller bundling, and end-to-end launch/quit still need validation on the target systems.
