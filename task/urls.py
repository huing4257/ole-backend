from django.urls import path

import task.distribute_views
import task.question_views
import task.tag_views
import task.upload_data_views
import task.views as views

urlpatterns = [
    path('', views.create_task),
    path('<int:task_id>', views.task_ops),
    path('all', views.get_all_tasks),
    path('get_all_tasks', views.get_all_tasks),
    path('get_my_tasks', views.get_my_tasks),
    path('upload_data', task.upload_data_views.upload_data),
    path('upload_res/<int:task_id>/<int:q_id>', task.question_views.upload_res),
    path('<int:task_id>/<int:q_id>', task.question_views.get_task_question),
    path('distribute/<int:task_id>', task.distribute_views.distribute_task),
    path('refuse/<int:task_id>', task.tag_views.refuse_task),
    path('accept/<int:task_id>', task.tag_views.accept_task),
    # path('progress/<int:task_id>', task.tag_views.get_progress),
    # path('is_accepted/<task_id>', task.tag_views.is_accepted),
    path('is_distributed/<task_id>', task.distribute_views.is_distributed),
    path('redistribute/<int:task_id>', task.distribute_views.redistribute_task),
    path('to_agent/<int:task_id>', task.distribute_views.to_agent),
    path('distribute_to_user/<int:task_id>/<int:user_id>', task.distribute_views.distribute_to_user),
    path('get_free_tasks', views.get_free_tasks),
    path('check_task/<int:task_id>', views.check_task),
    path('taginfo/<int:task_id>', task.tag_views.taginfo),
    path('startquestion/<int:task_id>/<int:q_id>', task.question_views.startquestion),
    path('upload_res/<int:task_id>', task.tag_views.upload_many_res),
    path('get_batch_data/<int:task_id>', task.tag_views.get_batch_data)
]
