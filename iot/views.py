from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import LecturaSensor, SesionWiimote, Falla
from .serializers import LecturaSensorSerializer
from .utils import evaluar_lectura
from equipos.models import Equipo
from mantenimiento.models import OrdenMantenimiento


class LecturaCreateView(generics.CreateAPIView):
    """Recibe una lectura nueva (POST) y evalúa si genera una falla."""
    queryset = LecturaSensor.objects.all()
    serializer_class = LecturaSensorSerializer

    def perform_create(self, serializer):
        lectura = serializer.save()
        evaluar_lectura(lectura)


class UltimaLecturaView(generics.RetrieveAPIView):
    """Devuelve la lectura más reciente de un equipo (para el dashboard)."""
    serializer_class = LecturaSensorSerializer

    def get_object(self):
        equipo_id = self.kwargs['equipo_id']
        return LecturaSensor.objects.filter(equipo_id=equipo_id).first()

    def retrieve(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj is None:
            return Response({'sin_datos': True})
        return Response(self.get_serializer(obj).data)


# ── Sesión Wiimote ────────────────────────────────────────────────────────────

class SesionWiimoteView(APIView):
    """
    GET  /api/wiimote/sesion/       → sesión activa actual (o null)
    POST /api/wiimote/sesion/       → vincular Wiimote a un equipo
                                      body: {"equipo_id": 2}
    DELETE /api/wiimote/sesion/     → desvincular (cerrar sesión activa)
    """

    def get(self, request):
        sesion = SesionWiimote.objects.filter(activa=True).first()
        if sesion is None:
            return Response({'activa': False})
        return Response({
            'activa': True,
            'sesion_id': sesion.id,
            'equipo_id': sesion.equipo.id,
            'equipo_nombre': sesion.equipo.nombre,
            'inicio': sesion.inicio,
        })

    def post(self, request):
        equipo_id = request.data.get('equipo_id')
        if not equipo_id:
            return Response({'error': 'equipo_id requerido'}, status=400)
        try:
            equipo = Equipo.objects.get(id=equipo_id)
        except Equipo.DoesNotExist:
            return Response({'error': 'Equipo no encontrado'}, status=404)

        # Cierra cualquier sesión activa anterior
        SesionWiimote.objects.filter(activa=True).update(activa=False)

        sesion = SesionWiimote.objects.create(equipo=equipo)
        return Response({
            'activa': True,
            'sesion_id': sesion.id,
            'equipo_id': equipo.id,
            'equipo_nombre': equipo.nombre,
        }, status=201)

    def delete(self, request):
        count = SesionWiimote.objects.filter(activa=True).update(activa=False)
        return Response({'desvinculado': count > 0})


class RepararViaWiimoteView(APIView):
    """
    POST /api/wiimote/reparar/
    El script del Wiimote llama esto cuando el usuario presiona el botón A.
    Resuelve la falla activa del equipo vinculado y cierra la OT.
    """
    def post(self, request):
        sesion = SesionWiimote.objects.filter(activa=True).first()
        if sesion is None:
            return Response({'error': 'No hay sesión Wiimote activa'}, status=400)

        equipo = sesion.equipo
        falla = Falla.objects.filter(equipo=equipo, resuelta=False).order_by('-fecha').first()

        if falla is None:
            return Response({'resultado': 'sin_falla', 'equipo': equipo.nombre})

        falla.resuelta = True
        falla.save()
        OrdenMantenimiento.objects.filter(falla=falla).update(estado='completada')

        return Response({
            'resultado': 'reparado',
            'equipo': equipo.nombre,
            'falla_id': falla.id,
        })
    


class EstadoEquipoView(APIView):
    """
    GET /api/equipos/<equipo_id>/estado/
    Devuelve si hay una Falla sin resolver para el equipo.
    El dashboard usa esto en lugar de los valores de la última lectura
    para determinar si mostrar alerta, de modo que la lectura de heartbeat
    (con valores bajos) no oculte una falla activa.
    """
    def get(self, request, equipo_id):
        falla = Falla.objects.filter(
            equipo_id=equipo_id,
            resuelta=False
        ).order_by('-fecha').first()
 
        if falla is None:
            return Response({'hay_falla': False, 'falla': None})
 
        return Response({
            'hay_falla': True,
            'falla': {
                'id'         : falla.id,
                'descripcion': falla.descripcion,
                'severidad'  : falla.severidad,
                'fecha'      : falla.fecha,
            }
        })
 



