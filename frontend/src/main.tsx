import React, {useState} from 'react';
import {createRoot} from 'react-dom/client';
import './style.css';
import ReviewerConsole from './ReviewerConsole';
import CandidateCapture from './CandidateCapture';

function App(){
  const [mode,setMode]=useState<'reviewer'|'candidate'>(window.location.hash==='#capture'?'candidate':'reviewer');
  const change=(next:'reviewer'|'candidate')=>{setMode(next); window.location.hash=next==='candidate'?'capture':'reviewer';};
  return <>{mode==='candidate'?<CandidateCapture onBack={()=>change('reviewer')}/>:<><div className="mode-switch"><button className="ghost" onClick={()=>change('candidate')}>Open candidate capture →</button></div><ReviewerConsole/></>}</>;
}
createRoot(document.getElementById('root')!).render(<App/>);
