from django.db import models


# Create your models here.
class User(models.Model):
    user_id = models.AutoField(primary_key=True, default=1)
    user_name = models.CharField(max_length=200, unique=True)
    password = models.CharField(max_length=200)
    user_type = models.CharField(max_length=20)
    score = models.IntegerField(default=0)
    membership_level = models.IntegerField(default=0)
    invite_code = models.CharField(max_length=20)

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
