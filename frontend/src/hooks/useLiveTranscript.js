import { useState, useRef, useCallback } from "react";

/**
 * Live on-screen transcript while dictating, via the browser's Web Speech API
 * (Chrome/Edge/Safari). This is a PREVIEW only — the authoritative transcript
 * still comes from Whisper on the backend, which is far better with drug
 * names. On unsupported browsers `supported` is false and the UI falls back
 * to the waveform-only view.
 */
const Recognition =
  typeof window !== "undefined"
    ? window.SpeechRecognition || window.webkitSpeechRecognition
    : null;

export function useLiveTranscript() {
  const [preview, setPreview] = useState("");
  const recRef = useRef(null);
  const finalRef = useRef("");

  const start = useCallback(() => {
    if (!Recognition) return;
    try {
      const rec = new Recognition();
      rec.continuous = true;
      rec.interimResults = true;
      rec.lang = navigator.language?.startsWith("en") ? navigator.language : "en-IN";

      finalRef.current = "";
      setPreview("");

      rec.onresult = (e) => {
        let interim = "";
        for (let i = e.resultIndex; i < e.results.length; i++) {
          const chunk = e.results[i][0].transcript;
          if (e.results[i].isFinal) finalRef.current += chunk + " ";
          else interim += chunk;
        }
        setPreview((finalRef.current + interim).trim());
      };

      // Chrome stops recognition after silence — restart while dictating.
      rec.onend = () => {
        if (recRef.current === rec) {
          try { rec.start(); } catch { /* already restarted */ }
        }
      };

      rec.onerror = () => { /* preview is best-effort — ignore */ };

      recRef.current = rec;
      rec.start();
    } catch {
      /* preview unavailable — recording still works */
    }
  }, []);

  const stop = useCallback(() => {
    const rec = recRef.current;
    recRef.current = null;          // signals onend not to restart
    if (rec) {
      try { rec.stop(); } catch { /* noop */ }
    }
    setPreview("");
  }, []);

  return { supported: !!Recognition, preview, start, stop };
}
