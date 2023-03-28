from django.db import models


# Create your models here.
class Data(models.Model):
    data = models.JSONField()

    def serialize(self):
        return {
            "data": self.data
        }


class Result(models.Model):
    user_id = models.IntegerField()
    result = models.JSONField()

    def serialize(self):
        return {
            "user_id": self.user_id,
            "result": self.result
        }


class Task(models.Model):
    task_type = models.CharField(max_length=20)
    task_style = models.CharField(max_length=200)
    reward_per_q = models.IntegerField(default=0)
    time_limit_per_q = models.IntegerField(default=0)
    total_time_limit = models.IntegerField(default=0)
    auto_ac = models.BooleanField(default=True)
    manual_ac = models.BooleanField(default=False)
    publisher = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name="published_task", null=True)
    data = models.ManyToManyField('task.Data', related_name="task", blank=True)
    distribute_users = models.ManyToManyField('user.User', related_name="distributed_tasks", null=True)
    task_id = models.AutoField(primary_key=True)
    distribute_user_num = models.IntegerField(default=0)
    result = models.ManyToManyField('task.Result')


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
            "result": [result.serialize() for result in self.result.all()]
        }

