from django.urls import path
import task.views as views

urlpatterns = [
    path('', views.create_task),
    path('<task_id>', views.task_ops),
    path('all', views.all),
    path('get_my_tasks', views.get_my_tasks),
    path('upload_data/<task_id>', views.upload_data),
    path('upload_res/<task_id>', views.upload_res)
]
