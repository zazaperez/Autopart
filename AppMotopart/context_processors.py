from .models import Carrito, Categoria


def carrito_contador(request):
    """Inyecta el conteo del carrito Y las categorías en todos los templates."""
    count = 0
    if request.user.is_authenticated:
        try:
            count = request.user.carrito.cantidad_items()
        except Carrito.DoesNotExist:
            pass

    categorias_nav = Categoria.objects.filter(activo=True)[:10]

    return {
        "carrito_count": count,
        "categorias_nav": categorias_nav,
    }
