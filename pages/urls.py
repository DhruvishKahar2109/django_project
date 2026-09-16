from django.urls import path
from . import views

urlpatterns = [
    path('simple_login',views.login_view,name='simple_login'),
    path('pages/',views.pages,name='pages'),
    path('home',views.home,name='home'),
    path('about/',views.about,name='about'),
    path('services/',views.services,name='services'),
    path('services/details/<int:id>',views.details,name='details'),
    path('contact/',views.contact,name='contact'),
    path('first_login/',views.login_view,name='first_login'),
    path('logout/',views.logout_view,name='logout'),
    path('register/',views.register_view,name='register'),
    path('employee_profile/',views.employee_profile,name='employee_profile'),
    path('all_users/',views.all_users,name='all_users'),
    path('',views.shop_home,name='shop_home'),
    path('shop/list',views.shop_list,name='shop_list'),
    path('shop/details/<slug:slug>',views.shop_details,name='shop_details'),
    path('cart/add/<slug:slug>/',views.add_to_cart,name='add_to_cart'),
    path('cart/update/<int:item_id>/',views.cart_update,name='cart_update'),
    path('cart/remove/<int:item_id>/',views.cart_remove,name='cart_remove'),
    path('shop/cart_list',views.cart_list,name='cart_list'),
    path('shop/checkout',views.checkout,name='checkout'),
    path('shop/checkout_success/<str:order_number>/',views.checkout_success,name="checkout_success"),
    path('shop/my_orders',views.my_orders,name='my_orders'),
    path('shop/my_orders/order_detail/<int:order_id>',views.shop_order_detail,name='shop_order_detail'),
    path('shop/login',views.shop_login,name='shop_login'),
    path('shop/register',views.shop_register,name='shop_register'),
    path('shop/my_profile',views.my_profile,name='my_profile'),
    path('shop/logout',views.shop_logout,name='shop_logout'),
    path('logout/',views.logout_view,name='logout'),

    path('shop/about',views.shop_about,name='shop_about'),
    path('categories/', views.shop_categories, name='shop_categories'),
    path('deals/', views.shop_deals, name='shop_deals'),

    path('shop/forgot_password',views.forgot_password,name='forgot_password'),

    path('test-email/',views.test_email,name='test_email'),
]