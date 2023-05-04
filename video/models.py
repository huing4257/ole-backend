from django.db import models


# Create your models here.
class Video(models.Model):
    video_id = models.AutoField(primary_key=True)
    video_file = models.FileField(upload_to='data/video/uploads/%Y/%m/%d/', null=False)
    filename = models.CharField(max_length=255, null=True)
