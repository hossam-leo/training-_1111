import hashlib, uuid, yaml
from .models import RiskLevel, Recommendation

ORDER={RiskLevel.NORMAL:0,RiskLevel.WATCH:1,RiskLevel.ELEVATED:2,RiskLevel.HIGH:3}
REC={RiskLevel.NORMAL:Recommendation.NO_ACTION,RiskLevel.WATCH:Recommendation.ROUTINE_REVIEW,RiskLevel.ELEVATED:Recommendation.HUMAN_REVIEW,RiskLevel.HIGH:Recommendation.PRIORITY_REVIEW}
class RiskEngine:
    def __init__(self,path='configs/risk_rules.yaml'):
        with open(path) as f: self.rules=yaml.safe_load(f)['rules']
    def score(self, events, missing_channels=None):
        missing=set(missing_channels or []); flags=[]; highest=RiskLevel.NORMAL
        for e in events:
            if not e.get('quality',{}).get('usable',True): continue
            for r in self.rules:
                if r['event_type'] != e['event_type']: continue
                if e.get('channel') in missing: continue
                lvl=RiskLevel(r['severity']); highest=lvl if ORDER[lvl]>ORDER[highest] else highest
                eid=e.get('event_id') or f"{e['session_id']}:{e['ts_ms']}:{e['event_type']}"
                flags.append({'flag_id':str(uuid.uuid4()),'type':e['event_type'],'interval':{'start_ms':e['ts_ms'],'end_ms':e['ts_ms']},'confidence':e.get('confidence'),'rule_id':r['id'],'triggering_events':[eid],'explanation':r['explanation'],'evidence_ref':f"event:{eid}"})
        available=sorted({e.get('channel','unknown') for e in events if e.get('channel') not in missing})
        return {'schema':'session_result.v1','risk_level':highest.value,'recommendation':REC[highest].value,'flags':flags,'triggering_events':[x for f in flags for x in f['triggering_events']],'rule_ids':[f['rule_id'] for f in flags],'evidence_references':[f['evidence_ref'] for f in flags],'processing_metadata':{'engine':'rules-v1','event_count':len(events)},'available_channels':available,'missing_channels':sorted(missing)}
