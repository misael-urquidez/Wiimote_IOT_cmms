from .models import Falla
from mantenimiento.models import OrdenMantenimiento


def evaluar_lectura(lectura):
    """
    Revisa si una lectura excede los umbrales del equipo.
    Si los excede, crea automáticamente una Falla y una OrdenMantenimiento.
    """
    equipo = lectura.equipo

    es_golpe = getattr(lectura, 'golpe', False)

    if es_golpe:
        falla_activa = Falla.objects.filter(equipo=equipo, resuelta=False).order_by('-fecha').first()
        if falla_activa:
            return falla_activa

        severidad = 'alta' if lectura.movimiento >= 1.5 else 'media'

        falla = Falla.objects.create(
            equipo=equipo,
            lectura=lectura,
            descripcion="Vibración o inclinación excesiva detectada",
            severidad=severidad,
        )

        OrdenMantenimiento.objects.create(
            equipo=equipo,
            falla=falla,
            tipo='preventivo',
        )

        return falla

    return None