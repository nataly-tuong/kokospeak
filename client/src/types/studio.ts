export type LanguageCode = 'a'|'b'|'j'|'z'|'f'|'h'|'i'|'e'|'p';
export type AudioFormat = 'wav'|'flac'|'ogg'|'mp3';
export interface BlendVoice { voice: string; weight: number }
export interface VoiceSettings {
  language: LanguageCode; voice: string; blend: BlendVoice[]; speed: number; pitch: number;
  sentencePause: number; paragraphPause: number; gain: number; bass: number; treble: number;
  effect: 'clean'|'room'|'radio'; trimSilence: boolean; normalize: boolean; fadeIn: number; fadeOut: number;
}
export interface GenerateRequest extends VoiceSettings { text: string; label: string }
export interface Cue { start: number; end: number; text: string; voice: string }
export interface GeneratedAudio { id: string; url: string; sampleRate: number; duration: number; waveform: number[]; cues: Cue[]; limitedSamples: number; label: string }
export interface Job {
  id: string; state: 'queued'|'running'|'complete'|'cancelled'|'error'; stage: string;
  completed: number; total: number; indeterminate: boolean; result: GeneratedAudio|null; error: string|null;
}
export interface Take { audio: GeneratedAudio; text: string; settings: VoiceSettings }
export interface BatchScript { name: string; text: string }
