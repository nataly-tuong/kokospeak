import { useEffect,useRef,useState } from 'react';
import { voices } from '../data/voices';
import { defaultSettings } from '../data/presets';
import { cancelJob,exportSpeech,getHealth,getJob,saveBlob,startJob,validateSettings } from '../lib/engine';
import type { AudioFormat,BatchScript,GeneratedAudio,Job,LanguageCode,Take,VoiceSettings } from '../types/studio';

export function useStudio() {
  const [text,setText]=useState('');
  const [settings,setSettings]=useState<VoiceSettings>(structuredClone(defaultSettings));
  const [filename,setFilename]=useState('koko');
  const [format,setFormat]=useState<AudioFormat>('wav');
  const [status,setStatus]=useState('Ready to write');
  const [connected,setConnected]=useState(false);
  const [ffmpeg,setFfmpeg]=useState(false);
  const [version,setVersion]=useState('');
  const [busy,setBusy]=useState(false);
  const [exporting,setExporting]=useState(false);
  const [audio,setAudio]=useState<GeneratedAudio|null>(null);
  const [job,setJob]=useState<Job|null>(null);
  const [takes,setTakes]=useState<Take[]>([]);
  const [batch,setBatch]=useState<BatchScript[]>([]);
  const [batchPosition,setBatchPosition]=useState('');
  const [stopping,setStopping]=useState(false);
  const pending=useRef<AbortController|null>(null);
  const currentJob=useRef<string|null>(null);
  const stop=useRef(false);
  const running=useRef(false);
  const mounted=useRef(true);
  const words=text.trim()?text.trim().split(/\s+/u).length:0;

  useEffect(()=>{
    mounted.current=true;
    let checking=false;
    const controller=new AbortController();
    async function check() {
      if(checking)return;checking=true;
      try {
        const health=await getHealth(AbortSignal.any([controller.signal,AbortSignal.timeout(4000)]));
        if(!controller.signal.aborted){setConnected(true);setVersion(health.kokoroVersion);setFfmpeg(health.ffmpegAvailable);}
      }catch{if(!controller.signal.aborted)setConnected(false);}
      finally{checking=false;}
    }
    void check();const interval=window.setInterval(()=>{void check();},5000);
    return ()=>{mounted.current=false;controller.abort();pending.current?.abort();window.clearInterval(interval);};
  },[]);

  function changeText(value:string){setText(value);setAudio(null);}
  function changeSettings(value:VoiceSettings){setSettings(value);setAudio(null);}
  function changeLanguage(language:LanguageCode){changeSettings({...settings,language,voice:Object.keys(voices[language])[0]!,blend:[]});}
  function clearText(){changeText('');setStatus('Text cleared');}
  function newScript(){clearText();setFilename('koko');setStatus('New script');}
  async function poll(initial:Job,signal:AbortSignal){
    let latest=initial;currentJob.current=initial.id;
    while(latest.state==='queued'||latest.state==='running'){
      if(stop.current)await cancelJob(latest.id);
      setJob(latest);setStatus(latest.stage);
      await new Promise<void>((resolve,reject)=>{
        const abort=()=>{window.clearTimeout(timer);signal.removeEventListener('abort',abort);reject(new DOMException('Aborted','AbortError'));};
        const timer=window.setTimeout(()=>{signal.removeEventListener('abort',abort);resolve();},450);
        signal.addEventListener('abort',abort,{once:true});
        if(signal.aborted)abort();
      });
      latest=await getJob(latest.id,signal);
    }
    setJob(latest);currentJob.current=null;
    if(latest.state==='error')throw new Error(latest.error||'Generation failed.');
    if(latest.state==='cancelled')return null;
    if(!latest.result)throw new Error('The server returned no audio.');
    return latest.result;
  }
  async function generate(items?:BatchScript[]){
    if(running.current||!connected)return;
    const inputs=items??[{name:filename||'Untitled take',text}];
    if(!inputs.length||inputs.some(item=>!item.text.trim())){setStatus('Add some spoken text first.');return;}
    running.current=true;stop.current=false;setStopping(false);setBusy(true);setAudio(null);setJob(null);
    const controller=new AbortController();pending.current=controller;
    const recipe=structuredClone(settings);
    let completed=0;
    try{
      for(let index=0;index<inputs.length;index++){
        if(stop.current)break;
        const item=inputs[index]!;
        setBatchPosition(inputs.length>1?`File ${index+1} of ${inputs.length} · ${item.name}`:'');
        const initial=await startJob({...recipe,text:item.text,label:item.name.slice(0,120)},controller.signal);
        const result=await poll(initial,controller.signal);
        if(!result)break;
        completed++;
        setAudio(result);setFilename(item.name.replace(/\.(txt|md)$/i,''));
        setTakes(current=>[{audio:result,text:item.text,settings:structuredClone(recipe)},...current].slice(0,12));
      }
      setStatus(stop.current?`Stopped. ${completed} completed take(s) kept.`:`${completed} take(s) ready.`);
    }catch(error){if(!controller.signal.aborted)setStatus(error instanceof Error?error.message:'Generation failed.');}
    finally{running.current=false;currentJob.current=null;if(mounted.current){setBusy(false);setStopping(false);setBatchPosition('');}}
  }
  async function cancel(){
    stop.current=true;setStopping(true);
    try{if(currentJob.current)await cancelJob(currentJob.current);}
    catch(error){setStatus(error instanceof Error?error.message:'Could not cancel.');setStopping(false);}
  }
  async function exportAudio(){
    if(!audio||exporting)return;setExporting(true);setStatus('Preparing audio download…');
    try{await exportSpeech(audio.id,filename,format);setStatus('Audio download started');}
    catch(error){setStatus(error instanceof Error?error.message:'Export failed.');}
    finally{setExporting(false);}
  }
  function selectTake(take:Take){setAudio(take.audio);setFilename(take.audio.label.replace(/\.(txt|md)$/i,''));setStatus('Selected saved take. Restore its script to edit or regenerate.');}
  function restoreTake(take:Take){setText(take.text);setSettings(structuredClone(take.settings));selectTake(take);}
  function saveRecipe(){saveBlob(new Blob([JSON.stringify({version:1,settings},null,2)],{type:'application/json'}),'kokospeak-voice-recipe.json');setStatus('Voice recipe downloaded');}
  async function importRecipe(file:File){
    try{
      if(file.size>100000)throw new Error('Choose a recipe smaller than 100 KB.');
      const recipe=JSON.parse(await file.text()) as {version?:number;settings?:unknown};
      if(recipe.version!==1)throw new Error('Unsupported recipe version.');
      changeSettings(await validateSettings(recipe.settings));setStatus('Voice recipe loaded');
    }catch(error){setStatus(error instanceof Error?error.message:'Could not import recipe.');}
  }
  async function loadBatch(files:FileList|null){
    if(!files)return;
    try{
      if(files.length>8)throw new Error('Choose up to eight text files per batch.');
      const items=await Promise.all(Array.from(files).map(async file=>{
        if(file.size>400000)throw new Error(`${file.name} is too large.`);
        const value=await file.text();
        if(!value.trim()||value.length>100000)throw new Error(`${file.name} must contain 1–100,000 characters.`);
        return {name:file.name,text:value};
      }));
      setBatch(items);setStatus(`${items.length} file(s) ready for the batch queue.`);
    }catch(error){setStatus(error instanceof Error?error.message:'Could not load files.');}
  }
  return {text,setText:changeText,settings,setSettings:changeSettings,filename,setFilename,format,setFormat,
    status,setStatus,words,changeLanguage,clearText,newScript,connected,ffmpeg,version,busy,audio,
    generate,exporting,exportAudio,job,cancel,stopping,takes,selectTake,restoreTake,saveRecipe,importRecipe,batch,loadBatch,batchPosition};
}
