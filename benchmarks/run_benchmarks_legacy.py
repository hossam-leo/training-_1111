import csv,json,time,statistics,sys
sys.path.insert(0,'.')
from services.api.risk import RiskEngine
e=[{'session_id':'bench','ts_ms':i,'channel':'video','event_type':'FACE_PRESENT','quality':{'usable':True}} for i in range(100)]
r=RiskEngine(); samples=[]
for _ in range(100):
 t=time.perf_counter(); r.score(e); samples.append((time.perf_counter()-t)*1000)
out={'count':len(samples),'mean_ms':statistics.mean(samples),'p50_ms':sorted(samples)[49],'p95_ms':sorted(samples)[94],'p99_ms':sorted(samples)[98],'environment':'local CPU'}
open('benchmarks/results.json','w').write(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))
