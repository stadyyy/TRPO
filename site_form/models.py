from django.db import models

# Create your models here.

class MedicalDocument(models.Model):
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='documents/')

    def __str__(self):
        return f"Document uploaded on {self.uploaded_at}"
