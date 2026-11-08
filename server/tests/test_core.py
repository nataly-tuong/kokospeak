"""Core checks run without downloading Kokoro or installing the web framework."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import shutil
import threading
import time
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
from pydantic import ValidationError
from src import dsp, engine
from src.catalog import ALL_VOICES
from src.models import GenerateRequest, VoiceSettings
from src.script import plan_script
from src.jobs import JobQueue, QueueFull

class CoreTests(unittest.TestCase):
    def test_schema_and_script_validation(self):
        self.assertEqual(sum(map(len,ALL_VOICES.values())),54)
        for values in ({'text':' '},{'text':'Hello','speed':0.2},{'text':'Hi','pitch':13},
                       {'text':'Hi','language':'f','voice':'af_heart'},
                       {'text':'Hi','blend':[{'voice':'af_heart','weight':0}]},
                       {'text':'[pause=NaN]\nHello'}, {'text':'[voice=bad]\nHello'}):
            with self.assertRaises((ValidationError,ValueError)): GenerateRequest(**values)
        VoiceSettings(speed=0.5,pitch=-12)
        VoiceSettings(speed=2,pitch=12)

    def test_script_pauses_dialogue_and_cjk(self):
        segments=plan_script('Hello. There.\n\n[voice=am_adam]\nAgain.\n[pause=1.2]\nDone.','a','af_heart',0.1,0.5)
        self.assertEqual([s.text for s in segments],['Hello.','There.','Again.','','Done.'])
        self.assertEqual(segments[1].gap,0.5)
        self.assertEqual(segments[2].voice,'am_adam')
        self.assertEqual(segments[2].gap,0)
        self.assertEqual(segments[3].pause,1.2)
        self.assertEqual(segments[-1].gap,0)
        self.assertEqual(len(plan_script('你好。世界！','z','zf_xiaobei',0,0)),2)
        self.assertTrue(all(len(s.text)<=350 for s in plan_script('a'*900,'a','af_heart',0,0)))

    def test_blend_normalizes_weights(self):
        pipeline=SimpleNamespace(load_voice=lambda voice:np.array([1.,2.]) if voice=='a' else np.array([3.,4.]))
        blend=[SimpleNamespace(voice='a',weight=25),SimpleNamespace(voice='b',weight=75)]
        np.testing.assert_allclose(engine.blend_voice(pipeline,blend),[2.5,3.5])
        for item in blend: item.weight*=0.1
        np.testing.assert_allclose(engine.blend_voice(pipeline,blend),[2.5,3.5])

    def test_render_measures_captions_and_silence(self):
        class Tensor:
            def detach(self):return self
            def cpu(self):return self
            def numpy(self):return np.full(2400,0.2,dtype='float32')
        calls=[]
        def pipeline(text,voice,speed):
            calls.append(voice)
            yield SimpleNamespace(audio=Tensor())
        request=GenerateRequest(text='One.\n[pause=0.2]\n[voice=am_adam]\nTwo.',sentencePause=0,paragraphPause=0,
                                trimSilence=False,normalize=False,fadeIn=0,fadeOut=0)
        events=[]
        with patch.object(engine,'get_pipeline',return_value=pipeline):
            audio,cues,limited=engine.render(request,lambda *v:events.append(v),threading.Event())
        self.assertEqual(len(audio),9600)
        self.assertAlmostEqual(cues[1]['start'],0.3)
        self.assertAlmostEqual(cues[1]['end'],0.4)
        self.assertEqual(calls,['af_heart','am_adam'])
        self.assertEqual(limited,0)
        self.assertEqual(events[-1][1:3],(3,3))

    def test_cancellation_stops_before_model_load(self):
        event=threading.Event();event.set()
        with patch.object(engine,'get_pipeline') as load:
            with self.assertRaises(dsp.Cancelled): engine.render(GenerateRequest(text='Hi'),lambda *args:None,event)
            load.assert_not_called()

    def test_trim_fades_normalize_and_gain_limit(self):
        audio=np.r_[np.zeros(2400),np.full(2400,0.2),np.zeros(2400)].astype('float32')
        trimmed=dsp.trim_edges(audio,24000)
        self.assertEqual(len(trimmed),3120)
        settings=VoiceSettings(fadeIn=10,fadeOut=10,normalize=True)
        finished,limited=dsp.finish_audio(trimmed,24000,settings)
        self.assertAlmostEqual(float(np.max(finished)),10**(-1/20),places=5)
        self.assertEqual(float(finished[0]),0)
        self.assertEqual(float(finished[-1]),0)
        self.assertEqual(limited,0)
        settings.gain=12
        finished,limited=dsp.finish_audio(trimmed,24000,settings)
        self.assertGreater(limited,0)
        self.assertLessEqual(float(np.max(np.abs(finished))),1)
        self.assertEqual(len(dsp.waveform(finished)),160)

    @unittest.skipUnless(shutil.which('ffmpeg'),'ffmpeg unavailable')
    def test_pitch_changes_frequency_and_preserves_duration(self):
        sr=24000
        audio=(np.sin(np.arange(sr*2)*2*np.pi*440/sr)*0.3).astype('float32')
        result=dsp.process_segment(audio,sr,VoiceSettings(pitch=12,trimSilence=False))
        self.assertLess(abs(len(result)/sr-2),0.15)
        spectrum=np.abs(np.fft.rfft(result))
        frequency=np.argmax(spectrum)*sr/len(result)
        self.assertLess(abs(frequency-880),8)

    @unittest.skipUnless(shutil.which('ffmpeg'),'ffmpeg unavailable')
    def test_eq_and_effects_produce_valid_audio(self):
        audio=np.random.default_rng(1).normal(0,0.1,12000).astype('float32')
        for effect in ('radio','room'):
            result=dsp.process_segment(audio,24000,VoiceSettings(effect=effect,bass=2,treble=-2,trimSilence=False))
            self.assertGreater(len(result),10000)
            self.assertTrue(np.all(np.isfinite(result)))

    def test_subtitle_boundaries(self):
        cues=[dict(start=1.234,end=2.5,text='Hello --> there.')]
        self.assertIn('00:00:01,234 --> 00:00:02,500',dsp.subtitles(cues,'srt'))
        self.assertTrue(dsp.subtitles(cues,'vtt').startswith('WEBVTT\n'))

class JobTests(unittest.TestCase):
    def test_queue_capacity_and_queued_cancellation(self):
        started=threading.Event();release=threading.Event();calls=[]
        def worker(request,progress,cancel):
            calls.append(request.label);started.set();release.wait(2)
            dsp.check_cancel(cancel)
            progress('Done',1,1,False)
            return {'ok':True}
        queue=JobQueue(worker,capacity=2)
        try:
            first=queue.submit(SimpleNamespace(label='first'));self.assertTrue(started.wait(1))
            second=queue.submit(SimpleNamespace(label='second'))
            with self.assertRaises(QueueFull):queue.submit(SimpleNamespace(label='third'))
            self.assertEqual(queue.cancel(second['id'])['state'],'cancelled')
            release.set()
            deadline=time.monotonic()+2
            while queue.snapshot(first['id'])['state']=='running' and time.monotonic()<deadline:time.sleep(0.005)
            self.assertEqual(queue.snapshot(first['id'])['state'],'complete')
        finally:release.set();queue.pool.shutdown(wait=True)
        self.assertEqual(calls,['first'])

    def test_running_cancel_signal(self):
        started=threading.Event()
        def worker(request,progress,cancel):
            started.set();cancel.wait(2);dsp.check_cancel(cancel)
        queue=JobQueue(worker)
        try:
            job=queue.submit(SimpleNamespace(label='cancel'));self.assertTrue(started.wait(1))
            queue.cancel(job['id'])
            queue.pool.shutdown(wait=True)
            self.assertEqual(queue.snapshot(job['id'])['state'],'cancelled')
        finally:queue.pool.shutdown(wait=True)

if __name__=='__main__':unittest.main()
