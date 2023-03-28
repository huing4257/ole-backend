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
    reward_per_q = models.IntegerField()
    time_limit_per_q = models.IntegerField()
    total_time_limit = models.IntegerField()
    auto_ac = models.BooleanField()
    manual_ac = models.BooleanField()
    publisher = models.ForeignKey('user.User', on_delete=models.CASCADE, related_name="published_task")
    data = models.ManyToManyField('task.Data')
    distribute_users = models.ManyToManyField('user.User', related_name="distributed_tasks")
    task_id = models.AutoField(primary_key=True)
    distribute_user_num = models.IntegerField()
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

