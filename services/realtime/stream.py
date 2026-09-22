import json, os, time

class RedisStreamBus:
    def __init__(self,url=None,stream='proctorstream.events',group='realtime',consumer=None,max_retries=3):
        try:
            import redis
        except ImportError as exc: raise RuntimeError('Install redis to enable Redis Streams') from exc
        self.redis=redis.Redis.from_url(url or os.getenv('REDIS_URL','redis://localhost:6379/0'),decode_responses=True); self.stream=stream; self.group=group; self.consumer=consumer or f'consumer-{os.getpid()}'; self.max_retries=max_retries
    def ensure_group(self):
        try: self.redis.xgroup_create(self.stream,self.group,id='0-0',mkstream=True)
        except Exception as exc:
            if 'BUSYGROUP' not in str(exc): raise
    def publish(self,event): return self.redis.xadd(self.stream,{'event':json.dumps(event)},maxlen=100000,approximate=True)
    def read(self,count=10,block_ms=1000):
        self.ensure_group(); rows=self.redis.xreadgroup(self.group,self.consumer,{self.stream:'>'},count=count,block=block_ms)
        return [(msg_id,json.loads(fields['event'])) for _,messages in rows for msg_id,fields in messages]
    def ack(self,msg_id): return self.redis.xack(self.stream,self.group,msg_id)
    def retry_or_dead_letter(self,msg_id,event):
        key=f'{self.stream}:retries:{msg_id}'; attempts=int(self.redis.incr(key)); self.redis.expire(key,86400)
        if attempts>self.max_retries:
            self.redis.xadd(f'{self.stream}:dead-letter',{'event':json.dumps(event),'source_id':msg_id,'attempts':attempts}); self.ack(msg_id); return 'dead-letter'
        return 'retry'
    def recover_pending(self,idle_ms=60000,count=100):
        self.ensure_group(); pending=self.redis.xpending_range(self.stream,self.group,'-','+',count)
        return [p['message_id'] for p in pending if p['time_since_delivered']>=idle_ms]
    def claim_pending(self,idle_ms=60000,count=100):
        ids=self.recover_pending(idle_ms,count)
        if not ids: return []
        rows=self.redis.xclaim(self.stream,self.group,self.consumer,min_idle_time=idle_ms,message_ids=ids)
        return [(msg_id,json.loads(fields['event'])) for msg_id,fields in rows]
