// Lifecycle controller: current scene owns voice, text and completion.
// The adapter must expose play/pause/stop, returning a completion Promise.
export class Mentor{
 constructor(adapter,{status=()=>{},subtitle=()=>{}}={}){this.adapter=adapter;this.status=status;this.subtitle=subtitle;this.enabled=true;this.scene=null;this.generation=0;this.phase='idle';this.starts=0;this.queue=[];this.current=null;}
 enter(scene){if(this.scene?.id===scene.id)return false;this.stop();this.scene=scene;this.current=scene;this.subtitle(scene.text);if(this.enabled)this.start(scene);return true;}
 start(item){const own=++this.generation;this.current=item;this.subtitle(item.text);this.phase='playing';this.starts++;this.status('讲解中');let task;try{task=this.adapter.play(item)}catch(e){task=Promise.reject(e)}Promise.resolve(task).then(()=>{if(own!==this.generation)return;this.phase='idle';this.status('讲解结束');if(this.queue.length)this.start(this.queue.shift());}).catch(()=>{if(own!==this.generation)return;this.phase='error';this.status('语音暂时无法播放，请重播；也可以先看字幕。');});}
 action(){return false;}// Same-scene controls never restart narration.
 event(item){if(!this.enabled||!this.scene)return;this.queue=[item];if(this.phase==='idle')this.start(this.queue.shift());}
 pause(){if(this.phase!=='playing')return;this.adapter.pause();this.phase='paused';this.status('讲解已暂停');}
 resume(){if(this.phase!=='paused')return;this.adapter.resume();this.phase='playing';this.status('讲解中');}
 replay(){if(!this.scene)return;this.stop();this.current=this.scene;this.subtitle(this.scene.text);if(this.enabled)this.start(this.scene);}
 setEnabled(v){this.enabled=v;if(!v){this.stop();this.status('教师声音已关');}else if(this.scene)this.replay();}
 stop(){++this.generation;this.adapter.stop();this.phase='idle';this.queue=[];}
 dispose(){this.stop();this.scene=null;this.current=null;}
}
export function htmlAudioAdapter(audio){let rejectPending=null;
 return{play(item){this.stop();return new Promise((resolve,reject)=>{rejectPending=reject;audio.src=item.audio;audio.onended=()=>{rejectPending=null;resolve()};audio.onerror=()=>{rejectPending=null;reject(Error('audio failed'))};audio.play().catch(reject);});},pause(){audio.pause()},resume(){audio.play().catch(()=>{audio.onerror?.()})},stop(){audio.pause();audio.onended=null;audio.onerror=null;if(rejectPending){let r=rejectPending;rejectPending=null;r(Error('superseded'));}audio.removeAttribute('src');audio.load();}};
}
