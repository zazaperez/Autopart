# AppMotopart/management/commands/seeds.py
#
# USO:
#   python manage.py seeds           → carga todo sin borrar nada
#   python manage.py seeds --flush   → borra todo y recarga limpio

from decimal import Decimal

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from AppMotopart.models import (
    Categoria,
    Compatibilidad,
    MarcaProducto,
    MarcaVehiculo,
    ModeloVehiculo,
    Producto,
    Proveedor,
    Vehiculo,
)

CATEGORIAS = [
    ("Frenos", "Pastillas, discos y kits de freno", "fa-circle-stop"),
    ("Filtros", "Filtros de aceite, aire y combustible", "fa-filter"),
    ("Aceites", "Lubricantes y fluidos", "fa-oil-can"),
    ("Baterías", "Baterías para todo tipo de vehículo", "fa-car-battery"),
    ("Amortiguadores", "Suspensión y amortiguación", "fa-car-bump"),
    ("Luces", "Bombillas, faros y accesorios", "fa-lightbulb"),
    ("Correas", "Correas de distribución y accesorios", "fa-gear"),
    ("Motor", "Piezas internas del motor", "fa-wrench"),
    ("Eléctrico", "Alternadores, arranques y sensores", "fa-bolt"),
    ("Carrocería", "Espejos, manijas y piezas externas", "fa-car"),
]

MARCAS = [
    "Bosch",
    "NGK",
    "Mobil",
    "Castrol",
    "Brembo",
    "Monroe",
    "Gates",
    "Denso",
    "ACDelco",
    "Bendix",
]

VEHICULOS = [
    ("Chevrolet", "Spark GT", 2019, "1.2", "GT", "gasolina"),
    ("Chevrolet", "Aveo", 2020, "1.4", "LS", "gasolina"),
    ("Mazda", "3", 2018, "2.0", "Touring", "gasolina"),
    ("Mazda", "CX-5", 2021, "2.5", "Grand", "gasolina"),
    ("Toyota", "Corolla", 2020, "1.8", "XEI", "gasolina"),
    ("Toyota", "Hilux", 2022, "2.8", "SRX", "diesel"),
    ("Renault", "Logan", 2019, "1.6", "Expression", "gasolina"),
    ("Renault", "Duster", 2021, "1.3", "Intens", "gasolina"),
    ("Kia", "Picanto", 2020, "1.0", "EX", "gasolina"),
    ("Kia", "Sportage", 2022, "2.0", "EX", "gasolina"),
    ("Hyundai", "i10", 2019, "1.1", "GL", "gasolina"),
    ("Hyundai", "Tucson", 2021, "2.0", "GLS", "gasolina"),
    ("Nissan", "Sentra", 2020, "1.8", "Advance", "gasolina"),
    ("Ford", "EcoSport", 2021, "1.5", "Titanium", "gasolina"),
    ("Volkswagen", "Polo", 2020, "1.6", "Comfortline", "gasolina"),
]

