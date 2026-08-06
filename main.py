from nicegui import ui, app
from pathlib import Path
import asyncio, uuid, subprocess, base64, io, tempfile, sys, platform
import numpy as np
import soundfile as sf
from kokoro import KPipeline

try:
    from importlib.metadata import version as _pkg_version
    KOKORO_VERSION = _pkg_version('kokoro')
except Exception:
    KOKORO_VERSION = '0.9.4'

GENERATED_DIR = Path('generated')
GENERATED_DIR.mkdir(exist_ok=True)
SAVE_DEFAULT = str(GENERATED_DIR.resolve())

app.add_static_files('/generated', str(GENERATED_DIR))
app.add_static_files('/assets', 'assets')
app.native.window_args['title'] = 'KokoSpeak'
app.native.window_args['width'] = 1280
app.native.window_args['height'] = 800
app.native.window_args['min_size'] = (960, 620)

ACCENT = '#8A2BE2'

ui.add_css(f"""
html, body, #q-app, #app {{ height:100%; overflow:hidden; overscroll-behavior:none; }}
.q-layout, .q-page-container, .q-page {{ height:100%; overflow:hidden; }}
* {{ box-sizing:border-box; }}
.no-resize {{ resize: none !important; }}
audio::-webkit-media-controls-panel {{ background-color: rgba(0,0,0,0.92); }}
audio::-webkit-media-controls-enclosure {{ border-radius: 8px; }}
audio::-webkit-media-controls-current-time-display,
audio::-webkit-media-controls-time-remaining-display {{ color: #fff; }}
audio::-webkit-media-controls-play-button,
audio::-webkit-media-controls-mute-button,
audio::-webkit-media-controls-timeline,
audio::-webkit-media-controls-volume-slider {{ filter: invert(1) hue-rotate(180deg); }}
a:hover {{ color: {ACCENT}; }}

.koko-menu-item {{ min-height: 0 !important; padding: 2px 10px !important; font-size: 12px !important; }}
.koko-menu-item:hover {{ background: rgba(255,255,255,0.08) !important; color: #fff !important; }}
.koko-toolbar-icon .q-icon {{ font-size: 18px; }}
.koko-toolbar-icon {{ min-height: 0 !important; padding: 6px !important; }}
.koko-badge-dot {{ box-shadow: 0 0 6px 1px rgba(74,222,128,0.7); }}
@keyframes koko-spin {{ from {{ transform: rotate(0deg); }} to {{ transform: rotate(360deg); }} }}
.koko-spin .q-icon {{ animation: koko-spin 0.9s linear infinite; display:inline-block; }}
.koko-accent-btn {{ background: {ACCENT} !important; color: #fff !important; }}
.koko-accent-btn:hover {{ background: #7a24c9 !important; }}
.koko-accent-btn.disabled, .koko-accent-btn[disabled] {{ background: #5b3a7d !important; opacity: 0.7; }}
.koko-outline-btn {{ background: rgba(0,0,0,0.4) !important; color: #fff !important; border: 1px solid rgba(255,255,255,0.2) !important; }}
.koko-outline-btn:hover {{ background: rgba(255,255,255,0.08) !important; }}
.koko-menu-surface {{ background: #171718 !important; color: #d1d5db !important; }}
.koko-dialog {{ background: #141416 !important; color: #fff !important; }}
.koko-generating-badge {{ color: #c084fc !important; }}
""")

_pipeline = None
_last_audio = None

LANGUAGE_OPTIONS = {
    'a': 'American English',
    'b': 'British English', 
    'j': 'Japanese',
    'z': 'Mandarin Chinese',
    'f': 'French',
    'h': 'Hindi',
    'i': 'Italian',
    'e': 'Spanish',
    'p': 'Brazilian Portuguese'
}

