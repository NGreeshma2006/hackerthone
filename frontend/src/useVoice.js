import { useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';
import messages from '../../shared/voice_messages.json';

export const languages = { 'Hindi + English': 'hi-IN', English: 'en-IN', हिंदी: 'hi-IN', తెలుగు: 'te-IN', தமிழ்: 'ta-IN', ಕನ್ನಡ: 'kn-IN', മലയാളം: 'ml-IN', मराठी: 'mr-IN', বাংলা: 'bn-IN' };
function initialLanguage() {
  try { const value = JSON.parse(localStorage.getItem('boli-language')); return languages[value] ? value : 'Hindi + English'; }
  catch { return 'Hindi + English'; }
}

export function useVoice({ request, refresh, open, command, setCommand }) {
  const [language, changeLanguage] = useState(initialLanguage);
  const locale = languages[language];
  const code = locale.split('-')[0];
  const voiceText = messages[code];
  const [transcript, setTranscript] = useState(() => messages[languages[initialLanguage()].split('-')[0]].ready);
  const [recognizedText, setRecognizedText] = useState('');
  const [isListening, setListening] = useState(false);
  const [busy, setBusy] = useState(false);
  const [isSpeaking, setSpeaking] = useState(false);
  const recognition = useRef(null), processing = useRef(false), speech = useRef(null);
  const latestResponse = useRef(null), mounted = useRef(true);
  const remoteSpeech = useRef(null);

  function cancelRecognition() {
    const rec = recognition.current;
    recognition.current = null;
    if (rec) { rec.onresult = rec.onerror = rec.onend = null; rec.abort(); }
    setListening(false);
  }
  function cancelSpeech() {
    speech.current = null;
    const remote = remoteSpeech.current;
    remoteSpeech.current = null;
    if (remote) {
      remote.controller.abort();
      clearTimeout(remote.timer);
      if (remote.audio) { remote.audio.pause(); remote.audio.removeAttribute('src'); remote.audio.load(); }
      if (remote.url) URL.revokeObjectURL(remote.url);
    }
    window.speechSynthesis?.cancel();
    setSpeaking(false);
  }
  useEffect(() => {
    mounted.current = true;
    // The browser may populate voices asynchronously. getVoices primes that list.
    window.speechSynthesis?.getVoices();
    return () => { mounted.current = false; cancelRecognition(); cancelSpeech(); };
  }, []);

  async function speakOnline(text, responseLocale) {
    const remote = { controller: new AbortController() };
    remoteSpeech.current = remote;
    setSpeaking(true);
    remote.timer = setTimeout(() => remote.controller.abort(), 25000);
    const current = () => mounted.current && remoteSpeech.current === remote;
    const finish = (failed = false) => {
      if (!current()) return;
      cancelSpeech();
      if (failed) toast.info(messages[responseLocale.split('-')[0]].noVoice);
    };
    try {
      const response = await fetch(`${import.meta.env.VITE_API_URL || '/api'}/voice/speak`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, language: responseLocale.split('-')[0] }),
        signal: remote.controller.signal,
      });
      if (!response.ok) throw new Error('Speech unavailable');
      const blob = await response.blob();
      if (!current()) return;
      clearTimeout(remote.timer);
      remote.url = URL.createObjectURL(blob);
      remote.audio = new Audio(remote.url);
      remote.audio.onended = () => finish();
      remote.audio.onerror = () => finish(true);
      await remote.audio.play();
    } catch { finish(true); }
  }

  function speak(text, responseLocale = locale) {
    cancelSpeech();
    const synthesis = window.speechSynthesis;
    if (!synthesis || !window.SpeechSynthesisUtterance) { void speakOnline(text, responseLocale); return; }
    const voices = synthesis.getVoices();
    const matching = voices.find(v => v.lang.toLowerCase() === responseLocale.toLowerCase()) || voices.find(v => v.lang.split('-')[0] === responseLocale.split('-')[0]);
    if (!matching) { void speakOnline(text, responseLocale); return; }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = responseLocale;
    if (matching) utterance.voice = matching;
    utterance.rate = .95;
    speech.current = utterance;
    utterance.onstart = () => { if (speech.current === utterance) setSpeaking(true); };
    utterance.onend = () => { if (speech.current === utterance) { speech.current = null; setSpeaking(false); } };
    utterance.onerror = event => {
      if (speech.current !== utterance) return;
      speech.current = null; setSpeaking(false);
      if (!['canceled', 'interrupted'].includes(event.error)) void speakOnline(text, responseLocale);
    };
    try { synthesis.speak(utterance); }
    catch { speech.current = null; void speakOnline(text, responseLocale); }
  }

  async function runCommand(text = command) {
    if (typeof text !== 'string' || !text.trim() || processing.current) return;
    cancelRecognition(); cancelSpeech();
    processing.current = true; setBusy(true);
    setRecognizedText(text.trim()); setTranscript(voiceText.processing);
    try {
      const result = await request('/voice/process', { text: text.trim(), language: code });
      if (!mounted.current) return;
      if (!['ok', 'answer', 'error'].includes(result.status) || typeof result.message !== 'string') throw new Error('Invalid response');
      setTranscript(result.message);
      latestResponse.current = { text: result.message, locale };
      speak(result.message, locale);
      if (result.status === 'ok') { toast.success(result.message); await refresh(); }
      else if (result.status === 'answer') open('Boli’s answer', { answer: result.message });
      else toast.error(result.message);
      if (result.status !== 'error') setCommand('');
    } catch (error) {
      if (!mounted.current) return;
      const message = error.status === 422 ? voiceText.invalid : voiceText.server;
      setTranscript(message); latestResponse.current = { text: message, locale };
      toast.error(message); speak(message, locale);
    } finally { processing.current = false; if (mounted.current) setBusy(false); }
  }

  function stopListening() { cancelRecognition(); setTranscript(voiceText.paused); }
  function voiceFailure(key) {
    cancelRecognition(); setTranscript(voiceText[key]); toast.error(voiceText[key]); open('Voice entry');
  }
  function startListening() {
    if (processing.current) return;
    if (recognition.current) { stopListening(); return; }
    cancelSpeech();
    const Speech = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Speech || !window.isSecureContext) { voiceFailure('unavailable'); return; }
    const rec = new Speech(); recognition.current = rec;
    rec.lang = locale; rec.continuous = false; rec.interimResults = true; rec.maxAlternatives = 1;
    let received = false;
    rec.onstart = () => { if (recognition.current === rec) { setListening(true); setTranscript(voiceText.listening); } };
    rec.onresult = event => {
      if (recognition.current !== rec || received) return;
      const results = Array.from(event.results);
      const text = results.map(result => result[0].transcript).join(' ').trim();
      setRecognizedText(text);
      if (results.length && results.every(result => result.isFinal)) { received = true; runCommand(text); }
    };
    rec.onerror = event => {
      if (recognition.current !== rec) return;
      if (event.error === 'aborted') { stopListening(); return; }
      voiceFailure(['not-allowed', 'service-not-allowed', 'audio-capture'].includes(event.error) ? 'permission' : event.error === 'no-speech' ? 'noSpeech' : event.error === 'network' ? 'network' : 'unavailable');
    };
    rec.onend = () => {
      if (recognition.current !== rec) return;
      recognition.current = null; setListening(false);
      if (!received) setTranscript(voiceText.noSpeech);
    };
    try { setListening(true); setRecognizedText(''); setTranscript(voiceText.listening); rec.start(); }
    catch { voiceFailure('unavailable'); }
  }
  function setLanguage(value) {
    if (!languages[value] || processing.current) return;
    cancelRecognition(); cancelSpeech(); latestResponse.current = null;
    changeLanguage(value); setRecognizedText('');
    setTranscript(messages[languages[value].split('-')[0]].ready);
    try { localStorage.setItem('boli-language', JSON.stringify(value)); } catch { /* Selection still works without storage. */ }
  }
  function replayResponse() {
    if (isSpeaking) { cancelSpeech(); return; }
    if (recognition.current || processing.current) return;
    const response = latestResponse.current || { text: transcript, locale };
    speak(response.text, response.locale);
  }
  return { language, setLanguage, isListening, transcript, recognizedText, voiceText, busy, isSpeaking, replayResponse, startListening, stopListening, runCommand };
}

