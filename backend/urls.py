from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_login, name='login'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('categories', views.categories, name='categories'),
    path('categories/create/', views.category_create, name='category_create'),
    path("category/delete/<int:id>/",views.category_delete,name="category_delete"),
    path('category/update/<int:id>/',views.category_update,name='category_update'),
    path("products/", views.products, name="products"),
    path("products/create", views.product_create, name="product_create"),
    path("product/update/<int:id>/",views.product_update,name="product_update"),
    path("product/delete/<int:id>/",views.product_delete,name="product_delete"),
    path('customers/', views.customers, name='customers'),
    path('customers/create/', views.customer_create, name='customer_create'),
    path('customers/update/<int:id>/',views.customer_update,name='customer_update'),
    path('customers/delete/<int:id>/',views.customer_delete,name='customer_delete'),
    path('orders/', views.orders, name='orders'),
    path('orders/detail/<int:id>/',views.order_detail,name='order_detail'),
    path('logout', views.admin_logout, name='logout'),
]
