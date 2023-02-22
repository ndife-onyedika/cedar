from pathlib import Path

from celery import shared_task
from django.conf import settings as dj_sett
from django.core.mail import EmailMessage, get_connection


@shared_task
def send_mail(messages):
    message_list = []
    connection = get_connection()
    connection.open()

    for message in messages:
        new_list = []
        if not message[-1] is None:
            for file in message[-1]:
                path = Path(file)
                with path.open("rb") as f:
                    content = f.read()
                    new_list.append((path.name, content))
            message[-1] = new_list

    for subject, message, sender, recipient, cc, bcc, attachments in messages:
        msg = EmailMessage(
            cc=cc,
            bcc=bcc,
            body=message,
            to=recipient,
            subject=subject,
            from_email=sender,
            attachments=attachments,
            reply_to=["admin@Marafa Cedarco.com"],
            headers={"sender": sender or dj_sett.DEFAULT_FROM_EMAIL},
        )
        msg.content_subtype = "html"
        message_list.append(msg)

    try:
        # Send the two emails in a single call -
        connection.send_messages(message_list)
    except Exception as e:
        raise Exception(f"EMAIL_SEND_ERROR: {e}")
    # We need to manually close the connection.
    connection.close()
