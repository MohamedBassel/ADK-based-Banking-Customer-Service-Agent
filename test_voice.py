import speech_recognition as sr
import requests
import json

BASE_URL = "http://localhost:8000"

# Step 1: Login
print("Logging in...")
login_data = {"username": "user123", "password": "password123"}
response = requests.post(f"{BASE_URL}/login", json=login_data)
token = response.json()["access_token"]
print(f"✅ Got token\n")

# Step 2: Record audio from microphone
print("🎤 Recording... Speak your question now!")
print("(Will record for 5 seconds)\n")

recognizer = sr.Recognizer()

try:
    with sr.Microphone() as source:
        print("Adjusting for ambient noise... Please wait")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        print("✅ Ready! Speak now...")
        
        audio = recognizer.listen(source, timeout=50, phrase_time_limit=50)
        print("✅ Recording complete!\n")
        
        # Save audio to file
        with open("test_audio.wav", "wb") as f:
            f.write(audio.get_wav_data())
        
        print("Transcribing locally...")
        text = recognizer.recognize_google(audio)
        print(f"You said: '{text}'\n")
        
        # Step 3: Send to API
        print("Sending to API...")
        headers = {"Authorization": f"Bearer {token}"}
        
        with open("test_audio.wav", "rb") as f:
            files = {"audio": ("audio.wav", f, "audio/wav")}
            data = {"user_id": "user123"}
            
            response = requests.post(
                f"{BASE_URL}/query/voice",
                headers=headers,
                files=files,
                data=data
            )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Agent Response:\n{result['response']}")
        else:
            print(f"\n❌ Error: {response.json()}")
            
except sr.WaitTimeoutError:
    print("❌ No speech detected within timeout")
except sr.UnknownValueError:
    print("❌ Could not understand audio")
except sr.RequestError as e:
    print(f"❌ Recognition service error: {e}")
except Exception as e:
    print(f"❌ Error: {e}")