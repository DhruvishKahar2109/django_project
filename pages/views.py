from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from .models import Service, Customer, Cart, CartItem, Order, OrderItem
from backend.models import Category, Product
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
from decimal import Decimal
import requests
from django.conf import settings


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


def details(request, id):
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
    template = loader.get_template('admin_login.html')
    return HttpResponse(template.render({}, request))


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
    return HttpResponse(template.render({}, request))


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
    }, request))


@login_required
def all_users(request):
    all_user = User.objects.all()
    template = loader.get_template('all_users.html')
    return HttpResponse(template.render({
        'all_user': all_user
    }, request))


def shop_home(request):
    Categories = Category.objects.filter(is_active=True)
    Products = Product.objects.filter(is_active=True).select_related('category')
    template = loader.get_template('shop/home.html')
    return HttpResponse(template.render({
        'categories': Categories,
        'products': Products
    }, request))


def shop_list(request):
    print("CUSTOMER ID:", request.session.get('customer_id'))
    print("CUSTOMER NAME:", request.session.get('customer_name'))

    categories = Category.objects.filter(
        is_active=True
    )
    products = Product.objects.filter(
        is_active=True
    ).select_related('category')

    selected_category = request.GET.get('category')

    if selected_category:
        products = products.filter(
            category_id=selected_category
        )

    search = request.GET.get("search")
    if search:
        products = products.filter(
            name__icontains=search
        )

    sort = request.GET.get("sort")
    if sort == "price_low":
        products = products.order_by("price")
    elif sort == "price_high":
        products = products.order_by("-price")
    elif sort == "name":
        products = products.order_by("name")
    else:
        products = products.order_by("-id")

    return render(request, 'shop/shop_list.html', {
        'categories': categories,
        'products': products,
        'selected_category': selected_category,
        'search': search,
        'sort': sort,
    })


def shop_details(request, slug):
    product = get_object_or_404(Product.objects.select_related('category'), slug=slug, is_active=True)
    return render(request, 'shop/product_detail.html', {
        "product": product
    })


def add_to_cart(request, slug):
    customer_id = request.session.get("customer_id")

    if not customer_id:
        return redirect("shop_login")

    if request.method != "POST":
        return redirect("shop_details", slug=slug)

    customer_id = request.session.get("customer_id")

    # Product
    product = get_object_or_404(Product, slug=slug)

    # Quantity
    quantity = int(request.POST.get("quantity", 1))

    if quantity < 1:
        quantity = 1

    # Customer
    customer = get_object_or_404(Customer, id=customer_id)

    cart, created = Cart.objects.get_or_create(
        customer=customer
    )

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product
    )

    # Quantity
    if created:
        cart_item.quantity = quantity
    else:
        cart_item.quantity += quantity

    cart_item.save()

    messages.success(
        request,
        f"{product.name} added to cart."
    )

    return redirect("shop_details", slug=product.slug)


def cart_list(request):
    if not request.session.get("customer_id"):
        return redirect('shop_login')

    customer_id = request.session.get("customer_id")

    customer = get_object_or_404(Customer, id=customer_id)

    cart, created = Cart.objects.get_or_create(
        customer=customer
    )

    cart_items = cart.items.select_related(
        'product',
        'product__category',
    )

    subtotal = Decimal('0.00')

    for item in cart_items:
        item.item_total = item.product.price * item.quantity
        subtotal += item.item_total

    delivery = Decimal('0.00')

    total = subtotal + delivery

    context = {
        'cart': cart,
        'cart_items': cart_items,
        'subtotal': subtotal,
        'delivery': delivery,
        'total': total,
    }

    return render(request, 'shop/cart.html', context)


def cart_update(request, item_id):
    if not request.session.get("customer_id"):
        return redirect("shop_login")

    customer_id = request.session.get("customer_id")

    item = get_object_or_404(
        CartItem,
        id=item_id,
        cart__customer_id=customer_id
    )

    if request.method == "POST":

        quantity = int(
            request.POST.get("quantity", 1)
        )

        # Quantity 1 se kam nahi honi chahiye
        if quantity < 1:
            quantity = 1

        # Stock check
        if quantity > item.product.stock:
            messages.error(
                request,
                f"Only {item.product.stock} items available."
            )

            return redirect("cart_list")

        item.quantity = quantity
        item.save()

    return redirect("cart_list")


