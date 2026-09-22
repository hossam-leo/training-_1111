from services.api.risk import RiskEngine
def test_missing_channel_never_increases_risk():
    e=[{'session_id':'s','ts_ms':1,'channel':'audio','event_type':'SECOND_VOICE','quality':{'usable':True}}]
    r=RiskEngine().score(e,missing_channels=['audio'])
    assert r['risk_level']=='NORMAL' and r['flags']==[]
def test_multi_face_is_flagged():
    e=[{'session_id':'s','ts_ms':1,'channel':'video','event_id':'x','event_type':'MULTI_FACE','confidence':.9,'quality':{'usable':True}}]
    r=RiskEngine().score(e)
    assert r['risk_level']=='ELEVATED' and r['flags'][0]['rule_id']=='R-MULTI-FACE'
