"""Executable checkpointed batch worker boundary."""
import argparse, json, os, time
from pathlib import Path
from services.api.storage import Store

def process_segments(session_id: str, segments: list[str], checkpoint_file: str, store=None):
    checkpoint=Path(checkpoint_file); completed=set(json.loads(checkpoint.read_text())) if checkpoint.exists() else set(); store=store or Store()
    for segment in segments:
        if segment in completed: continue
        path=Path(segment)
        event={'event_id':f'batch:{session_id}:{path.name}','session_id':session_id,'ts_ms':int(path.stat().st_mtime*1000) if path.exists() else 0,'channel':'batch','detector':'batch-boundary','model_version':'unknown-1','event_type':'BATCH_UNKNOWN','payload':{'segment':str(path),'reason':'decoder/model adapter must be configured'},'quality':{'usable':False},'demo':False}
        # Keep the event contract explicit; store persistence is real even when inference is unavailable.
        store.add_event(event); completed.add(segment); checkpoint.write_text(json.dumps(sorted(completed)))
    return {'session_id':session_id,'completed':sorted(completed),'resumable':True}

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--session',required=False,default='batch-session'); parser.add_argument('--once',action='store_true'); args=parser.parse_args()
    media=Path(os.getenv('PROCTORSTREAM_STORAGE_DIR','./data/media')); segments=[str(p) for p in media.glob('*') if p.is_file()]; result=process_segments(args.session,segments,str(media/f'.{args.session}.checkpoint.json'))
    print(result)
    if not args.once:
        while True: time.sleep(60)
if __name__=='__main__': main()
