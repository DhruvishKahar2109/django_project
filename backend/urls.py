from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_login, name='login'),
    path('dashboard',views.dashboard,name='dashboard'),
    path('categories',views.categories,name='categories'),
    path('logout',views.admin_logout,name='logout'),
]