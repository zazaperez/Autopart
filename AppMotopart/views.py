# ============================================================
# AUTH
# ============================================================

import json

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .colombia_data import DEPARTAMENTOS_CIUDADES
from .models import (
    Carrito,
    Categoria,
    Compatibilidad,
    DetallePedido,
    ItemCarrito,
    Movimiento,
    Pago,
    Pedido,
    Perfil,
    Producto,
    Proveedor,
)


def vista_registro(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        email = request.POST.get("email", "").strip()
        password1 = request.POST.get("password1", "")
        password2 = request.POST.get("password2", "")
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()

        if password1 != password2:
            messages.error(request, "Las contraseñas no coinciden.")

        elif User.objects.filter(username=username).exists():
            messages.error(request, "El usuario ya existe.")

        elif User.objects.filter(email=email).exists():
            messages.error(request, "El correo ya está registrado.")

        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1,
                first_name=first_name,
                last_name=last_name,
            )

            # Perfil creado por signal
            perfil = user.perfil
            perfil.telefono = request.POST.get("telefono", "").strip()
            perfil.direccion = request.POST.get("direccion", "").strip()
            perfil.ciudad = request.POST.get("ciudad", "").strip()
            perfil.save()

            # Iniciar sesión automáticamente
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")

            messages.success(request, f"¡Bienvenido, {user.first_name or username}!")

            return redirect("catalogo")

    return render(request, "tienda/registro.html")


def vista_login(request):
    if request.user.is_authenticated:
        return redirect("catalogo")

    if request.method == "POST":
        email = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        try:
            usuario = User.objects.get(email__iexact=email)

            user = authenticate(request, username=usuario.username, password=password)

            if user:
                login(request, user)
                return redirect("catalogo")

        except User.DoesNotExist:
            pass

        messages.error(request, "Correo o contraseña incorrectos.")

    return render(request, "tienda/login.html")


def vista_logout(request):
    logout(request)
    return redirect("login")


# ============================================================
# CATÁLOGO
# ============================================================


def catalogo(request):
    productos = Producto.objects.filter(activo=True).select_related(
        "categoria", "marca"
    )

    # Filtros
    categoria_id = request.GET.get("categoria")
    busqueda = request.GET.get("q", "").strip()
    orden = request.GET.get("orden", "")

    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    if busqueda:
        productos = productos.filter(nombre__icontains=busqueda)
    if orden == "precio_asc":
        productos = productos.order_by("precio")
    elif orden == "precio_desc":
        productos = productos.order_by("-precio")
    elif orden == "nuevo":
        productos = productos.order_by("-fecha_creacion")

    categorias = Categoria.objects.filter(activo=True)
    context = {
        "productos": productos,
        "categorias": categorias,
        "categoria_activa": categoria_id,
        "busqueda": busqueda,
        "orden": orden,
    }
    return render(request, "tienda/index.html", context)


def detalle_producto(request, pk):
    producto = get_object_or_404(Producto, pk=pk, activo=True)
    compatibilidades = Compatibilidad.objects.filter(producto=producto).select_related(
        "vehiculo__modelo__marca"
    )
    relacionados = Producto.objects.filter(
        categoria=producto.categoria, activo=True
    ).exclude(pk=pk)[:4]

    context = {
        "producto": producto,
        "compatibilidades": compatibilidades,
        "relacionados": relacionados,
    }
    return render(request, "tienda/detalle.html", context)


from .models import Carrito, DetallePedido, ItemCarrito, Pago, Pedido, Producto


def _get_carrito(usuario):
    """Obtiene o crea el carrito del usuario logueado."""
    carrito, _ = Carrito.objects.get_or_create(usuario=usuario)
    return carrito


def _carrito_count(request):
    """Devuelve la cantidad de items en el carrito (para el badge del navbar).
    Úsala en un context_processor si quieres que carrito_count esté
    disponible en TODOS los templates automáticamente."""
    if request.user.is_authenticated:
        carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
        return carrito.cantidad_items()
    return 0


@login_required
def ver_carrito(request):
    carrito = _get_carrito(request.user)
    items = carrito.items.select_related(
        "producto", "producto__categoria", "producto__marca"
    ).all()
    return render(
        request,
        "tienda/carrito.html",
        {
            "carrito": carrito,
            "items": items,
        },
    )


@login_required
@require_POST
def agregar_carrito(request, producto_id):
    producto = get_object_or_404(Producto, pk=producto_id, activo=True)
    carrito = _get_carrito(request.user)

    cantidad = int(request.POST.get("cantidad", 1))
    if cantidad < 1:
        cantidad = 1

    item, creado = ItemCarrito.objects.get_or_create(
        carrito=carrito,
        producto=producto,
        defaults={"cantidad": cantidad},
    )
    if not creado:
        item.cantidad += cantidad

    # No permitir agregar más de lo que hay en stock
    if item.cantidad > producto.stock:
        item.cantidad = producto.stock
        messages.warning(
            request,
            f"Solo hay {producto.stock} unidades disponibles de {producto.nombre}.",
        )

    if item.cantidad <= 0:
        item.delete()
        messages.error(request, f"{producto.nombre} no tiene stock disponible.")
    else:
        item.save()
        messages.success(request, f"{producto.nombre} agregado al carrito.")

    siguiente = (
        request.POST.get("next") or request.META.get("HTTP_REFERER") or "catalogo"
    )
    return redirect(siguiente)


@login_required
@require_POST
def actualizar_carrito(request, item_id):
    """Actualiza la cantidad de un item del carrito desde un input numérico.
    Si cantidad <= 0, el item se elimina."""
    item = get_object_or_404(ItemCarrito, pk=item_id, carrito__usuario=request.user)

    try:
        nueva_cantidad = int(request.POST.get("cantidad", item.cantidad))
    except (TypeError, ValueError):
        nueva_cantidad = item.cantidad

    if nueva_cantidad <= 0:
        nombre = item.producto.nombre
        item.delete()
        messages.info(request, f"{nombre} fue eliminado del carrito.")
    else:
        if nueva_cantidad > item.producto.stock:
            nueva_cantidad = item.producto.stock
            messages.warning(
                request,
                f"Solo hay {item.producto.stock} unidades disponibles de {item.producto.nombre}.",
            )
        item.cantidad = nueva_cantidad
        item.save()

    return redirect("carrito")


