"""HTTP integration checks; mocked inference, real WAV and export files."""
import io
from pathlib import Path
from tempfile import TemporaryDirectory
import time
import unittest
from unittest.mock import patch
from uuid import uuid4
from fastapi.testclient import TestClient
import numpy as np
import soundfile as sf
from src import main
from src.jobs import JobQueue

class BackendTests(unittest.TestCase):
    def setUp(self):
        self.directory=TemporaryDirectory()
        self.output_patch=patch.object(main,'GENERATED_DIR',Path(self.directory.name));self.output_patch.start()
        self.queue=JobQueue(main.make_take)
        self.queue_patch=patch.object(main,'queue',self.queue);self.queue_patch.start()
        self.client=TestClient(main.app,base_url='http://127.0.0.1')
        self.samples=np.sin(np.arange(2400)*2*np.pi*440/24000).astype('float32')*0.2

    def tearDown(self):
        self.queue.pool.shutdown(wait=True);self.client.close();self.queue_patch.stop();self.output_patch.stop();self.directory.cleanup()

    def generate(self):
        with patch.object(main.engine,'render',return_value=(self.samples,[dict(start=0,end=0.1,text='Hello',voice='af_heart')],0)):
            response=self.client.post('/api/jobs',json={'text':'Hello'})
            self.assertEqual(response.status_code,202,response.text)
            key=response.json()['id'];deadline=time.monotonic()+3
            while time.monotonic()<deadline:
                job=self.client.get(f'/api/jobs/{key}').json()
                if job['state'] in ('complete','error'):break
                time.sleep(0.01)
            self.assertEqual(job['state'],'complete',job)
            return job['result']

    def test_job_preview_exports_and_captions(self):
        result=self.generate()
        response=self.client.get(result['url']);self.assertEqual(response.status_code,200)
        self.assertEqual(sf.info(io.BytesIO(response.content)).samplerate,24000)
        self.assertEqual(len(result['waveform']),160)
        for fmt in ('wav','flac','ogg'):
            response=self.client.post('/api/export',json={'id':result['id'],'filename':'../../speech','format':fmt})
            self.assertEqual(response.status_code,200,response.text)
            self.assertNotIn('/',response.headers['content-disposition'])
            self.assertEqual(sf.info(io.BytesIO(response.content)).samplerate,24000)
        for fmt in ('srt','vtt'):
            response=self.client.get(f'/api/audio/{result["id"]}/subtitles?format={fmt}')
            self.assertEqual(response.status_code,200)
            self.assertIn('Hello',response.text)

    def test_validation_and_missing_resources(self):
        for body in ({'text':' '},{'text':'Hi','blend':[{'voice':'ff_siwis','weight':100}]},{'text':'[pause=99]\nHi'}):
            self.assertEqual(self.client.post('/api/jobs',json=body).status_code,422)
        self.assertEqual(self.client.get(f'/api/jobs/{uuid4()}').status_code,404)
        self.assertEqual(self.client.get('/api/audio/not-a-uuid').status_code,422)
        self.assertEqual(self.client.get(f'/api/audio/{uuid4()}').status_code,404)

    def test_health_catalog_and_recipe_validation(self):
        self.assertEqual(self.client.get('/api/health').status_code,200)
        options=self.client.get('/api/options').json()
        self.assertEqual(len(options['languages']),9)
        self.assertEqual(self.client.post('/api/settings/validate',json={'speed':0.8,'pitch':2}).status_code,200)
        self.assertEqual(self.client.post('/api/settings/validate',json={'emotion':'happy'}).status_code,422)

if __name__=='__main__':unittest.main()
