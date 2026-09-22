from dataclasses import dataclass

@dataclass
class AudioActivity:
    event_type: str
    payload: dict
    model_version: str

class WebRTCVADAdapter:
    name='webrtc-vad'; version='webrtcvad-2.0.14'; sample_rates={8000,16000,32000,48000}; frame_ms={10,20,30}
    def __init__(self, aggressiveness:int=2):
        try: import webrtcvad
        except ImportError as exc: raise RuntimeError('Install webrtcvad-wheels to enable CPU audio activity detection') from exc
        self.vad=webrtcvad.Vad(aggressiveness)
    def infer(self, pcm_mono_s16le:bytes, sample_rate:int, frame_duration_ms:int=30)->AudioActivity:
        if sample_rate not in self.sample_rates or frame_duration_ms not in self.frame_ms: raise ValueError('WebRTC VAD requires 8/16/32/48kHz and 10/20/30ms frames')
        bytes_per_frame=int(sample_rate*frame_duration_ms/1000)*2; frames=[pcm_mono_s16le[i:i+bytes_per_frame] for i in range(0,len(pcm_mono_s16le)-bytes_per_frame+1,bytes_per_frame)]
        voiced=sum(self.vad.is_speech(frame,sample_rate) for frame in frames); ratio=voiced/len(frames) if frames else 0.0
        return AudioActivity('AUDIO_ACTIVITY',{'input_schema':'mono signed PCM16','sample_rate':sample_rate,'frame_duration_ms':frame_duration_ms,'frames':len(frames),'voiced_frames':voiced,'voiced_ratio':round(ratio,4),'speech_present':ratio>0.1},self.version)
