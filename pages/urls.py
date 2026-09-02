from django.urls import path
from . import views

urlpatterns = [
    path('',views.login_view,name='home'),
    path('pages/',views.pages,name='pages'),
    path('home',views.home,name='home'),
    path('about/',views.about,name='about'),
    path('services/',views.services,name='services'),
    path('services/details/<int:id>',views.details,name='details'),
    path('contact/',views.contact,name='contact'),
    path('login/',views.login_view,name='login'),
    path('register/',views.register_view,name='register'),
    path('employee_profile/',views.employee_profile,name='employee_profile'),
    path('all_users/',views.all_users,name='all_users'),
    path('logout/',views.logout_view,name='logout'),
]