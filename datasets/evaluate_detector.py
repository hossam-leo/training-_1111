import argparse, json
from collections import Counter
from pathlib import Path

def validate(rows):
    required={'image','split','labels'}; errors=[]
    for i,row in enumerate(rows):
        missing=required-set(row)
        if missing: errors.append(f'row {i}: missing {sorted(missing)}')
        if row.get('split') not in {'train','val','test'}: errors.append(f'row {i}: invalid split')
    return errors

def report(rows):
    labels=Counter(label for row in rows for label in row.get('labels',[]))
    return {'images':len(rows),'classes':dict(labels),'synthetic_or_user_supplied':True,'accuracy_claimed':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('manifest'); p.add_argument('--out',default='datasets/evaluation_report.json'); args=p.parse_args()
    rows=json.loads(Path(args.manifest).read_text()); errors=validate(rows)
    result={'valid':not errors,'errors':errors,'report':report(rows) if not errors else None}; Path(args.out).write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))
