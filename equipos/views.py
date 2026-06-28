from django.shortcuts import render, get_object_or_404, redirect
from django.utils.safestring import mark_safe
from .models import Equipo
from .icons import ICONOS_SVG, ICONO_DEFAULT
from iot.models import Falla
from mantenimiento.models import OrdenMantenimiento


def _con_icono(equipo):
    equipo.icono_svg = mark_safe(ICONOS_SVG.get(equipo.nombre, ICONO_DEFAULT))
    return equipo


def lista_equipos(request):
    equipos = [_con_icono(e) for e in Equipo.objects.all()]
    return render(request, 'equipos/lista.html', {'equipos': equipos})


def detalle_equipo(request, equipo_id):
    equipo = get_object_or_404(Equipo, id=equipo_id)
    equipo = _con_icono(equipo)
    return render(request, 'equipos/detalle.html', {'equipo': equipo})


def reparar_equipo(request, equipo_id):
    if request.method == 'POST':
        falla = Falla.objects.filter(equipo_id=equipo_id, resuelta=False).order_by('-fecha').first()
        if falla:
            falla.resuelta = True
            falla.save()
            OrdenMantenimiento.objects.filter(falla=falla).update(estado='completada')
    return redirect('detalle-equipo', equipo_id=equipo_id)