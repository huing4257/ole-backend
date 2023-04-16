from django.urls import path
import review.views as views

urlpatterns = [
    path('manual_check/<int:task_id>/<int:user_id>', views.manual_check),
    path('refuse/<int:task_id>/<int:user_id>', views.review_reject),
    path('accept/<int:task_id>/<int:user_id>', views.review_accept),
]
