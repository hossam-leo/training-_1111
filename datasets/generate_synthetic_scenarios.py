import argparse, json, random
from pathlib import Path

SCENARIOS=['clean','phone_use','second_person','impersonation_attempt','tab_switching','note_reading','poor_environment']
LIGHTING=['daylight','low_light','backlit']; WEBCAM=['720p','low_quality']; NOISE=['quiet','household_noise']

def generate(count:int, seed:int):
    rng=random.Random(seed); rows=[]
    for i in range(count):
        rows.append({'session_id':f'synthetic_{i:04d}','synthetic':True,'scenario':rng.choice(SCENARIOS),'lighting':rng.choice(LIGHTING),'webcam_class':rng.choice(WEBCAM),'noise':rng.choice(NOISE),'script_label_source':'assigned_scenario_not_posthoc'})
    return rows

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--count',type=int,default=50); p.add_argument('--seed',type=int,default=20260921); p.add_argument('--out',default='datasets/sample/scenarios.json')
    args=p.parse_args(); out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(generate(args.count,args.seed),indent=2)); print(f'wrote {args.count} synthetic metadata rows to {out}; no media or accuracy claims created')
