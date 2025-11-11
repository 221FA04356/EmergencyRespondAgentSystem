# src/recorder.py
import sounddevice as sd
import soundfile as sf
import numpy as np
import os
import time
from collections import deque
from datetime import datetime

SAMPLE_RATE = 44100          # clear voice quality
CHANNELS = 1

# 🔧 Adjusted thresholds for stability
RMS_TRIGGER = 0.055          # slightly higher to avoid noise false triggers
RMS_SILENCE = 0.020          # silence level for stop detection
SILENCE_HOLD = 2.0           # seconds of silence before stop
PREBUFFER_SECONDS = 3        # include a few seconds before speech
WAIT_AFTER_SAVE = 1.0        # make sure file is flushed
MIC_WARMUP_SECONDS = 3       # wait before monitoring starts (important!)

class AudioMonitor:
    def __init__(self, out_folder="clips"):
        self.out_folder = out_folder
        os.makedirs(out_folder, exist_ok=True)
        self.prebuffer = deque(maxlen=int(PREBUFFER_SECONDS * SAMPLE_RATE))

    def _rms(self, data):
        return np.sqrt(np.mean(np.square(data)))

    def _record_stream(self):
        """Continuously yield audio blocks from the mic."""
        blocksize = int(0.1 * SAMPLE_RATE)  # 100 ms blocks for smoothness
        with sd.InputStream(samplerate=SAMPLE_RATE,
                            channels=CHANNELS,
                            dtype="float32",
                            blocksize=blocksize) as stream:
            # 🕓 Allow mic to stabilize before triggering
            print(f"⏳ Warming up microphone for {MIC_WARMUP_SECONDS}s...")
            time.sleep(MIC_WARMUP_SECONDS)
            print("🎙️ Microphone ready — starting detection.")
            while True:
                data, _ = stream.read(blocksize)
                yield data[:, 0] if CHANNELS == 1 else data

    def _save_clip(self, audio):
        """Write array to WAV and return filename."""
        filename = os.path.join(
            self.out_folder,
            f"clip_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
        )
        sf.write(filename, audio, SAMPLE_RATE, subtype="PCM_16")
        time.sleep(WAIT_AFTER_SAVE)
        return filename

    def run(self, on_event_callback):
        print("🎧 Monitoring started. Speak or play an alert sound to test.")
        try:
            stream_gen = self._record_stream()
            recording = []
            active = False
            silence_start = None

            for block in stream_gen:
                rms = self._rms(block)

                # Keep rolling prebuffer
                if not active:
                    self.prebuffer.extend(block)

                # Start recording on loud sound
                if not active and rms > RMS_TRIGGER:
                    print(f"🔊 Loud event detected (rms={rms:.4f}) — start recording")
                    active = True
                    recording = list(self.prebuffer)
                    self.prebuffer.clear()

                # Continue while active
                if active:
                    recording.extend(block)
                    if rms < RMS_SILENCE:
                        if silence_start is None:
                            silence_start = time.time()
                        elif time.time() - silence_start > SILENCE_HOLD:
                            print("🕊️ Silence held — stop recording")
                            active = False
                            silence_start = None
                            clip = np.array(recording, dtype="float32")
                            path = self._save_clip(clip)
                            print(f"✅ Saved clip: {path}")
                            try:
                                on_event_callback(path)
                            except Exception as e:
                                print("⚠️ Callback error:", e)
                            recording.clear()
                    else:
                        silence_start = None

        except KeyboardInterrupt:
            print("\n🛑 Stopping monitor.")
