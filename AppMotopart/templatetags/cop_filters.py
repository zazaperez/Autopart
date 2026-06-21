"""
Filtros de plantilla para formatear dinero en pesos colombianos.
Uso en templates: {% load cop_filters %}  →  ${{ valor|cop }}
"""

from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter(name="cop")
def cop(valor):
    """Formatea un número como pesos colombianos: sin decimales,
    con punto como separador de miles. Ej: 1500000 -> '1.500.000'.
    El signo '$' se agrega en el template, este filtro NO lo incluye.
    """
    if valor in (None, ""):
        return "0"
    try:
        numero = int(Decimal(valor).to_integral_value(rounding="ROUND_HALF_UP"))
    except (InvalidOperation, TypeError, ValueError):
        return valor

    negativo = numero < 0
    numero = abs(numero)
    texto = f"{numero:,}".replace(",", ".")
    return f"-{texto}" if negativo else texto


@register.filter(name="cop_completo")
def cop_completo(valor):
    """Igual que 'cop' pero incluye el signo '$' delante."""
    return f"${cop(valor)}"
