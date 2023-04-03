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
    distribute_users = models.ManyToManyField('user.User', related_name="distributed_tasks")
    task_id = models.AutoField(primary_key=True)
    distribute_user_num = models.IntegerField(default=0)
    result = models.ManyToManyField('task.Result')
    task_name = models.CharField(max_length=24, default="task")

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


class Question(models.Model):
    # 1-index
    q_id = models.AutoField()
    q_description = models.CharField()
    data = models.ManyToManyField()
    result = models.CharField()
    # 文字/图片/视频
    data_type = models.CharField()


class SubTask(models.Model):
    subtask_id = models.IntegerField(primary_key=True, unique=True)
    # 问题信息列表
    questions = models.ManyToManyField()
    # 问题数目 子任务中包含的问题数目
    q_num = models.IntegerField()
    # 子任务是否已被分发
    distributed = models.BooleanField()
    # 被分发者的user_id
    tag_user = models.IntegerField()
    # 任务被标注方接受时间 默认值为0，重新分发时需要设置为0
    accepted_at = models.IntegerField(default=0)
    # 被分发用户id列表 用于确保重新分发时不重复分发给同一个用户
    tag_user_list = models.ManyToManyField()
