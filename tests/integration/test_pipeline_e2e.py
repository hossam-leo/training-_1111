import json, os, time, uuid, pytest

@pytest.mark.skipif(not (os.getenv('PROCTORSTREAM_TEST_REDIS_URL') and os.getenv('PROCTORSTREAM_TEST_POSTGRES_URL')), reason='live Redis and PostgreSQL URLs not configured')
def test_candidate_api_redis_worker_postgres_reviewer_report(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    import services.api.main as api
    from services.api.storage import PostgresStore
    from services.realtime.stream import RedisStreamBus
    sid=f'e2e-{uuid.uuid4().hex[:10]}'; stream=f'e2e.events.{uuid.uuid4().hex[:8]}'; group=f'e2e-group-{uuid.uuid4().hex[:8]}'
    store=PostgresStore(db_url=os.environ['PROCTORSTREAM_TEST_POSTGRES_URL'],report_dir=tmp_path)
    bus=RedisStreamBus(url=os.environ['PROCTORSTREAM_TEST_REDIS_URL'],stream=stream,group=group,consumer='ci-consumer')
    old_store,old_bus=api.store,api.event_bus; api.store,api.event_bus=store,bus
    evidence={'session_id':sid,'event_id':f'event-{uuid.uuid4().hex}','stages':{}}
    try:
        client=TestClient(api.app)
        created=client.post('/api/sessions',json={'candidate_id':'candidate-e2e','consent':True}); assert created.status_code==200
        evidence['stages']['candidate_to_api']={'http_status':created.status_code,'session_id':sid}
        # Use the API-created ID so the evidence reflects the actual candidate request.
        sid=created.json()['id']; evidence['session_id']=sid
        event={'schema':'event.v1','session_id':sid,'ts_ms':int(time.time()*1000),'channel':'video','detector':'integration-fixture','model_version':'fixture-v1','event_type':'MULTI_FACE','payload':{'face_count':2},'quality':{'usable':True},'event_id':evidence['event_id']}
        accepted=client.post(f'/api/sessions/{sid}/events',json=event); assert accepted.status_code==200 and accepted.json()['accepted'] is True
        duplicate=client.post(f'/api/sessions/{sid}/events',json=event); assert duplicate.status_code==200 and duplicate.json()['deduplicated'] is True
        evidence['stages']['api_received_and_published']={'http_status':accepted.status_code,'redis_stream':stream,'event_id':event['event_id'],'duplicate_deduplicated':duplicate.json()['deduplicated']}
        from services.workers.realtime import handle_once
        processed=handle_once(bus,store,pending_idle_ms=0); assert processed==1
        pending=bus.redis.xpending(stream,group); assert pending['pending']==0
        evidence['stages']['worker_consumed_and_acked']={'processed':processed,'pending_after_ack':pending['pending'],'consumer':bus.consumer}
        stored_events=store.events(sid); assert any(e['event_id']==event['event_id'] for e in stored_events)
        stopped=client.post(f'/api/sessions/{sid}/stop'); assert stopped.status_code==200
        assert stopped.json()['session']['result']['risk_level']=='ELEVATED'
        evidence['stages']['risk_and_postgres']={'risk_level':stopped.json()['session']['result']['risk_level'],'postgres_event_count':len(stored_events)}
        reviewed=client.get(f'/api/sessions/{sid}'); assert reviewed.status_code==200 and any(e['event_id']==event['event_id'] for e in reviewed.json()['events'])
        report=client.get(f'/api/sessions/{sid}/report'); assert report.status_code==200 and event['event_type'] in report.text and 'ELEVATED' in report.text
        evidence['stages']['reviewer_and_report']={'reviewer_event_visible':True,'report_contains_event':True,'report_contains_risk':True}
        evidence_path=tmp_path/'pipeline-evidence.json'
        if os.getenv('PROCTORSTREAM_EVIDENCE_DIR'):
            evidence_path=os.path.join(os.environ['PROCTORSTREAM_EVIDENCE_DIR'],f'pipeline-evidence-{sid}.json'); os.makedirs(os.path.dirname(evidence_path),exist_ok=True)
        from pathlib import Path
        Path(evidence_path).write_text(json.dumps(evidence,indent=2))
    finally: api.store,api.event_bus=old_store,old_bus

@pytest.mark.skipif(not os.getenv('PROCTORSTREAM_TEST_REDIS_URL'), reason='live Redis URL not configured')
def test_redis_pending_recovery_retry_and_dlq():
    from services.realtime.stream import RedisStreamBus
    stream=f'recovery.{uuid.uuid4().hex[:8]}'; group=f'recovery-group-{uuid.uuid4().hex[:8]}'
    bus=RedisStreamBus(url=os.environ['PROCTORSTREAM_TEST_REDIS_URL'],stream=stream,group=group,consumer='recovery-a',max_retries=1); bus.ensure_group(); bus.publish({'event_id':'recovery-event'})
    first=bus.read(); assert first; recovered=bus.claim_pending(idle_ms=0); assert recovered and recovered[0][1]['event_id']=='recovery-event'; assert bus.ack(recovered[0][0])==1
    msg=bus.publish({'event_id':'dlq-event'}); rows=bus.read(); assert rows
    assert bus.retry_or_dead_letter(rows[0][0],rows[0][1])=='retry'; assert bus.retry_or_dead_letter(rows[0][0],rows[0][1])=='dead-letter'
    dlq=bus.redis.xrange(f'{stream}:dead-letter'); assert any(json.loads(fields['event'])['event_id']=='dlq-event' for _,fields in dlq)
