from django.utils import log


class CustomAdminEmailHandler(log.AdminEmailHandler):
    def __init__(self, include_html=True, email_backend=None):
        super().__init__()
        self.include_html = include_html
        self.email_backend = email_backend
