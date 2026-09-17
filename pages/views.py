from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from .models import Service, Customer, Cart, CartItem, Order, OrderItem
from backend.models import Category, Product
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.hashers import make_password, check_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.urls import reverse
from decimal import Decimal
import requests
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
import secrets
import json


class CustomerPasswordResetTokenGenerator(PasswordResetTokenGenerator):
    pass


customer_password_reset_token = CustomerPasswordResetTokenGenerator()


# Create your views here.

def pages(request):
    return HttpResponse("Hello World")


# create HTML function with renader
def home(request):
    return render(request, "home.html")


def about(request):
    return render(request, "about.html")


def services(request):
    allServices = Service.objects.all()
    return render(request, 'services.html', {'allServices': allServices})


def details(request, id):
    myService = Service.objects.get(id=id)
    return render(request, 'details.html', {'myService': myService})


def contact(request):
    return render(request, 'contact.html')


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
    return render(request, 'login.html')


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
    return render(request, 'register.html')


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

    return render(request, 'employee_profile.html', {
        'user': user
    })


@login_required
def all_users(request):
    all_user = User.objects.all()
    return render(request, 'all_users.html', {'all_users': all_user})


def shop_home(request):
    Categories = Category.objects.filter(is_active=True)
    Products = Product.objects.filter(is_active=True).select_related('category')
    return render(request, 'shop/home.html', {
        'categories': Categories,
        'products': Products
    })


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
    if request.method != "POST":
        return redirect("shop_details", slug=slug)

    # Product
    product = get_object_or_404(Product, slug=slug, is_active=True)

    # Quantity
    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1

    if quantity < 1:
        quantity = 1

    if product.stock <= 0:
        messages.error(
            request,
            f"{product.name} is currently out of stock."
        )
        return redirect("shop_details", slug=slug)

    customer_id = request.session.get("customer_id")

    if customer_id:
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
            if quantity > product.stock:
                messages.error(
                    request,
                    f"Only {product.stock} items available."
                )
                return redirect("shop_details", slug=slug)

            cart_item.quantity = quantity
        else:
            new_quantity = (cart_item.quantity + quantity)

            if new_quantity > product.stock:
                messages.error(
                    request,
                    f"Only {product.stock} items available."
                )
                return redirect("shop_details", slug=slug)
            cart_item.quantity = new_quantity

        cart_item.save(update_fields=["quantity"])

        messages.success(
            request,
            f"{product.name} added to cart."
        )
        return redirect("shop_details", slug=product.slug)
    else:
        cookie_cart = request.COOKIES.get("guest_cart")

        if cookie_cart:
            try:
                guest_cart = json.loads(cookie_cart)

                if not isinstance(guest_cart, dict):
                    guest_cart = {}
            except (json.JSONDecodeError, TypeError, ValueError):
                guest_cart = {}
        else:
            guest_cart = {}

        product_id = str(product.id)

        current_quantity = int(guest_cart.get(product_id, 0))

        new_quantity = (
                current_quantity + quantity
        )

        if new_quantity > product.stock:
            messages.error(
                request,
                f"Only {product.stock} items available."
            )
            return redirect("shop_details", slug=product.slug)

        guest_cart[product_id] = new_quantity

        response = redirect('shop_details', slug=product.slug)

        response.set_cookie(
            key='guest_cart',
            value=json.dumps(guest_cart),
            max_age=60 * 60 * 24 * 30,
            httponly=True,
            samesite='Lax',
            secure=False,
        )
        messages.success(
            request,
            f"{product.name} added to cart."
        )
        return response


