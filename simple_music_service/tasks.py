from anymail.message import AnymailMessage
from backend.celery import app
from pydub import AudioSegment
from speech_recognition import Recognizer, AudioFile, UnknownValueError, RequestError
from io import BytesIO
import requests


@app.task
def send_welcome_email(user_email):
    message = AnymailMessage(
        subject="Welcome to Simple music service",
        body="Thank you for creating an account on our service.",
        to=[user_email],
    )
    message.send()


@app.task()
def recognize_speech_from_file(location):
    response = requests.get(location)
    with BytesIO(response.content) as file:
        sound = AudioSegment.from_mp3(file)

    recognizer = Recognizer()
    recognized_string = []

    for chunk in split_file_to_chunks(sound):
        with BytesIO() as memory_buffer:
            chunk.export(memory_buffer, format="wav")
            with AudioFile(memory_buffer) as source:
                recognizer.adjust_for_ambient_noise(source)
                audio = recognizer.record(source)
        try:
            s = recognizer.recognize_google(audio)
            recognized_string.append(s)
        except (UnknownValueError, RequestError):
            pass

        if len(recognized_string) > 0:
            return " ".join(recognized_string)
        else:
            return None


def split_file_to_chunks(sound, *, chunk_size=60000):
    for i in range(0, len(sound), chunk_size):
        yield sound[i:i + chunk_size]