# (nombre, sku, categoría, marca, descripción, precio_COP, stock, stock_mínimo)
PRODUCTOS = [
    (
        "Pastillas freno delanteras Bosch",
        "FRE-001",
        "Frenos",
        "Bosch",
        "Pastillas semimetálicas de alto rendimiento. Baja generación de polvo y ruido.",
        89_900,
        25,
        5,
    ),
    (
        "Disco freno ventilado Brembo",
        "FRE-002",
        "Frenos",
        "Brembo",
        "Disco ventilado de acero de alta resistencia al calor. Diámetro 280 mm.",
        145_000,
        15,
        3,
    ),
    (
        "Filtro de aceite Bosch",
        "FIL-001",
        "Filtros",
        "Bosch",
        "Filtro larga duración. Retiene partículas hasta 20 micras. Cambia cada 5.000 km.",
        18_500,
        60,
        10,
    ),
    (
        "Filtro aire deportivo Bosch",
        "FIL-002",
        "Filtros",
        "Bosch",
        "Alto flujo de aire para mayor rendimiento del motor.",
        35_000,
        40,
        8,
    ),
    (
        "Filtro de combustible Denso",
        "FIL-003",
        "Filtros",
        "Denso",
        "Filtra impurezas antes del inyector. Cambia cada 30.000 km.",
        22_000,
        50,
        10,
    ),
    (
        "Aceite Mobil 1 5W-30 1L",
        "ACE-001",
        "Aceites",
        "Mobil",
        "Aceite 100% sintético para motores modernos. Reduce fricción y consumo.",
        32_000,
        80,
        15,
    ),
    (
        "Aceite Castrol GTX 10W-40 4L",
        "ACE-002",
        "Aceites",
        "Castrol",
        "Semisintético gasolina y diésel. Protege en arranque en frío.",
        98_000,
        50,
        10,
    ),
    (
        "Batería Bosch S4 45Ah",
        "BAT-001",
        "Baterías",
        "Bosch",
        "Batería 45Ah para compactos. 18 meses garantía. Libre de mantenimiento.",
        280_000,
        12,
        3,
    ),
    (
        "Batería ACDelco 60Ah",
        "BAT-002",
        "Baterías",
        "ACDelco",
        "60Ah libre de mantenimiento para SUV y sedanes medianos.",
        320_000,
        8,
        2,
    ),
    (
        "Amortiguador delantero Monroe",
        "AMO-001",
        "Amortiguadores",
        "Monroe",
        "Gas nitrógeno de alta durabilidad. Mejora el control y la estabilidad. Unitario.",
        185_000,
        20,
        4,
    ),
    (
        "Kit amortiguadores traseros Monroe",
        "AMO-002",
        "Amortiguadores",
        "Monroe",
        "Par trasero con gas nitrógeno. Mejora el confort y la estabilidad.",
        340_000,
        10,
        2,
    ),
    (
        "Bombillo H4 60/55W Bosch par",
        "LUZ-001",
        "Luces",
        "Bosch",
        "Par bombillos halógenos de larga vida útil. Instalación directa.",
        28_000,
        70,
        15,
    ),
    (
        "Kit LED H7 6000K Bosch par",
        "LUZ-002",
        "Luces",
        "Bosch",
        "Conversión LED. +200% luminosidad. Menor consumo energético.",
        95_000,
        30,
        6,
    ),
    (
        "Correa distribución Gates",
        "COR-001",
        "Correas",
        "Gates",
        "Alta resistencia. Cambia cada 60.000 km. Fabricación alemana.",
        75_000,
        25,
        5,
    ),
    (
        "Kit correa distribución Gates",
        "COR-002",
        "Correas",
        "Gates",
        "Kit completo: correa, tensor y rodillo.",
        180_000,
        15,
        3,
    ),
    (
        "Bujías NGK Iridium IX x4",
        "MOT-001",
        "Motor",
        "NGK",
        "Set 4 bujías iridio. Encendido más potente, menor consumo de combustible.",
        85_000,
        40,
        8,
    ),
    (
        "Bomba de agua Bosch",
        "MOT-002",
        "Motor",
        "Bosch",
        "Bomba de agua con rodamiento sellado. Larga vida útil.",
        95_000,
        15,
        3,
    ),
    (
        "Sensor oxígeno lambda Bosch",
        "ELE-001",
        "Eléctrico",
        "Bosch",
        "Sensor O2 para control de mezcla aire/combustible. Sonda upstream.",
        125_000,
        15,
        3,
    ),
    (
        "Alternador remanufacturado ACDelco",
        "ELE-002",
        "Eléctrico",
        "ACDelco",
        "Alternador 12V 70A remanufacturado. 1 año de garantía.",
        420_000,
        6,
        2,
    ),
    (
        "Escobillas limpiaparabrisas Bosch",
        "CAR-001",
        "Carrocería",
        "Bosch",
        'Par de escobillas grafito 24". Limpieza silenciosa y uniforme.',
        48_000,
        50,
        10,
    ),
]

COMPATIBILIDADES = [
    ("FRE-001", [0, 1, 6, 8]),
    ("FRE-002", [2, 4, 9, 11]),
    ("FIL-001", list(range(15))),
    ("FIL-002", [2, 4, 9, 11, 13]),
    ("ACE-001", [0, 1, 2, 4, 6, 8, 10, 12, 14]),
    ("ACE-002", [3, 5, 7, 9, 11, 13]),
    ("BAT-001", [0, 1, 6, 8, 10]),
    ("BAT-002", [3, 5, 7, 9, 11, 13]),
    ("AMO-001", [0, 1, 2, 4, 6, 8]),
    ("LUZ-001", [0, 1, 2, 4, 6, 7, 8, 10, 12, 14]),
    ("COR-001", [2, 4, 9, 11]),
    ("MOT-001", [0, 1, 2, 4, 6, 8, 10, 12, 14]),
    ("ELE-001", [0, 1, 2, 4, 6, 8, 10, 12, 14]),
]

PROVEEDORES = [
    (
        "AutoPartes Colombia S.A.S",
        "Carlos Ruiz",
        "3001234567",
        "ventas@autopartescol.com",
        "Calle 80 # 45-20",
        "Bogotá",
    ),
    (
        "Distribuidora Bosch",
        "Ana Martínez",
        "3109876543",
        "distribuidora@bosch.com.co",
        "Av. 68 # 13-50",
        "Bogotá",
    ),
    (
        "Importadora Motorex",
        "Luis Gómez",
        "3207654321",
        "importadora@motorex.co",
        "Cra 50 # 22-10",
        "Medellín",
    ),
    (
        "Repuestos del Valle",
        "Sandra Torres",
        "3154321098",
        "info@repuestosvalle.com",
        "Av. Roosevelt 15",
        "Cali",
    ),
]