@login_required
@require_POST
def eliminar_carrito(request, item_id):
    item = get_object_or_404(ItemCarrito, pk=item_id, carrito__usuario=request.user)
    nombre = item.producto.nombre
    item.delete()
    messages.info(request, f"{nombre} fue eliminado del carrito.")
    return redirect("carrito")


@login_required
@require_POST
def vaciar_carrito(request):
    carrito = _get_carrito(request.user)
    carrito.items.all().delete()
    messages.info(request, "Tu carrito fue vaciado.")
    return redirect("carrito")


# ════════════════════════════════════════════════════
# CHECKOUT — crea Pedido + DetallePedido + Pago
# ════════════════════════════════════════════════════


@login_required
def checkout(request):
    carrito = _get_carrito(request.user)
    items = list(carrito.items.select_related("producto").all())

    if not items:
        messages.warning(request, "Tu carrito está vacío.")
        return redirect("carrito")

    # Validación de stock ANTES de mostrar el formulario,
    # por si algo cambió desde que se agregó al carrito.
    sin_stock = [i for i in items if i.cantidad > i.producto.stock]
    if sin_stock:
        nombres = ", ".join(i.producto.nombre for i in sin_stock)
        messages.error(
            request,
            f"Stock insuficiente para: {nombres}. Ajusta las cantidades en tu carrito.",
        )
        return redirect("carrito")

    perfil, _ = Perfil.objects.get_or_create(usuario=request.user)

    if request.method == "POST":
        documento = request.POST.get("documento", "").strip()
        telefono = request.POST.get("telefono", "").strip()
        departamento = request.POST.get("departamento", "").strip()
        ciudad = request.POST.get("ciudad", "").strip()
        direccion = request.POST.get("direccion", "").strip()
        notas = request.POST.get("notas", "").strip()

        if (
            not documento
            or not telefono
            or not departamento
            or not ciudad
            or not direccion
        ):
            messages.error(
                request, "Completa todos los campos del formulario de envío."
            )
            return redirect("checkout")

        # Guarda/actualiza estos datos en el Perfil para la próxima compra
        perfil.documento = documento
        perfil.telefono = telefono
        perfil.departamento = departamento
        perfil.ciudad = ciudad
        perfil.direccion = direccion
        perfil.save()

        direccion_envio = f"{direccion}, {ciudad}, {departamento}"

        try:
            with transaction.atomic():
                # Revalidar stock dentro de la transacción (evita condiciones de carrera)
                pedido = Pedido.objects.create(
                    usuario=request.user,
                    estado=Pedido.PENDIENTE,
                    direccion_envio=direccion_envio,
                    notas=notas,
                    total=0,
                )

                for item in items:
                    producto = Producto.objects.select_for_update().get(
                        pk=item.producto_id
                    )
                    if item.cantidad > producto.stock:
                        raise ValueError(f"Stock insuficiente para {producto.nombre}.")

                    DetallePedido.objects.create(
                        pedido=pedido,
                        producto=producto,
                        nombre_producto=producto.nombre,
                        sku_producto=producto.sku,
                        cantidad=item.cantidad,
                        precio_unitario=producto.precio_con_descuento(),
                    )

                    producto.stock -= item.cantidad
                    producto.save(update_fields=["stock"])

                pedido.calcular_total()

                # Se crea el Pago automáticamente, sin preguntarle al usuario.
                # Por defecto queda como "contra entrega", pendiente de confirmar.
                Pago.objects.create(
                    pedido=pedido,
                    metodo=Pago.CONTRA_ENTREGA,
                    estado=Pago.PENDIENTE,
                )

                carrito.items.all().delete()

        except ValueError as e:
            messages.error(request, str(e))
            return redirect("carrito")

        messages.success(request, f"¡Pedido #{pedido.pk} realizado con éxito!")
        return redirect("comprobante", pk=pedido.pk)

    departamentos = sorted(DEPARTAMENTOS_CIUDADES.keys())

    return render(
        request,
        "tienda/checkout.html",
        {
            "carrito": carrito,
            "items": items,
            "perfil": perfil,
            "departamentos": departamentos,
            "departamentos_ciudades_json": json.dumps(
                DEPARTAMENTOS_CIUDADES, ensure_ascii=False
            ),
        },
    )


@login_required
def comprobante(request, pk):
    pedido = get_object_or_404(
        Pedido.objects.select_related("pago").prefetch_related("detalles"),
        pk=pk,
        usuario=request.user,
    )
    return render(request, "tienda/comprobante.html", {"pedido": pedido})


# ════════════════════════════════════════════════════
# PERFIL DEL CLIENTE
# ════════════════════════════════════════════════════


from .models import Pedido, Perfil


@login_required
def perfil(request):
    perfil_obj, _ = Perfil.objects.get_or_create(usuario=request.user)
    pedidos = Pedido.objects.filter(usuario=request.user).order_by("-fecha_pedido")
    seccion = request.GET.get("s", "resumen")

    if request.method == "POST":
        accion = request.POST.get("accion", "perfil")

        if accion == "perfil":
            request.user.first_name = request.POST.get("first_name", "").strip()
            request.user.last_name = request.POST.get("last_name", "").strip()
            request.user.email = request.POST.get("email", "").strip()
            request.user.save()
            perfil_obj.telefono = request.POST.get("telefono", "").strip()
            perfil_obj.direccion = request.POST.get("direccion", "").strip()
            perfil_obj.departamento = request.POST.get("departamento", "").strip()
            perfil_obj.ciudad = request.POST.get("ciudad", "").strip()
            if request.FILES.get("foto"):
                perfil_obj.foto = request.FILES["foto"]
            perfil_obj.save()
            messages.success(request, "Tu información fue actualizada correctamente.")
            return redirect(f"{request.path}?s=perfil")

        elif accion == "direccion":
            perfil_obj.direccion = request.POST.get("direccion", "").strip()
            perfil_obj.departamento = request.POST.get("departamento", "").strip()
            perfil_obj.ciudad = request.POST.get("ciudad", "").strip()
            perfil_obj.save()
            messages.success(request, "Dirección actualizada correctamente.")
            return redirect(f"{request.path}?s=direcciones")

        elif accion == "password":
            from django.contrib.auth import update_session_auth_hash

            old_pass = request.POST.get("old_password", "")
            new_pass = request.POST.get("new_password1", "")
            new_pass2 = request.POST.get("new_password2", "")
            if not request.user.check_password(old_pass):
                messages.error(request, "La contraseña actual es incorrecta.")
            elif new_pass != new_pass2:
                messages.error(request, "Las contraseñas nuevas no coinciden.")
            elif len(new_pass) < 8:
                messages.error(
                    request, "La contraseña debe tener al menos 8 caracteres."
                )
            else:
                request.user.set_password(new_pass)
                request.user.save()
                update_session_auth_hash(request, request.user)
                messages.success(request, "Contraseña actualizada correctamente.")
            return redirect(f"{request.path}?s=seguridad")

    return render(
        request,
        "tienda/perfil.html",
        {
            "perfil": perfil_obj,
            "pedidos": pedidos,
            "seccion": seccion,
        },
    )


