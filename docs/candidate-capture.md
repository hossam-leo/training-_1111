# Candidate capture workflow

The React application now exposes two modes:

- Reviewer mode at `/`.
- Candidate mode at `/#capture`, also reachable from the reviewer console through **Open candidate capture**.

Candidate mode requests explicit consent before creating a session and requesting camera/microphone permissions. When capture starts, `MediaRecorder` emits five-second WebM segments to the API, the preview remains visible, and a persistent red recording indicator is displayed. Browser visibility, focus/blur, copy/paste, fullscreen, and media-device changes are sent as signed telemetry where the browser exposes those signals.

The client uses a low baseline sampling interval and switches to a burst interval in its adaptive-sampling demonstration. The current implementation is a browser plumbing path, not a measured edge face detector. CPU usage, bandwidth reduction, cross-browser compatibility, reconnect resilience, and HTTPS deployment must still be measured on target browsers and laptops.

Telemetry uses a per-session key returned by the consented development session endpoint. The browser signs `session_id|ts_ms|event_type|nonce` with WebCrypto HMAC-SHA256. The server rejects invalid signatures, timestamps older/newer than 30 seconds, and repeated nonces. Heartbeats are emitted every five seconds; a gap greater than 15 seconds emits `HEARTBEAT_MISSED`.

For production, the session key must be delivered through a protected authenticated channel and kept non-exportable. The current local development response exposes it to the candidate client by design.
