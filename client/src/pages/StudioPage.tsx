import { useState } from 'react';
import { AudioLines,ArrowDownRight } from 'lucide-react';
import AppToolbar from '../components/AppToolbar';
import TextEditor from '../components/TextEditor';
import VoiceControls from '../components/VoiceControls';
import AudioPreview from '../components/AudioPreview';
import TakeHistory from '../components/TakeHistory';
import AboutDialog from '../components/AboutDialog';
import { useStudio } from '../hooks/useStudio';
export default function StudioPage(){
  const studio=useStudio();
  const [about,setAbout]=useState(false);
  function example(){studio.changeLanguage('a');studio.setText('[voice=af_heart]\nEvery story begins with a voice.\n\n[pause=1.0]\n[voice=am_adam]\nAnd sometimes, a second perspective.');}
  return <div className="app-shell">
    <a href="#script" className="skip-link">Skip to script</a>
    <AppToolbar onQuit={studio.canQuit?()=>{void studio.quit();}:undefined} connected={studio.connected} busy={studio.busy} text={studio.text} onNew={studio.newScript} onImport={studio.setText} onStatus={studio.setStatus} onAbout={()=>setAbout(true)}/>
    <main id="main" className="workspace">
      <section className="workspace-heading" aria-labelledby="studio-title">
        <div className="spotlight-copy"><p className="eyebrow"><span className="studio-pill"><span className="status-dot"/>KOKOSPEAK STUDIO</span></p><h1 id="studio-title">A space for<br/><span>every voice.</span></h1><p className="workspace-description">Write something. Find its voice.<br/>Make it sound the way you imagined.</p></div>
        <div className="spotlight-aside"><div className="spotlight-signal" aria-hidden="true"><AudioLines size={54} strokeWidth={1}/></div><span className="spotlight-caption">YOUR WORDS. YOUR WORKSPACE.</span><div className="spotlight-facts"><span>09 languages</span><span>54 voices</span><span>Local synthesis</span></div><a className="spotlight-link" href="#script">Start with your script<ArrowDownRight size={16}/></a></div>
      </section>
      <div className="workspace-section-label"><span>THE WORKSPACE</span><span>Compose. Shape. Listen.</span></div>
      <div className="workspace-grid"><div className="compose-column">
        <TextEditor text={studio.text} onChange={studio.setText} onClear={studio.clearText} words={studio.words} connected={studio.connected} busy={studio.busy} onGenerate={()=>{void studio.generate();}} job={studio.job} onCancel={()=>{void studio.cancel();}} stopping={studio.stopping} batch={studio.batch} onBatch={files=>{void studio.loadBatch(files);}} onRunBatch={()=>{void studio.generate(studio.batch);}} batchPosition={studio.batchPosition} onExample={example}/>
        <TakeHistory takes={studio.takes} active={studio.audio?.id} busy={studio.busy} onSelect={studio.selectTake} onRestore={studio.restoreTake}/>
      </div><div className="output-column">
        <fieldset disabled={studio.busy} className="min-w-0 border-0 p-0 m-0"><VoiceControls settings={studio.settings} onChange={studio.setSettings} onLanguage={studio.changeLanguage} ffmpeg={studio.ffmpeg} onSave={studio.saveRecipe} onImport={file=>{void studio.importRecipe(file);}}/></fieldset>
        <AudioPreview audio={studio.audio} exporting={studio.exporting} connected={studio.connected} onExport={()=>{void studio.exportAudio();}} filename={studio.filename} onFilename={studio.setFilename} format={studio.format} onFormat={studio.setFormat}/>
      </div></div>
    </main>
    <footer className="status-bar"><span role="status" className="min-w-0 break-words">{studio.status}</span><span>LOCAL WORKSPACE<span className="footer-detail"> · {studio.connected?`Kokoro ${studio.version}`:'Engine offline'}</span></span></footer>
    {about&&<AboutDialog onClose={()=>setAbout(false)}/>}
  </div>;
}
