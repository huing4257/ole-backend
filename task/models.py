from django.db import models
from user.models import User
from utils.utils_require import MAX_CHAR_LENGTH


# Create your models here.


class TextData(models.Model):
    data = models.TextField(max_length=2000)
    id = models.AutoField(primary_key=True)
    filename = models.CharField(max_length=MAX_CHAR_LENGTH)

    def serialize(self):
        return {
            "data": self.data,
            "id": self.id,
            "filename": self.filename,
        }


class Result(models.Model):
    tag_user = models.ForeignKey('user.User', on_delete=models.CASCADE, default=None)
    tag_res = models.CharField(max_length=MAX_CHAR_LENGTH)

    def serialize(self):
        return {
            "tag_user": self.tag_user,
            "tag_res": self.tag_res
        }


class Question(models.Model):
    q_id = models.BigIntegerField(null=False, default=1)
    data = models.CharField(max_length=MAX_CHAR_LENGTH)
    result = models.ManyToManyField(Result, null=True, default=None)
    # 文字/图片/视频
    data_type = models.CharField(max_length=MAX_CHAR_LENGTH)

    def serialize(self, detail=False):
        if detail:
            if self.data_type == "text":
                data = TextData.objects.filter(id=int(self.data)).first().data.split('\n')
            else:
                data = self.data
        else:
            data = self.data
        return {
            "data": data,
            "result": [user.serialize() for user in self.result.all()],
            "data_type": self.data_type,
        }


class Current_tag_user(models.Model):
    tag_user = models.ManyToManyField(User, null=True, default=None)
    # todo 
    accepted_at = models.FloatField()

    def serialize(self):
        return {
            "tag_user": [user.serialize() for user in self.tag_user.all()],
            "accepted_at": self.accepted_at,
        }


class Progress(models.Model):
    tag_user = models.ManyToManyField(User, null=True, default=None)
    q_id = models.IntegerField()

    def serialize(self):
        return {
            "tag_user": [user.serialize() for user in self.tag_user.all()],
            "q_id": self.q_id
        }


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
    questions = models.ManyToManyField(Question, default=None)
    current_tag_user_list = models.ManyToManyField(Current_tag_user, default=None)
    past_tag_user_list = models.ManyToManyField(User, default=None)
    progress = models.ManyToManyField(Progress, default=None)
    result_type = models.CharField(max_length=MAX_CHAR_LENGTH)
    accept_method = models.CharField(max_length=MAX_CHAR_LENGTH, default="manual")

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
            "questions": [user.serialize() for user in self.questions.all()],
            "current_tag_user_list": [user.serialize() for user in self.current_tag_user_list.all()],
            "past_tag_user_list": [user.serialize() for user in self.past_tag_user_list.all()],
            "progress": [user.serialize() for user in self.progress.all()],
            "result_type": self.result_type,
            "accept_method": self.accept_method,
        }