# ============================================================
# PANEL ADMIN
# ============================================================

from functools import wraps

from django.utils import timezone

from .models import Proveedor


def admin_required(view_func):
    """Decorador: solo admins pueden acceder."""

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        try:
            if not request.user.perfil.es_admin():
                messages.error(request, "No tienes permisos de administrador.")
                return redirect("catalogo")
        except Exception:
            return redirect("catalogo")
        return view_func(request, *args, **kwargs)

    return wrapper


@admin_required
def admin_dashboard(request):

    from django.db.models import Count, Sum

    hoy = timezone.now()
    inicio_hoy = hoy.replace(hour=0, minute=0, second=0, microsecond=0)

    # Ventas y pedidos de hoy
    ventas_hoy = (
        Pedido.objects.filter(
            fecha_pedido__gte=inicio_hoy,
            estado__in=["confirmado", "preparando", "enviado", "entregado"],
        ).aggregate(total=Sum("total"))["total"]
        or 0
    )

    pedidos_hoy = Pedido.objects.filter(fecha_pedido__gte=inicio_hoy).count()

    # Contadores generales
    pedidos_pendientes = Pedido.objects.filter(estado="pendiente").count()
    pedidos_enviados = Pedido.objects.filter(estado="enviado").count()
    pedidos_entregados = Pedido.objects.filter(estado="entregado").count()
    total_productos = Producto.objects.filter(activo=True).count()
    total_clientes = User.objects.filter(perfil__rol="C").count()

    # Ventas últimos 12 meses
    import calendar

    meses_labels = []
    ventas_mensuales = []
    nombres_meses = [
        "Ene",
        "Feb",
        "Mar",
        "Abr",
        "May",
        "Jun",
        "Jul",
        "Ago",
        "Sep",
        "Oct",
        "Nov",
        "Dic",
    ]
    for i in range(11, -1, -1):
        mes_dt = hoy - timezone.timedelta(days=i * 30)
        mes_num = mes_dt.month
        anio = mes_dt.year
        total = (
            Pedido.objects.filter(
                fecha_pedido__year=anio,
                fecha_pedido__month=mes_num,
                estado__in=["confirmado", "preparando", "enviado", "entregado"],
            ).aggregate(t=Sum("total"))["t"]
            or 0
        )
        meses_labels.append(nombres_meses[mes_num - 1])
        ventas_mensuales.append(float(total))

    # Top productos
    from .models import DetallePedido

    top_raw = (
        DetallePedido.objects.values("nombre_producto")
        .annotate(total_vendido=Sum("cantidad"))
        .order_by("-total_vendido")[:5]
    )

    max_v = top_raw[0]["total_vendido"] if top_raw else 1
    top_productos = [
        {
            "nombre_producto": p["nombre_producto"],
            "total_vendido": p["total_vendido"],
            "porcentaje": round(p["total_vendido"] / max_v * 100),
        }
        for p in top_raw
    ]

    # Pedidos recientes
    pedidos_recientes = Pedido.objects.select_related("usuario").order_by(
        "-fecha_pedido"
    )[:5]

    # Últimos clientes
    colores = ["#c0392b", "#2980b9", "#27ae60", "#8e44ad", "#f39c12"]
    ultimos_clientes_qs = User.objects.filter(perfil__rol="C").order_by("-date_joined")[
        :5
    ]
    ultimos_clientes = []
    for i, u in enumerate(ultimos_clientes_qs):
        nombre = u.get_full_name() or u.username
        ultimos_clientes.append(
            {
                "nombre": nombre,
                "email": u.email,
                "inicial": nombre[0].upper(),
                "color": colores[i % len(colores)],
                "fecha": u.date_joined.strftime("%d/%m/%Y"),
            }
        )

    ventas_mes = (
        Pedido.objects.filter(
            fecha_pedido__year=hoy.year,
            fecha_pedido__month=hoy.month,
            estado__in=["confirmado", "preparando", "enviado", "entregado"],
        ).aggregate(t=Sum("total"))["t"]
        or 0
    )

    context = {
        "ventas_hoy": ventas_hoy,
        "ventas_mes": ventas_mes,
        "pedidos_hoy": pedidos_hoy,
        "pedidos_pendientes": pedidos_pendientes,
        "pedidos_enviados": pedidos_enviados,
        "pedidos_entregados": pedidos_entregados,
        "total_productos": total_productos,
        "total_clientes": total_clientes,
        "meses_labels": json.dumps(meses_labels),
        "ventas_mensuales": json.dumps(ventas_mensuales),
        "top_productos": top_productos,
        "pedidos_recientes": pedidos_recientes,
        "ultimos_clientes": ultimos_clientes,
    }
    return render(request, "admin/dashboard.html", context)


# ── Productos ──
@admin_required
def admin_productos(request):
    from django.core.paginator import Paginator

    qs = Producto.objects.select_related("categoria").all()

    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(nombre__icontains=q) | Q(sku__icontains=q))

    cat = request.GET.get("categoria", "")
    if cat:
        qs = qs.filter(categoria_id=cat)

    estado = request.GET.get("estado", "")
    if estado == "activo":
        qs = qs.filter(activo=True)
    elif estado == "inactivo":
        qs = qs.filter(activo=False)
    elif estado == "stock_bajo":
        from django.db.models import F

        qs = qs.filter(stock__lte=F("stock_minimo"))

    paginator = Paginator(qs, 15)
    productos = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "admin/productos/productos.html",
        {
            "productos": productos,
            "categorias": Categoria.objects.filter(activo=True),
            "total": qs.count(),
        },
    )