ALL_VOICES = {
    'a': {
        'af_heart': 'F · Heart', 'af_alloy': 'F · Alloy', 'af_aoede': 'F · Aoede', 'af_bella': 'F · Bella',
        'af_jessica': 'F · Jessica', 'af_kore': 'F · Kore', 'af_nicole': 'F · Nicole', 'af_nova': 'F · Nova',
        'af_river': 'F · River', 'af_sarah': 'F · Sarah', 'af_sky': 'F · Sky',
        'am_adam': 'M · Adam', 'am_echo': 'M · Echo', 'am_eric': 'M · Eric', 'am_fenrir': 'M · Fenrir',
        'am_liam': 'M · Liam', 'am_michael': 'M · Michael', 'am_onyx': 'M · Onyx', 'am_puck': 'M · Puck',
        'am_santa': 'M · Santa'
    },
    'b': {
        'bf_alice': 'F · Alice', 'bf_emma': 'F · Emma', 'bf_isabella': 'F · Isabella', 'bf_lily': 'F · Lily',
        'bm_daniel': 'M · Daniel', 'bm_fable': 'M · Fable', 'bm_george': 'M · George', 'bm_lewis': 'M · Lewis'
    },
    'j': {
        'jf_alpha': 'F · Alpha', 'jf_gongitsune': 'F · Gongitsune', 'jf_nezumi': 'F · Nezumi',
        'jf_tebukuro': 'F · Tebukuro', 'jm_kumo': 'M · Kumo'
    },
    'z': {
        'zf_xiaobei': 'F · Xiaobei', 'zf_xiaoni': 'F · Xiaoni', 'zf_xiaoxiao': 'F · Xiaoxiao',
        'zf_xiaoyi': 'F · Xiaoyi', 'zm_yunjian': 'M · Yunjian', 'zm_yunxi': 'M · Yunxi',
        'zm_yunxia': 'M · Yunxia', 'zm_yunyang': 'M · Yunyang'
    },
    'f': {'ff_siwis': 'F · Siwis'},
    'h': {'hf_alpha': 'F · Alpha', 'hf_beta': 'F · Beta', 'hm_omega': 'M · Omega', 'hm_psi': 'M · Psi'},
    'i': {'if_sara': 'F · Sara', 'im_nicola': 'M · Nicola'},
    'e': {'ef_dora': 'F · Dora', 'em_alex': 'M · Alex', 'em_santa': 'M · Santa'},
    'p': {'pf_dora': 'F · Dora', 'pm_alex': 'M · Alex', 'pm_santa': 'M · Santa'}
}

FORMAT_OPTIONS = {'wav': 'WAV', 'flac': 'FLAC', 'ogg': 'OGG', 'mp3': 'MP3'}

SILENCE = GENERATED_DIR / 'silence.wav'
if not SILENCE.exists():
    sf.write(SILENCE, np.zeros(2400, dtype='float32'), 24000)
SILENCE_URL = f'/generated/{SILENCE.name}'

def kokoro_generate(text: str, voice: str, speed: float, lang_code: str):
    global _pipeline
    if _pipeline is None:
        _pipeline = KPipeline(lang_code=lang_code)
    stream = _pipeline(text, voice=voice, speed=speed)
    chunks = []
    for item in stream:
        audio = item[-1]
        chunks.append(audio)
    if not chunks:
        return np.zeros(1, dtype='float32'), 24000
    return np.concatenate(chunks), 24000

def write_format(audio, sr, out_dir: Path, base: str, fmt: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    if fmt == 'wav':
        p = out_dir / f'{base}.wav'
        sf.write(p, audio, sr)
        return p
    if fmt == 'flac':
        p = out_dir / f'{base}.flac'
        sf.write(p, audio, sr, format='FLAC')
        return p
    if fmt == 'ogg':
        p = out_dir / f'{base}.ogg'
        sf.write(p, audio, sr, format='OGG', subtype='VORBIS')
        return p
    if fmt == 'mp3':
        wav_tmp = GENERATED_DIR / f'{base}_tmp.wav'
        sf.write(wav_tmp, audio, sr)
        p = out_dir / f'{base}.mp3'
        try:
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(wav_tmp), '-vn', '-ar', str(sr), '-ac', '1', '-b:a', '192k', str(p)], check=True)
        finally:
            wav_tmp.unlink(missing_ok=True)
        return p
    p = out_dir / f'{base}.wav'
    sf.write(p, audio, sr)
    return p

def synthesize(text: str, voice: str, speed: float, pitch: float, lang_code: str):
    audio, sr = kokoro_generate(text, voice, speed, lang_code)
    if pitch != 0.0:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_dir_path = Path(temp_dir)
            semitones = pitch * 12
            rate = 2**(semitones/12)
            base = uuid.uuid4().hex
            in_path = temp_dir_path / f'{base}_in.wav'
            out_path = temp_dir_path / f'{base}_out.wav'
            sf.write(in_path, audio, sr)
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(in_path), '-filter:a', f'asetrate={sr*rate},aresample={sr}', str(out_path)], check=True)
            audio, sr = sf.read(out_path)

    with io.BytesIO() as buffer:
        sf.write(buffer, audio, sr, format='wav')
        buffer.seek(0)
        encoded_audio = base64.b64encode(buffer.read()).decode()
        play_url = f'data:audio/wav;base64,{encoded_audio}'
    
    return play_url, (audio, sr)

