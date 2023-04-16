from django.db import models
from user.models import User
from review.models import AnsList
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
    tag_user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    tag_res = models.CharField(max_length=MAX_CHAR_LENGTH)

    def serialize(self):
        return {
            "tag_user_id": self.tag_user.user_id,
            "tag_res": self.tag_res
        }


class TagType(models.Model):
    type_name = models.CharField(max_length=MAX_CHAR_LENGTH)

    def serialize(self):
        return {
            "type_name": self.type_name,
        }


class Question(models.Model):
    q_id = models.BigIntegerField(null=False, default=1)
    data = models.CharField(max_length=MAX_CHAR_LENGTH)
    result = models.ManyToManyField(Result, default=[])
    # 文字/图片/视频
    data_type = models.CharField(max_length=MAX_CHAR_LENGTH)
    tag_type = models.ManyToManyField(TagType, default=[])

    def serialize(self, detail=False, user_id: int = None):
        if detail:
            if self.data_type == "text":
                data = TextData.objects.filter(id=int(self.data)).first().data.split('\n')
            else:
                data = self.data
        else:
            data = self.data
        return {
            "q_id": self.q_id,
            "data": data,
            "result": [result.serialize() for result in self.result.all()],
            "data_type": self.data_type,
            "tag_type": [tag_type.type_name for tag_type in self.tag_type.all()]
        } if user_id is None else {
            "q_id": self.q_id,
            "data": data,
            "result": self.result.filter(tag_user=user_id).first().serialize(),
            "data_type": self.data_type,
        }


class Current_tag_user(models.Model):
    tag_user = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    # todo 
    accepted_at = models.FloatField(null=True)
    is_finished = models.BooleanField(default=False)
    is_check_accepted = models.CharField(max_length=MAX_CHAR_LENGTH, default="none")

    def serialize(self):
        return {
            "tag_user": self.tag_user.serialize(),
            "accepted_at": self.accepted_at,
            "is_finished": self.is_finished,
            "is_check_accepted": self.is_check_accepted,
        }


class Progress(models.Model):
    tag_user = models.ForeignKey(User, on_delete=models.CASCADE, default=None)
    q_id = models.IntegerField()

    def serialize(self):
        return {
            "tag_user": self.tag_user.serialize(),
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
    questions = models.ManyToManyField(Question, default=[])
    current_tag_user_list = models.ManyToManyField(Current_tag_user, default=[])
    past_tag_user_list = models.ManyToManyField(User, default=[])
    progress = models.ManyToManyField(Progress, default=[])
    result_type = models.CharField(max_length=MAX_CHAR_LENGTH)
    accept_method = models.CharField(max_length=MAX_CHAR_LENGTH, default="manual")
    tag_type = models.ManyToManyField(TagType, default=[])
    ans_list = models.ForeignKey(AnsList, on_delete=models.CASCADE, null=True)

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
            "tag_type": [tag_type.type_name for tag_type in self.tag_type.all()],
            "ans_list": [ansdata.serialize() for ansdata in self.ans_list.ans_list.all()] if self.ans_list else []
        }
