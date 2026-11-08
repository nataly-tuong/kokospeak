import type { VoiceSettings } from '../types/studio';
export const defaultSettings: VoiceSettings = {
  language:'a',voice:'af_heart',blend:[],speed:1,pitch:0,sentencePause:0.12,paragraphPause:0.45,
  gain:0,bass:0,treble:0,effect:'clean',trimSilence:true,normalize:true,fadeIn:10,fadeOut:50,
};
export const presets: {name:string; description:string; values:Partial<VoiceSettings>}[] = [
  {name:'Natural',description:'Clean voice, natural pacing',values:{}},
  {name:'Narration',description:'Slower pace, more space between ideas',values:{speed:0.9,sentencePause:0.24,paragraphPause:0.8,bass:2}},
  {name:'Bright',description:'Quicker pace with a treble lift',values:{speed:1.12,treble:3,sentencePause:0.08}},
  {name:'Broadcast',description:'Lower register and fuller low end',values:{pitch:-1,bass:3,treble:1,speed:0.98}},
  {name:'Soft room',description:'A small room echo with a relaxed pace',values:{speed:0.94,effect:'room',gain:-2}},
];