def cart_list(request):
    customer_id = request.session.get("customer_id")

    # =========================================================
    # LOGGED-IN CUSTOMER CART
    # =========================================================

    if customer_id:

        customer = get_object_or_404(
            Customer,
            id=customer_id
        )

        cart, created = Cart.objects.get_or_create(
            customer=customer
        )

        cart_items = cart.items.select_related(
            "product",
            "product__category"
        )

        subtotal = Decimal("0.00")

        for item in cart_items:
            item.item_total = (
                    item.product.price * item.quantity
            )

            subtotal += item.item_total

        delivery = Decimal("0.00")

        total = subtotal + delivery

        context = {
            "cart": cart,
            "cart_items": cart_items,
            "subtotal": subtotal,
            "delivery": delivery,
            "total": total,
            "is_guest": False,
        }

        return render(
            request,
            "shop/cart.html",
            context
        )

    # =========================================================
    # GUEST CART - COOKIE
    # =========================================================

    cookie_cart = request.COOKIES.get("guest_cart")

    guest_cart = {}

    if cookie_cart:

        try:

            guest_cart = json.loads(cookie_cart)

            if not isinstance(guest_cart, dict):
                guest_cart = {}

        except (
                json.JSONDecodeError,
                TypeError,
                ValueError
        ):

            guest_cart = {}

    # Cart items
    cart_items = []

    subtotal = Decimal("0.00")

    # =========================================================
    # GET PRODUCTS FROM COOKIE
    # =========================================================

    for product_id, quantity in guest_cart.items():

        try:

            product = Product.objects.select_related(
                "category"
            ).get(
                id=product_id,
                is_active=True
            )

        except Product.DoesNotExist:

            continue

        # Safe quantity conversion
        try:

            quantity = int(quantity)

        except (
                TypeError,
                ValueError
        ):

            continue

        # Quantity validation
        if quantity <= 0:
            continue

        # Stock validation
        if quantity > product.stock:
            quantity = product.stock

        # If product is out of stock
        if quantity <= 0:
            continue

        # Item total
        item_total = (
                product.price * quantity
        )

        cart_items.append({
            "product": product,
            "quantity": quantity,
            "item_total": item_total,
        })

        subtotal += item_total

    # =========================================================
    # SUMMARY
    # =========================================================

    delivery = Decimal("0.00")

    total = subtotal + delivery

    context = {
        "cart": None,
        "cart_items": cart_items,
        "subtotal": subtotal,
        "delivery": delivery,
        "total": total,
        "is_guest": True,
    }

    return render(
        request,
        "shop/cart.html",
        context
    )


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


def guest_cart_update(request, product_id):
    if request.method != "POST":
        return redirect("cart_list")

    try:
        quantity = int(request.POST.get("quantity", 1))
    except (TypeError, ValueError):
        quantity = 1

    product = get_object_or_404(
        Product,
        id=product_id,
        is_active=True
    )

    # Stock validation
    if quantity > product.stock:
        quantity = product.stock

    if quantity < 1:
        quantity = 1

    # Get cookie cart
    cookie_cart = request.COOKIES.get("guest_cart")

    guest_cart = {}

    if cookie_cart:
        try:
            guest_cart = json.loads(cookie_cart)

            if not isinstance(guest_cart, dict):
                guest_cart = {}

        except (json.JSONDecodeError, TypeError, ValueError):
            guest_cart = {}

    # Update quantity
    guest_cart[str(product_id)] = quantity

    response = redirect("cart_list")

    response.set_cookie(
        key="guest_cart",
        value=json.dumps(guest_cart),
        max_age=60 * 60 * 24 * 30,
        httponly=True,
        samesite="Lax",
        secure=False,
    )

    return response


def guest_cart_remove(request, product_id):
    if request.method != "POST":
        return redirect("cart_list")

    cookie_cart = request.COOKIES.get("guest_cart")

    guest_cart = {}

    if cookie_cart:
        try:
            guest_cart = json.loads(cookie_cart)

            if not isinstance(guest_cart, dict):
                guest_cart = {}

        except (json.JSONDecodeError, TypeError, ValueError):
            guest_cart = {}

    # Remove product
    guest_cart.pop(str(product_id), None)

    response = redirect("cart_list")

    if guest_cart:
        response.set_cookie(
            key="guest_cart",
            value=json.dumps(guest_cart),
            max_age=60 * 60 * 24 * 30,
            httponly=True,
            samesite="Lax",
            secure=False,
        )
    else:
        response.delete_cookie("guest_cart")

    return response


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

        transaction.on_commit(
            lambda: send_order_confirmation_email(order)
        )

        messages.success(
            request,
            f"Order {order.order_number} Place Successfully."
        )
    return redirect('checkout_success', order_number=order.order_number)


