from services.models import BaseAdapter
from services.workers.batch import process_segments

def test_unconfigured_model_is_explicitly_unknown():
    d=BaseAdapter().infer(None)
    assert d.event_type.endswith('UNKNOWN') and d.usable is False

def test_batch_checkpoint_resume(tmp_path):
    checkpoint=tmp_path/'checkpoint.json'
    first=process_segments('s',['a','b'],str(checkpoint))
    second=process_segments('s',['a','b','c'],str(checkpoint))
    assert first['completed']==['a','b']
    assert second['completed']==['a','b','c']
