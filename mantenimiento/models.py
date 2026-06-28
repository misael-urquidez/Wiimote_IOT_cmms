from django.db import models
from equipos.models import Equipo
from iot.models import Falla


class OrdenMantenimiento(models.Model):
    TIPO_CHOICES = [
        ('preventivo', 'Preventivo'),
        ('correctivo', 'Correctivo'),
    ]
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En proceso'),
        ('completada', 'Completada'),
    ]
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE)
    falla = models.ForeignKey(Falla, on_delete=models.SET_NULL, null=True, blank=True)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='preventivo')
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    tecnico_asignado = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"OT-{self.id} {self.equipo.nombre} ({self.estado})"