def checkout_success(request, order_number):
    customer_id = request.session.get("customer_id")

    if not customer_id:
        return redirect("shop_login")

    order = get_object_or_404(Order.objects.prefetch_related('items'), order_number=order_number,
                              customer_id=customer_id)

    return render(request, 'shop/order_success.html', {
        "order": order
    })


def my_orders(request):
    customer_id = request.session.get("customer_id")
    if not customer_id:
        return redirect("shop_login")

    myOrders = Order.objects.filter(customer_id=customer_id).prefetch_related('items').order_by('-created_at')
    return render(request, 'shop/my_orders.html', {
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
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')

        # reCapTCHA
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

        # customer login
        try:
            customer = Customer.objects.get(email__iexact=email)

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

            guest_cart_exists = request.COOKIES.get('guest_cart')

            merge_guest_cart(request, customer)

            response = redirect('shop_home')

            if guest_cart_exists:
                response.delete_cookie('guest_cart')

            messages.success(
                request,
                'Login Successfully.'
            )
            return response

        else:
            messages.error(request, 'Invalid email or password')
            return redirect('shop_login')

    return render(request, 'shop/login.html', {
        'recaptcha_site_key': settings.RECAPTCHA_SITE_KEY,
    })


def shop_register(request):
    if request.method == 'POST':
        firstname = request.POST.get('first_name', '').strip()
        lastname = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirmation = request.POST.get('confirm_password', '')

        # reCaptcha

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

        # password code
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
    return render(request, 'shop/register.html', {
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

    return render(request, 'shop/my_profile.html', {
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


def shop_contact(request):
    return render(request, 'shop/contact.html')


def shop_categories(request):
    categories = Category.objects.all()
    return render(request, 'shop/categories.html', {'categories': categories})


def shop_deals(request):
    deal_products = Product.objects.all()
    return render(request, 'shop/deals.html', {'deal_products': deal_products})


def forgot_password(request):
    email = request.GET.get('email', '').strip()

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()

        if not email:
            messages.error(request, 'Please enter your email address.')
            return render(request, 'shop/forgot_password.html', {
                "email": email,
            })

        try:
            customer = Customer.objects.get(email__iexact=email)
        except Customer.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
            return render(request, 'shop/forgot_password.html', {
                "email": email,
            })

        # generate token
        token = secrets.token_urlsafe(32)
        customer.reset_token = token
        customer.reset_token_created_at = timezone.now()
        customer.reset_token_used = False
        customer.save(update_fields=['reset_token', 'reset_token_created_at', 'reset_token_used'])
        uid = urlsafe_base64_encode(force_bytes(customer.pk))
        # token = customer_password_reset_token.make_token(customer)

        reset_url = request.build_absolute_uri(
            reverse(
                'reset_password',
                kwargs={
                    "uidb64": uid,
                    "token": token,
                }
            )
        )

        subject = "Reset Your Nova Cart Password"

        context = {
            "customer": customer,
            "reset_url": reset_url,
        }

        html_message = render_to_string(
            'shop/email/reset_password.html',
            context
        )

        text_message = f"""
Hello {customer.first_name},

We received a request to reset your Nova Cart password.

Click the link below to reset your password:

{reset_url}

If you did not request this password reset,
you can safely ignore this email.

Thank you,
Nova Cart
"""

        email_message = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[customer.email],
        )

        email_message.attach_alternative(html_message, "text/html")
        email_message.send(fail_silently=False)
        messages.success(
            request,
            "Password reset link has been sent to your email."
        )
        return redirect('forgot_password')
    return render(request, 'shop/forgot_password.html', {
        "email": email,
    })


def reset_password(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(
            uidb64
        ).decode()

        customer = Customer.objects.get(
            pk=uid
        )

    except (
            TypeError,
            ValueError,
            OverflowError,
            Customer.DoesNotExist
    ):
        customer = None

    if customer is None:
        messages.error(
            request,
            "This password reset link is invalid."
        )

        return redirect("forgot_password")

    # Verify token
    if not customer.reset_token:
        messages.error(
            request,
            "This password reset link has expired or is invalid."
        )

        return redirect("forgot_password")

    if customer.reset_token != token:
        messages.error(
            request,
            "This password reset link has expired or is invalid."
        )

        return redirect("forgot_password")

    if not customer.reset_token_created_at:
        messages.error(
            request,
            "This password reset link is invalid."
        )
        return redirect("forgot_password")

    expiry_time = customer.reset_token_created_at + timedelta(minutes=15)

    if timezone.now() > expiry_time:
        customer.reset_token = None
        custpmer.reset_token_created_at = None
        customer.reset_token_used = True

        customer.save(update_fields=['reset_token', 'reset_token_created_at', 'reset_token_used'])

        messages.error(
            request,
            "This password reset link has expired."
        )

        return redirect('forgot_password')

    if request.method == 'GET':
        customer.reset_token_used = True
        customer.save(update_fields=['reset_token_used'])

        request.session['password_reset_customer_id'] = customer.id

        request.session['password_reset_verified'] = True

        return render(request, 'shop/reset_password.html')

    if request.method == "POST":

        session_customer_id = request.session.get(
            'password_reset_customer_id'
        )

        reset_verified = request.session.get(
            'password_reset_verified'
        )

        if (
                not reset_verified
                or session_customer_id != customer.id
        ):
            messages.error(
                request,
                "Your password reset session is invalid."
            )

            return redirect(
                "forgot_password"
            )

        new_password = request.POST.get(
            "new_password",
            ""
        )

        confirm_password = request.POST.get(
            "confirm_password",
            ""
        )

        if not new_password:
            messages.error(
                request,
                "Please enter your new password."
            )

            return render(
                request,
                "shop/reset_password.html"
            )

        if len(new_password) < 8:
            messages.error(
                request,
                "Password must be at least 8 characters."
            )

            return render(
                request,
                "shop/reset_password.html"
            )

        if new_password != confirm_password:
            messages.error(
                request,
                "Passwords do not match."
            )

            return render(
                request,
                "shop/reset_password.html"
            )

        # Update password
        customer.password = make_password(
            new_password
        )

        customer.reset_token = None

        customer.reset_token_created_at = None

        customer.reset_token_used = True

        customer.save(
            update_fields=["password", "reset_token", "reset_token_created_at", "reset_token_used"]
        )

        request.session.pop('password_reset_customer_id', None)
        request.session.pop('password_reset_verified', None)

        messages.success(
            request,
            "Password updated successfully. Please login."
        )

        return redirect("shop_login")

    return render(
        request,
        "shop/reset_password.html"
    )


def send_order_confirmation_email(order):
    subject = f"Order Confirmed - {order.order_number}"

    html_content = render_to_string(
        'shop/email/order_confirmation.html',
        {
            'order': order
        }
    )

    email = EmailMultiAlternatives(
        subject=subject,
        body=f"""
                Hello {order.first_name},
                
                Your order {order.order_number} has been successfully confirmed.
                
                Total Amount: ₹{order.total}
                
                Thank you for shopping with us.
                """,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[order.email],
    )
    email.attach_alternative(html_content, "text/html")

    email.send(fail_silently=False)


def merge_guest_cart(request, customer):
    cookie_cart = request.COOKIES.get('guest_cart')

    if not cookie_cart:
        return False

    try:
        guest_cart = json.loads(cookie_cart)

        if not isinstance(guest_cart, dict):
            return False
    except (json.decoder.JSONDecodeError, TypeError, ValueError):
        return False

    cart, created = Cart.objects.get_or_create(
        customer=customer
    )

    for product_id, guest_quantity in guest_cart.items():
        try:
            guest_quantity = int(guest_quantity)
        except (TypeError, ValueError):
            continue

        if guest_quantity <= 0:
            continue

        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            continue

        if product.stock <= 0:
            continue

        cart_item, item_created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
        )

        if item_created:
            cart_item.quantity = min(
                guest_quantity,
                product.stock
            )
        else:
            new_quantity = (
                    cart_item.quantity + guest_quantity
            )

            cart_item.quantity = min(
                new_quantity,
                product.stock
            )

        cart_item.save(
            update_fields=['quantity']
        )
    return True


def test_email(request):
    send_mail(
        subject='Django E-commerce Test Email',
        message='Hi my name dhruvish kahar i am working on django project now working test email sent successfully.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=["dhruvishkahar2109@gmail.com"],
        fail_silently=False,
    )
    return HttpResponse("Test email sent Successfully.")
