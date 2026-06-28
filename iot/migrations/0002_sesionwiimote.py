from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('equipos', '0002_equipo_icono'),
        ('iot', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SesionWiimote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('inicio', models.DateTimeField(auto_now_add=True)),
                ('activa', models.BooleanField(default=True)),
                ('equipo', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='sesiones_wiimote',
                    to='equipos.equipo',
                )),
            ],
            options={'ordering': ['-inicio']},
        ),
    ]