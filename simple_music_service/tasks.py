from anymail.message import AnymailMessage
from backend.celery import app


@app.task
def send_welcome_email(user_email):
    message = AnymailMessage(
        subject="Welcome to Simple music service",
        body="Thank you for creating an account on our service.",
        to=[user_email],
    )
    message.send()
