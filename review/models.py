from django.db import models

from task.models import Task
from user.models import User
from utils.utils_require import MAX_CHAR_LENGTH


class AnsData(models.Model):
    filename = models.CharField(max_length=MAX_CHAR_LENGTH)
    std_ans = models.CharField(max_length=MAX_CHAR_LENGTH)

    def serialize(self):
        return {
            "filename": self.filename,
            "std_ans": self.std_ans,
        }


class AnsList(models.Model):
    id = models.AutoField(primary_key=True)
    ans_list = models.ManyToManyField(AnsData, default=[])


class ReportInfo(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    result = models.BooleanField(default=None, null=True)

    def serialize(self):
        return {
            "task_id": self.task.task_id,
            "task_type": self.task.task_type,
            "task_name": self.task.task_name,
            "user_id": self.user.user_id,
            "user_name": self.user.user_name,
            "credit_score": self.user.credit_score
        }
