# Generated for CMMS-Wii realtime Wiimote readings

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('iot', '0002_sesionwiimote'),
    ]

    operations = [
        migrations.AddField(
            model_name='lecturasensor',
            name='movimiento',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='lecturasensor',
            name='magnitud',
            field=models.FloatField(default=0.0),
        ),
        migrations.AddField(
            model_name='lecturasensor',
            name='golpe',
            field=models.BooleanField(default=False),
        ),
    ]
