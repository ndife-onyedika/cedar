import socket

from celery.signals import task_failure
from django.conf import settings
from django.core.mail import mail_admins


@task_failure.connect()
def celery_task_failure_email(**kwargs):
    """celery 4.0 onward has no method to send emails on failed tasks
    so this event handler is intended to replace it
    """

    subject = "[{app_name} Django Celery Task] Error: Task {sender.name} ({task_id}): {exception}".format(
        **kwargs, app_name=settings.APP_NAME
    )

    message = """Task {sender.name} with id {task_id} raised exception:
        {exception!r}

        Task was called with args: {args} kwargs: {kwargs}.

        The contents of the full traceback was:

            {einfo}
    """.format(
        **kwargs
    )

    mail_admins(subject, message)
