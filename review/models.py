from django.db import models
from task.models import Task
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
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True)


