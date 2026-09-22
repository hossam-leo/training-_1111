import json, statistics, time, platform
from pathlib import Path
from services.models import WebRTCVADAdapter

def main():
    adapter=WebRTCVADAdapter(); pcm=b'\0'*(16000*2)
    for _ in range(20): adapter.infer(pcm,16000)
    values=[]
    for _ in range(100):
        start=time.perf_counter(); adapter.infer(pcm,16000); values.append((time.perf_counter()-start)*1000)
    ordered=sorted(values); result={'model':adapter.name,'version':adapter.version,'sample_rate':16000,'duration_seconds':1,'warmup':20,'iterations':100,'mean_ms':statistics.mean(values),'p50_ms':ordered[49],'p95_ms':ordered[94],'p99_ms':ordered[98],'throughput_realtime_factor':1000/statistics.mean(values),'python':platform.python_version()}
    Path('benchmarks/audio_results.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))
if __name__=='__main__': main()