def _validar_datos_producto(request):
    """Valida precio/stock/stock_minimo del POST antes de tocar la BD.
    Devuelve (datos_limpios, error) — si error no es None, no debe guardarse nada.
    """
    from decimal import Decimal, InvalidOperation

    # Límite real de la columna: DecimalField(max_digits=12, decimal_places=2)
    PRECIO_MAXIMO = Decimal("9999999999.99")

    precio_raw = request.POST.get("precio", "0").strip().replace(",", "")
    try:
        precio = Decimal(precio_raw)
    except (InvalidOperation, TypeError):
        return None, "El precio ingresado no es un número válido."

    if precio < 0:
        return None, "El precio no puede ser negativo."
    if precio > PRECIO_MAXIMO:
        return None, (
            f"El precio ingresado es demasiado grande. "
            f"El máximo permitido es ${PRECIO_MAXIMO:,.2f}."
        )

    try:
        stock = int(request.POST.get("stock", 0))
        stock_minimo = int(request.POST.get("stock_minimo", 5))
    except (TypeError, ValueError):
        return None, "Stock y stock mínimo deben ser números enteros."

    if stock < 0 or stock_minimo < 0:
        return None, "Stock y stock mínimo no pueden ser negativos."

    return {"precio": precio, "stock": stock, "stock_minimo": stock_minimo}, None


@admin_required
def admin_producto_crear(request):
    from .models import MarcaProducto

    if request.method == "POST":
        datos, error = _validar_datos_producto(request)
        if error:
            messages.error(request, error)
            return render(
                request,
                "admin/productos/producto_crear.html",
                {
                    "categorias": Categoria.objects.filter(activo=True),
                    "marcas": MarcaProducto.objects.all(),
                },
            )

        p = Producto(
            nombre=request.POST.get("nombre", "").strip(),
            sku=request.POST.get("sku", "").strip(),
            precio=datos["precio"],
            descripcion=request.POST.get("descripcion", "").strip(),
            stock=datos["stock"],
            stock_minimo=datos["stock_minimo"],
            activo="activo" in request.POST,
        )
        cat = request.POST.get("categoria")
        if cat:
            p.categoria_id = cat
        marca = request.POST.get("marca")
        if marca:
            p.marca_id = marca
        if "imagen" in request.FILES:
            p.imagen = request.FILES["imagen"]
        p.save()
        messages.success(request, "Producto creado correctamente.")
        return redirect("admin_productos")
    return render(
        request,
        "admin/productos/producto_crear.html",
        {
            "categorias": Categoria.objects.filter(activo=True),
            "marcas": __import__(
                "AppMotopart.models", fromlist=["MarcaProducto"]
            ).MarcaProducto.objects.all(),
        },
    )


@admin_required
def admin_producto_editar(request, pk):
    from .models import MarcaProducto

    p = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        datos, error = _validar_datos_producto(request)
        if error:
            messages.error(request, error)
            return render(
                request,
                "admin/productos/producto_editar.html",
                {
                    "producto": p,
                    "categorias": Categoria.objects.filter(activo=True),
                    "marcas": MarcaProducto.objects.all(),
                },
            )

        p.nombre = request.POST.get("nombre", "").strip()
        p.sku = request.POST.get("sku", "").strip()
        p.precio = datos["precio"]
        p.descripcion = request.POST.get("descripcion", "").strip()
        p.stock = datos["stock"]
        p.stock_minimo = datos["stock_minimo"]
        p.activo = "activo" in request.POST
        cat = request.POST.get("categoria")
        p.categoria_id = cat if cat else None
        marca = request.POST.get("marca")
        p.marca_id = marca if marca else None
        if "imagen" in request.FILES:
            p.imagen = request.FILES["imagen"]
        p.save()
        messages.success(request, "Producto actualizado correctamente.")
        return redirect("admin_productos")
    return render(
        request,
        "admin/productos/producto_editar.html",
        {
            "producto": p,
            "categorias": Categoria.objects.filter(activo=True),
            "marcas": MarcaProducto.objects.all(),
        },
    )


@admin_required
def admin_producto_eliminar(request, pk):
    p = get_object_or_404(Producto, pk=pk)
    if request.method == "POST":
        p.delete()
        messages.success(request, "Producto eliminado.")
        return redirect("admin_productos")
    return render(request, "admin/productos/producto_eliminar.html", {"producto": p})


@admin_required
def admin_producto_toggle(request, pk):
    p = get_object_or_404(Producto, pk=pk)
    p.activo = not p.activo
    p.save()
    messages.success(request, f'Producto {"activado" if p.activo else "desactivado"}.')
    return redirect("admin_productos")


# ── Categorías ──
@admin_required
def admin_categorias(request):
    from django.db.models import Count

    categorias = Categoria.objects.annotate(num_productos=Count("productos")).order_by(
        "nombre"
    )

    return render(
        request, "admin/categorias/categorias.html", {"categorias": categorias}
    )


