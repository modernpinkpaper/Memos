"""Hold Right Ctrl, talk (or whisper), let go. The words are typed where your cursor is.
Runs fully on your PC. No internet needed after the first model download."""
import threading
import time

import numpy as np
import pyperclip
import sounddevice as sd
from faster_whisper import WhisperModel
from pynput import keyboard

HOLD_KEY = keyboard.Key.ctrl_r   # change this to use another key
MIN_SECONDS = 0.4                # shorter holds are ignored (so normal Ctrl use is safe)
MODEL_NAME = "small.en"          # "base.en" = faster, "medium.en" = more accurate
RATE = 16000

try:
    import winsound
    def beep(freq):
        threading.Thread(target=winsound.Beep, args=(freq, 80), daemon=True).start()
except ImportError:
    def beep(freq):
        pass

print(f"Loading model '{MODEL_NAME}' (first run downloads it)...")
model = WhisperModel(MODEL_NAME, device="cpu", compute_type="int8")
print("Ready. Hold Right Ctrl and talk. Press Ctrl+C here to quit.")

frames = []
recording = False
start_time = 0.0
typer = keyboard.Controller()


def on_audio(indata, frame_count, time_info, status):
    if recording:
        frames.append(indata.copy())


def transcribe_and_type(audio):
    # Whispers are quiet, so make the sound louder first.
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak < 0.005:
        return
    audio = audio * (0.9 / peak)
    segments, _ = model.transcribe(audio, language="en", beam_size=5, vad_filter=True,
                                   condition_on_previous_text=False)
    text = " ".join(s.text.strip() for s in segments).strip()
    if not text:
        return
    print("Heard:", text)
    old = ""
    try:
        old = pyperclip.paste()
    except Exception:
        pass
    pyperclip.copy(text + " ")
    time.sleep(0.05)
    with typer.pressed(keyboard.Key.ctrl):
        typer.press("v")
        typer.release("v")
    time.sleep(0.3)
    try:
        pyperclip.copy(old)  # put your old clipboard back
    except Exception:
        pass


def on_press(key):
    global recording, start_time, frames
    if key == HOLD_KEY and not recording:
        frames = []
        start_time = time.time()
        recording = True
        beep(900)


def on_release(key):
    global recording
    if key == HOLD_KEY and recording:
        recording = False
        beep(600)
        if time.time() - start_time < MIN_SECONDS or not frames:
            return
        audio = np.concatenate(frames).flatten().astype(np.float32)
        threading.Thread(target=transcribe_and_type, args=(audio,), daemon=True).start()


with sd.InputStream(samplerate=RATE, channels=1, dtype="float32", callback=on_audio):
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()
