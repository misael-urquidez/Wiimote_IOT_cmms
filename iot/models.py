from django.db import models
from equipos.models import Equipo


class LecturaSensor(models.Model):
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='lecturas')
    timestamp = models.DateTimeField(auto_now_add=True)
    vibracion = models.FloatField()
    inclinacion = models.FloatField()
    temperatura = models.FloatField(null=True, blank=True)
    movimiento = models.FloatField(default=0.0)
    magnitud = models.FloatField(default=0.0)
    golpe = models.BooleanField(default=False)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.equipo.nombre} - {self.timestamp:%H:%M:%S}"


class Falla(models.Model):
    SEVERIDAD_CHOICES = [
        ('baja', 'Baja'),
        ('media', 'Media'),
        ('alta', 'Alta'),
    ]
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='fallas')
    lectura = models.ForeignKey(LecturaSensor, on_delete=models.SET_NULL, null=True)
    descripcion = models.CharField(max_length=200)
    severidad = models.CharField(max_length=20, choices=SEVERIDAD_CHOICES)
    fecha = models.DateTimeField(auto_now_add=True)
    resuelta = models.BooleanField(default=False)

    def __str__(self):
        return f"Falla en {self.equipo.nombre} ({self.severidad})"


class SesionWiimote(models.Model):
    """
    Registro de qué equipo tiene el Wiimote vinculado en este momento.
    Solo puede haber una sesión activa a la vez.
    """
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name='sesiones_wiimote')
    inicio = models.DateTimeField(auto_now_add=True)
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ['-inicio']

    def __str__(self):
        estado = "activa" if self.activa else "cerrada"
        return f"Wiimote → {self.equipo.nombre} ({estado})"