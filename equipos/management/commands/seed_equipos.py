from django.core.management.base import BaseCommand

from equipos.models import Equipo


EQUIPOS = [
    ('Solder Paste Printer', 'Linea SMT'),
    ('Pick & Place', 'Linea SMT'),
    ('Horno Reflow', 'Linea SMT'),
    ('Cinta Transportadora', 'Linea SMT'),
    ('AOI', 'Inspeccion'),
    ('Flying Probe / ICT', 'Pruebas'),
    ('Selective Soldering', 'Ensamble'),
]


class Command(BaseCommand):
    help = 'Carga las maquinas base del prototipo CMMS-Wii.'

    def handle(self, *args, **options):
        creados = 0
        actualizados = 0
        for nombre, ubicacion in EQUIPOS:
            equipo, created = Equipo.objects.update_or_create(
                nombre=nombre,
                defaults={
                    'ubicacion': ubicacion,
                    'umbral_vibracion': 4.0,
                    'umbral_inclinacion': 15.0,
                    'activo': True,
                },
            )
            if created:
                creados += 1
            else:
                actualizados += 1

        self.stdout.write(self.style.SUCCESS(
            f'Equipos listos: {creados} creados, {actualizados} actualizados.'
        ))
