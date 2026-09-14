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

    return {
        "cart_count": cart_count
    }