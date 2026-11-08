"""Measurable audio transforms; no model or web-framework dependencies."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import wave
import numpy as np

class Cancelled(Exception):
    pass


def check_cancel(cancel):
    if cancel is not None and cancel.is_set():
        raise Cancelled('Generation cancelled.')


def write_wav(path: Path, audio, sr=24000):
    values = np.clip(np.asarray(audio), -1, 1)
    with wave.open(str(path), 'wb') as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sr)
        output.writeframes((values * 32767).astype('<i2').tobytes())


def read_wav(path: Path):
    with wave.open(str(path), 'rb') as source:
        if source.getsampwidth() != 2 or source.getnchannels() != 1:
            raise ValueError('Expected a mono 16-bit WAV file.')
        sr = source.getframerate()
        audio = np.frombuffer(source.readframes(source.getnframes()), dtype='<i2').astype('float32') / 32768
    return audio, sr


def require_ffmpeg():
    executable = shutil.which('ffmpeg')
    if not executable:
        raise RuntimeError('Install ffmpeg for pitch, EQ, room/radio effects, and MP3 export; then restart Python.')
    return executable


def run_ffmpeg(arguments, cancel=None):
    check_cancel(cancel)
    process = subprocess.Popen([require_ffmpeg(), '-y', '-loglevel', 'error', *arguments], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        while True:
            check_cancel(cancel)
            try:
                _, stderr = process.communicate(timeout=0.1)
                break
            except subprocess.TimeoutExpired:
                pass
        if process.returncode:
            raise RuntimeError('ffmpeg processing failed: ' + stderr.decode(errors='replace')[-400:])
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate()


def trim_edges(audio, sr):
    active = np.flatnonzero(np.abs(audio) > 0.001)
    if not len(active):
        return audio
    pad = round(sr * 0.015)
    return audio[max(0, active[0]-pad):min(len(audio), active[-1]+pad+1)]


def process_segment(audio, sr, settings, cancel=None):
    check_cancel(cancel)
    if settings.trimSilence:
        audio = trim_edges(audio, sr)
    filters = []
    if settings.pitch:
        factor = 2 ** (settings.pitch / 12)
        filters += [f'asetrate={round(sr * factor)}', f'aresample={sr}', f'atempo={1/factor:.8f}']
    if settings.bass:
        filters.append(f'bass=g={settings.bass}:f=150')
    if settings.treble:
        filters.append(f'treble=g={settings.treble}:f=3000')
    if settings.effect == 'radio':
        filters += ['highpass=f=300', 'lowpass=f=3400']
    elif settings.effect == 'room':
        filters.append('aecho=0.8:0.7:60|90:0.18|0.12')
    if filters:
        with tempfile.TemporaryDirectory(prefix='kokospeak-fx-') as directory:
            source, target = Path(directory)/'in.wav', Path(directory)/'out.wav'
            write_wav(source, audio, sr)
            run_ffmpeg(['-i', str(source), '-af', ','.join(filters), '-ar', str(sr), '-ac', '1', '-c:a', 'pcm_s16le', str(target)], cancel)
            audio, _ = read_wav(target)
    check_cancel(cancel)
    return np.asarray(audio, dtype='float32')


def finish_audio(audio, sr, settings):
    audio = np.array(audio, dtype='float32', copy=True)
    if not len(audio) or not np.all(np.isfinite(audio)):
        raise RuntimeError('The engine produced invalid or empty audio.')
    for milliseconds, start in ((settings.fadeIn, True), (settings.fadeOut, False)):
        frames = min(round(sr * milliseconds / 1000), len(audio)//2)
        if frames:
            ramp = np.linspace(0, 1, frames) if start else np.linspace(1, 0, frames)
            if start: audio[:frames] *= ramp
            else: audio[-frames:] *= ramp
    peak = float(np.max(np.abs(audio)))
    if settings.normalize and peak > 0:
        audio *= (10 ** (-1/20)) / peak
    audio *= 10 ** (settings.gain/20)
    limited = int(np.count_nonzero(np.abs(audio) > 0.999))
    return np.clip(audio, -0.999, 0.999), limited


def waveform(audio, bins=160):
    return [round(float(np.max(np.abs(part))), 4) if len(part) else 0 for part in np.array_split(audio, bins)]


def timestamp(seconds, srt=False):
    milliseconds = max(0, round(seconds*1000))
    hours, rest = divmod(milliseconds, 3600000)
    minutes, rest = divmod(rest, 60000)
    seconds, ms = divmod(rest, 1000)
    return f'{hours:02}:{minutes:02}:{seconds:02}{"," if srt else "."}{ms:03}'


def subtitles(cues, fmt):
    lines = ['WEBVTT', ''] if fmt == 'vtt' else []
    for index, cue in enumerate(cues, 1):
        lines += [str(index), f'{timestamp(cue["start"], fmt=="srt")} --> {timestamp(cue["end"], fmt=="srt")}', cue['text'].replace('-->', '→'), '']
    return '\n'.join(lines)+'\n'
