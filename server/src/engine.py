"""Kokoro inference, weighted voice blending, and measured script assembly."""
from pathlib import Path
from threading import Lock
import tempfile
import numpy as np
from .catalog import ALL_VOICES, LANGUAGE_OPTIONS, FORMAT_OPTIONS, SAMPLE_RATE, KOKORO_REPO_ID
from .script import plan_script
from . import dsp

_pipelines = {}
_shared_model = None
_generation_lock = Lock()


def get_pipeline(language):
    global _shared_model
    if language not in _pipelines:
        from kokoro import KPipeline
        pipeline = KPipeline(lang_code=language, repo_id=KOKORO_REPO_ID,
                             model=_shared_model if _shared_model is not None else True)
        _shared_model = pipeline.model
        _pipelines[language] = pipeline
    return _pipelines[language]


def blend_voice(pipeline, voices):
    total = sum(v.weight for v in voices)
    if total <= 0:
        raise ValueError('Blend weights must have a positive total.')
    result = None
    for item in voices:
        if item.weight <= 0:
            continue
        part = pipeline.load_voice(item.voice) * (item.weight/total)
        result = part if result is None else result + part
    return result


def render(request, progress, cancel):
    segments = plan_script(request.text, request.language, request.voice, request.sentencePause, request.paragraphPause)
    total = len(segments)
    progress('Loading language and model', 0, total, True)
    # Only one model inference at a time, including direct callers outside the job queue.
    with _generation_lock:
        dsp.check_cancel(cancel)
        pipeline = get_pipeline(request.language)
        dsp.check_cancel(cancel)
        progress('Preparing voice blend' if request.blend else 'Preparing voice', 0, total, True)
        mixed = blend_voice(pipeline, request.blend) if request.blend else None
        chunks, cues = [], []
        cursor = 0
        for index, segment in enumerate(segments):
            dsp.check_cancel(cancel)
            if not segment.text:
                silence = np.zeros(round(segment.pause*SAMPLE_RATE), dtype='float32')
                chunks.append(silence)
                cursor += len(silence)
            else:
                progress(f'Generating segment {index+1} of {total}', index, total, False)
                # Explicit script voice commands override the base blend.
                voice = mixed if mixed is not None and segment.voice == request.voice else segment.voice
                samples = []
                for result in pipeline(segment.text, voice=voice, speed=request.speed):
                    dsp.check_cancel(cancel)
                    if result.audio is not None:
                        samples.append(result.audio.detach().cpu().numpy().reshape(-1).astype('float32'))
                if not samples or not sum(map(len, samples)):
                    raise RuntimeError(f'No audio was produced for segment {index+1}.')
                progress(f'Finishing segment {index+1} of {total}', index, total, False)
                audio = dsp.process_segment(np.concatenate(samples), SAMPLE_RATE, request, cancel)
                cues.append({'start': cursor/SAMPLE_RATE, 'end': (cursor+len(audio))/SAMPLE_RATE,
                             'text': segment.text, 'voice': segment.voice})
                chunks.append(audio)
                cursor += len(audio)
                if segment.gap:
                    silence = np.zeros(round(segment.gap*SAMPLE_RATE), dtype='float32')
                    chunks.append(silence)
                    cursor += len(silence)
            progress(f'{index+1} of {total} segments ready', index+1, total, False)
        dsp.check_cancel(cancel)
        progress('Normalizing and saving', total, total, False)
        audio, limited = dsp.finish_audio(np.concatenate(chunks), SAMPLE_RATE, request)
        return audio, cues, limited


def write_format(audio, sr: int, out_dir: Path, base: str, fmt: str):
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f'{base}.{fmt}'
    if fmt == 'wav':
        dsp.write_wav(target, audio, sr)
    elif fmt in ('flac','ogg'):
        import soundfile as sf
        if fmt == 'flac': sf.write(target, audio, sr, format='FLAC')
        else: sf.write(target, audio, sr, format='OGG', subtype='VORBIS')
    elif fmt == 'mp3':
        with tempfile.TemporaryDirectory(prefix='kokospeak-mp3-') as directory:
            source = Path(directory)/'input.wav'
            dsp.write_wav(source, audio, sr)
            dsp.run_ffmpeg(['-i',str(source),'-vn','-ar',str(sr),'-ac','1','-b:a','192k',str(target)])
    else:
        raise ValueError(f'Unsupported format: {fmt}')
    return target
