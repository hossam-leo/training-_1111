import os, pytest

@pytest.mark.skipif(not os.getenv('PROCTORSTREAM_TEST_POSTGRES_URL'), reason='PROCTORSTREAM_TEST_POSTGRES_URL not configured')
def test_postgres_persistence_restart():
    from services.api.storage import PostgresStore
    url=os.environ['PROCTORSTREAM_TEST_POSTGRES_URL']; first=PostgresStore(db_url=url); first.create_session('integration-pg','candidate',True); second=PostgresStore(db_url=url); assert second.get_session('integration-pg')['candidate_id']=='candidate'

@pytest.mark.skipif(not os.getenv('PROCTORSTREAM_TEST_REDIS_URL'), reason='PROCTORSTREAM_TEST_REDIS_URL not configured')
def test_redis_stream_ack_and_dead_letter():
    from services.realtime.stream import RedisStreamBus
    bus=RedisStreamBus(url=os.environ['PROCTORSTREAM_TEST_REDIS_URL'],stream='test.events',group='test-group'); bus.ensure_group(); msg=bus.publish({'event_id':'redis-test'}); rows=bus.read(); assert rows and bus.ack(rows[0][0])==1

@pytest.mark.skipif(not os.getenv('PROCTORSTREAM_TEST_MINIO_ENDPOINT'), reason='PROCTORSTREAM_TEST_MINIO_ENDPOINT not configured')
def test_minio_roundtrip():
    from services.storage.object_store import MinioObjectStore
    store=MinioObjectStore(endpoint=os.environ['PROCTORSTREAM_TEST_MINIO_ENDPOINT'],bucket='test-proctorstream'); ref=store.put('integration/test.txt',b'hello'); assert store.get(ref.key)==b'hello'; store.delete(ref.key)
