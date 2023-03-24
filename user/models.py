from django.db import models
from utils.utils_require import MAX_CHAR_LENGTH


# Create your models here.
class User(models.Model):
    user_id = models.BigAutoField(primary_key=True)
    user_name = models.CharField(max_length=MAX_CHAR_LENGTH)
    password = models.CharField(max_length=MAX_CHAR_LENGTH)
    user_type = models.CharField(max_length=MAX_CHAR_LENGTH)
    score = models.IntegerField()
    membership_level = models.IntegerField()
    invite_code = models.CharField(max_length=MAX_CHAR_LENGTH)


class Meta:
    indexes = [models.Index(fields=["user_name"])]


def serialize(self):
    return {
        "user_id": self.user_id,
        "user_name": self.user_name,
        "user_type": self.user_type,
        "score": self.score,
        "membership_level": self.membership_level,
        "invite_code": self.invite_code
    }


def __str__(self) -> str:
    return self.user_name
