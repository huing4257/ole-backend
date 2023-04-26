from django.db import models
from utils.utils_require import MAX_CHAR_LENGTH


# Create your models here.
class Category(models.Model):
    category = models.CharField(unique=True, max_length=MAX_CHAR_LENGTH)

    def serialize(self):
        return {
            "category": self.category,
        }


class UserCategory(models.Model):
    # 关联的用户
    user = models.ForeignKey('User', on_delete=models.CASCADE)
    # 任务分类
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    # 接取该分类的任务的次数
    count = models.IntegerField(default=0)


class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    user_name = models.CharField(max_length=200, unique=True)
    password = models.BinaryField()
    user_type = models.CharField(max_length=20)
    score = models.IntegerField(default=100)
    membership_level = models.IntegerField(default=0)
    invite_code = models.CharField(max_length=20)
    credit_score = models.IntegerField(default=100)
    bank_account = models.CharField(max_length=20, default="")
    account_balance = models.IntegerField(default=100)
    grow_value = models.IntegerField(default=0)
    vip_expire_time = models.FloatField(default=0)
    is_checked = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    categories = models.ManyToManyField(Category, through=UserCategory)

    class Meta:
        indexes = [models.Index(fields=["user_name"])]

    def serialize(self, private: bool = False):
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "user_type": self.user_type,
            "score": self.score,
            "membership_level": self.membership_level,
            "invite_code": self.invite_code,
            "credit_score": self.credit_score,
            "bank_account": self.bank_account,
            "account_balance": self.account_balance,
            "grow_value": self.grow_value,
            "vip_expire_time": self.vip_expire_time,
            "is_checked": self.is_checked,
            "is_banned": self.is_banned,
        } if private else {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "user_type": self.user_type,
            "membership_level": self.membership_level,
            "credit_score": self.credit_score,
            "grow_value": self.grow_value,
            "is_checked": self.is_checked,
            "is_banned": self.is_banned,
        }

    def __str__(self) -> str:
        return self.user_name


class UserToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'user_token'