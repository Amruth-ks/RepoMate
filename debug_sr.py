import speech_recognition as sr
print("Imported sr")
try:
    r = sr.Recognizer()
    print("Recognizer created")
except Exception as e:
    print(f"Error creating Recognizer: {e}")

try:
    m = sr.Microphone()
    print("Microphone created (Unexpected!)")
except AttributeError:
    print("AttributeError creating Microphone (Expected if PyAudio missing)")
except Exception as e:
    print(f"Error creating Microphone: {e}")