@admin_required
def admin_categoria_crear(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre", "").strip()
        if Categoria.objects.filter(nombre__iexact=nombre).exists():
            messages.error(request, "Ya existe una categoría con ese nombre.")
            return render(request, "admin/categorias/categoria_crear.html", {})
        Categoria.objects.create(
            nombre=nombre,
            descripcion=request.POST.get("descripcion", "").strip(),
            icono=request.POST.get("icono", "").strip(),
            activo="activo" in request.POST,
        )
        messages.success(request, "Categoría creada correctamente.")
        return redirect("admin_categorias")
    return render(request, "admin/categorias/categoria_crear.html", {})


@admin_required
def admin_categoria_editar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == "POST":
        categoria.nombre = request.POST.get("nombre", "").strip()
        categoria.descripcion = request.POST.get("descripcion", "").strip()
        categoria.icono = request.POST.get("icono", "").strip()
        categoria.activo = "activo" in request.POST
        categoria.save()
        messages.success(request, "Categoría actualizada correctamente.")
        return redirect("admin_categorias")
    return render(
        request, "admin/categorias/categoria_editar.html", {"categoria": categoria}
    )


@admin_required
def admin_categoria_toggle(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    categoria.activo = not categoria.activo
    categoria.save()
    messages.success(
        request, f'Categoría {"activada" if categoria.activo else "desactivada"}.'
    )
    return redirect("admin_categorias")


@admin_required
def admin_categoria_eliminar(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    num_productos = Producto.objects.filter(categoria=categoria).count()
    if request.method == "POST":
        categoria.delete()
        messages.success(request, "Categoría eliminada.")
        return redirect("admin_categorias")
    return render(
        request,
        "admin/categorias/categoria_eliminar.html",
        {
            "categoria": categoria,
            "num_productos": num_productos,
        },
    )


# ── Pedidos ──
@admin_required
def admin_pedidos(request):
    pedidos = Pedido.objects.select_related("usuario").order_by("-fecha_pedido")

    estado_filtro = request.GET.get("estado", "")
    if estado_filtro:
        pedidos = pedidos.filter(estado=estado_filtro)

    q = request.GET.get("q", "").strip()
    if q:
        pedidos = pedidos.filter(
            Q(id__icontains=q)
            | Q(usuario__username__icontains=q)
            | Q(usuario__first_name__icontains=q)
            | Q(usuario__last_name__icontains=q)
        )

    return render(
        request,
        "admin/pedidos/pedidos.html",
        {
            "pedidos": pedidos,
            "estados": Pedido.ESTADOS,
            "estado_filtro": estado_filtro,
            "q": q,
        },
    )


@admin_required
def admin_pedido_detalle(request, pk):
    pedido = get_object_or_404(
        Pedido.objects.select_related("usuario").prefetch_related("detalles"), pk=pk
    )
    pago = Pago.objects.filter(pedido=pedido).first()

    return render(
        request,
        "admin/pedidos/pedido_detalle.html",
        {
            "pedido": pedido,
            "pago": pago,
            "estados": Pedido.ESTADOS,
        },
    )


@admin_required
def admin_pedido_estado(request, pk):
    pedido = get_object_or_404(Pedido, pk=pk)
    if request.method == "POST":
        nuevo_estado = request.POST.get("estado")
        estados_validos = [e[0] for e in Pedido.ESTADOS]
        if nuevo_estado in estados_validos:
            pedido.estado = nuevo_estado
            pedido.save(update_fields=["estado", "fecha_actualizacion"])
            messages.success(
                request,
                f"Pedido #{pedido.pk} actualizado a '{pedido.get_estado_display()}'.",
            )
        else:
            messages.error(request, "Estado no válido.")
    return redirect("admin_pedido_detalle", pk=pk)


# ── Inventario ──
@admin_required
def admin_inventario(request):
    movimientos = Movimiento.objects.select_related(
        "producto", "proveedor", "usuario"
    ).order_by("-fecha")

    tipo_filtro = request.GET.get("tipo", "")
    if tipo_filtro:
        movimientos = movimientos.filter(tipo=tipo_filtro)

    q = request.GET.get("q", "").strip()
    if q:
        movimientos = movimientos.filter(
            Q(producto__nombre__icontains=q)
            | Q(producto__sku__icontains=q)
            | Q(referencia__icontains=q)
        )

    productos_stock_bajo = Producto.objects.filter(activo=True).order_by("stock")
    productos_stock_bajo = [p for p in productos_stock_bajo if p.stock_bajo()]

    return render(
        request,
        "admin/inventario/inventario.html",
        {
            "movimientos": movimientos[:200],
            "tipos": Movimiento.TIPOS,
            "tipo_filtro": tipo_filtro,
            "q": q,
            "productos_stock_bajo": productos_stock_bajo,
        },
    )


@admin_required
def admin_movimiento_crear(request):
    if request.method == "POST":
        producto_id = request.POST.get("producto")
        tipo = request.POST.get("tipo")
        cantidad_raw = request.POST.get("cantidad", "0")
        referencia = request.POST.get("referencia", "").strip()
        notas = request.POST.get("notas", "").strip()
        proveedor_id = request.POST.get("proveedor") or None

        producto = get_object_or_404(Producto, pk=producto_id)
        tipos_validos = [t[0] for t in Movimiento.TIPOS]

        try:
            cantidad = int(cantidad_raw)
        except (TypeError, ValueError):
            cantidad = 0

        if tipo not in tipos_validos or cantidad == 0:
            messages.error(
                request, "Revisa el tipo de movimiento y la cantidad ingresada."
            )
        else:
            if tipo in (Movimiento.ENTRADA, Movimiento.COMPRA):
                cantidad_final = abs(cantidad)
            else:
                cantidad_final = -abs(cantidad)

            Movimiento.objects.create(
                producto=producto,
                tipo=tipo,
                cantidad=cantidad_final,
                proveedor_id=proveedor_id,
                referencia=referencia,
                notas=notas,
                usuario=request.user,
            )
            messages.success(
                request,
                f"Movimiento registrado: {producto.nombre} → stock actualizado.",
            )
            return redirect("admin_inventario")

    return render(
        request,
        "admin/inventario/movimiento_crear.html",
        {
            "productos": Producto.objects.filter(activo=True).order_by("nombre"),
            "proveedores": Proveedor.objects.filter(activo=True).order_by("nombre"),
            "tipos": Movimiento.TIPOS,
        },
    )


# ── Proveedores ──
@admin_required
def admin_proveedores(request):

    proveedores = Proveedor.objects.all()

    context = {"proveedores": proveedores}

    return render(request, "admin/proveedores/proveedores.html", context)


@admin_required
def admin_proveedor_crear(request):

    if request.method == "POST":

        Proveedor.objects.create(
            nombre=request.POST.get("nombre", "").strip(),
            contacto=request.POST.get("contacto", "").strip(),
            telefono=request.POST.get("telefono", "").strip(),
            correo=request.POST.get("correo", "").strip(),
            direccion=request.POST.get("direccion", "").strip(),
            ciudad=request.POST.get("ciudad", "").strip(),
            nit=request.POST.get("nit", "").strip(),
            activo="activo" in request.POST,
        )

        messages.success(request, "Proveedor creado correctamente.")
        return redirect("admin_proveedores")

    return render(request, "admin/proveedores/proveedor_crear.html", {})


@admin_required
def admin_proveedor_eliminar(request, pk):

    proveedor = get_object_or_404(Proveedor, pk=pk)

    if request.method == "POST":
        proveedor.delete()
        messages.success(request, "Proveedor eliminado correctamente.")
        return redirect("admin_proveedores")

    return render(
        request, "admin/proveedores/proveedor_eliminar.html", {"proveedor": proveedor}
    )


@admin_required
def admin_proveedor_editar(request, pk):

    proveedor = get_object_or_404(Proveedor, pk=pk)

    if request.method == "POST":

        proveedor.nombre = request.POST.get("nombre", "")
        proveedor.contacto = request.POST.get("contacto", "")
        proveedor.telefono = request.POST.get("telefono", "")
        proveedor.correo = request.POST.get("correo", "")
        proveedor.direccion = request.POST.get("direccion", "")
        proveedor.ciudad = request.POST.get("ciudad", "")
        proveedor.nit = request.POST.get("nit", "")
        proveedor.activo = "activo" in request.POST

        proveedor.save()

        messages.success(request, "Proveedor actualizado correctamente.")
        return redirect("admin_proveedores")

    return render(
        request, "admin/proveedores/proveedor_editar.html", {"proveedor": proveedor}
    )


@admin_required
def admin_proveedor_toggle(request, pk):
    return redirect("admin_proveedores")


# ── Usuarios ──
@admin_required
def admin_usuarios(request):
    from django.core.paginator import Paginator

    qs = User.objects.filter(perfil__rol="C").select_related("perfil")

    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(username__icontains=q)
            | Q(email__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
        )

    estado = request.GET.get("estado", "")
    if estado == "activo":
        qs = qs.filter(is_active=True)
    elif estado == "inactivo":
        qs = qs.filter(is_active=False)

    qs = qs.order_by("-date_joined")
    paginator = Paginator(qs, 15)
    pagina = paginator.get_page(request.GET.get("page"))

    colores = ["#c0392b", "#2980b9", "#27ae60", "#8e44ad", "#f39c12", "#16a085"]
    clientes = []
    for i, u in enumerate(pagina):
        clientes.append(
            {
                "usuario": u,
                "perfil": getattr(u, "perfil", None),
                "nombre": u.get_full_name() or u.username,
                "inicial": u.username[0].upper(),
                "color": colores[i % len(colores)],
                "num_pedidos": Pedido.objects.filter(usuario=u).count(),
            }
        )

    return render(
        request,
        "admin/usuarios/usuarios.html",
        {
            "clientes": clientes,
            "total": qs.count(),
        },
    )


# ── Usuarios ──
@admin_required
def admin_usuarios(request):
    from django.core.paginator import Paginator

    qs = User.objects.filter(perfil__rol="C").select_related("perfil")

    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(username__icontains=q)
            | Q(email__icontains=q)
            | Q(first_name__icontains=q)
            | Q(last_name__icontains=q)
            | Q(perfil__documento__icontains=q)
        )

    estado = request.GET.get("estado", "")
    if estado == "activo":
        qs = qs.filter(is_active=True)
    elif estado == "inactivo":
        qs = qs.filter(is_active=False)

    qs = qs.order_by("-date_joined")
    paginator = Paginator(qs, 15)
    pagina = paginator.get_page(request.GET.get("page"))

    colores = ["#c0392b", "#2980b9", "#27ae60", "#8e44ad", "#f39c12", "#16a085"]
    clientes = []
    for i, u in enumerate(pagina):
        clientes.append(
            {
                "usuario": u,
                "perfil": getattr(u, "perfil", None),
                "nombre": u.get_full_name() or u.username,
                "inicial": u.username[0].upper(),
                "color": colores[i % len(colores)],
                "num_pedidos": Pedido.objects.filter(usuario=u).count(),
            }
        )

    return render(
        request,
        "admin/usuarios/usuarios.html",
        {
            "clientes": clientes,
            "total": qs.count(),
        },
    )


@admin_required
def admin_usuario_crear(request):

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        if User.objects.filter(username=username).exists():
            messages.error(request, "Ese nombre de usuario ya existe.")
            return render(request, "admin/usuarios/usuario_crear.html", {})

        u = User.objects.create_user(
            username=username,
            email=request.POST.get("email", "").strip(),
            password=request.POST.get("password"),
            first_name=request.POST.get("first_name", "").strip(),
            last_name=request.POST.get("last_name", "").strip(),
            is_active="activo" in request.POST,
        )
        Perfil.objects.filter(usuario=u).update(
            rol=request.POST.get("rol", "C"),
            documento=request.POST.get("documento", "").strip() or None,
            telefono=request.POST.get("telefono", "").strip(),
            direccion=request.POST.get("direccion", "").strip(),
            ciudad=request.POST.get("ciudad", "").strip(),
        )
        messages.success(request, "Cliente creado correctamente.")
        return redirect("admin_usuarios")
    return render(request, "admin/usuarios/usuario_crear.html", {})


@admin_required
def admin_usuario_editar(request, pk):

    cliente = get_object_or_404(User, pk=pk)
    if request.method == "POST":
        cliente.username = request.POST.get("username", "").strip()
        cliente.email = request.POST.get("email", "").strip()
        cliente.first_name = request.POST.get("first_name", "").strip()
        cliente.last_name = request.POST.get("last_name", "").strip()
        cliente.is_active = "activo" in request.POST
        nueva_pass = request.POST.get("password", "").strip()
        if nueva_pass:
            cliente.set_password(nueva_pass)
        cliente.save()

        Perfil.objects.filter(usuario=cliente).update(
            rol=request.POST.get("rol", "C"),
            documento=request.POST.get("documento", "").strip() or None,
            telefono=request.POST.get("telefono", "").strip(),
            direccion=request.POST.get("direccion", "").strip(),
            ciudad=request.POST.get("ciudad", "").strip(),
        )
        messages.success(request, "Cliente actualizado correctamente.")
        return redirect("admin_usuarios")
    return render(request, "admin/usuarios/usuario_editar.html", {"cliente": cliente})


@admin_required
def admin_usuario_toggle(request, pk):

    cliente = get_object_or_404(User, pk=pk)
    cliente.is_active = not cliente.is_active
    cliente.save()
    messages.success(
        request, f'Cliente {"activado" if cliente.is_active else "desactivado"}.'
    )
    return redirect("admin_usuarios")


@admin_required
def admin_usuario_eliminar(request, pk):

    cliente = get_object_or_404(User, pk=pk)
    num_pedidos = Pedido.objects.filter(usuario=cliente).count()
    if request.method == "POST":
        cliente.delete()
        messages.success(request, "Cliente eliminado.")
        return redirect("admin_usuarios")
    return render(
        request,
        "admin/usuarios/usuario_eliminar.html",
        {"cliente": cliente, "num_pedidos": num_pedidos},
    )


@admin_required
def admin_usuario_detalle(request, pk):

    cliente = get_object_or_404(User, pk=pk)
    pedidos = Pedido.objects.filter(usuario=cliente).order_by("-fecha_pedido")
    return render(
        request,
        "admin/usuarios/usuario_detalle.html",
        {"cliente": cliente, "pedidos": pedidos},
    )


# ── Reportes ──

ESTADOS_VENTA = ["confirmado", "preparando", "enviado", "entregado"]


@admin_required
def admin_reportes(request):
    return render(request, "admin/reportes/reportes.html", {})


def _datos_reporte_ventas(request):
    from datetime import datetime

    from django.db.models import Count, Sum
    from django.db.models.functions import TruncDate

    hoy = timezone.now()

    # Rango de fechas: por defecto, mes actual
    desde_raw = request.GET.get("desde", "")
    hasta_raw = request.GET.get("hasta", "")

    if desde_raw:
        desde = datetime.strptime(desde_raw, "%Y-%m-%d").replace(
            hour=0, minute=0, second=0
        )
        desde = timezone.make_aware(desde) if timezone.is_naive(desde) else desde
    else:
        desde = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    if hasta_raw:
        hasta = datetime.strptime(hasta_raw, "%Y-%m-%d").replace(
            hour=23, minute=59, second=59
        )
        hasta = timezone.make_aware(hasta) if timezone.is_naive(hasta) else hasta
    else:
        hasta = hoy

    pedidos = Pedido.objects.filter(
        fecha_pedido__gte=desde,
        fecha_pedido__lte=hasta,
        estado__in=ESTADOS_VENTA,
    ).select_related("usuario")

    resumen = pedidos.aggregate(total_ventas=Sum("total"), num_pedidos=Count("id"))
    total_ventas = resumen["total_ventas"] or 0
    num_pedidos = resumen["num_pedidos"] or 0
    ticket_promedio = (total_ventas / num_pedidos) if num_pedidos else 0

    subtotal_sin_iva = sum(p.subtotal_sin_iva() for p in pedidos)
    iva_total = sum(p.valor_iva() for p in pedidos)

    # Comparación con periodo anterior (misma duración, inmediatamente antes)
    duracion = hasta - desde
    desde_anterior = desde - duracion - timezone.timedelta(seconds=1)
    hasta_anterior = desde - timezone.timedelta(seconds=1)
    total_anterior = (
        Pedido.objects.filter(
            fecha_pedido__gte=desde_anterior,
            fecha_pedido__lte=hasta_anterior,
            estado__in=ESTADOS_VENTA,
        ).aggregate(t=Sum("total"))["t"]
        or 0
    )
    if total_anterior:
        variacion_pct = round(
            float((total_ventas - total_anterior) / total_anterior * 100), 1
        )
    else:
        variacion_pct = None

    # Ventas agrupadas por día (para el gráfico)
    por_dia_qs = (
        pedidos.annotate(dia=TruncDate("fecha_pedido"))
        .values("dia")
        .annotate(total=Sum("total"))
        .order_by("dia")
    )
    dias_labels = [
        d["dia"].strftime("%d/%m") for d in por_dia_qs if d["dia"] is not None
    ]
    dias_totales = [float(d["total"] or 0) for d in por_dia_qs if d["dia"] is not None]

    # Ventas por método de pago
    por_metodo = (
        Pago.objects.filter(pedido__in=pedidos, estado="aprobado")
        .values("metodo")
        .annotate(total=Sum("pedido__total"), num=Count("id"))
        .order_by("-total")
    )
    metodos_dict = dict(Pago.METODOS)
    por_metodo = [
        {
            "metodo": metodos_dict.get(m["metodo"], m["metodo"]),
            "total": m["total"] or 0,
            "num": m["num"],
        }
        for m in por_metodo
    ]

    pedidos_detalle = list(pedidos.order_by("-fecha_pedido"))

    return {
        "desde": desde.strftime("%Y-%m-%d"),
        "hasta": hasta.strftime("%Y-%m-%d"),
        "desde_dt": desde,
        "hasta_dt": hasta,
        "total_ventas": total_ventas,
        "num_pedidos": num_pedidos,
        "ticket_promedio": ticket_promedio,
        "subtotal_sin_iva": subtotal_sin_iva,
        "iva_total": iva_total,
        "variacion_pct": variacion_pct,
        "dias_labels": dias_labels,
        "dias_totales": dias_totales,
        "por_metodo": por_metodo,
        "pedidos_detalle": pedidos_detalle,
    }


@admin_required
def admin_reporte_ventas(request):
    datos = _datos_reporte_ventas(request)
    context = {
        **datos,
        "dias_labels": json.dumps(datos["dias_labels"]),
        "dias_totales": json.dumps(datos["dias_totales"]),
    }
    return render(request, "admin/reportes/reporte_ventas.html", context)


@admin_required
def admin_reporte_ventas_excel(request):
    from . import exportes

    datos = _datos_reporte_ventas(request)
    return exportes.exportar_ventas_excel(datos)


@admin_required
def admin_reporte_ventas_pdf(request):
    from . import exportes

    datos = _datos_reporte_ventas(request)
    return exportes.exportar_ventas_pdf(datos)


def _datos_reporte_inventario(request):
    from django.db.models import F

    productos = Producto.objects.filter(activo=True).select_related(
        "categoria", "marca"
    )

    q = request.GET.get("q", "").strip()
    if q:
        productos = productos.filter(Q(nombre__icontains=q) | Q(sku__icontains=q))

    cat = request.GET.get("categoria", "")
    if cat:
        productos = productos.filter(categoria_id=cat)

    solo_bajo = request.GET.get("solo_bajo", "") == "1"
    if solo_bajo:
        productos = productos.filter(stock__lte=F("stock_minimo"))

    productos = productos.order_by("stock")

    productos_lista = []
    for p in productos:
        productos_lista.append(
            {
                "obj": p,
                "valor_stock": p.precio_sin_iva() * p.stock,
            }
        )

    valor_inventario_total = sum(
        p.precio_sin_iva() * p.stock for p in Producto.objects.filter(activo=True)
    )
    valor_inventario_filtrado = sum(item["valor_stock"] for item in productos_lista)
    unidades_totales = sum(item["obj"].stock for item in productos_lista)

    productos_stock_bajo = [
        p for p in Producto.objects.filter(activo=True) if p.stock_bajo()
    ]
    productos_sin_stock = Producto.objects.filter(activo=True, stock=0).count()

    categoria_nombre = ""
    if cat:
        cat_obj = Categoria.objects.filter(pk=cat).first()
        categoria_nombre = cat_obj.nombre if cat_obj else ""

    return {
        "productos": productos_lista,
        "categorias": Categoria.objects.filter(activo=True),
        "categoria_filtro": cat,
        "categoria_nombre": categoria_nombre,
        "q": q,
        "solo_bajo": solo_bajo,
        "valor_inventario_total": valor_inventario_total,
        "valor_inventario_filtrado": valor_inventario_filtrado,
        "unidades_totales": unidades_totales,
        "total_stock_bajo": len(productos_stock_bajo),
        "total_sin_stock": productos_sin_stock,
        "total_productos": Producto.objects.filter(activo=True).count(),
    }


@admin_required
def admin_reporte_inventario(request):
    context = _datos_reporte_inventario(request)
    return render(request, "admin/reportes/reporte_inventario.html", context)


@admin_required
def admin_reporte_inventario_excel(request):
    from . import exportes

    datos = _datos_reporte_inventario(request)
    return exportes.exportar_inventario_excel(datos)


@admin_required
def admin_reporte_inventario_pdf(request):
    from . import exportes

    datos = _datos_reporte_inventario(request)
    return exportes.exportar_inventario_pdf(datos)


def _datos_reporte_productos_vendidos(request):
    from datetime import datetime

    from django.db.models import Count, F, Sum

    hoy = timezone.now()

    desde_raw = request.GET.get("desde", "")
    hasta_raw = request.GET.get("hasta", "")

    if desde_raw:
        desde = timezone.make_aware(
            datetime.strptime(desde_raw, "%Y-%m-%d").replace(hour=0, minute=0, second=0)
        )
    else:
        desde = hoy - timezone.timedelta(days=90)

    if hasta_raw:
        hasta = timezone.make_aware(
            datetime.strptime(hasta_raw, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59
            )
        )
    else:
        hasta = hoy

    categoria_id = request.GET.get("categoria", "")

    detalles = DetallePedido.objects.filter(
        pedido__fecha_pedido__gte=desde,
        pedido__fecha_pedido__lte=hasta,
        pedido__estado__in=ESTADOS_VENTA,
    )
    if categoria_id:
        detalles = detalles.filter(producto__categoria_id=categoria_id)

    ranking = (
        detalles.values("producto_id", "nombre_producto", "sku_producto")
        .annotate(
            unidades_vendidas=Sum("cantidad"),
            ingresos=Sum(F("cantidad") * F("precio_unitario")),
            num_pedidos=Count("pedido", distinct=True),
        )
        .order_by("-unidades_vendidas")
    )

    max_unidades = ranking[0]["unidades_vendidas"] if ranking else 1

    ranking_list = []
    for idx, r in enumerate(ranking[:50], start=1):
        producto_obj = None
        stock_actual = None
        if r["producto_id"]:
            producto_obj = Producto.objects.filter(pk=r["producto_id"]).first()
            if producto_obj:
                stock_actual = producto_obj.stock
        ranking_list.append(
            {
                "puesto": idx,
                "nombre": r["nombre_producto"],
                "sku": r["sku_producto"],
                "unidades_vendidas": r["unidades_vendidas"],
                "ingresos": r["ingresos"] or 0,
                "num_pedidos": r["num_pedidos"],
                "porcentaje": round(r["unidades_vendidas"] / max_unidades * 100),
                "stock_actual": stock_actual,
                "producto": producto_obj,
            }
        )

    # Productos sin ventas en el periodo (no se mueven)
    productos_vendidos_ids = detalles.values_list("producto_id", flat=True).distinct()
    sin_movimiento = Producto.objects.filter(activo=True).exclude(
        id__in=productos_vendidos_ids
    )
    if categoria_id:
        sin_movimiento = sin_movimiento.filter(categoria_id=categoria_id)
    sin_movimiento = list(sin_movimiento.select_related("categoria").order_by("-stock"))

    categoria_nombre = ""
    if categoria_id:
        cat_obj = Categoria.objects.filter(pk=categoria_id).first()
        categoria_nombre = cat_obj.nombre if cat_obj else ""

    return {
        "desde": desde.strftime("%Y-%m-%d"),
        "hasta": hasta.strftime("%Y-%m-%d"),
        "desde_dt": desde,
        "hasta_dt": hasta,
        "categoria_filtro": categoria_id,
        "categoria_nombre": categoria_nombre,
        "categorias": Categoria.objects.filter(activo=True),
        "ranking": ranking_list,
        "top10_labels": [r["nombre"][:22] for r in ranking_list[:10]],
        "top10_data": [r["unidades_vendidas"] for r in ranking_list[:10]],
        "sin_movimiento": sin_movimiento,
        "total_sin_movimiento": len(sin_movimiento),
    }


@admin_required
def admin_reporte_productos_vendidos(request):
    datos = _datos_reporte_productos_vendidos(request)
    context = {
        **datos,
        "top10_labels": json.dumps(datos["top10_labels"]),
        "top10_data": json.dumps(datos["top10_data"]),
    }
    return render(request, "admin/reportes/reporte_productos_vendidos.html", context)


@admin_required
def admin_reporte_productos_vendidos_excel(request):
    from . import exportes

    datos = _datos_reporte_productos_vendidos(request)
    return exportes.exportar_productos_vendidos_excel(datos)


@admin_required
def admin_reporte_productos_vendidos_pdf(request):
    from . import exportes

    datos = _datos_reporte_productos_vendidos(request)
    return exportes.exportar_productos_vendidos_pdf(datos)
