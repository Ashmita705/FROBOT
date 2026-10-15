import os
import queue
import threading
import time

import cv2
import numpy as np
import pythoncom
import scipy.io.wavfile as wav
import sounddevice as sd
import whisper
import win32com.client
from deepface import DeepFace
from groq import Groq

API_KEY = os.getenv("GROQ_API_KEY")
if not API_KEY:
    raise SystemExit("GROQ_API_KEY not found. Set it in Windows and restart VS Code.")

client = Groq(api_key=API_KEY)
print("Loading Whisper model...")
whisper_model = whisper.load_model("base")

SAMPLE_RATE = 16000
MIC_DEVICE = 1                      # change to your microphone's index
AUDIO_FILE = "frobot_audio.wav"

PROMPT = """You are Frobot, a caring AI companion robot designed to help
elderly people, blind individuals, and children with special needs.
You provide emotional support, companionship and assistance.

The user's face shows they are {emotion}. Their voice tone is {tone}.

If they seem sad or lonely, respond with warmth and empathy.
If they seem anxious or stressed, respond with calm reassurance.
If they seem happy, match their energy.
If they need help, provide clear gentle guidance.

Always be warm, patient, caring and supportive.
Keep responses conversational and clear."""


# ==================== TEXT TO SPEECH ====================

tts_queue = queue.Queue()
stop_speech = threading.Event()
speaking = False


def tts_worker():
    global speaking
    pythoncom.CoInitialize()
    speaker = win32com.client.Dispatch("SAPI.SpVoice")
    voices = speaker.GetVoices()
    for i in range(voices.Count):
        if "Zira" in voices.Item(i).GetDescription():
            speaker.Voice = voices.Item(i)
            break
    speaker.Rate = -2

    while True:
        text = tts_queue.get()
        if text is None:
            break
        stop_speech.clear()
        speaking = True
        speaker.Speak(text, 1)                       # async
        while not speaker.WaitUntilDone(50):         # check every 50 ms
            if stop_speech.is_set():
                speaker.Speak("", 2)                 # purge current speech
                break
        speaking = False
    pythoncom.CoUninitialize()


def speak(text):
    text = text.encode("ascii", "ignore").decode()   # no emojis
    print(f"Frobot: {text}")
    stop_speech.set()                                # interrupt current speech
    while not tts_queue.empty():                     # drop old messages
        try:
            tts_queue.get_nowait()
        except queue.Empty:
            break
    tts_queue.put(text)


# ==================== RECORDING ====================

chunks, recording, rec_thread = [], False, None


def record():
    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32",
                        device=MIC_DEVICE,
                        callback=lambda indata, *_: chunks.append(indata.copy())):
        while recording:
            sd.sleep(100)


def start_recording():
    global recording, rec_thread
    chunks.clear()
    recording = True
    rec_thread = threading.Thread(target=record, daemon=True)
    rec_thread.start()
    print("Recording... press SPACE again to stop.")


def stop_recording():
    global recording
    recording = False
    rec_thread.join()
    if not chunks:
        return None
    audio = (np.concatenate(chunks) * 32767).astype(np.int16)
    wav.write(AUDIO_FILE, SAMPLE_RATE, audio)
    return AUDIO_FILE


# ==================== AI PIPELINE ====================

def detect_emotion(frame):
    try:
        result = DeepFace.analyze(frame, actions=["emotion"],
                                  enforce_detection=False, silent=True)
        return result[0]["dominant_emotion"]
    except Exception as e:
        print("DEEPFACE ERROR:", e)
        return "unknown"


def voice_tone(path):
    _, data = wav.read(path)
    energy = np.sqrt(np.mean(data.astype(float) ** 2))
    return "stressed" if energy > 3000 else "normal" if energy > 1000 else "calm"


def get_reply(user_text, emotion, tone):
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[
                {"role": "system", "content": PROMPT.format(emotion=emotion, tone=tone)},
                {"role": "user", "content": user_text},
            ],
            max_tokens=200,
        )
        return response.choices[0].message.content
    except Exception as e:
        print("Groq error:", e)
        return "I am here with you. How can I help?"


def process_audio(path, emotion):
    if not path:
        return speak("I didn't hear anything. Please try again.")
    text = whisper_model.transcribe(path)["text"].strip()
    print(f"You said: {text}")
    if not text:
        return speak("I didn't catch that. Could you try again?")
    speak(get_reply(text, emotion, voice_tone(path)))


# ==================== MAIN LOOP ====================

def main():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    tts_thread = threading.Thread(target=tts_worker, daemon=True)
    tts_thread.start()

    speak("Hello! I am Frobot, your AI companion. I am here for you. "
          "Press SPACE to start talking. Press SPACE again to stop.")

    emotion, frame_count = "neutral", 0
    print("\nSPACE = talk / stop | Q = quit\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Camera frame could not be read.")
            break

        frame_count += 1
        if frame_count % 30 == 0:                    # emotion every 30 frames
            emotion = detect_emotion(frame)

        status, color = (("Recording... press SPACE to stop", (0, 0, 255)) if recording
                         else ("Press SPACE to talk", (0, 255, 0)))
        for text, y, col in [(f"Emotion: {emotion}", 30, (0, 255, 0)),
                             (status, 70, color),
                             ("Q = Quit", frame.shape[0] - 10, (255, 255, 255))]:
            cv2.putText(frame, text, (10, y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, col, 2)
        cv2.imshow("Frobot Emotion Companion", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord(" "):
            if speaking:                             # SPACE interrupts speech
                stop_speech.set()
                time.sleep(0.1)
            if not recording:
                start_recording()
            else:
                process_audio(stop_recording(), emotion)
        elif key == ord("q"):
            break

    if recording:
        stop_recording()
    cap.release()
    cv2.destroyAllWindows()
    stop_speech.set()
    tts_queue.put("Goodbye! Take care of yourself.")
    tts_queue.put(None)
    tts_thread.join()
    print("Frobot closed.")


if __name__ == "__main__":
    main()
