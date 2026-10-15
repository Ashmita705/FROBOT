# Emotion Companion

This is the second AI module of Frobot, my accessibility companion robot.

It watches your face, listens to what you say, and replies out loud in a warm, caring voice. Its answer changes with how you feel: more comforting if you look sad, calmer if you sound stressed. It's meant for elderly people, blind people and children with special needs, who may want company and gentle help.

## Why I built this
Frobot has to do more than see the world. It also has to talk to the person in a way that fits how they feel. I wanted a companion that notices both your face and your voice, not just your words.

## What it does
- Reads your facial emotion from the webcam every 30 frames
- Records your voice when you press SPACE, and stops when you press SPACE again
- Turns your speech into text with Whisper
- Estimates your voice tone (calm, normal or stressed) from how loud you speak
- Sends your words, face emotion and voice tone to an AI model, which writes a caring reply
- Speaks the reply out loud in a natural voice
- Lets you interrupt Frobot at any time by pressing SPACE
- Shows the live camera feed with the detected emotion on screen

## How the program runs
![Flowchart](ai-2%20architecture.png)

## Technology Stack and Rationale
- **DeepFace** - ready-made facial emotion recognition, no training needed
- **OpenAI Whisper (base)** - accurate speech-to-text that runs on my own computer
- **Groq API (openai/gpt-oss-20b)** - fast AI replies, so the conversation doesn't feel slow
- **Windows SAPI voice (Microsoft Zira)** - a natural-sounding voice that works offline
- **sounddevice** - records microphone audio
- **OpenCV** - captures the webcam and draws the live video with text
- **Python threading** - recording and speaking run in their own threads, so the camera feed never freezes

## Design Decisions
- **Face emotion every 30 frames** - emotion analysis is slow, so checking every frame would make the video lag
- **Push-to-talk with SPACE** - simple and predictable, and the user decides when to speak
- **SPACE interrupts speech** - the user can cut Frobot off instead of waiting for a long reply
- **Voice tone from loudness** - a simple, fast signal that doesn't need another model
- **Reply limited to 200 tokens** - keeps answers short and easy to follow
- **System prompt built around emotion** - tells the AI how to respond to sad, stressed or happy users
- **Fallback reply** - if the AI service fails, Frobot still says "I am here with you. How can I help?"
- **API key in an environment variable** - the secret key never appears in the code or the repo

## Running it (Windows)
Tested with Python 3.12.

1. Install [FFmpeg](https://www.gyan.dev/ffmpeg/builds/) and add it to your PATH (Whisper needs it).
2. Get a free API key from Groq and save it as a Windows environment variable:
```bash
setx GROQ_API_KEY "your-key-here"
```
3. Close and reopen VS Code, then run:
```bash
git clone https://github.com/ashmita705/frobot.git
cd frobot/emotion-companion
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Press **SPACE** to start talking, **SPACE** again to stop, and **Q** to quit. The microphone number is set by `MIC_DEVICE` in `main.py`, so change it if your microphone is on a different number.

## How well it works
Tested on: laptop with 13th Gen Intel Core i5-1340P CPU, 16 GB RAM

| Situation | What happened |
|---|---|
| Smiling face | Detected happy |
| Sad face (slightly sad eyes, hand on cheek or mouth) | Detected sad |
| No expression | Detected neutral |
| Mouth open with wide eyes | Detected surprised |
| Flared nose, big eyes, raised eyebrows | Detected angry |
| Asked "how am I feeling?" with a sad face | Replied that I seemed a bit low, said everyone has these moments, and offered to help |
| Asked the same with a happy face | Replied that I looked upbeat and offered help if I needed anything |
| Asked simple questions | Answered correctly |
| Interrupted with SPACE and asked a new question | Stopped speaking immediately and answered the new question |
| Speaking quietly | Whisper sometimes misheard me, and Frobot replied to the wrong words instead of what I actually said |
| Speaking loudly | Heard me correctly and gave the right reply |

Time from pressing SPACE to the start of Frobot's reply: ___ seconds

## Problems I ran into
- **Problem:** Whisper and DeepFace kept failing because of missing or incompatible libraries (FFmpeg not found, OpenCV 5.0.0 had no `CascadeClassifier`, and changing NumPy broke Whisper).
  **Fix:** I installed FFmpeg and added it to PATH, went back to OpenCV 4.10.0, and restored NumPy 2.4.0. Then I pinned these versions in `requirements.txt`.

- **Problem:** The microphone wasn't recording usable audio.
  **Fix:** I found the correct input device (index 1) and confirmed the saved WAV file contained audio.

- **Problem:** My API key was pasted directly in the code, so anyone who saw the file could use it.
  **Fix:** I stored it as a Windows environment variable (`GROQ_API_KEY`) and read it with `os.getenv`, so the key never appears in the repo.

- **Problem:** pyttsx3 raised `run loop already started` when speech overlapped.
  **Fix:** I replaced it with a single speech worker thread using the Windows SAPI voice, fed by a queue.

- **Problem:** Frobot kept talking when I wanted to speak.
  **Fix:** Pressing SPACE now stops the current speech and starts recording.

## What it can't do yet
- It only works on Windows because it uses the Windows speech voice and the Windows camera setting
- It needs an internet connection for the AI replies
- Voice tone is estimated from loudness only, so a loud voice isn't always a stressed one
- Face emotion is a guess from the camera and can be wrong in poor light, or with several faces in view
- It is push-to-talk, so it can't listen hands-free
- It can mishear quiet speech, so it needs a clear, normal-volume voice

## What I want to add next
- [ ] Use a cross-platform speech setup so it runs on Mac and Linux
- [ ] Add an offline AI model for use without internet
- [ ] Analyse real voice features such as pitch and speed, not just loudness
- [ ] Combine emotion over several seconds instead of one frame, and choose the main face
- [ ] Add a wake word so it listens hands-free
- [ ] Analyse real voice features such as pitch and speed, not just loudness, and improve how quiet speech is picked up

## Where this could be useful
- A companion for elderly people who live alone
- Emotional support for children with special needs
- A voice assistant for blind users
- The conversation module of Frobot

## Author
Titli · [GitHub](https://github.com/ashmita705)
