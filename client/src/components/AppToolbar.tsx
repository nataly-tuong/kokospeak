import { useRef } from 'react';
import { AudioLines, FilePlus2, FolderOpen, Download, Maximize2, CircleHelp, Power } from 'lucide-react';
import { downloadText } from '../lib/files';

interface Props {
  text: string;
  connected: boolean;
  busy: boolean;
  onNew: () => void;
  onImport: (text: string) => void;
  onAbout: () => void;
  onStatus: (status: string) => void;
  onQuit?: () => void;
}

export default function AppToolbar({ text, connected, busy, onNew, onImport, onAbout, onStatus, onQuit }: Props) {
  const input = useRef<HTMLInputElement>(null);
  async function fullscreen() {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await document.documentElement.requestFullscreen();
    } catch { onStatus('Fullscreen is unavailable in this window.'); }
  }
  return (
    <header className="app-toolbar" aria-label="Workspace toolbar">
      <a className="brand" href="#main" aria-label="KokoSpeak workspace"><AudioLines size={25} strokeWidth={1.4} aria-hidden="true" /><span>KokoSpeak<span className="brand-detail"> / Studio</span></span></a>
      <span className="toolbar-divider" />
      <div className="flex items-center gap-1" role="group" aria-label="Script tools">
        <button className="toolbar-button" onClick={onNew} disabled={busy} title="New script"><FilePlus2 size={16} /><span>New</span></button>
        <button className="toolbar-button" onClick={() => input.current?.click()} disabled={busy} title="Open a text file"><FolderOpen size={16} /><span>Open text</span></button>
        <button className="toolbar-button" disabled={!text.trim()} onClick={() => { downloadText(text); onStatus('Script downloaded'); }} title="Download script"><Download size={16} /><span>Save text</span></button>
      </div>
      <input ref={input} type="file" accept=".txt,.md,text/plain,text/markdown" className="hidden" aria-label="Import text file" onChange={async event => {
        const file = event.currentTarget.files?.[0];
        event.currentTarget.value = '';
        if (!file) return;
        if (file.size > 2 * 1024 * 1024) { onStatus('Choose a text file smaller than 2 MB.'); return; }
        try { const value=await file.text(); if(value.length>100000){onStatus('Choose a script with at most 100,000 characters.');return;} onImport(value); onStatus(`Opened ${file.name}`); }
        catch { onStatus('Could not read that text file.'); }
      }} />
      <div className="ml-auto flex items-center gap-2">
        <span className="engine-label"><span className="status-dot" />{connected ? 'Local engine connected' : 'Start the Python server'}</span>
        <button className="icon-button" onClick={fullscreen} title="Toggle fullscreen" aria-label="Toggle fullscreen"><Maximize2 size={16} /></button>
        {onQuit&&<button className="icon-button" onClick={onQuit} disabled={busy} title="Quit KokoSpeak" aria-label="Quit KokoSpeak"><Power size={16}/></button>}
        <button className="icon-button" onClick={onAbout} title="About KokoSpeak" aria-label="About KokoSpeak"><CircleHelp size={17} /></button>
      </div>
    </header>
  );
}
