import { useRef,useState } from 'react';
import { ArrowUpRight,Eraser,Files,Play } from 'lucide-react';
import GenerationProgress from './GenerationProgress';
import type { BatchScript,Job } from '../types/studio';
interface Props {text:string;onChange:(text:string)=>void;onClear:()=>void;words:number;connected:boolean;busy:boolean;onGenerate:()=>void;job:Job|null;onCancel:()=>void;stopping:boolean;batch:BatchScript[];onBatch:(files:FileList|null)=>void;onRunBatch:()=>void;batchPosition:string;onExample:()=>void}
export default function TextEditor(p:Props){
  const batchInput=useRef<HTMLInputElement>(null);
  const [help,setHelp]=useState(false);
  return <section className="panel editor-panel" aria-labelledby="script-heading">
    <div className="panel-heading"><h2 id="script-heading">Your script</h2><span className="eyebrow">01 / COMPOSE</span></div>
    <div className="script-tools"><button className="text-button" disabled={p.busy} onClick={()=>setHelp(!help)} aria-expanded={help}>Script commands</button><button className="text-button" disabled={p.busy} onClick={p.onExample} title="Load an American English dialogue script">Load dialogue example</button></div>
    {help&&<div className="script-help">Put <code>[pause=1.2]</code> or <code>[voice=af_heart]</code> alone on a line. Choose voice IDs from the selected language. Plain text works too. <span>Subtitles follow measured segment durations.</span></div>}
    <label htmlFor="script" className="sr-only">Text to turn into speech</label>
    <textarea id="script" disabled={p.busy} maxLength={100000} value={p.text} onChange={e=>p.onChange(e.target.value)} placeholder={'Every voice starts with a few words.\n\nWrite, paste, or open your script…'} spellCheck onKeyDown={e=>{if((e.ctrlKey||e.metaKey)&&e.key==='Enter'&&p.connected&&!p.busy){e.preventDefault();p.onGenerate();}}} className="script-editor"/>
    <div className="editor-meta"><span>{p.words.toLocaleString()} {p.words===1?'word':'words'}</span><span>{p.text.length.toLocaleString()} / 100,000 characters</span></div>
    <div className="editor-progress"><GenerationProgress job={p.job} busy={p.busy} stopping={p.stopping} onCancel={p.onCancel} batchPosition={p.batchPosition}/></div>
    <div className="editor-actions"><button className="button button-primary flex-1" disabled={!p.connected||p.busy||!p.text.trim()} onClick={p.onGenerate}>{p.busy?'Generating…':'Generate speech'}<ArrowUpRight size={17}/></button><button className="button button-secondary" onClick={p.onClear} disabled={!p.text||p.busy}><Eraser size={15}/>Clear</button></div>
    <p className="panel-note">Generated on your computer. ⌘ / Ctrl + Enter to generate. First use may download model files.</p>
    <div className="batch-area"><div className="flex items-center justify-between gap-3"><span className="eyebrow">BATCH FILES / UP TO 8</span><button className="text-button" disabled={p.busy} onClick={()=>batchInput.current?.click()}><Files size={13}/>Choose files</button></div>
      <input ref={batchInput} type="file" accept=".txt,.md,text/plain,text/markdown" multiple className="hidden" aria-label="Choose batch text files" onChange={e=>{p.onBatch(e.target.files);e.target.value='';}}/>
      {p.batch.length?<><ul>{p.batch.map((file,index)=><li key={index}><span>{file.name}</span><small>{file.text.length.toLocaleString()} chars</small></li>)}</ul><button className="button button-secondary w-full mt-3" disabled={p.busy||!p.connected} onClick={p.onRunBatch}><Play size={13}/>Generate {p.batch.length} files with current settings</button></>:<p className="panel-note">Turn several .txt or .md files into separate takes. Files run one at a time.</p>}
    </div>
  </section>;
}
