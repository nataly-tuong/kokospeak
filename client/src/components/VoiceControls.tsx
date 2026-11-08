import { useRef,useState } from 'react';
import { Download,Plus,RotateCcw,SlidersHorizontal,Upload,X } from 'lucide-react';
import { languages,voices } from '../data/voices';
import { defaultSettings,presets } from '../data/presets';
import type { LanguageCode,VoiceSettings } from '../types/studio';

interface Props {settings:VoiceSettings;onChange:(settings:VoiceSettings)=>void;onLanguage:(language:LanguageCode)=>void;ffmpeg:boolean;onSave:()=>void;onImport:(file:File)=>void}
function Slider({id,label,value,min,max,step=1,unit='',onChange}:{id:string;label:string;value:number;min:number;max:number;step?:number;unit?:string;onChange:(v:number)=>void}){
  return <div className="slider-field"><div className="flex justify-between gap-3"><label htmlFor={id}>{label}</label><output htmlFor={id}>{step<1?value.toFixed(2):value}{unit}</output></div><input id={id} type="range" min={min} max={max} step={step} value={value} onChange={e=>onChange(Number(e.target.value))}/><div className="range-labels"><span>{min}{unit}</span><span>{max}{unit}</span></div></div>;
}
export default function VoiceControls({settings,onChange,onLanguage,ffmpeg,onSave,onImport}:Props){
  const [tab,setTab]=useState('voice');
  const recipe=useRef<HTMLInputElement>(null);
  const available=Object.keys(voices[settings.language]);
  const total=settings.blend.reduce((sum,item)=>sum+item.weight,0);
  function set<K extends keyof VoiceSettings>(key:K,value:VoiceSettings[K]){onChange({...settings,[key]:value});}
  return <section className="panel settings-panel" aria-labelledby="voice-heading">
    <div className="panel-heading"><h2 id="voice-heading"><SlidersHorizontal size={16}/>Shape the voice</h2><span className="eyebrow">02 / TUNE</span></div>
    <div className="settings-body">
      <div className="preset-row" aria-label="Voice effect presets">{presets.map(preset=><button key={preset.name} className="preset-chip" title={preset.description} onClick={()=>onChange({...structuredClone(defaultSettings),language:settings.language,voice:settings.voice,blend:settings.blend,...preset.values})}>{preset.name}</button>)}</div>
      <div className="settings-tabs" role="group" aria-label="Voice settings categories">{['voice','delivery','finish'].map(name=><button key={name} aria-pressed={tab===name} onClick={()=>setTab(name)}>{name}</button>)}</div>
      {tab==='voice'&&<div>
        <div className="select-grid">
          <label className="field" htmlFor="language"><span>Language</span><select id="language" value={settings.language} onChange={e=>onLanguage(e.target.value as LanguageCode)}>{Object.entries(languages).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></label>
          <label className="field" htmlFor="voice"><span>Base voice</span><select id="voice" value={settings.voice} onChange={e=>set('voice',e.target.value)}>{Object.entries(voices[settings.language]).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select></label>
        </div>
        <label className="toggle-row"><span><strong>Voice mixer</strong><small>Blend up to three voices from this language.</small></span><input type="checkbox" checked={settings.blend.length>0} disabled={available.length<2} onChange={e=>set('blend',e.target.checked?[{voice:settings.voice,weight:50},{voice:available.find(v=>v!==settings.voice)!,weight:50}]:[])}/></label>
        {settings.blend.length>0&&<div className="blend-panel">{settings.blend.map((item,index)=><div key={index} className="blend-slot">
          <label htmlFor={`blend-${index}`} className="sr-only">Blend voice {index+1}</label><select id={`blend-${index}`} value={item.voice} onChange={e=>set('blend',settings.blend.map((v,i)=>i===index?{...v,voice:e.target.value}:v))}>{Object.entries(voices[settings.language]).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select>
          <button className="icon-button" aria-label={`Remove blend voice ${index+1}`} onClick={()=>set('blend',settings.blend.filter((_,i)=>i!==index))}><X size={14}/></button>
          <label htmlFor={`weight-${index}`}>Weight <span>{total?Math.round(item.weight/total*100):0}%</span></label><input id={`weight-${index}`} aria-label={`Weight for blend voice ${index+1}`} type="range" min={0} max={100} value={item.weight} onChange={e=>set('blend',settings.blend.map((v,i)=>i===index?{...v,weight:Number(e.target.value)}:v))}/>
        </div>)}{settings.blend.length<3&&<button className="text-button" onClick={()=>set('blend',[...settings.blend,{voice:available.find(v=>!settings.blend.some(x=>x.voice===v))??available[0]!,weight:25}])}><Plus size={12}/>Add voice</button>}<p className="panel-note">Weights are normalized before mixing the voice embeddings. {total===0?'Increase at least one weight before generating.':''}</p></div>}
        <p className="panel-note">Base voice ID: <code>{settings.voice}</code>. Use this ID in script commands. Try a short script before a longer document.</p>
      </div>}
      {tab==='delivery'&&<div>
        <Slider id="speed" label="Speaking speed" value={settings.speed} min={0.5} max={2} step={0.01} unit="×" onChange={v=>set('speed',v)}/>
        <Slider id="pitch" label="Pitch · preserve speaking pace" value={settings.pitch} min={-12} max={12} step={0.5} unit=" st" onChange={v=>set('pitch',v)}/>
        <Slider id="sentencePause" label="Extra space between segments" value={settings.sentencePause} min={0} max={3} step={0.05} unit=" s" onChange={v=>set('sentencePause',v)}/>
        <Slider id="paragraphPause" label="Extra space between paragraphs" value={settings.paragraphPause} min={0} max={5} step={0.05} unit=" s" onChange={v=>set('paragraphPause',v)}/>
        <p className="panel-note">Pitch is measured in semitones. Pauses are added after generated speech; natural pauses may remain.</p>
      </div>}
      {tab==='finish'&&<div>
        <div className="select-grid"><label className="field" htmlFor="effect"><span>Space & texture</span><select id="effect" value={settings.effect} onChange={e=>set('effect',e.target.value as VoiceSettings['effect'])}><option value="clean">Clean studio</option><option value="room">Small room echo</option><option value="radio">Radio bandpass</option></select></label><label className="field" htmlFor="gain"><span>Output gain · dB</span><input id="gain" type="number" min={-12} max={12} step={1} value={settings.gain} onChange={e=>set('gain',Math.max(-12,Math.min(12,Number(e.target.value))))}/></label></div>
        <Slider id="bass" label="Bass · low-frequency warmth" value={settings.bass} min={-10} max={10} unit=" dB" onChange={v=>set('bass',v)}/>
        <Slider id="treble" label="Treble · high-frequency presence" value={settings.treble} min={-10} max={10} unit=" dB" onChange={v=>set('treble',v)}/>
        <div className="select-grid mt-5">{(['fadeIn','fadeOut'] as const).map(key=><label className="field" key={key} htmlFor={key}><span>{key==='fadeIn'?'Fade in':'Fade out'} · ms</span><input id={key} type="number" min={0} max={2000} step={10} value={settings[key]} onChange={e=>set(key,Math.round(Math.max(0,Math.min(2000,Number(e.target.value)))))}/></label>)}</div>
        <label className="toggle-row"><span>Trim segment edge silence</span><input type="checkbox" checked={settings.trimSilence} onChange={e=>set('trimSilence',e.target.checked)}/></label>
        <label className="toggle-row"><span>Normalize peak to −1 dB before gain</span><input type="checkbox" checked={settings.normalize} onChange={e=>set('normalize',e.target.checked)}/></label>
      </div>}
      {!ffmpeg&&<p className="capability-note">ffmpeg is unavailable. Install it for pitch, EQ, room/radio effects, and MP3.</p>}
      <div className="recipe-actions"><button className="text-button" onClick={onSave}><Download size={12}/>Save recipe</button><button className="text-button" onClick={()=>recipe.current?.click()}><Upload size={12}/>Load recipe</button><button className="text-button" onClick={()=>onChange(structuredClone(defaultSettings))}><RotateCcw size={12}/>Reset</button></div>
      <input ref={recipe} className="hidden" type="file" accept=".json,application/json" aria-label="Import voice recipe" onChange={e=>{const file=e.target.files?.[0];e.target.value='';if(file)onImport(file);}}/>
    </div>
  </section>;
}
