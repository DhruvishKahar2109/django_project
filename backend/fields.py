from django.db import models

class OrderedForeignKey(models.ForeignKey):

    def __init__(self, *args, after=None, **kwargs):
        self.after = after
        super().__init__(*args, **kwargs)