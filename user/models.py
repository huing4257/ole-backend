import datetime

from django.db import models
from utils.utils_require import MAX_CHAR_LENGTH
from utils.utils_time import get_timestamp


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


class BankCard(models.Model):
    card_id = models.CharField(max_length=MAX_CHAR_LENGTH)
    card_balance = models.IntegerField(default=0)


class EmailVerify(models.Model):
    email = models.EmailField()
    email_valid = models.CharField(max_length=MAX_CHAR_LENGTH, null=True)
    email_valid_expire = models.DateTimeField(
        default=datetime.datetime.fromtimestamp(0).replace(tzinfo=datetime.timezone.utc))


class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    user_name = models.CharField(max_length=200, unique=True)
    password = models.BinaryField()
    user_type = models.CharField(max_length=20)
    score = models.IntegerField(default=100)
    membership_level = models.IntegerField(default=0)
    invite_code = models.CharField(max_length=20)
    credit_score = models.IntegerField(default=100)
    bank_account = models.ForeignKey(BankCard, on_delete=models.CASCADE, null=True)
    account_balance = models.IntegerField(default=100)
    grow_value = models.IntegerField(default=0)
    vip_expire_time = models.FloatField(default=0)
    is_checked = models.BooleanField(default=False)
    is_banned = models.BooleanField(default=False)
    categories = models.ManyToManyField(Category, through=UserCategory)
    email = models.ForeignKey(EmailVerify, null=True, on_delete=models.CASCADE)
    tag_score = models.IntegerField(default=0)

    class Meta:
        indexes = [models.Index(fields=["user_name"])]

    def serialize(self, private: bool = False):
        if self.vip_expire_time < get_timestamp():
            self.membership_level = 0
            self.save()
        return {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "user_type": self.user_type,
            "score": self.score,
            "membership_level": self.membership_level,
            "invite_code": self.invite_code,
            "credit_score": self.credit_score,
            "bank_account": self.bank_account.card_id if self.bank_account else "",
            "account_balance": self.account_balance,
            "grow_value": self.grow_value,
            "vip_expire_time": self.vip_expire_time,
            "is_checked": self.is_checked,
            "is_banned": self.is_banned,
            "email": self.email.email if self.email else "",
            "tag_score": self.tag_score,
        } if private else {
            "user_id": self.user_id,
            "user_name": self.user_name,
            "user_type": self.user_type,
            "membership_level": self.membership_level,
            "credit_score": self.credit_score,
            "grow_value": self.grow_value,
            "is_checked": self.is_checked,
            "is_banned": self.is_banned,
            "tag_score": self.tag_score,
        }

    def __str__(self) -> str:
        return self.user_name


class UserToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'user_token'
