import csv, json, platform, statistics, time
from pathlib import Path
import sys
sys.path.insert(0, '.')
from services.api.risk import RiskEngine

BATCH_SIZES=[1,2,4,8,16,32]
REPEATS=3
WARMUP=100
MEASURED=1000

def percentile(values, p):
    values=sorted(values); index=min(len(values)-1, max(0, int(round((p/100)*(len(values)-1))))); return values[index]

def run_once(batch_size):
    events=[{'session_id':'bench','ts_ms':i,'channel':'video','event_type':'FACE_PRESENT','quality':{'usable':True}} for i in range(batch_size)]
    engine=RiskEngine()
    for _ in range(WARMUP): engine.score(events)
    samples=[]
    for _ in range(MEASURED):
        start=time.perf_counter(); engine.score(events); samples.append((time.perf_counter()-start)*1000)
    return {'batch_size':batch_size,'repeat_samples':len(samples),'mean_ms':statistics.mean(samples),'stdev_ms':statistics.stdev(samples),'p50_ms':percentile(samples,50),'p95_ms':percentile(samples,95),'p99_ms':percentile(samples,99),'environment':'local CPU risk path'}

def main():
    rows=[]
    for batch in BATCH_SIZES:
        for repeat in range(1,REPEATS+1):
            row=run_once(batch); row['repeat']=repeat; rows.append(row)
    result={'protocol':{'warmup':WARMUP,'measured':MEASURED,'batch_sizes':BATCH_SIZES,'repeats':REPEATS},'environment':{'python':platform.python_version(),'platform':platform.platform()},'rows':rows,'claims':'These measurements cover only the deterministic local risk path; no model accuracy, GPU, Tier 1, Tier 2, or concurrency claim is made.'}
    out=Path('benchmarks'); out.mkdir(exist_ok=True); (out/'results.json').write_text(json.dumps(result,indent=2))
    with (out/'results.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0].keys())); writer.writeheader(); writer.writerows(rows)
    lines=['# Local benchmark report','',result['claims'],'', '| batch | repeat | mean ms | p50 ms | p95 ms | p99 ms |','|---:|---:|---:|---:|---:|---:|']
    lines += [f"| {r['batch_size']} | {r['repeat']} | {r['mean_ms']:.4f} | {r['p50_ms']:.4f} | {r['p95_ms']:.4f} | {r['p99_ms']:.4f} |" for r in rows]
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n'); print(json.dumps(result['protocol'],indent=2)); print('wrote benchmarks/results.json, results.csv, REPORT.md')
if __name__=='__main__': main()
