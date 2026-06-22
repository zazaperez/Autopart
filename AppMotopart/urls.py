from django.urls import path

from . import views

urlpatterns = [
    # Auth
    path("registro/", views.vista_registro, name="registro"),
    path("login/", views.vista_login, name="login"),
    path("logout/", views.vista_logout, name="logout"),
    # Catálogo
    path("", views.catalogo, name="catalogo"),
    path("producto/<int:pk>/", views.detalle_producto, name="detalle_producto"),
    # Carrito
    path("carrito/", views.ver_carrito, name="carrito"),
    path(
        "carrito/agregar/<int:producto_id>/",
        views.agregar_carrito,
        name="agregar_carrito",
    ),
    path(
        "carrito/item/<int:item_id>/actualizar/",
        views.actualizar_carrito,
        name="actualizar_carrito",
    ),
    path(
        "carrito/item/<int:item_id>/eliminar/",
        views.eliminar_carrito,
        name="eliminar_carrito",
    ),
    path("carrito/vaciar/", views.vaciar_carrito, name="vaciar_carrito"),
    path("checkout/", views.checkout, name="checkout"),
    path("pedido/<int:pk>/comprobante/", views.comprobante, name="comprobante"),
    # Pedido
    path("checkout/", views.checkout, name="checkout"),
    path("comprobante/<int:pk>/", views.comprobante, name="comprobante"),
    # Perfil
    path("perfil/", views.perfil, name="perfil"),
    # ── PANEL ADMIN ──
    path("panel/", views.admin_dashboard, name="admin_dashboard"),
    # =========================
    # PRODUCTOS
    # =========================
    path(
        "panel/productos/",
        views.admin_productos,
        name="admin_productos",
    ),
    path(
        "panel/productos/crear/",
        views.admin_producto_crear,
        name="admin_producto_crear",
    ),
    path(
        "panel/productos/<int:pk>/editar/",
        views.admin_producto_editar,
        name="admin_producto_editar",
    ),
    path(
        "panel/productos/<int:pk>/toggle/",
        views.admin_producto_toggle,
        name="admin_producto_toggle",
    ),
    path(
        "panel/productos/<int:pk>/eliminar/",
        views.admin_producto_eliminar,
        name="admin_producto_eliminar",
    ),
    # =========================
    # CATEGORÍAS
    # =========================
    path(
        "panel/categorias/",
        views.admin_categorias,
        name="admin_categorias",
    ),
    path(
        "panel/categorias/crear/",
        views.admin_categoria_crear,
        name="admin_categoria_crear",
    ),
    path(
        "panel/categorias/<int:pk>/editar/",
        views.admin_categoria_editar,
        name="admin_categoria_editar",
    ),
    path(
        "panel/categorias/<int:pk>/eliminar/",
        views.admin_categoria_eliminar,
        name="admin_categoria_eliminar",
    ),
    path(
        "panel/categorias/<int:pk>/toggle/",
        views.admin_categoria_toggle,
        name="admin_categoria_toggle",
    ),
    # =========================
    # PEDIDOS
    # =========================
    path(
        "panel/pedidos/",
        views.admin_pedidos,
        name="admin_pedidos",
    ),
    path(
        "panel/pedidos/<int:pk>/",
        views.admin_pedido_detalle,
        name="admin_pedido_detalle",
    ),
    path(
        "panel/pedidos/<int:pk>/estado/",
        views.admin_pedido_estado,
        name="admin_pedido_estado",
    ),
    # =========================
    # INVENTARIO
    # =========================
    path(
        "panel/inventario/",
        views.admin_inventario,
        name="admin_inventario",
    ),
    path(
        "panel/inventario/registrar/",
        views.admin_movimiento_crear,
        name="admin_movimiento_crear",
    ),
    # =========================
    # PROVEEDORES
    # =========================
    path(
        "panel/proveedores/",
        views.admin_proveedores,
        name="admin_proveedores",
    ),
    path(
        "panel/proveedores/crear/",
        views.admin_proveedor_crear,
        name="admin_proveedor_crear",
    ),
    path(
        "panel/proveedores/<int:pk>/editar/",
        views.admin_proveedor_editar,
        name="admin_proveedor_editar",
    ),
    path(
        "panel/proveedores/<int:pk>/toggle/",
        views.admin_proveedor_toggle,
        name="admin_proveedor_toggle",
    ),
    path(
        "panel/proveedores/<int:pk>/eliminar/",
        views.admin_proveedor_eliminar,
        name="admin_proveedor_eliminar",
    ),
    # =========================
    # USUARIOS
    # =========================
    path(
        "panel/usuarios/",
        views.admin_usuarios,
        name="admin_usuarios",
    ),
    path(
        "panel/usuarios/crear/",
        views.admin_usuario_crear,
        name="admin_usuario_crear",
    ),
    path(
        "panel/usuarios/<int:pk>/",
        views.admin_usuario_detalle,
        name="admin_usuario_detalle",
    ),
    path(
        "panel/usuarios/<int:pk>/editar/",
        views.admin_usuario_editar,
        name="admin_usuario_editar",
    ),
    path(
        "panel/usuarios/<int:pk>/toggle/",
        views.admin_usuario_toggle,
        name="admin_usuario_toggle",
    ),
    path(
        "panel/usuarios/<int:pk>/eliminar/",
        views.admin_usuario_eliminar,
        name="admin_usuario_eliminar",
    ),
    # =========================
    # REPORTES
    # =========================
    path(
        "panel/reportes/",
        views.admin_reportes,
        name="admin_reportes",
    ),
    path(
        "panel/reportes/ventas/",
        views.admin_reporte_ventas,
        name="admin_reporte_ventas",
    ),
    path(
        "panel/reportes/ventas/excel/",
        views.admin_reporte_ventas_excel,
        name="admin_reporte_ventas_excel",
    ),
    path(
        "panel/reportes/ventas/pdf/",
        views.admin_reporte_ventas_pdf,
        name="admin_reporte_ventas_pdf",
    ),
    path(
        "panel/reportes/inventario/",
        views.admin_reporte_inventario,
        name="admin_reporte_inventario",
    ),
    path(
        "panel/reportes/inventario/excel/",
        views.admin_reporte_inventario_excel,
        name="admin_reporte_inventario_excel",
    ),
    path(
        "panel/reportes/inventario/pdf/",
        views.admin_reporte_inventario_pdf,
        name="admin_reporte_inventario_pdf",
    ),
    path(
        "panel/reportes/productos-vendidos/",
        views.admin_reporte_productos_vendidos,
        name="admin_reporte_productos_vendidos",
    ),
    path(
        "panel/reportes/productos-vendidos/excel/",
        views.admin_reporte_productos_vendidos_excel,
        name="admin_reporte_productos_vendidos_excel",
    ),
    path(
        "panel/reportes/productos-vendidos/pdf/",
        views.admin_reporte_productos_vendidos_pdf,
        name="admin_reporte_productos_vendidos_pdf",
    ),
]
