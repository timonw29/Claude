"""Optional voice I/O for Moni. Requires a local microphone/speakers, so this
only works when run on your own machine - not inside a remote sandbox."""


def listen():
    try:
        import speech_recognition as sr
    except ImportError:
        raise RuntimeError(
            "Voice-Modus benötigt zusätzliche Pakete: "
            "pip install SpeechRecognition PyAudio"
        )

    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("[Moni hört zu...]")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source)

    try:
        return recognizer.recognize_google(audio, language="de-DE")
    except sr.UnknownValueError:
        return None
    except sr.RequestError as e:
        raise RuntimeError(f"Spracherkennung fehlgeschlagen: {e}")


def speak(text):
    try:
        import pyttsx3
    except ImportError:
        raise RuntimeError("Voice-Modus benötigt zusätzliches Paket: pip install pyttsx3")

    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