def cart_remove(request, item_id):
    if not request.session.get("customer_id"):
        return redirect("shop_login")

    customer_id = request.session.get("customer_id")

    item = get_object_or_404(
        CartItem,
        id=item_id,
        cart__customer_id=customer_id
    )

    product_name = item.product.name

    item.delete()

    messages.success(
        request,
        f"{product_name} removed from cart."
    )

    return redirect("cart_list")


def checkout(request):
    if not request.session.get("customer_id"):
        return redirect("shop_login")

    customer_id = request.session.get("customer_id")

    customer = get_object_or_404(Customer, id=customer_id)

    cart, created = Cart.objects.get_or_create(
        customer=customer
    )

    cart_items = cart.items.select_related(
        "product",
        "product__category"
    )

    if not cart_items.exists():
        messages.info(
            request,
            "Your cart is empty."
        )
        return redirect("cart_list")

    if request.method == "GET":
        subtotal = Decimal("0.00")
        for item in cart_items:
            item.item_total = (item.product.price * item.quantity)
            subtotal += item.item_total

        delivery = Decimal("0.00")
        total = subtotal + delivery

        context = {
            'customer': customer,
            'cart': cart,
            'cart_items': cart_items,
            'subtotal': subtotal,
            'delivery': delivery,
            'total': total,
        }
        return render(request, 'shop/checkout.html', context)

    if request.method == "POST":
        email = request.POST.get('email', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        pincode = request.POST.get('pincode', '').strip()
        country = request.POST.get('country', '').strip()
        landmark = request.POST.get('landmark', '').strip()
        payment_method = request.POST.get('payment_method', 'cod')

        subtotal = Decimal('0.00')

        for item in cart_items:
            item_total = (item.product.price * item.quantity)
            subtotal += item_total
        delivery = Decimal('0.00')
        total = subtotal + delivery

        with transaction.atomic():

            order = Order.objects.create(
                customer=customer,
                first_name=first_name,
                last_name=last_name,
                email=email,
                phone=phone,
                address=address,
                city=city,
                state=state,
                pincode=pincode,
                country=country,
                landmark=landmark,
                payment_method=payment_method,
                status='confirmed',
                subtotal=subtotal,
                delivery=delivery,
                total=total,
            )

            for item in cart_items:
                item_total = (item.product.price * item.quantity)

                OrderItem.objects.create(
                    order=order,
                    product=item.product,
                    product_name=item.product.name,
                    product_price=item.product.price,
                    quantity=item.quantity,
                    subtotal=item_total,
                )
            cart.items.all().delete()

        messages.success(
            request,
            f"Order {order.order_number} Place Successfully."
        )
    return redirect('checkout_success', order_number=order.order_number)


def checkout_success(request, order_number):
    if not request.session.get("customer_id"):
        return redirect("shop_login")

    customer_id = request.session.get("customer_id")

    order = get_object_or_404(Order, order_number=order_number, customer_id=customer_id)

    return render(request, 'shop/order_success.html', {
        "order": order
    })


def my_orders(request):
    customer_id = request.session.get("customer_id")
    if not customer_id:
        return redirect("shop_login")

    myOrders = Order.objects.filter(customer_id=customer_id).prefetch_related('items').order_by('-created_at')
    return render(request, 'shop/my_orders.html',{
        "orders": myOrders
    })

def shop_order_detail(request, order_id):

    customer_id = request.session.get("customer_id")

    if not customer_id:
        return redirect("shop_login")

    order = get_object_or_404(
        Order.objects.prefetch_related("items"),
        id=order_id,
        customer_id=customer_id
    )

    context = {
        "order": order,
    }

    return render(
        request,
        "shop/order_detail.html",
        context
    )


def shop_login(request):
    if request.session.get('customer_id'):
        return redirect('shop_home')

    if request.method == 'POST':
        email = request.POST.get('email','').strip()
        password = request.POST.get('password','')

        #reCapTCHA
        recaptcha_response = request.POST.get('g-recaptcha-response')
        if not recaptcha_response:
            messages.error(
                request,
                'Please complete the reCAPTCHA verification.'
            )
            return redirect('shop_login')
        try:

            captcha_response = requests.post(
                'https://www.google.com/recaptcha/api/siteverify',
                data={
                    'secret': settings.RECAPTCHA_SECRET_KEY,
                    'response': recaptcha_response,
                    'remoteip': request.META.get('REMOTE_ADDR'),
                },
                timeout=10
            )

            captcha_result = captcha_response.json()

        except requests.RequestException:
            messages.error(
                request,
                'reCAPTCHA verification failed. Please try again.'
            )
            return redirect('shop_login')

        if not captcha_result.get('success'):
            messages.error(
                request,
                'reCAPTCHA verification failed. Please try again.'
            )
            return redirect('shop_login')

        #customer login
        try:
            customer = Customer.objects.get(email=email)

        except Customer.DoesNotExist:
            messages.error(request, 'Invalid email or password')
            return redirect('shop_login')

        if check_password(password, customer.password):
            customer.last_login = timezone.now()
            customer.save(update_fields=['last_login'])

            request.session['logged_in'] = True
            request.session['customer_id'] = customer.id
            request.session['customer_name'] = customer.first_name + " " + customer.last_name
            request.session['customer_email'] = customer.email

            return redirect('shop_home')

        else:
            messages.error(request, 'Invalid email or password')
            return redirect('shop_login')

    return render(request, 'shop/login.html',{
        'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY,
    })


def shop_register(request):
    if request.method == 'POST':
        firstname = request.POST.get('first_name','').strip()
        lastname = request.POST.get('last_name','').strip()
        username = request.POST.get('username','').strip()
        email = request.POST.get('email','').strip()
        password = request.POST.get('password','')
        confirmation = request.POST.get('confirm_password','')

        #reCaptcha

        recaptcha_response = request.POST.get(
            'g-recaptcha-response'
        )

        if not recaptcha_response:

            messages.error(
                request,
                'Please complete the reCAPTCHA verification.'
            )

            return redirect('shop_register')

        try:

            captcha_response = requests.post(
                'https://www.google.com/recaptcha/api/siteverify',
                data={
                    'secret': settings.RECAPTCHA_SECRET_KEY,
                    'response': recaptcha_response,
                    'remoteip': request.META.get('REMOTE_ADDR'),
                },
                timeout=10
            )

            captcha_result = captcha_response.json()

        except requests.RequestException:

            messages.error(
                request,
                'reCAPTCHA verification failed. Please try again.'
            )

            return redirect('shop_register')

        if not captcha_result.get('success'):

            messages.error(
                request,
                'reCAPTCHA verification failed. Please try again.'
            )

            return redirect('shop_register')

        #password code
        if password != confirmation:
            messages.error(request, 'Passwords do not match')
            return redirect('shop_register')

        if Customer.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('shop_register')

        Customer.objects.create(
            first_name=firstname,
            last_name=lastname,
            username=username,
            email=email,
            password=make_password(password),
            is_active=1,
        )

        messages.success(request, 'Registration successful.Please Login.')
        return redirect('shop_login')
    return render(request, 'shop/register.html',{
        'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY,
    })


def my_profile(request):
    customer_id = request.session.get('customer_id')

    if not customer_id:
        return redirect('shop_login')

    customer = get_object_or_404(Customer, id=customer_id)

    if request.method == 'POST':
        first_name = request.POST.get('first_name').strip()
        last_name = request.POST.get('last_name').strip()
        email = request.POST.get('email').strip()
        phone = request.POST.get('phone').strip()
        if not first_name:
            messages.error(request, "First name is required.")
            return redirect("my_profile")

        if not last_name:
            messages.error(request, "Last name is required.")
            return redirect("my_profile")

        if not email:
            messages.error(request, "Email address is required.")
            return redirect("my_profile")

        if not phone:
            messages.error(request, "Phone number is required.")
            return redirect("my_profile")

        email_exists = Customer.objects.filter(
            email=email
        ).exclude(
            id=customer.id
        ).exists()

        if email_exists:
            messages.error(
                request,
                "This email address is already registered."
            )
            return redirect("my_profile")

        customer.first_name = first_name
        customer.last_name = last_name
        customer.email = email
        customer.phone = phone
        customer.save()

        request.session['customer_name'] = (
            f"{customer.first_name} {customer.last_name}"
        ).strip()

        request.session['customer_email'] = customer.email
        request.session['customer_id'] = customer.id

        messages.success(
            request,
            "Profile Update Successfully."
        )
        return redirect("my_profile")

    return render(request, 'shop/my_profile.html',{
        'customer': customer,
    })


def shop_logout(request):
    request.session.flush()
    return redirect("shop_login")


def logout_view(request):
    logout(request)
    return redirect('login')


def shop_about(request):
    return render(request, 'shop/about.html')


def shop_categories(request):
    categories = Category.objects.all()
    return render(request, 'shop/categories.html', {'categories': categories})


def shop_deals(request):
    deal_products = Product.objects.all()
    return render(request, 'shop/deals.html', {'deal_products': deal_products})
