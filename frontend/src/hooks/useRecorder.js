import { useState, useRef, useCallback, useEffect } from "react";

const BAR_COUNT = 24;

export function useRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState(null);
  // live per-bar levels (0..1) for the waveform meter
  const [levels, setLevels] = useState(() => new Array(BAR_COUNT).fill(0));

  const mediaRecorder = useRef(null);
  const chunks = useRef([]);
  const audioCtx = useRef(null);
  const rafId = useRef(null);

  const stopMeter = () => {
    if (rafId.current) cancelAnimationFrame(rafId.current);
    rafId.current = null;
    if (audioCtx.current) {
      audioCtx.current.close().catch(() => {});
      audioCtx.current = null;
    }
    setLevels(new Array(BAR_COUNT).fill(0));
  };

  const startMeter = (stream) => {
    try {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      audioCtx.current = new Ctx();
      const source = audioCtx.current.createMediaStreamSource(stream);
      const analyser = audioCtx.current.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);

      const data = new Uint8Array(analyser.frequencyBinCount);
      let last = 0;
      const tick = (t) => {
        rafId.current = requestAnimationFrame(tick);
        if (t - last < 60) return;   // ~16fps is plenty for a meter
        last = t;
        analyser.getByteFrequencyData(data);
        // sample the spectrum into BAR_COUNT buckets (skip the very lowest bins)
        const step = Math.floor((data.length * 0.7) / BAR_COUNT);
        const next = new Array(BAR_COUNT);
        for (let i = 0; i < BAR_COUNT; i++) {
          next[i] = Math.min(1, data[2 + i * step] / 220);
        }
        setLevels(next);
      };
      rafId.current = requestAnimationFrame(tick);
    } catch {
      /* meter is decorative — recording continues without it */
    }
  };

  const start = useCallback(async () => {
    setError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream, { mimeType: "audio/webm" });
      chunks.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunks.current.push(e.data);
      };

      mediaRecorder.current = recorder;
      recorder.start();
      startMeter(stream);
      setIsRecording(true);
    } catch (err) {
      setError("Microphone access denied. Please allow microphone access.");
    }
  }, []);

  const stop = useCallback(() => {
    return new Promise((resolve) => {
      stopMeter();
      if (!mediaRecorder.current) return resolve(null);

      mediaRecorder.current.onstop = () => {
        const blob = new Blob(chunks.current, { type: "audio/webm" });
        mediaRecorder.current.stream.getTracks().forEach((t) => t.stop());
        setIsRecording(false);
        resolve(blob);
      };

      mediaRecorder.current.stop();
    });
  }, []);

  useEffect(() => stopMeter, []);   // clean up on unmount

  return { isRecording, start, stop, error, levels };
}
