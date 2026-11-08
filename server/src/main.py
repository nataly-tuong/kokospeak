"""Local speech API. Run: python -m uvicorn src.main:app --host 127.0.0.1 --port 8000"""
from contextlib import asynccontextmanager
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4
import json
import logging
import re
import shutil
import tempfile
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.background import BackgroundTask
from starlette.middleware.trustedhost import TrustedHostMiddleware
from . import engine, dsp
from .catalog import ALL_VOICES, LANGUAGE_OPTIONS, FORMAT_OPTIONS, SAMPLE_RATE
from .models import GenerateRequest, ExportRequest, VoiceSettings
from .jobs import JobQueue, QueueFull

SERVER_DIR = Path(__file__).resolve().parents[1]
GENERATED_DIR = SERVER_DIR/'generated'
GENERATED_DIR.mkdir(parents=True, exist_ok=True)
CLIENT_DIST = SERVER_DIR.parent/'client'/'dist'
try: KOKORO_VERSION = version('kokoro')
except PackageNotFoundError: KOKORO_VERSION = 'not installed'
MEDIA_TYPES = {'wav':'audio/wav','flac':'audio/flac','ogg':'audio/ogg','mp3':'audio/mpeg'}


def make_take(request, progress, cancel):
    if request.pitch or request.bass or request.treble or request.effect!='clean':
        dsp.require_ffmpeg()
    audio, cues, limited = engine.render(request, progress, cancel)
    dsp.check_cancel(cancel)
    key = uuid4()
    result = dict(id=str(key),url=f'/api/audio/{key}',sampleRate=SAMPLE_RATE,duration=len(audio)/SAMPLE_RATE,
                  waveform=dsp.waveform(audio),cues=cues,limitedSamples=limited,label=request.label)
    paths = [GENERATED_DIR/f'{key}.wav', GENERATED_DIR/f'{key}.json']
    try:
        dsp.write_wav(paths[0],audio,SAMPLE_RATE)
        paths[1].write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')
        dsp.check_cancel(cancel)
    except BaseException:
        for path in paths: path.unlink(missing_ok=True)
        raise
    return result

queue = JobQueue(make_take)

@asynccontextmanager
async def lifespan(app):
    yield
    with queue.lock:
        for job in queue.jobs.values(): job['cancel'].set()
    queue.pool.shutdown(wait=False,cancel_futures=True)

app = FastAPI(title='KokoSpeak Studio Local API',version='0.3.0',lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware,allowed_hosts=['127.0.0.1','localhost'])


def audio_path(key: UUID):
    path = GENERATED_DIR/f'{key}.wav'
    if not path.is_file(): raise HTTPException(404,'Audio not found. Generate it again.')
    return path


def download_name(filename, fmt):
    name = re.sub(r'[^\w .-]','_',filename.strip(),flags=re.UNICODE).strip(' .')
    name = re.sub(r'\.(wav|flac|ogg|mp3)$','',name,flags=re.I).rstrip(' .')
    return f'{name or "koko"}.{fmt}'


@app.get('/api/health')
def health():
    return dict(status='ok',kokoroVersion=KOKORO_VERSION,modelLoaded=engine._shared_model is not None,
                ffmpegAvailable=bool(shutil.which('ffmpeg')))


@app.get('/api/options')
def options():
    return dict(languages=LANGUAGE_OPTIONS,voices=ALL_VOICES,formats=FORMAT_OPTIONS)


@app.post('/api/settings/validate')
def validate_settings(settings: VoiceSettings):
    return settings


@app.post('/api/jobs',status_code=202)
def create_job(request: GenerateRequest):
    try: return queue.submit(request)
    except QueueFull as error: raise HTTPException(429,str(error)) from error


@app.get('/api/jobs/{job_id}')
def get_job(job_id: UUID):
    try: return queue.snapshot(str(job_id))
    except KeyError: raise HTTPException(404,'Job not found. It may have expired or the server restarted.')


@app.post('/api/jobs/{job_id}/cancel')
def cancel_job(job_id: UUID):
    try: return queue.cancel(str(job_id))
    except KeyError: raise HTTPException(404,'Job not found.')


@app.get('/api/audio/{audio_id}')
def preview(audio_id: UUID):
    return FileResponse(audio_path(audio_id),media_type='audio/wav')


@app.get('/api/audio/{audio_id}/subtitles')
def subtitle_download(audio_id: UUID, format: Literal['srt','vtt']='srt'):
    audio_path(audio_id)
    metadata = GENERATED_DIR/f'{audio_id}.json'
    if not metadata.is_file(): raise HTTPException(404,'Subtitle metadata not found.')
    cues = json.loads(metadata.read_text(encoding='utf-8'))['cues']
    return Response(dsp.subtitles(cues,format),media_type='text/vtt' if format=='vtt' else 'application/x-subrip',
                    headers={'Content-Disposition':f'attachment; filename="kokospeak.{format}"'})


@app.post('/api/export')
def export_audio(request: ExportRequest):
    source = audio_path(request.id)
    directory = Path(tempfile.mkdtemp(prefix='kokospeak-export-'))
    try:
        if request.format=='wav':
            output = directory/'audio.wav'
            shutil.copyfile(source,output)
        else:
            audio,sr = dsp.read_wav(source)
            output = engine.write_format(audio,sr,directory,'audio',request.format)
        return FileResponse(output,media_type=MEDIA_TYPES[request.format],filename=download_name(request.filename,request.format),
                            background=BackgroundTask(shutil.rmtree,directory,ignore_errors=True))
    except Exception as error:
        shutil.rmtree(directory,ignore_errors=True)
        logging.getLogger('kokospeak').exception('Export failed')
        raise HTTPException(503 if isinstance(error,RuntimeError) else 500,str(error)) from error

if CLIENT_DIST.is_dir():
    app.mount('/',StaticFiles(directory=CLIENT_DIST,html=True),name='frontend')
