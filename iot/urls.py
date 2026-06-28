from django.urls import path
from .views import (
    LecturaCreateView,
    UltimaLecturaView,
    SesionWiimoteView,
    RepararViaWiimoteView,
    EstadoEquipoView,          # ← nuevo
)

urlpatterns = [
    # Sensores
    path('lecturas/', LecturaCreateView.as_view(), name='crear-lectura'),
    path('equipos/<int:equipo_id>/ultima/', UltimaLecturaView.as_view(), name='ultima-lectura'),
    path('equipos/<int:equipo_id>/estado/', EstadoEquipoView.as_view(), name='estado-equipo'),  # ← nuevo

    # Wiimote
    path('wiimote/sesion/', SesionWiimoteView.as_view(), name='wiimote-sesion'),
    path('wiimote/reparar/', RepararViaWiimoteView.as_view(), name='wiimote-reparar'),
]