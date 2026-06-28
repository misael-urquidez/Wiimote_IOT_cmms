from django.urls import path
from .views import lista_equipos, detalle_equipo, reparar_equipo

urlpatterns = [
    path('', lista_equipos, name='lista-equipos'),
    path('<int:equipo_id>/', detalle_equipo, name='detalle-equipo'),
    path('<int:equipo_id>/reparar/', reparar_equipo, name='reparar-equipo'),
]