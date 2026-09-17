import json
from .models import Cart


def cart_context(request):
    cart_count = 0

    customer_id = request.session.get("customer_id")

    if customer_id:

        try:
            cart = Cart.objects.get(
                customer_id=customer_id
            )

            cart_count = sum(
                item.quantity
                for item in cart.items.all()
            )

        except Cart.DoesNotExist:
            cart_count = 0

    else:
        cookie_cart = request.COOKIES.get("guest_cart")
        if cookie_cart:
            try:
                guest_cart = json.loads(cookie_cart)

                if isinstance(guest_cart, dict):
                    cart_count = sum(
                        int(quantity)
                        for quantity in guest_cart.values()
                    )
            except (json.JSONDecodeError, TypeError, ValueError):
                cart_count = 0
    return {
        "cart_count": cart_count
    }