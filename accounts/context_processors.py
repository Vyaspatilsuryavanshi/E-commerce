from .models import Wishlist


def account_context(request):
    if not request.user.is_authenticated:
        return {"wishlist_count": 0}
    return {"wishlist_count": Wishlist.objects.filter(user=request.user).count()}
