from .cart import Cart

def cart_context(request):
    """Context processor making the live Cart instance available in all templates."""
    return {'cart': Cart(request)}
