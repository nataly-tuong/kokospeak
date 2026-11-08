import { LoaderCircle,Square } from 'lucide-react';
import type { Job } from '../types/studio';
export default function GenerationProgress({job,busy,stopping,onCancel,batchPosition}:{job:Job|null;busy:boolean;stopping:boolean;onCancel:()=>void;batchPosition:string}){
  if(!busy&&!job)return null;
  const indefinite=!job||job.indeterminate||job.state==='queued';
  return <div className={`generation-progress ${job?.state==='error'?'has-error':''}`}>
    <div className="flex items-center justify-between gap-3"><span className="flex items-center gap-2">{busy&&<LoaderCircle className="progress-spinner" size={14}/>}<span role="status">{stopping?'Stopping after the current model chunk…':job?.stage??'Submitting to the local engine…'}</span></span>{busy&&<button className="cancel-button" disabled={stopping} onClick={onCancel}><Square size={10}/>{stopping?'Stopping':'Cancel'}</button>}</div>
    {indefinite&&busy?<progress aria-label="Preparing model or waiting for generation"/>:<progress aria-label="Completed script segments" max={Math.max(1,job?.total??1)} value={job?.state==='complete'?Math.max(1,job.total):job?.completed??0}/>}
    <p>{batchPosition||((job?.total??0)>0?`${job?.completed} / ${job?.total} script segments ready`:'Model or voice downloads can take longer on the first run.')}</p>
  </div>;
}
