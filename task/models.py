import json

from django.db import models
from user.models import User, Category
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


class InputType(models.Model):
    input_tip = models.CharField(max_length=MAX_CHAR_LENGTH)

    def serialize(self):
        return {
            "input_tip": self.input_tip
        }


class InputResult(models.Model):
    input_type = models.ForeignKey(InputType, on_delete=models.CASCADE)
    input_res = models.CharField(max_length=MAX_CHAR_LENGTH)

    def serialize(self):
        return {
            "input_type": self.input_type.input_tip,
            "input_res": self.input_res,
        }


class Result(models.Model):
    tag_user = models.ForeignKey('user.User', on_delete=models.CASCADE)
    tag_res = models.CharField(max_length=MAX_CHAR_LENGTH)
    input_result = models.ManyToManyField(InputResult, default=[])

    def serialize(self):
        return {
            "tag_user_id": self.tag_user.user_id,
            "result": json.loads(self.tag_res),
            "input_result": [input_res.serialize() for input_res in self.input_result.all()],
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
    input_type = models.ManyToManyField(InputType, default=[])
    cut_num = models.IntegerField(default=None)

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
            "tag_type": [tag_type.type_name for tag_type in self.tag_type.all()],
            "input_type": [input_type.input_tip for input_type in self.input_type.all()],
            "cut_num": self.cut_num,
        } if user_id is None else {
            "q_id": self.q_id,
            "data": data,
            "result": self.result.filter(tag_user=user_id).first().serialize(),
            "data_type": self.data_type,
        }


class CurrentTagUser(models.Model):
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
    task_style = models.ManyToManyField(Category, default=[])  # 用任务样式作为给任务分类的依据
    reward_per_q = models.IntegerField(default=0)
    time_limit_per_q = models.IntegerField(default=0)
    total_time_limit = models.IntegerField(default=0)
    publisher = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name="published_task", null=True)
    task_id = models.AutoField(primary_key=True)
    distribute_user_num = models.IntegerField(default=0)
    q_num = models.IntegerField(default=0)
    task_name = models.CharField(max_length=24, default="task")
    questions = models.ManyToManyField(Question, default=[])
    current_tag_user_list = models.ManyToManyField(CurrentTagUser, default=[])
    past_tag_user_list = models.ManyToManyField(User, default=[])
    progress = models.ManyToManyField(Progress, default=[])
    result_type = models.CharField(max_length=MAX_CHAR_LENGTH)
    accept_method = models.CharField(max_length=MAX_CHAR_LENGTH, default="manual")
    tag_type = models.ManyToManyField(TagType, default=[])
    ans_list = models.ForeignKey(AnsList, on_delete=models.CASCADE, null=True)
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name="hand_out_task", null=True)
    check_result = models.CharField(max_length=MAX_CHAR_LENGTH, default="wait")
    strategy = models.CharField(max_length=MAX_CHAR_LENGTH, default="order")  # 分发策略
    input_type = models.ManyToManyField(InputType, default=[])
    cut_num = models.IntegerField(default=None)

    def serialize(self, short=False):
        return {
            "task_type": self.task_type,
            "task_style": " ".join([tag.category for tag in self.task_style.all()]),
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
            "ans_list": [ansdata.serialize() for ansdata in self.ans_list.ans_list.all()] if self.ans_list else [],
            "agent": self.agent.serialize() if self.agent else None,
            "check_result": self.check_result,
            "strategy": self.strategy,

        } if not short else {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "task_type": self.task_type,
            "task_style": " ".join([tag.category for tag in self.task_style.all()]),
            "accept_method": self.accept_method,
            "publisher": self.publisher.serialize(),
            "check_result": self.check_result,
            "distribute_user_num": self.distribute_user_num,
        }
