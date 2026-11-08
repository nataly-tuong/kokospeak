import { useEffect,useRef,useState } from 'react';
import { AudioLines,Download,FileText } from 'lucide-react';
import type { AudioFormat,GeneratedAudio } from '../types/studio';
interface Props {filename:string;onFilename:(value:string)=>void;format:AudioFormat;onFormat:(format:AudioFormat)=>void;audio:GeneratedAudio|null;exporting:boolean;connected:boolean;onExport:()=>void}
export default function AudioPreview({filename,onFilename,format,onFormat,audio,exporting,connected,onExport}:Props){
  const player=useRef<HTMLAudioElement>(null);
  const [loop,setLoop]=useState(false);
  const [autoplay,setAutoplay]=useState(false);
  const [rate,setRate]=useState(1);
  useEffect(()=>{if(player.current)player.current.playbackRate=rate;},[rate,audio?.id]);
  return <section className="panel audio-panel" aria-labelledby="audio-heading">
    <div className="panel-heading"><h2 id="audio-heading"><AudioLines size={17}/>Listen & export</h2><span className="eyebrow">03 / OUTPUT</span></div>
    <div className="audio-body">
      {audio?<>
        <div className="take-title"><span>{audio.label}</span><small>{audio.duration.toFixed(1)} s · {audio.sampleRate.toLocaleString()} Hz</small></div>
        <svg className="waveform" viewBox="0 0 640 72" role="img" aria-label="Waveform peaks from the generated audio" preserveAspectRatio="none">{audio.waveform.map((peak,index)=><rect key={index} x={index*4} y={36-Math.max(1,peak*32)} width={2} height={Math.max(2,peak*64)} rx={1} className={index%7<3?'wave-primary':'wave-secondary'}/>)}</svg>
        <audio ref={player} key={audio.id} className="w-full" src={audio.url} controls preload="metadata" loop={loop} autoPlay={autoplay} aria-label="Generated speech"/>
        <div className="playback-options"><label><input type="checkbox" checked={loop} onChange={e=>setLoop(e.target.checked)}/>Loop</label><label><input type="checkbox" checked={autoplay} onChange={e=>setAutoplay(e.target.checked)}/>Autoplay next</label><label>Listen at <select aria-label="Preview playback speed" value={rate} onChange={e=>setRate(Number(e.target.value))}>{[0.75,1,1.25,1.5].map(v=><option key={v} value={v}>{v}×</option>)}</select></label></div>
        {audio.limitedSamples>0&&<p className="capability-note">Output reached the peak limit. Lower gain for more dynamic range.</p>}
        <details className="transcript"><summary>Timed transcript · {audio.cues.length} segments</summary><ol>{audio.cues.map((cue,index)=><li key={index}><button title="Seek to this segment" onClick={()=>{if(player.current)player.current.currentTime=cue.start;}}><time>{cue.start.toFixed(1)}s</time><span>{cue.text}</span></button></li>)}</ol></details>
      </>:<div className="audio-empty"><AudioLines size={36} strokeWidth={1}/><p>Your next voice is waiting</p><span>Generate a script, then listen and compare takes.</span></div>}
      <div className="export-fields mt-5"><label className="field min-w-0" htmlFor="filename"><span>Filename</span><input id="filename" maxLength={120} value={filename} onChange={e=>onFilename(e.target.value)} placeholder="koko"/></label><label className="field" htmlFor="format"><span>Format</span><select id="format" value={format} onChange={e=>onFormat(e.target.value as AudioFormat)}>{(['wav','flac','ogg','mp3'] as const).map(f=><option key={f} value={f}>{f.toUpperCase()}</option>)}</select></label></div>
      <button className="button button-primary w-full mt-4" disabled={!audio||exporting||!connected} onClick={onExport}><Download size={15}/>{exporting?'Preparing download…':'Export audio'}</button>
      {audio&&<div className="subtitle-links"><FileText size={12}/><span>Subtitles</span><a href={`/api/audio/${audio.id}/subtitles?format=srt`} download={`${filename||'koko'}.srt`}>SRT</a><a href={`/api/audio/${audio.id}/subtitles?format=vtt`} download={`${filename||'koko'}.vtt`}>VTT</a></div>}
      <p className="panel-note">{audio?'Captions use generated segment timing, rather than word-level alignment. Playback speed changes preview only.':'WAV / FLAC / OGG / MP3 · SRT / VTT captions'}</p>
    </div>
  </section>;
}
