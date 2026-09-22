import json, os, time
from datasets.evaluate_detector import validate
from services.api.privacy import delete_expired_files

def test_manifest_validator():
    assert validate([{'image':'a.jpg','split':'train','labels':['phone']}])==[]
    assert validate([{'image':'a.jpg','split':'bad','labels':[]}])

def test_retention_deletes_old_files(tmp_path):
    old=tmp_path/'old.webm'; old.write_bytes(b'x'); old_time=time.time()-3*86400; os.utime(old,(old_time,old_time))
    fresh=tmp_path/'fresh.webm'; fresh.write_bytes(b'x')
    deleted=delete_expired_files(tmp_path,retention_days=1)
    assert str(old) in deleted and not old.exists() and fresh.exists()