def _open_output_folder():
    path = str(GENERATED_DIR.resolve())
    try:
        if sys.platform == 'darwin':
            subprocess.run(['open', path])
        elif sys.platform.startswith('win'):
            subprocess.run(['explorer', path])
        else:
            subprocess.run(['xdg-open', path])
    except Exception:
        pass

def _exit_app():
    try:
        app.native.main_window.destroy()
    except Exception:
        app.shutdown()

def _toggle_fullscreen():
    try:
        app.native.main_window.toggle_fullscreen()
    except Exception:
        ui.run_javascript(
            'document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen()'
        )

with ui.element('div').classes('fixed inset-0 flex flex-col min-h-screen').style('background-color:#0b0b0d'):
    with ui.element('video').props('autoplay muted loop playsinline')\
        .classes('absolute inset-0 w-full h-full object-cover pointer-events-none opacity-20'):
        ui.element('source').props('src="/assets/gradient.webm" type="video/webm"')
    ui.element('div').classes('absolute inset-0 bg-black/80 pointer-events-none')

    with ui.column().classes('relative z-10 flex flex-1 min-h-0 w-full gap-0'):

        with ui.row().classes('w-full items-center gap-1 px-3 py-1 bg-black/70 border-b border-white/10 shrink-0'):
            with ui.button('File', color=None).props('flat dense no-caps').classes('text-gray-300 text-xs koko-toolbar-icon'):
                with ui.menu().props('dark auto-close').classes('koko-menu-surface'):
                    ui.menu_item('New', on_click=lambda: on_clear()).classes('koko-menu-item')
                    ui.menu_item('Open Output Folder', on_click=_open_output_folder).classes('koko-menu-item')
                    ui.separator()
                    ui.menu_item('Exit', on_click=_exit_app).classes('koko-menu-item')
            with ui.button('Edit', color=None).props('flat dense no-caps').classes('text-gray-300 text-xs koko-toolbar-icon'):
                with ui.menu().props('dark auto-close').classes('koko-menu-surface'):
                    ui.menu_item('Clear Text', on_click=lambda: on_clear()).classes('koko-menu-item')
                    ui.menu_item('Copy Output Path', on_click=lambda: ui.run_javascript(
                        f'navigator.clipboard.writeText({str(GENERATED_DIR.resolve())!r})'
                    )).classes('koko-menu-item')
            with ui.button('View', color=None).props('flat dense no-caps').classes('text-gray-300 text-xs koko-toolbar-icon'):
                with ui.menu().props('dark auto-close').classes('koko-menu-surface'):
                    ui.menu_item('Toggle Fullscreen', on_click=_toggle_fullscreen).classes('koko-menu-item')
            with ui.button('Help', color=None).props('flat dense no-caps').classes('text-gray-300 text-xs koko-toolbar-icon'):
                with ui.menu().props('dark auto-close').classes('koko-menu-surface'):
                    ui.menu_item('About KokoSpeak', on_click=lambda: about_dialog.open()).classes('koko-menu-item')

        with ui.dialog() as about_dialog, ui.card().classes('koko-dialog'):
            ui.label('KokoSpeak').classes('font-bold text-xl')
            ui.label(f'Kokoro engine v{KOKORO_VERSION}').classes('text-white/60 text-sm')
            ui.label('Local, offline text-to-speech powered by the open-source Kokoro model.').classes('text-white/80 text-sm mt-2 max-w-xs')
            with ui.row().classes('w-full justify-end mt-3'):
                ui.button('Close', on_click=about_dialog.close).props('flat color=white')

        with ui.row().classes('w-full items-center gap-2 px-4 py-2 bg-black/50 border-b border-white/10 shrink-0'):
            ui.button(icon='note_add', on_click=lambda: on_clear()).props('flat dense round color=white').classes('koko-toolbar-icon').tooltip('New')
            ui.button(icon='folder_open', on_click=_open_output_folder).props('flat dense round color=white').classes('koko-toolbar-icon').tooltip('Open output folder')
            ui.element('div').classes('w-px h-5 bg-white/15 mx-1')
            with ui.column().classes('gap-0'):
                ui.label('KokoSpeak').classes('text-white font-bold text-sm leading-tight')
                ui.label('Using open-sourced AI, Kokoro').classes('text-white/50 text-[11px] leading-tight')
            ui.element('div').classes('flex-1')
            with ui.row().classes('items-center gap-1.5 px-2.5 py-1 rounded-full border border-white/15 bg-white/5'):
                ui.element('div').classes('w-1.5 h-1.5 rounded-full bg-green-400 koko-badge-dot')
                ui.label('KOKORO ENGINE · LOCAL').classes('text-white/60 text-[10px] font-semibold tracking-widest')

        with ui.element('div').classes('flex flex-1 min-h-0 w-full p-4'):
            with ui.element('div').classes('bg-black/70 rounded-lg border border-white/10 w-full p-5 gap-5 flex-1 flex flex-col min-h-0 overflow-hidden'):
                with ui.element('div').classes('flex flex-1 min-h-0 min-w-0 flex-col sm:flex-row gap-4'):
                    with ui.element('div').classes('flex-1 min-w-0 flex min-h-0 flex-col gap-3'):
                        ui.label('Prompt / Text').classes('text-white/80 font-semibold text-xs tracking-wide uppercase')
                        with ui.scroll_area().classes('flex-1 min-w-0 w-full rounded-md bg-black/90 border border-white/10 p-2 min-h-0'):
                            text_box = ui.textarea(placeholder='Type something...').props('dark color=purple-12 autogrow input-class="no-resize text-white" input-style="overflow:hidden"').classes('w-full')
                        with ui.element('div').classes('flex gap-3 w-full'):
                            gen_btn = ui.button('Generate', color=None).props('unelevated no-caps').classes('font-semibold flex-1 koko-accent-btn')
                            clr_btn = ui.button('Clear', color=None).props('unelevated no-caps').classes('font-semibold flex-1 koko-outline-btn')

                    with ui.element('div').classes('flex-1 min-w-0 flex min-h-0 flex-col gap-3'):
                        with ui.row().classes('w-full items-center justify-between'):
                            ui.label('Audio Preview').classes('text-white/80 font-semibold text-xs tracking-wide uppercase')
                            generating_badge = ui.label('GENERATING').classes('koko-generating-badge font-bold text-[10px] tracking-widest')
                            generating_badge.set_visibility(False)
                        ui.label('SCROLL TO SEE ALL SETTINGS').classes('text-white/40 text-[10px] tracking-wide')
                        with ui.scroll_area().classes('w-full flex-1 flex flex-col'):
                            with ui.expansion('Language', value=False).classes('w-full bg-black/80 border border-white/10 text-white rounded-md mb-1'):
                                with ui.row().classes('w-full gap-4'):
                                    language_select = ui.select(
                                        options=LANGUAGE_OPTIONS, value='a', label='Language'
                                    ).classes('w-full text-white').props(
                                        'outlined dense dark popup-content-class="bg-black text-white" input-class="text-white"'
                                    )
                            with ui.expansion('Voice', value=False).classes('w-full bg-black/80 border border-white/10 text-white rounded-md mb-1'):
                                with ui.row().classes('w-full gap-4'):
                                    voice_select = ui.select(
                                        options=ALL_VOICES['a'], value='af_heart', label='Voice'
                                    ).classes('w-full text-white').props(
                                        'outlined dense dark popup-content-class="bg-black text-white" input-class="text-white"'
                                    )
                            with ui.expansion('Speed', value=False).classes('w-full bg-black/80 border border-white/10 text-white rounded-md mb-1'):
                                with ui.column().classes('w-full gap-2'):
                                    ui.label('Speed').classes('text-white/80 text-sm')
                                    speed_slider = ui.slider(min=0.80, max=1.20, value=1.00, step=0.01).props(f'color=purple-12').classes('w-full')
                                    ui.label().bind_text_from(speed_slider, 'value', backward=lambda v: f'{v:.2f}x').classes('text-white/60 text-xs')
                            with ui.expansion('Pitch', value=False).classes('w-full bg-black/80 border border-white/10 text-white rounded-md mb-1'):
                                with ui.column().classes('w-full gap-2'):
                                    ui.label('Pitch (octaves)').classes('text-white/80 text-sm')
                                    pitch_slider = ui.slider(min=-2.00, max=2.00, value=0.00, step=0.01).props(f'color=purple-12').classes('w-full')
                                    ui.label().bind_text_from(pitch_slider, 'value', backward=lambda v: f'{v:+.2f}').classes('text-white/60 text-xs')
                        with ui.element('div').classes('w-full rounded-md bg-black/90 border border-white/10 p-2 flex items-center'):
                            audio_el = ui.audio(src=SILENCE_URL).props('controls controlslist="nodownload noplaybackrate noremoteplayback" preload=metadata').classes('flex-1')
                        with ui.element('div').classes('w-full rounded-md bg-black/90 border border-white/10 p-2 flex items-end gap-2'):
                            with ui.column().classes('flex-1 gap-0'):
                                ui.label('FILENAME').classes('text-white/40 text-[10px] tracking-widest')
                                filename_input = ui.input(value='koko', placeholder='Enter filename').props('dense dark borderless').classes('flex-1 text-white font-semibold')
                            with ui.column().classes('w-24 gap-0'):
                                ui.label('FORMAT').classes('text-white/40 text-[10px] tracking-widest')
                                format_select = ui.select(
                                    options=FORMAT_OPTIONS, value='wav'
                                ).props('dense dark borderless popup-content-class="bg-black text-white" input-class="text-white"').classes('text-white font-semibold')
                            save_btn = ui.button(icon='save', color=None).props('unelevated round dense').classes('koko-accent-btn')

                progress_bar = ui.linear_progress(show_value=False, value=0).props('color=purple-12').classes('w-full shrink-0')

                async def on_generate():
                    global _last_audio
                    txt = (text_box.value or '').replace('\n', ' ')
                    if not txt:
                        status_bar.text = 'Please enter some text.'
                        return
                    v = voice_select.value or list(ALL_VOICES[language_select.value].keys())[0]
                    s = float(speed_slider.value or 1.0)
                    p = float(pitch_slider.value or 0.0)
                    l = language_select.value or 'a'
                    gen_btn.disable()
                    clr_btn.disable()
                    gen_btn.set_text('Generating...')
                    gen_btn.props(add='icon=autorenew')
                    gen_btn.classes(add='koko-spin')
                    generating_badge.set_visibility(True)
                    progress_bar.set_visibility(True)
                    progress_bar.props('indeterminate')
                    status_bar.text = 'Generating audio...'
                    try:
                        play_url, (audio, sr) = await asyncio.to_thread(synthesize, txt, v, s, p, l)
                        audio_el.set_source(play_url if play_url else SILENCE_URL)
                        _last_audio = (audio, sr)
                        status_bar.text = 'Ready'
                    except Exception as e:
                        audio_el.set_source(SILENCE_URL)
                        status_bar.text = f'Error: {e}'
                    finally:
                        progress_bar.props(remove='indeterminate')
                        progress_bar.set_visibility(False)
                        generating_badge.set_visibility(False)
                        gen_btn.classes(remove='koko-spin')
                        gen_btn.props(remove='icon=autorenew')
                        gen_btn.set_text('Generate')
                        gen_btn.enable()
                        clr_btn.enable()

                def on_language_change():
                    selected_lang = language_select.value
                    voices_for_lang = ALL_VOICES.get(selected_lang, {})
                    voice_select.set_options(voices_for_lang)
                    if voices_for_lang:
                        voice_select.set_value(list(voices_for_lang.keys())[0])

                language_select.on_value_change(lambda: on_language_change())

                async def save_file():
                    global _last_audio
                    if not _last_audio:
                        status_bar.text = 'Please generate audio first.'
                        return
                    (audio, sr) = _last_audio
                    filename = (filename_input.value or 'koko').strip()
                    if not filename:
                        filename = 'koko'
                    selected_format = format_select.value or 'wav'
                    try:
                        save_path = GENERATED_DIR / f'{filename}.{selected_format}'
                        write_format(audio, sr, save_path.parent, save_path.stem, selected_format)
                        status_bar.text = f'Saved: {save_path.name}'
                    except Exception as e:
                        status_bar.text = f'Save failed: {e}'

                def on_clear():
                    text_box.value = ''
                    audio_el.set_source(SILENCE_URL)
                    status_bar.text = 'Ready'
                    update_word_count()

                gen_btn.on_click(on_generate)
                clr_btn.on_click(on_clear)
                save_btn.on_click(save_file)

        with ui.row().classes('w-full items-center justify-between px-4 py-1.5 bg-black/80 border-t border-white/10 text-[11px] shrink-0'):
            status_bar = ui.label('Ready').classes('text-white/60 whitespace-normal overflow-wrap-anywhere break-words')
            word_count_label = ui.label(f'Kokoro v{KOKORO_VERSION} · 0 words').classes('text-white/40')

        def update_word_count():
            txt = (text_box.value or '').strip()
            n = len(txt.split()) if txt else 0
            word_count_label.text = f'Kokoro v{KOKORO_VERSION} · {n} word{"s" if n != 1 else ""}'

        text_box.on_value_change(lambda: update_word_count())

ui.run(native=True, reload=False)