class Command(BaseCommand):
    help = "Carga el catálogo de datos de prueba para MOTOPART"

    def add_arguments(self, parser):
        parser.add_argument(
            "--flush",
            action="store_true",
            help="Borra todos los datos existentes antes de cargar",
        )

    def handle(self, *args, **options):
        self.stdout.write("\n🚀 MOTOPART — Cargando datos de prueba\n")

        if options["flush"]:
            self._flush()

        cats = self._categorias()
        marcas = self._marcas()
        veh = self._vehiculos()
        prods = self._productos(cats, marcas)
        self._compatibilidades(prods, veh)
        self._proveedores()
        self._usuario_prueba()

        self.stdout.write(
            self.style.SUCCESS("\n✅ ¡Listo! Abre http://127.0.0.1:8000/\n")
        )

    def _flush(self):
        self.stdout.write("  🗑  Limpiando base de datos...")
        Compatibilidad.objects.all().delete()
        Producto.objects.all().delete()
        Proveedor.objects.all().delete()
        Vehiculo.objects.all().delete()
        ModeloVehiculo.objects.all().delete()
        MarcaVehiculo.objects.all().delete()
        MarcaProducto.objects.all().delete()
        Categoria.objects.all().delete()
        self.stdout.write("  ✅ Base de datos limpia\n")

    def _categorias(self):
        cats = {}
        for nombre, desc, icono in CATEGORIAS:
            c, _ = Categoria.objects.get_or_create(
                nombre=nombre,
                defaults={"descripcion": desc, "icono": icono, "activo": True},
            )
            cats[nombre] = c
        self.stdout.write(f"  ✅ {len(cats)} categorías")
        return cats

    def _marcas(self):
        marcas = {}
        for nombre in MARCAS:
            m, _ = MarcaProducto.objects.get_or_create(nombre=nombre)
            marcas[nombre] = m
        self.stdout.write(f"  ✅ {len(marcas)} marcas")
        return marcas

    def _vehiculos(self):
        veh = []
        for marca_n, modelo_n, anio, motor, version, combustible in VEHICULOS:
            marca_v, _ = MarcaVehiculo.objects.get_or_create(nombre=marca_n)
            modelo_v, _ = ModeloVehiculo.objects.get_or_create(
                marca=marca_v, nombre=modelo_n
            )
            v, _ = Vehiculo.objects.get_or_create(
                modelo=modelo_v,
                anio=anio,
                defaults={
                    "motor": motor,
                    "version": version,
                    "combustible": combustible,
                },
            )
            veh.append(v)
        self.stdout.write(f"  ✅ {len(veh)} vehículos")
        return veh

    def _productos(self, cats, marcas):
        prods = {}
        creados = 0
        for nombre, sku, cat_n, marca_n, desc, precio, stock, stock_min in PRODUCTOS:
            p, creado = Producto.objects.get_or_create(
                sku=sku,
                defaults={
                    "nombre": nombre,
                    "categoria": cats.get(cat_n),
                    "marca": marcas.get(marca_n),
                    "descripcion": desc,
                    "precio": Decimal(str(precio)),
                    "stock": stock,
                    "stock_minimo": stock_min,
                    "activo": True,
                },
            )
            prods[sku] = p
            if creado:
                creados += 1
        self.stdout.write(f"  ✅ {len(prods)} productos ({creados} nuevos)")
        return prods

    def _compatibilidades(self, prods, veh):
        count = 0
        for sku, indices in COMPATIBILIDADES:
            p = prods.get(sku)
            if not p:
                continue
            for i in indices:
                if i < len(veh):
                    _, creado = Compatibilidad.objects.get_or_create(
                        producto=p, vehiculo=veh[i]
                    )
                    if creado:
                        count += 1
        self.stdout.write(f"  ✅ {count} compatibilidades")

    def _proveedores(self):
        for nombre, contacto, tel, correo, dir_, ciudad in PROVEEDORES:
            Proveedor.objects.get_or_create(
                nombre=nombre,
                defaults={
                    "contacto": contacto,
                    "telefono": tel,
                    "correo": correo,
                    "direccion": dir_,
                    "ciudad": ciudad,
                },
            )
        self.stdout.write(f"  ✅ {len(PROVEEDORES)} proveedores")

    def _usuario_prueba(self):
        if not User.objects.filter(username="cliente1").exists():
            u = User.objects.create_user(
                username="cliente1",
                password="motopart123",
                first_name="Juan",
                last_name="Pérez",
                email="juan@ejemplo.com",
            )
            u.perfil.telefono = "3001234567"
            u.perfil.direccion = "Calle 123 # 45-67"
            u.perfil.ciudad = "Bogotá"
            u.perfil.save()
            self.stdout.write("  ✅ Usuario prueba: cliente1 / motopart123")
