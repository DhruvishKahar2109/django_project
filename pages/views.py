from django.shortcuts import render,redirect
from django.http import HttpResponse
from django.template import loader
from .models import Service
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone


# Create your views here.

def pages(request):
    return HttpResponse("Hello World")


# create HTML function with renader
def home(request):
    template = loader.get_template('home.html')
    return HttpResponse(template.render())


def about(request):
    template = loader.get_template('about.html')
    return HttpResponse(template.render())


def services(request):
    allServices = Service.objects.all()
    template = loader.get_template('services.html')
    return HttpResponse(template.render({
        'services': allServices
    })
    )
def details(request,id):
    myService = Service.objects.get(id=id)
    template = loader.get_template('details.html')
    return HttpResponse(template.render({
        'myService': myService
    }))

def contact(request):
    template = loader.get_template('contact.html')
    return HttpResponse(template.render())


def login_view(request):

    # return HttpResponse("Hello World")
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('employee_profile')
        else:
            print("Login failed")
            return HttpResponse("Invaild credentials")
    template = loader.get_template('login.html')
    return HttpResponse(template.render({},request))

def register_view(request):

    if request.method == 'POST':
        firstname = request.POST['fullName']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']

        if User.objects.filter(username=username).exists():
            return HttpResponse("Username already exists")

        user = User.objects.create_user(
            first_name=firstname,
            username=username,
            email=email,
            password=password,
            last_login=timezone.now(),
            is_superuser=False,
            is_staff=False,
            is_active=True,
            date_joined=timezone.now()
        )
        user.save()
        messages.success(request, 'User created successfully')
        return redirect('login')
    template = loader.get_template('register.html')
    return HttpResponse(template.render({},request))

@login_required
def employee_profile(request):
    user = User.objects.get(id=request.user.id)
    if request.method == 'POST':
        user.first_name = request.POST['first_name']
        user.last_name = request.POST['last_name']
        user.username = request.POST['username']
        user.email = request.POST['email']

        user.save()

        messages.success(request, 'User updated successfully')

        return redirect('employee_profile')

    template = loader.get_template('employee_profile.html')
    return HttpResponse(template.render({
        'user': user
    },request))

@login_required
def all_users(request):
    all_user = User.objects.all()
    template = loader.get_template('all_users.html')
    return HttpResponse(template.render({
        'all_user': all_user
    },request))

def logout_view(request):
    logout(request)
    return redirect('login')