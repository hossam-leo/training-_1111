import sys
sys.path.insert(0,'.')
from services.api.main import store,risk
from services.api.reports import generate
sid='sess_demo_001'; s=store.get_session(sid)
if not s: exec(open('scripts/seed_demo.py').read(),globals()) ; s=store.get_session(sid)
e=store.events(sid); result=risk.score(e,missing_channels=['audio']); store.update_status(sid,'COMPLETED',result); s=store.get_session(sid); p=generate(s,e,result,store.report_dir/f'{sid}.html'); print('demo complete:',p); print('risk:',result['risk_level'],result['recommendation'])
