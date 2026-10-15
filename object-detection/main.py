import cv2
import pyttsx3
from ultralytics import YOLO
import time
import threading

# Initialize YOLO model
model = YOLO('yolov8n.pt')  # downloads automatically first time ~6MB

def speak(text):
    print(f"Speaking: {text}")
    def run():
        engine = pyttsx3.init('sapi5')
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    t = threading.Thread(target=run)
    t.start()

# Position estimator based on box location in frame
def get_position(box, frame_width):
    center_x = (box.xyxy[0][0] + box.xyxy[0][2]) / 2
    if center_x < frame_width / 3:
        return "on your left"
    elif center_x > 2 * frame_width / 3:
        return "on your right"
    else:
        return "ahead of you"

# Start camera
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Camera not found!")
    exit()

speak("Accessibility Navigator started. I will describe what I see around you.")

last_spoken_time = time.time()
speak_interval = 3 # speak every 3 seconds

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_width = frame.shape[1]
    current_time = time.time()

    # Run YOLO detection
    results = model(frame, verbose=False)

    # Draw boxes on frame
    annotated_frame = results[0].plot()

    # Speak description every 3 seconds
    if current_time - last_spoken_time >= speak_interval:
        detected_objects = []

        for result in results:
            for box in result.boxes:
                label = model.names[int(box.cls)]
                confidence = float(box.conf)
                position = get_position(box, frame_width)

                # Only include if confidence above 50%
                if confidence > 0.5:
                    detected_objects.append(f"{label} {position}")

        if detected_objects:
            # Remove duplicates
            unique_objects = list(set(detected_objects))
            description = "I can see " + ", ".join(unique_objects[:3])  # max 3 objects
            speak(description)
            
        else:
            speak("Path appears clear")
            
        last_spoken_time = current_time

    # Show camera feed with detections
    cv2.imshow('Accessibility Navigator - Press Q to quit', annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
speak("Accessibility Navigator stopped.")
