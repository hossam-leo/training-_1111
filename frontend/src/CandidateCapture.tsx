import React, {useEffect, useRef, useState} from 'react';

type Props = { onBack: () => void };
const API = '';
const now = () => Date.now();
async function hmac(value: string, secret: string) {
  const cryptoKey = await crypto.subtle.importKey('raw', new TextEncoder().encode(secret), {name:'HMAC', hash:'SHA-256'}, false, ['sign']);
  const bytes = await crypto.subtle.sign('HMAC', cryptoKey, new TextEncoder().encode(value));
  return [...new Uint8Array(bytes)].map(b => b.toString(16).padStart(2, '0')).join('');
}

export default function CandidateCapture({onBack}: Props) {
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const timerRef = useRef<number | null>(null);
  const heartbeatRef = useRef<number | null>(null);
  const [sessionId, setSessionId] = useState('');
  const [key, setKey] = useState('');
  const sessionRef = useRef('');
  const keyRef = useRef('');
  const [consent, setConsent] = useState(false);
  const [recording, setRecording] = useState(false);
  const [status, setStatus] = useState('Awaiting consent');
  const [telemetry, setTelemetry] = useState<string[]>([]);
  const [error, setError] = useState('');
  const [sampleMs, setSampleMs] = useState(1000);

  const signAndSend = async (event_type: string, payload: Record<string, unknown> = {}) => {
    const activeSessionId=sessionRef.current; const activeKey=keyRef.current;
    if (!activeSessionId || !activeKey) return;
    const ts_ms = now(); const nonce = crypto.randomUUID();
    const signature = await hmac(`${activeSessionId}|${ts_ms}|${event_type}|${nonce}`, activeKey);
    // The development server accepts the session key as returned by the consented session API.
    // Production deployments should replace this with a non-exportable WebCrypto session key.
    const response = await fetch(`${API}/api/sessions/${activeSessionId}/telemetry`, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({schema:'telemetry.v1', session_id:activeSessionId, ts_ms, event_type, payload, nonce, signature})});
    if (!response.ok) { setStatus(`Telemetry rejected (${response.status})`); return; }
    setTelemetry(items => [`${event_type} · ${new Date(ts_ms).toLocaleTimeString()}`, ...items].slice(0, 8));
  };

  const createSession = async () => {
    if (!consent) return;
    const response = await fetch(`${API}/api/sessions`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({candidate_id:'browser-candidate', consent:true})});
    if (!response.ok) throw new Error('Session creation failed');
    const data = await response.json(); sessionRef.current=data.id; keyRef.current=data.telemetry_key; setSessionId(data.id); setKey(data.telemetry_key); await fetch(`${API}/api/sessions/${data.id}/start`, {method:'POST'}); setStatus('Session ready'); return data;
  };

  const start = async () => {
    setError('');
    try {
      const active=await createSession();
      const stream = await navigator.mediaDevices.getUserMedia({video:true, audio:true});
      streamRef.current = stream; if (videoRef.current) { videoRef.current.srcObject = stream; await videoRef.current.play(); }
      const mime = MediaRecorder.isTypeSupported('video/webm;codecs=vp8,opus') ? 'video/webm;codecs=vp8,opus' : 'video/webm';
      const recorder = new MediaRecorder(stream, {mimeType:mime}); recorderRef.current = recorder;
      recorder.ondataavailable = async (event) => { if (!event.data.size || !active?.id) return; const fd = new FormData(); fd.append('file', event.data, `segment-${now()}.webm`); await fetch(`${API}/api/sessions/${active.id}/media`, {method:'POST', body:fd}); };
      recorder.start(5000); setRecording(true); setStatus('Recording · indicator active');
      heartbeatRef.current = window.setInterval(() => void signAndSend('HEARTBEAT'), 5000);
      timerRef.current = window.setInterval(() => setSampleMs(value => value === 1000 ? 250 : 1000), 10000);
    } catch (err) { setError(err instanceof Error ? err.message : 'Camera or microphone permission failed'); setStatus('Capture unavailable'); }
  };
  const stop = async () => { if (heartbeatRef.current) clearInterval(heartbeatRef.current); if (timerRef.current) clearInterval(timerRef.current); recorderRef.current?.stop(); streamRef.current?.getTracks().forEach(t => t.stop()); setRecording(false); setStatus('Stopping…'); if (sessionRef.current) { await fetch(`${API}/api/sessions/${sessionRef.current}/stop`, {method:'POST'}); setStatus('Session completed'); } };

  useEffect(() => {
    const onVisibility = () => void signAndSend(document.hidden ? 'TAB_HIDDEN' : 'TAB_VISIBLE');
    const onBlur = () => void signAndSend('WINDOW_BLUR');
    const onFocus = () => void signAndSend('WINDOW_FOCUS');
    const onPaste = () => void signAndSend('PASTE');
    const onCopy = () => void signAndSend('COPY');
    const onFullscreen = () => void signAndSend(document.fullscreenElement ? 'TAB_VISIBLE' : 'FULLSCREEN_EXIT');
    const onDevice = () => void signAndSend('DEVICE_CHANGE');
    document.addEventListener('visibilitychange', onVisibility); window.addEventListener('blur', onBlur); window.addEventListener('focus', onFocus); document.addEventListener('paste', onPaste); document.addEventListener('copy', onCopy); document.addEventListener('fullscreenchange', onFullscreen); navigator.mediaDevices?.addEventListener('devicechange', onDevice);
    return () => { document.removeEventListener('visibilitychange', onVisibility); window.removeEventListener('blur', onBlur); window.removeEventListener('focus', onFocus); document.removeEventListener('paste', onPaste); document.removeEventListener('copy', onCopy); document.removeEventListener('fullscreenchange', onFullscreen); navigator.mediaDevices?.removeEventListener('devicechange', onDevice); };
  }, [sessionId, key]);

  return <div className="capture-shell"><div className="capture-card"><div className="capture-top"><span className="brand"><span className="dot"/>PROCTORSTREAM</span><button className="ghost" onClick={onBack}>Reviewer console</button></div><p className="eyebrow">CANDIDATE CAPTURE / CONSENTED MOCK EXAM</p><h1>Ready when you are.</h1><p className="muted">This local capture client requests camera and microphone permission, records visible short segments, and sends signed browser telemetry. It is for consented synthetic or mock sessions only.</p>{recording && <div className="record-indicator"><span/> RECORDING ACTIVE · CAMERA + MICROPHONE</div>}<video ref={videoRef} muted playsInline className="preview"/><div className="capture-controls"><label><input type="checkbox" checked={consent} onChange={e=>setConsent(e.target.checked)}/> I consent to this mock session being recorded and processed.</label>{!recording ? <button disabled={!consent} onClick={start}>Grant permissions and start</button> : <button className="stop" onClick={stop}>Stop session</button>}</div><div className="capture-status"><b>{status}</b><span>Adaptive sample interval: {sampleMs} ms</span></div>{error && <p className="error">{error}</p>}<div className="telemetry-log"><b>Client signal log</b>{telemetry.length ? telemetry.map(item=><span key={item}>{item}</span>) : <span className="muted">Signals appear after consent and session start.</span>}</div></div></div>;
}
