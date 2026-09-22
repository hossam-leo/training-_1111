import json, statistics, time, platform
from pathlib import Path
import numpy as np
from services.models import OpenCVHaarFaceAdapter

def percentile(values,p): return sorted(values)[min(len(values)-1,int((p/100)*(len(values)-1)))]
def measure(adapter,width,height):
    frame=np.zeros((height,width,3),dtype=np.uint8)
    for _ in range(20): adapter.infer(frame)
    samples=[]
    for _ in range(100):
        start=time.perf_counter(); adapter.infer(frame); samples.append((time.perf_counter()-start)*1000)
    return {'width':width,'height':height,'warmup':20,'iterations':100,'mean_ms':statistics.mean(samples),'p50_ms':percentile(samples,50),'p95_ms':percentile(samples,95),'p99_ms':percentile(samples,99),'throughput_fps':1000/statistics.mean(samples)}
def main():
    adapter=OpenCVHaarFaceAdapter(); rows=[measure(adapter,w,h) for w,h in [(320,240),(640,480),(1280,720)]]
    result={'model':adapter.name,'version':adapter.version,'input':'BGR uint8 black frames','sizes':rows,'python':platform.python_version(),'accuracy_claimed':False}
    Path('benchmarks/face_results.json').write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))
if __name__=='__main__': main()
