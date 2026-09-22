from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, Field, ConfigDict

class RiskLevel(str, Enum):
    NORMAL = "NORMAL"; WATCH = "WATCH"; ELEVATED = "ELEVATED"; HIGH = "HIGH"
class Recommendation(str, Enum):
    NO_ACTION = "NO_ACTION"; ROUTINE_REVIEW = "ROUTINE_REVIEW"; HUMAN_REVIEW = "HUMAN_REVIEW"; PRIORITY_REVIEW = "PRIORITY_REVIEW"
class Quality(BaseModel):
    frame_blur: float | None = None; frame_luma: float | None = None; usable: bool = True
class Event(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema: str = Field("event.v1", pattern=r"^event\.v1$")
    session_id: str; ts_ms: int; channel: str; detector: str; model_version: str
    event_type: str; payload: dict[str, Any] = Field(default_factory=dict); confidence: float | None = Field(None, ge=0, le=1)
    quality: Quality = Field(default_factory=Quality); latency_ms: float | None = Field(None, ge=0)
    event_id: str | None = None; demo: bool = False
class Telemetry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema: str = Field("telemetry.v1", pattern=r"^telemetry\.v1$")
    session_id: str; ts_ms: int; event_type: str; payload: dict[str, Any] = Field(default_factory=dict)
    nonce: str; signature: str
class Flag(BaseModel):
    flag_id: str; type: str; interval: dict[str, int]; confidence: float | None = None; rule_id: str
    triggering_events: list[str]; explanation: str; evidence_ref: str | None = None
class SessionResult(BaseModel):
    schema: str = "session_result.v1"; risk_level: RiskLevel; recommendation: Recommendation
    flags: list[Flag]; triggering_events: list[str]; rule_ids: list[str]; evidence_references: list[str]
    processing_metadata: dict[str, Any]; available_channels: list[str]; missing_channels: list[str]
class SessionCreate(BaseModel):
    candidate_id: str = "demo-candidate"; consent: bool = False
class Session(BaseModel):
    id: str; candidate_id: str; owner_id: str | None = None; status: str; created_at: datetime; ended_at: datetime | None = None
    consent: bool; result: SessionResult | None = None
