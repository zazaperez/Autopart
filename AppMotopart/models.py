"""
MOTOPART - Models
Todos los modelos del sistema en un solo archivo.
"""

from decimal import ROUND_HALF_UP, Decimal

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

# ============================================================
# 0. IVA — Colombia
# ============================================================
# Tarifa general de IVA en Colombia. Los precios de los productos
# se ingresan SIEMPRE como precio final (ya incluyen este IVA).
# El sistema desglosa el valor del IVA automáticamente para
# mostrarlo en el carrito, el checkout y la factura/comprobante.
IVA_TASA = Decimal("0.19")
DOS_DECIMALES = Decimal("0.01")


def _redondear(valor):
    return Decimal(valor).quantize(DOS_DECIMALES, rounding=ROUND_HALF_UP)


def desglosar_iva(precio_final):
    """A partir de un precio final (con IVA incluido) devuelve
    (precio_sin_iva, valor_iva), ambos redondeados a 2 decimales."""
    precio_final = Decimal(precio_final)
    precio_sin_iva = _redondear(precio_final / (1 + IVA_TASA))
    valor_iva = precio_final - precio_sin_iva
    return precio_sin_iva, valor_iva


# ============================================================
# 1. PERFIL DE USUARIO (extiende User de Django)
# ============================================================


class Perfil(models.Model):

    ROL_ADMIN = "A"
    ROL_CLIENTE = "C"
    ROLES = [
        (ROL_ADMIN, "Administrador"),
        (ROL_CLIENTE, "Cliente"),
    ]

    usuario = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="perfil"
    )
    rol = models.CharField(max_length=1, choices=ROLES, default=ROL_CLIENTE)
    documento = models.CharField(max_length=20, blank=True, unique=True, null=True)
    telefono = models.CharField(max_length=20, blank=True)
    direccion = models.TextField(blank=True)
    departamento = models.CharField(max_length=100, blank=True)  # ← LÍNEA NUEVA
    ciudad = models.CharField(max_length=100, blank=True)
    foto = models.ImageField(upload_to="perfiles/", blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "perfil"
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"

    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.username} ({self.get_rol_display()})"

    def es_admin(self):
        return self.rol == self.ROL_ADMIN


# ============================================================
# 2. VEHÍCULOS
# ============================================================


class MarcaVehiculo(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "marca_vehiculo"
        verbose_name = "Marca de Vehículo"
        verbose_name_plural = "Marcas de Vehículos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class ModeloVehiculo(models.Model):
    marca = models.ForeignKey(
        MarcaVehiculo, on_delete=models.CASCADE, related_name="modelos"
    )
    nombre = models.CharField(max_length=100)

    class Meta:
        db_table = "modelo_vehiculo"
        verbose_name = "Modelo de Vehículo"
        verbose_name_plural = "Modelos de Vehículos"
        unique_together = ("marca", "nombre")
        ordering = ["marca", "nombre"]

    def __str__(self):
        return f"{self.marca} {self.nombre}"


class Vehiculo(models.Model):
    COMBUSTIBLE_CHOICES = [
        ("gasolina", "Gasolina"),
        ("diesel", "Diésel"),
        ("hibrido", "Híbrido"),
        ("electrico", "Eléctrico"),
        ("gas", "Gas"),
    ]

    modelo = models.ForeignKey(
        ModeloVehiculo, on_delete=models.CASCADE, related_name="vehiculos"
    )
    anio = models.PositiveIntegerField(verbose_name="Año")
    motor = models.CharField(max_length=50, blank=True)
    version = models.CharField(max_length=100, blank=True)
    combustible = models.CharField(
        max_length=20, choices=COMBUSTIBLE_CHOICES, blank=True
    )

    class Meta:
        db_table = "vehiculo"
        verbose_name = "Vehículo"
        verbose_name_plural = "Vehículos"
        ordering = ["modelo", "-anio"]

    def __str__(self):
        partes = [str(self.modelo), str(self.anio)]
        if self.version:
            partes.append(self.version)
        if self.motor:
            partes.append(self.motor)
        return " ".join(partes)


# ============================================================
# 3. CATÁLOGO DE PRODUCTOS
# ============================================================


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    icono = models.CharField(
        max_length=50, blank=True, help_text="Clase CSS del ícono, ej: fa-wrench"
    )
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "categoria"
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class MarcaProducto(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    logo = models.ImageField(upload_to="marcas/", blank=True, null=True)

    class Meta:
        db_table = "marca_producto"
        verbose_name = "Marca de Repuesto"
        verbose_name_plural = "Marcas de Repuestos"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True, verbose_name="Código SKU")
    categoria = models.ForeignKey(
        Categoria, on_delete=models.SET_NULL, null=True, related_name="productos"
    )
    marca = models.ForeignKey(
        MarcaProducto,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="productos",
    )
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)]
    )
    stock = models.PositiveIntegerField(default=0)
    stock_minimo = models.PositiveIntegerField(
        default=5, help_text="Alerta de bajo inventario"
    )
    imagen = models.ImageField(upload_to="productos/", blank=True, null=True)
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "producto"
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} ({self.sku})"

    def stock_bajo(self):
        return self.stock <= self.stock_minimo

    def precio_con_descuento(self):
        return self.precio

    def precio_sin_iva(self):
        """Precio antes de IVA, calculado a partir del precio final."""
        precio_sin_iva, _ = desglosar_iva(self.precio_con_descuento())
        return precio_sin_iva

    def valor_iva(self):
        """Valor del IVA (19%) contenido en el precio final."""
        _, valor_iva = desglosar_iva(self.precio_con_descuento())
        return valor_iva


