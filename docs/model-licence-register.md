# Model licence register

This register covers code integrations present in the repository. It does not certify third-party weights for commercial use.

| Adapter/model | Code source | Code licence | Weights | Commercial verdict | Status |
|---|---|---|---|---|---|
| OpenCV Haar cascade | OpenCV | Apache-2.0 | Bundled with OpenCV package; verify package distribution terms | Must be verified for the exact distribution | Optional adapter only |
| ONNX Runtime adapter | Microsoft ONNX Runtime | MIT | Caller-supplied model; license not known by adapter | Cannot determine without model metadata | Integration boundary |
| CPU heuristic demo detector | Repository code | Repository MIT | None | MIT repository code | Demo/plumbing only |

Do not add AGPL detector packages or research-only weights to a production image without recording the exact source, version, code license, weight license, commercial-use verdict, and alternative. The SRS hazards around AGPL detector packages and research-only pretrained weights remain open until exact assets are selected and reviewed.

| WebRTC VAD | WebRTC Voice Activity Detector via `webrtcvad-wheels` 2.0.14 | WebRTC BSD-style license; verify wheel provenance before redistribution | No learned weights; embedded signal-processing/VAD implementation | Suitable for activity detection only; not speaker verification or transcription | Executable CPU adapter |
