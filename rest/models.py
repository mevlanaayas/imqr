import os

from django.db.models import Model
from django.db.models.fields import CharField, UUIDField, IntegerField

from imgqr import settings


class QR(Model):
    user = UUIDField()
    qr = UUIDField()
    content_type = CharField(max_length=4)
    view_count = IntegerField()

    @property
    def url(self):
        filename = 'qrized_%s.%s' % (self.qr, self.content_type)
        return os.path.join(settings.FILE_UPLOAD_TEMP_DIR, filename)