# ============================================================
# 4. COMPATIBILIDAD PRODUCTO ↔ VEHÍCULO
# ============================================================


class Compatibilidad(models.Model):
    producto = models.ForeignKey(
        Producto, on_delete=models.CASCADE, related_name="compatibilidades"
    )
    vehiculo = models.ForeignKey(
        Vehiculo, on_delete=models.CASCADE, related_name="compatibilidades"
    )
    notas = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "compatibilidad"
        verbose_name = "Compatibilidad"
        verbose_name_plural = "Compatibilidades"
        unique_together = ("producto", "vehiculo")

    def __str__(self):
        return f"{self.producto.nombre} → {self.vehiculo}"


# ============================================================
# 5. PROVEEDORES
# ============================================================


class Proveedor(models.Model):
    nombre = models.CharField(max_length=150)
    contacto = models.CharField(
        max_length=100, blank=True, verbose_name="Persona de contacto"
    )
    telefono = models.CharField(max_length=20, blank=True)
    correo = models.EmailField(blank=True)
    direccion = models.TextField(blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    nit = models.CharField(max_length=30, blank=True, verbose_name="NIT / RUC")
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "proveedor"
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


# ============================================================
# 6. INVENTARIO — MOVIMIENTOS
# ============================================================


class Movimiento(models.Model):
    ENTRADA = "E"
    SALIDA = "S"
    AJUSTE = "A"
    COMPRA = "C"
    TIPOS = [
        (ENTRADA, "Entrada"),
        (SALIDA, "Salida por venta"),
        (AJUSTE, "Ajuste manual"),
        (COMPRA, "Compra a proveedor"),
    ]

    producto = models.ForeignKey(
        Producto, on_delete=models.CASCADE, related_name="movimientos"
    )
    tipo = models.CharField(max_length=1, choices=TIPOS)
    cantidad = models.IntegerField(help_text="Positivo=entrada, Negativo=salida")
    proveedor = models.ForeignKey(
        Proveedor, on_delete=models.SET_NULL, null=True, blank=True
    )
    referencia = models.CharField(
        max_length=100, blank=True, help_text="Nro. factura, pedido, etc."
    )
    notas = models.TextField(blank=True)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "movimiento"
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.get_tipo_display()} | {self.producto.nombre} | {self.cantidad}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Actualizar stock del producto automáticamente
        self.producto.stock = max(0, self.producto.stock + self.cantidad)
        self.producto.save(update_fields=["stock"])


# ============================================================
# 7. CARRITO DE COMPRAS
# ============================================================


class Carrito(models.Model):
    usuario = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="carrito"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "carrito"
        verbose_name = "Carrito"
        verbose_name_plural = "Carritos"

    def __str__(self):
        return f"Carrito de {self.usuario.username}"

    def total(self):
        return sum(item.subtotal() for item in self.items.all())

    def cantidad_items(self):
        return sum(item.cantidad for item in self.items.all())

    def subtotal_sin_iva(self):
        return sum(item.subtotal_sin_iva() for item in self.items.all())

    def valor_iva(self):
        return self.total() - self.subtotal_sin_iva()


