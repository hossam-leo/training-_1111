import pytest
from pydantic import ValidationError
from services.api.models import Event
def test_event_contract():
    e=Event(session_id='s',ts_ms=0,channel='video',detector='x',model_version='v',event_type='FACE_PRESENT')
    assert e.schema=='event.v1'
def test_unknown_schema_rejected():
    with pytest.raises(ValidationError): Event(schema='event.v9',session_id='s',ts_ms=0,channel='x',detector='x',model_version='v',event_type='X')
