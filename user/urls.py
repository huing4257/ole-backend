from django.urls import path
import user.views as views

urlpatterns = [
    path('register', views.register),
    path('login', views.login),
    path('logout', views.logout),
    path('userinfo/<user_id>', views.user_info),
    path('modifypassword', views.modify_password),
    path('ban_user/<int:user_id>', views.ban_user),
    path('get_all_users', views.get_all_users),   
    path('getvip', views.getvip),
    path('check_user/<int:user_id>', views.check_user),
    path('get_agent_list', views.get_agent_list),
    path('recharge', views.recharge),
    path('withdraw', views.withdraw),
]
