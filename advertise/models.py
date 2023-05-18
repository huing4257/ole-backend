from django.db import models

from user.models import User
from utils.utils_require import MAX_CHAR_LENGTH


# Create your models here.
class Advertise(models.Model):
    ad_id = models.AutoField(primary_key=True)
    ad_pub_time = models.FloatField(default=0)
    ad_time = models.FloatField(default=0)
    ad_type = models.CharField(max_length=MAX_CHAR_LENGTH)
    img_url = models.CharField(max_length=MAX_CHAR_LENGTH)
    publisher = models.ForeignKey(User, on_delete=models.CASCADE)

    def serialize(self):
        return {
            "src": self.img_url,
            "expire_at": self.ad_time,
            "publish_at": self.ad_pub_time,
            "ad_id": self.ad_id,
        }
