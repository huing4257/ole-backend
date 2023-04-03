from django.db import models
from user.models import User
# Create your models here.


class Data(models.Model):
    data = models.JSONField()

    def serialize(self):
        return {
            "data": self.data
        }


class Result(models.Model):
    tag_user = models.ManyToManyField(User)
    tag_res = models.CharField(max_length=255)

    def serialize(self):
        return {
            "tag_user": self.tag_user,
            "tag_res": self.tag_res
        }


class Question(models.Model):
    data = models.CharField(max_length=255)
    result = models.ManyToManyField(Result)
    # 文字/图片/视频
    data_type = models.CharField(max_length=255)


class Current_tag_user(models.Model):
    tag_user = models.ManyToManyField(User)
    accepted_at = models.IntegerField()


class Progress(models.Model):
    tag_user = models.ManyToManyField(User)
    q_id = models.IntegerField()


class Task(models.Model):
    task_type = models.CharField(max_length=20)
    task_style = models.CharField(max_length=200)
    reward_per_q = models.IntegerField(default=0)
    time_limit_per_q = models.IntegerField(default=0)
    total_time_limit = models.IntegerField(default=0)
    auto_ac = models.BooleanField(default=True)
    manual_ac = models.BooleanField(default=False)
    publisher = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name="published_task", null=True)
    task_id = models.AutoField(primary_key=True)
    distribute_user_num = models.IntegerField(default=0)
    q_num = models.IntegerField(default=0)
    task_name = models.CharField(max_length=24, default="task")
    questions = models.ManyToManyField(Question)
    current_tag_user_list = models.ManyToManyField(Current_tag_user)
    past_tag_user_list = models.ManyToManyField(User)
    progress = models.ManyToManyField(Progress)
    result_type = models.CharField(max_length=255)

    def serialize(self):
        return {
            "task_type": self.task_type,
            "task_style": self.task_style,
            "reward_per_q": self.reward_per_q,
            "time_limit_per_q": self.time_limit_per_q,
            "total_time_limit": self.total_time_limit,
            "auto_ac": self.auto_ac,
            "manual_ac": self.manual_ac,
            "publisher": self.publisher.serialize(),
            "data": [data.serialize() for data in self.data.all()],
            "distribute_users": [user.serialize() for user in self.distribute_users.all()],
            "task_id": self.task_id,
            "distribute_user_num": self.distribute_user_num,
            "result": [result.serialize() for result in self.result.all()],
            "task_name": self.task_name,
        }

