from django.urls import path
import user.views as views
import user.vip_views as vip_views

urlpatterns = [
    path('register', views.register),
    path('login', views.login),
    path('logout', views.logout),
    path('userinfo/<user_id>', views.user_info),
    path('modifypassword', views.modify_password),
    path('ban_user/<int:user_id>', views.ban_user),
    path('get_all_users', views.get_all_users),
    path('getvip', vip_views.getvip),
    path('check_user/<int:user_id>', views.check_user),
    path('get_agent_list', views.get_agent_list),
    path('recharge', vip_views.recharge),
    path('withdraw', views.withdraw),
    path('get_verifycode', views.send_verify_code),
    path('get_all_tag_score', views.get_all_tag_score),
    path('modifybankaccount', views.modify_bank_card),
    path('change_email',views.change_email)
]
