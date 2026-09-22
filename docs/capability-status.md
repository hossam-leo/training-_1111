# AI capability status

| Capability | Status | Evidence or blocker |
|---|---|---|
| Face presence | IMPLEMENTED | OpenCV Haar cascade adapter executes on CPU and emits `FACE_PRESENT`/`FACE_ABSENT`; API endpoint persists traceable events. |
| Face count | IMPLEMENTED | Same adapter emits `face_count` and bounding boxes; unit/API tests cover the output schema. |
| Basic face quality | IMPLEMENTED | Brightness and Laplacian sharpness metrics are emitted with `usable`; benchmark script measures inference latency. |
| Head pose | BLOCKED | No selected licensed model and no validation dataset. |
| Audio activity/VAD | IMPLEMENTED for activity-only scope | WebRTC VAD 2.0.14 CPU adapter and API endpoint emit voiced-frame ratio; unit/API tests cover schema and invalid formats. This is not speaker verification, transcription, or cheating intelligence. |
| Identity verification | BLOCKED | No identity model, enrollment protocol, biometric storage, or evaluation set. |
| Anti-spoofing | BLOCKED | No validated anti-spoof model or physical spoof protocol execution. |
| Gaze estimation | BLOCKED | No selected model or labeled dataset. |
| Prohibited-object detection | PARTIAL | Adapter boundary and event contract exist; no approved weights or measured detector evidence. |
| Speaker verification | BLOCKED | No selected model, consent protocol, or evaluation set. |
| Multi-person identity attribution | BLOCKED | Face count is not identity attribution. |
| Reliable cheating detection | STUB | Rule-based risk aggregation exists for mock events; it is not a validated cheating detector. |

No accuracy, precision, recall, F1, robustness, or generalization claims are made for the implemented face path. The OpenCV Haar cascade is suitable for an executable CPU demonstration, not SRS acceptance evidence.
