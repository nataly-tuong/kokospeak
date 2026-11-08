"""A bounded single-worker queue with observable progress and cooperative cancellation."""
from concurrent.futures import ThreadPoolExecutor
from threading import Event, RLock
from uuid import uuid4
import time
from .dsp import Cancelled

class QueueFull(Exception):
    pass

class JobQueue:
    def __init__(self, worker, capacity=8):
        self.worker = worker
        self.capacity = capacity
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix='kokospeak')
        self.lock = RLock()
        self.jobs = {}

    def submit(self, request):
        with self.lock:
            active = sum(j['state'] in ('queued','running') for j in self.jobs.values())
            if active >= self.capacity:
                raise QueueFull('The queue is full. Wait for a take to finish.')
            terminal = [key for key,j in self.jobs.items() if j.get('settled',False)]
            for key in terminal[:max(0,len(self.jobs)-49)]:
                del self.jobs[key]
            key = str(uuid4())
            job = dict(id=key,state='queued',stage='Waiting in queue',completed=0,total=0,
                       indeterminate=True,result=None,error=None,created=time.time(),cancel=Event(),label=request.label,settled=False)
            self.jobs[key] = job
            self.pool.submit(self._run, key, request)
            return self.snapshot(key)

    def snapshot(self, key):
        with self.lock:
            job = self.jobs[key]
            return {k:v for k,v in job.items() if k not in ('cancel','settled')}

    def cancel(self, key):
        with self.lock:
            job = self.jobs[key]
            if job['state'] in ('queued','running'):
                job['cancel'].set()
                job['stage'] = 'Stopping after the current model chunk…'
                if job['state']=='queued':
                    job['state']='cancelled'
            return self.snapshot(key)

    def _run(self, key, request):
        with self.lock:
            job = self.jobs[key]
            if job['cancel'].is_set():
                job['settled']=True
                return
            job.update(state='running',stage='Starting local engine')
        def update(stage, completed, total, indeterminate):
            if job['cancel'].is_set():
                raise Cancelled('Generation cancelled.')
            with self.lock:
                job.update(stage=stage,completed=completed,total=total,indeterminate=indeterminate)
        try:
            result = self.worker(request, update, job['cancel'])
            with self.lock:
                # Worker checks cancellation before committing output; after commit completion wins.
                job.update(state='complete',stage='Take ready',result=result,indeterminate=False,settled=True)
        except Cancelled:
            with self.lock:
                job.update(state='cancelled',stage='Cancelled',indeterminate=False,settled=True)
        except Exception as error:
            import logging
            logging.getLogger('kokospeak').exception('Generation job failed')
            with self.lock:
                job.update(state='error',stage='Generation failed',error=str(error),indeterminate=False,settled=True)
