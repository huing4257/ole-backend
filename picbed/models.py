from django.db import models


# Create your models here.
class Image(models.Model):
    img_id = models.AutoField(primary_key=True)
    img_file = models.ImageField(upload_to='picbed/uploads/%Y/%m/%d/', null=False)
