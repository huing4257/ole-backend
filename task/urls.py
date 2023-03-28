from django.urls import path
import task.views as views

urlpatterns = [
    path('<task_id>', views.task_ops),
    path('all', views.get_all_tasks),
    path('get_my_tasks', views.get_my_tasks),
    path('upload_data/<task_id>', views.upload_data),
    path('upload_res/<task_id>', views.upload_res)
]
