from django.urls import path
from user.views import *

urlpatterns = [
    path('', index, name='index'),
    path('login/', login_view, name='user_login'),
    path('logout/', logout_view, name='user_logout'),
    path('user_change_password/', user_change_password, name='user_change_password'),
    path('user_register/', user_register, name='user_register'),
    path('borrow/', borrow_umbrella, name='borrow'),
    path('giveback/', give_back_umbrella, name='giveback'),

]
