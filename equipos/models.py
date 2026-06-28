from django.db import models


class Equipo(models.Model):
    nombre = models.CharField(max_length=100)
    ubicacion = models.CharField(max_length=100, blank=True)
    icono = models.CharField(max_length=10, default='⚙️')
    umbral_vibracion = models.FloatField(default=4.0)
    umbral_inclinacion = models.FloatField(default=15.0)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre