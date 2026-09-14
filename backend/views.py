from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.text import slugify
from .models import Category, Product
from pages.models import Customer, Order, OrderItem
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password


def admin_login(request):
    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        if not email or not password:
            messages.warning(
                request,
                "Please enter email and password."
            )

            return render(request, "admin_login.html")

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)

            messages.success(
                request,
                "Login successful! Welcome back."
            )

            return redirect("dashboard")

        else:

            messages.error(
                request,
                "Invalid email or password."
            )

            return render(request, "admin_login.html")

    return render(request, "admin_login.html")


@login_required
def dashboard(request):
    return render(request, "dashboard.html")


@login_required
def categories(request):
    allCategories = Category.objects.all()
    return render(request, "categories.html", {"categories": allCategories})


@login_required
def category_create(request):
    if request.method == "POST":
        name = request.POST.get("name")
        slug = slugify(name)
        parent_id = request.POST.get("parent_category_id")
        if not parent_id:
            parent_id = None
        image = request.FILES.get('image')
        description = request.POST.get("description")
        is_active = request.POST.get("status")

        Category.objects.create(name=name, slug=slug, parent_category_id=parent_id, description=description,
                                image=image, is_active=is_active)

        messages.success(
            request,
            "Category created successfully."
        )
        return redirect("categories")
    return render(request, "categiries.html")


@login_required
def category_update(request, id):
    category = get_object_or_404(Category, id=id)

    if request.method == "POST":
        category.name = request.POST.get("name")
        category.slug = slugify(category.name)
        category.parent_category_id = None
        category.description = request.POST.get("description")
        if request.FILES.get('image'):
            category.image = request.FILES.get('image')
        category.is_active = request.POST.get("status")
        category.save()

        return redirect("categories")

    allCategories = Category.objects.exclude(id=id)

    return render(request, "category_update.html", {
        "category": category,
        "categories": allCategories
    })


@login_required
def category_delete(request, id):
    category = get_object_or_404(Category, id=id)

    if request.method == "POST":
        category.delete()
        return JsonResponse({"success": True, "message": "Category deleted successfully."})
    return JsonResponse({"success": False}, status=400)


@login_required
def products(request):
    allProducts = Product.objects.select_related('category').all()
    allCategories = Category.objects.filter(is_active=True)
    return render(request, "products.html", {
        "products": allProducts,
        "allCategories": allCategories
    })


@login_required
def product_create(request):
    if request.method == "POST":
        name = request.POST.get("name")
        slug = slugify(name)
        category_id = request.POST.get("category_id")
        description = request.POST.get("description")
        price = request.POST.get("price")
        stock = request.POST.get("stock")
        image = request.FILES.get('image')
        is_active = request.POST.get("status")

        category = get_object_or_404(Category, id=category_id)

        Product.objects.create(name=name, slug=slug, category=category, description=description, price=price,
                               stock=stock, image=image, is_active=is_active)

        messages.success(
            request,
            "Product created successfully."
        )
        return redirect("products")
    return render(request, "product_create.html")


@login_required
def product_update(request, id):
    product = get_object_or_404(Product, id=id)

    if request.method == "POST":

        product.name = request.POST.get("name")
        product.slug = slugify(product.name)

        category_id = request.POST.get("category_id")
        product.category = get_object_or_404(
            Category,
            id=category_id
        )

        product.description = request.POST.get("description")
        product.price = request.POST.get("price")
        product.stock = request.POST.get("stock")

        # New image hai tabhi image update karo
        if request.FILES.get("image"):
            product.image = request.FILES.get("image")

        product.is_active = request.POST.get("status") == "1"

        product.save()

        messages.success(
            request,
            "Product updated successfully."
        )

        return redirect("products")

    return render(request, "product_update.html", {
        "product": product
    })


@login_required
def product_delete(request, id):
    product = get_object_or_404(Product, id=id)

    if request.method == "POST":
        product.delete()

        return JsonResponse({
            "success": True,
            "message": "Product deleted successfully."
        })

    return JsonResponse({
        "success": False,
        "message": "Invalid request."
    })


def customers(request):
    allCustomers = Customer.objects.all()
    return render(request, "customers.html", {
        "customers": allCustomers
    })


def customer_create(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        password = make_password(request.POST.get("password"))
        address = request.POST.get("address")
        city = request.POST.get("city")
        state = request.POST.get("state")
        pincode = request.POST.get("pincode")
        country = request.POST.get("country")
        is_active = request.POST.get("status")

        Customer.objects.create(first_name=first_name, last_name=last_name, username=username, email=email or None,
                                phone=phone or None,
                                password=password or None,
                                address=address or None,
                                city=city or None,
                                state=state or None,
                                pincode=pincode or None,
                                country=country or None,
                                is_active=True if is_active == "1" else False)
        messages.success(
            request,
            "Customer created successfully."
        )

        return redirect("customers")

    return render(request, "customer_create.html")


def customer_update(request, id):
    customer = get_object_or_404(Customer, id=id)

    if request.method == "POST":

        customer.first_name = request.POST.get("first_name")
        customer.last_name = request.POST.get("last_name")
        customer.username = request.POST.get("username")
        customer.email = request.POST.get("email")
        customer.phone = request.POST.get("phone")

        password = make_password(request.POST.get("password"))
        if password:
            customer.password = password

        customer.address = request.POST.get("address") or None
        customer.city = request.POST.get("city") or None
        customer.state = request.POST.get("state") or None
        customer.pincode = request.POST.get("pincode") or None
        customer.country = request.POST.get("country") or None

        customer.is_active = request.POST.get("status") or None

        customer.save()

        messages.success(
            request,
            "Customer updated successfully."
        )
        return redirect("customers")
    return render(request, "customer_update.html", {
        "customer": customer
    })


def customer_delete(request, id):
    customer = get_object_or_404(Customer, id=id)

    if request.method == "POST":
        customer.delete()

        return JsonResponse({
            "success": True,
            "message": "Customer deleted successfully."
        })

    return JsonResponse({
        "success": False,
        "message": "Invalid request."
    })

def orders(request):
    allOrders = Order.objects.select_related("customer").order_by("-created_at")
    return render(request, "orders.html", {
        "orders": allOrders
    })

def order_detail(request,id):
    order = get_object_or_404(Order.objects.select_related('customer'), id=id)

    order_items = OrderItem.objects.filter(order_id=order.id).order_by("id")

    return render(request, "order_detail.html", {
        "order": order,
        "order_items": order_items
    })

def admin_logout(request):
    logout(request)
    return redirect("login")