class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "item_carrito"
        verbose_name = "Ítem del Carrito"
        verbose_name_plural = "Ítems del Carrito"
        unique_together = ("carrito", "producto")

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre}"

    def subtotal(self):
        return self.producto.precio_con_descuento() * self.cantidad

    def subtotal_sin_iva(self):
        return self.producto.precio_sin_iva() * self.cantidad


# ============================================================
# 8. PEDIDOS
# ============================================================


class Pedido(models.Model):
    PENDIENTE = "pendiente"
    CONFIRMADO = "confirmado"
    PREPARANDO = "preparando"
    ENVIADO = "enviado"
    ENTREGADO = "entregado"
    CANCELADO = "cancelado"
    ESTADOS = [
        (PENDIENTE, "Pendiente"),
        (CONFIRMADO, "Confirmado"),
        (PREPARANDO, "Preparando"),
        (ENVIADO, "Enviado"),
        (ENTREGADO, "Entregado"),
        (CANCELADO, "Cancelado"),
    ]

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pedidos")
    estado = models.CharField(max_length=15, choices=ESTADOS, default=PENDIENTE)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    direccion_envio = models.TextField(blank=True)
    notas = models.TextField(blank=True)
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "pedido"
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ["-fecha_pedido"]

    def __str__(self):
        return f"Pedido #{self.pk} — {self.usuario.username}"

    def calcular_total(self):
        self.total = sum(d.subtotal() for d in self.detalles.all())
        self.save(update_fields=["total"])

    def subtotal_sin_iva(self):
        return sum(d.subtotal_sin_iva() for d in self.detalles.all())

    def valor_iva(self):
        return self.total - self.subtotal_sin_iva()


class DetallePedido(models.Model):
    pedido = models.ForeignKey(
        Pedido, on_delete=models.CASCADE, related_name="detalles"
    )
    producto = models.ForeignKey(Producto, on_delete=models.SET_NULL, null=True)
    nombre_producto = models.CharField(
        max_length=200
    )  # snapshot por si se elimina el producto
    sku_producto = models.CharField(max_length=50, blank=True)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "detalle_pedido"
        verbose_name = "Detalle de Pedido"
        verbose_name_plural = "Detalles de Pedido"

    def __str__(self):
        return f"{self.cantidad}x {self.nombre_producto}"

    def subtotal(self):
        return self.precio_unitario * self.cantidad

    def precio_unitario_sin_iva(self):
        precio_sin_iva, _ = desglosar_iva(self.precio_unitario)
        return precio_sin_iva

    def subtotal_sin_iva(self):
        return self.precio_unitario_sin_iva() * self.cantidad

    def valor_iva(self):
        return self.subtotal() - self.subtotal_sin_iva()


# ============================================================
# 9. PAGOS
# ============================================================


class Pago(models.Model):
    TRANSFERENCIA = "transferencia"
    TARJETA = "tarjeta"
    EFECTIVO = "efectivo"
    CONTRA_ENTREGA = "contra_entrega"
    METODOS = [
        (TRANSFERENCIA, "Transferencia bancaria"),
        (TARJETA, "Tarjeta débito/crédito"),
        (EFECTIVO, "Efectivo"),
        (CONTRA_ENTREGA, "Contra entrega"),
    ]

    PENDIENTE = "pendiente"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"
    ESTADOS_PAGO = [
        (PENDIENTE, "Pendiente"),
        (APROBADO, "Aprobado"),
        (RECHAZADO, "Rechazado"),
    ]

    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE, related_name="pago")
    metodo = models.CharField(max_length=20, choices=METODOS)
    estado = models.CharField(max_length=15, choices=ESTADOS_PAGO, default=PENDIENTE)
    comprobante = models.ImageField(upload_to="comprobantes/", blank=True, null=True)
    referencia = models.CharField(
        max_length=100, blank=True, help_text="Nro. transacción / recibo"
    )
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "pago"
        verbose_name = "Pago"
        verbose_name_plural = "Pagos"

    def __str__(self):
        return f"Pago #{self.pedido.pk} — {self.get_metodo_display()}"
