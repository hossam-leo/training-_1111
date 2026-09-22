# Manual real-device validation

These checks must be run on a machine with a physical webcam and microphone. They are not covered by the mocked Chromium suite.

1. Start the API and frontend with `uvicorn services.api.main:app --host 127.0.0.1 --port 8000` and `cd frontend && npm run dev -- --host 127.0.0.1 --port 4173`.
2. Open Chrome at `http://127.0.0.1:4173/#capture` and verify the consent checkbox is required before the start button enables.
3. Approve camera and microphone permissions. Verify the capture indicator appears, a session ID is shown, media segments are uploaded, and the signal log records heartbeat/copy/visibility events.
4. Deny camera permission, reload, and verify `Capture unavailable` appears without `RECORDING ACTIVE`.
5. During capture, disable the camera or microphone at the OS/browser level. Verify the client exits or reports capture failure without falsely showing an active recording.
6. Stop network access for one segment, restore it, and verify the upload/reconnect behavior. Record browser console errors and API response codes; this case is currently an unverified gap unless the upload retry implementation is observed.
7. Refresh during an active session. Verify the UI reports the interruption and does not create a second uncontrolled session.
8. Open the reviewer console, select the session, inspect the timeline, open the report, and record whether private media playback succeeds or displays the missing-evidence state.

Chrome is the only browser targeted by the automated suite. Firefox and Safari remain unverified. Record browser version, OS, camera/microphone model, permission result, session ID, and timestamps for every manual run.
