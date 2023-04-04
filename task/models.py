from django.db import models
from user.models import User
from utils.utils_require import MAX_CHAR_LENGTH
# Create your models here.


class Data(models.Model):
    data = models.JSONField()

    def serialize(self):
        return {
            "data": self.data
        }


class Result(models.Model):
    tag_user = models.ManyToManyField(User)
    tag_res = models.CharField(max_length=MAX_CHAR_LENGTH)

    def serialize(self):
        return {
            "tag_user": self.tag_user,
            "tag_res": self.tag_res
        }


class Question(models.Model):
    data = models.CharField(max_length=MAX_CHAR_LENGTH)
    result = models.ManyToManyField(Result)
    # 文字/图片/视频
    data_type = models.CharField(max_length=MAX_CHAR_LENGTH)

    def serialize(self):
        return {
            "data": self.data,
            "result": [self.result.serialize()],
            "data_type": self.data_type,
        }


class Current_tag_user(models.Model):
    tag_user = models.ManyToManyField(User)
    accepted_at = models.IntegerField()


class Progress(models.Model):
    tag_user = models.ManyToManyField(User)
    q_id = models.IntegerField()


class Task(models.Model):
    task_type = models.CharField(max_length=20)
    task_style = models.CharField(max_length=MAX_CHAR_LENGTH)
    reward_per_q = models.IntegerField(default=0)
    time_limit_per_q = models.IntegerField(default=0)
    total_time_limit = models.IntegerField(default=0)
    publisher = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name="published_task", null=True)
    task_id = models.AutoField(primary_key=True)
    distribute_user_num = models.IntegerField(default=0)
    q_num = models.IntegerField(default=0)
    task_name = models.CharField(max_length=24, default="task")
    questions = models.ManyToManyField(Question)
    current_tag_user_list = models.ManyToManyField(Current_tag_user)
    past_tag_user_list = models.ManyToManyField(User)
    progress = models.ManyToManyField(Progress)
    result_type = models.CharField(max_length=MAX_CHAR_LENGTH)
    accept_method = models.CharField(max_length=MAX_CHAR_LENGTH)

    def serialize(self):
        return {
            "task_type": self.task_type,
            "task_style": self.task_style,
            "reward_per_q": self.reward_per_q,
            "time_limit_per_q": self.time_limit_per_q,
            "total_time_limit": self.total_time_limit,
            "publisher": self.publisher.serialize(),
            "task_id": self.task_id,
            "distribute_user_num": self.distribute_user_num,
            "q_num": self.q_num,
            "task_name": self.task_name,
            "question": self.questions.serialize(),
            "current_tag_user_list": self.current_tag_user_list.serialize(),
            "past_tag_user_list": self.past_tag_user_list.serialize(),
            "progress": self.progress.serialize(),
            "result_type": self.result_type,
            "accept_method": self.accept_method,
        }

