from django.contrib import admin

from .models import (
    Carrito,
    Categoria,
    Compatibilidad,
    DetallePedido,
    ItemCarrito,
    MarcaProducto,
    MarcaVehiculo,
    ModeloVehiculo,
    Movimiento,
    Pago,
    Pedido,
    Perfil,
    Producto,
    Proveedor,
    Vehiculo,
)


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'rol', 'telefono', 'ciudad', 'fecha_creacion')
    list_filter = ('rol',)
    search_fields = ('usuario__username', 'usuario__email')


@admin.register(MarcaVehiculo)
class MarcaVehiculoAdmin(admin.ModelAdmin):
    search_fields = ('nombre',)


@admin.register(ModeloVehiculo)
class ModeloVehiculoAdmin(admin.ModelAdmin):
    list_display = ('marca', 'nombre')
    list_filter = ('marca',)
    search_fields = ('nombre',)


@admin.register(Vehiculo)
class VehiculoAdmin(admin.ModelAdmin):
    list_display = ('modelo', 'anio', 'motor', 'version', 'combustible')
    list_filter = ('modelo__marca', 'combustible', 'anio')
    search_fields = ('modelo__nombre',)


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre',)


@admin.register(MarcaProducto)
class MarcaProductoAdmin(admin.ModelAdmin):
    search_fields = ('nombre',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('sku', 'nombre', 'categoria', 'marca', 'precio', 'stock', 'stock_bajo', 'activo')
    list_filter = ('categoria', 'marca', 'activo')
    search_fields = ('sku', 'nombre')
    list_per_page = 25

    @admin.display(boolean=True, description='Stock bajo')
    def stock_bajo(self, obj):
        return obj.stock_bajo()


@admin.register(Compatibilidad)
class CompatibilidadAdmin(admin.ModelAdmin):
    list_display = ('producto', 'vehiculo', 'notas')
    search_fields = ('producto__nombre', 'vehiculo__modelo__nombre')
    autocomplete_fields = ['producto', 'vehiculo']


@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'contacto', 'telefono', 'correo', 'ciudad', 'activo')
    list_filter = ('activo',)
    search_fields = ('nombre', 'nit', 'correo')


@admin.register(Movimiento)
class MovimientoAdmin(admin.ModelAdmin):
    list_display = ('producto', 'tipo', 'cantidad', 'proveedor', 'referencia', 'usuario', 'fecha')
    list_filter = ('tipo', 'fecha')
    search_fields = ('producto__nombre', 'producto__sku', 'referencia')
    date_hierarchy = 'fecha'
    autocomplete_fields = ['producto']


class ItemCarritoInline(admin.TabularInline):
    model = ItemCarrito
    extra = 0
    readonly_fields = ('subtotal',)

    @admin.display(description='Subtotal')
    def subtotal(self, obj):
        return obj.subtotal()


@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'cantidad_items', 'total', 'fecha_actualizacion')
    search_fields = ('usuario__username',)
    inlines = [ItemCarritoInline]


class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0
    readonly_fields = ('subtotal',)

    @admin.display(description='Subtotal')
    def subtotal(self, obj):
        return obj.subtotal()


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'estado', 'total', 'fecha_pedido')
    list_filter = ('estado', 'fecha_pedido')
    search_fields = ('usuario__username', 'id')
    date_hierarchy = 'fecha_pedido'
    inlines = [DetallePedidoInline]


@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ('pedido', 'metodo', 'estado', 'referencia', 'fecha')
    list_filter = ('metodo', 'estado')
    search_fields = ('pedido__id', 'referencia')


