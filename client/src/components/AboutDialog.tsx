import { useEffect, useRef } from 'react';
import { AudioLines, X } from 'lucide-react';

export default function AboutDialog({ onClose }: { onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => { ref.current?.showModal(); }, []);
  return (
    <dialog ref={ref} onClose={onClose} className="about-dialog" aria-labelledby="about-title">
      <div className="flex items-center justify-between">
        <AudioLines size={24} strokeWidth={1.3} aria-hidden="true" />
        <button className="icon-button" onClick={() => ref.current?.close()} aria-label="Close about dialog"><X size={18} /></button>
      </div>
      <p className="eyebrow mt-8">LOCAL TEXT TO SPEECH</p>
      <h2 id="about-title" className="mt-3 text-3xl font-medium font-heading">KokoSpeak</h2>
      <p className="mt-4 text-sm leading-6 text-ash">A local studio for voice blending, dialogue scripts, batch generation, and audio finishing with the open-source Kokoro model.</p>
      <p className="mt-3 text-sm leading-6 text-ash">React provides the interface and a local Python API runs Kokoro. Your script and settings stay in memory and reset when you reload. Recent takes stay in this session; generated audio and caption metadata stay in the server’s generated folder. Model and voice files may download on first use.</p>
      <button className="button button-primary mt-8" onClick={() => ref.current?.close()}>Back to workspace</button>
    </dialog>
  );
}
