from __future__ import absolute_import

import os

from django.conf import settings

from celery import Celery
from celery.concurrency import asynpool
from celery.signals import setup_logging

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cedar.settings")
BASE_REDIS_URL = settings.CELERY_BROKER_URL
app = Celery("cedar")

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object("django.conf:settings")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
app.conf.broker_url = BASE_REDIS_URL

asynpool.PROC_ALIVE_TIMEOUT = 10.0  # set this long enough

if not settings.DEBUG:

    @setup_logging.connect
    def config_loggers(*args, **kwargs):
        from logging.config import dictConfig  # noqa

        dictConfig(settings.LOGGING)


@app.task(bind=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))
