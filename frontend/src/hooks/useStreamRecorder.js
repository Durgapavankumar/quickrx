import { useState, useRef, useCallback, useEffect } from "react";

const BAR_COUNT = 24;

/**
 * Real-time WebSocket-based voice streaming recorder.
 * Records audio and streams chunks to server via WebSocket.
 * Server processes and returns transcript + drug entries in real-time.
 */
export function useStreamRecorder() {
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState(null);
  const [levels, setLevels] = useState(() => new Array(BAR_COUNT).fill(0));
  const [isConnected, setIsConnected] = useState(false);

  const mediaRecorder = useRef(null);
  const audioCtx = useRef(null);
  const rafId = useRef(null);
  const ws = useRef(null);
  const stream = useRef(null);

  const stopMeter = () => {
    if (rafId.current) cancelAnimationFrame(rafId.current);
    rafId.current = null;
    if (audioCtx.current) {
      audioCtx.current.close().catch(() => {});
      audioCtx.current = null;
    }
    setLevels(new Array(BAR_COUNT).fill(0));
  };

  const startMeter = (audioStream) => {
    try {
      const Ctx = window.AudioContext || window.webkitAudioContext;
      audioCtx.current = new Ctx();
      const source = audioCtx.current.createMediaStreamSource(audioStream);
      const analyser = audioCtx.current.createAnalyser();
      analyser.fftSize = 256;
      source.connect(analyser);

      const data = new Uint8Array(analyser.frequencyBinCount);
      let last = 0;
      const tick = (t) => {
        rafId.current = requestAnimationFrame(tick);
        if (t - last < 60) return;
        last = t;
        analyser.getByteFrequencyData(data);
        const step = Math.floor((data.length * 0.7) / BAR_COUNT);
        const next = new Array(BAR_COUNT);
        for (let i = 0; i < BAR_COUNT; i++) {
          next[i] = Math.min(1, data[2 + i * step] / 220);
        }
        setLevels(next);
      };
      rafId.current = requestAnimationFrame(tick);
    } catch {
      /* meter is decorative */
    }
  };

  const start = useCallback(
    async (sessionId, wsUrl) => {
      setError(null);
      try {
        // Connect WebSocket first
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const baseUrl = wsUrl || `${protocol}//${window.location.host}`;
        const wsEndpoint = `${baseUrl}/api/v1/ws/transcribe/${sessionId}`;

        ws.current = new WebSocket(wsEndpoint);

        ws.current.onopen = () => {
          setIsConnected(true);
        };

        ws.current.onerror = (event) => {
          setError("WebSocket connection failed");
          setIsConnected(false);
        };

        ws.current.onclose = () => {
          setIsConnected(false);
        };

        // Get microphone stream
        const audioStream = await navigator.mediaDevices.getUserMedia({
          audio: true,
        });
        stream.current = audioStream;

        // Use MediaRecorder to send audio chunks
        const recorder = new MediaRecorder(audioStream, {
          mimeType: "audio/webm",
        });
        mediaRecorder.current = recorder;

        recorder.ondataavailable = (e) => {
          if (e.data.size > 0 && ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(e.data);
          }
        };

        recorder.start(100); // Send chunk every 100ms for low latency
        startMeter(audioStream);
        setIsRecording(true);
      } catch (err) {
        setError(
          err.name === "NotAllowedError"
            ? "Microphone access denied"
            : "Failed to start streaming"
        );
        if (ws.current) ws.current.close();
      }
    },
    []
  );

  const transcribe = useCallback(() => {
    return new Promise((resolve) => {
      if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
        resolve(null);
        return;
      }

      const messageHandler = (event) => {
        const data = JSON.parse(event.data);
        if (data.status === "success") {
          ws.current?.removeEventListener("message", messageHandler);
          resolve({
            transcript: data.transcript,
            drug_entry: data.drug_entry,
          });
        } else if (data.status === "error") {
          ws.current?.removeEventListener("message", messageHandler);
          resolve({ error: data.error });
        }
      };

      ws.current.addEventListener("message", messageHandler);
      ws.current.send(
        JSON.stringify({
          action: "transcribe",
          format: "webm",
        })
      );
    });
  }, []);

  const stop = useCallback(() => {
    return new Promise((resolve) => {
      stopMeter();

      if (mediaRecorder.current) {
        mediaRecorder.current.onstop = () => {
          if (stream.current) {
            stream.current.getTracks().forEach((t) => t.stop());
            stream.current = null;
          }
          setIsRecording(false);

          if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(
              JSON.stringify({
                action: "close",
              })
            );
          }
          ws.current = null;
          resolve();
        };

        mediaRecorder.current.stop();
      } else {
        resolve();
      }
    });
  }, []);

  const reset = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(
        JSON.stringify({
          action: "reset",
        })
      );
    }
  }, []);

  useEffect(() => stopMeter, []);

  return {
    isRecording,
    start,
    stop,
    transcribe,
    reset,
    error,
    levels,
    isConnected,
  };
}
