from django.urls import path
import task.views as views

urlpatterns = [
    path('', views.create_task),
    path('<int:task_id>', views.task_ops),
    path('all', views.get_all_tasks),
    path('get_all_tasks', views.get_all_tasks),
    path('get_my_tasks', views.get_my_tasks),
    path('upload_data', views.upload_data),
    path('upload_res/<int:task_id>/<int:q_id>', views.upload_res),
    path('<int:task_id>/<int:q_id>', views.get_task_question),
    path('distribute/<int:task_id>', views.distribute_task),
    path('refuse/<int:task_id>', views.refuse_task),
    path('accept/<int:task_id>', views.accept_task),
    path('progress/<int:task_id>', views.get_progress),
    path('is_accepted/<task_id>', views.is_accepted),
    path('is_distributed/<task_id>', views.is_distributed),
    path('redistribute/<int:task_id>', views.redistribute_task),
    path('to_agent/<int:task_id>', views.to_agent),
    path('distribute_to_user/<int:task_id>/<int:user_id>', views.distribute_to_user),
]
