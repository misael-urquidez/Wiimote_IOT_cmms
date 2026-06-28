# CMMS-Wii

Prototipo CMMS en Django que usa un Wiimote como sensor IoT. El Wiimote manda lecturas de acelerometro al backend; una sacudida/golpe fuerte crea una falla y una orden de mantenimiento. El boton A repara la falla activa.

## Flujo de uso

1. Arranca el backend Django.
2. Abre `http://127.0.0.1:8000/equipos/`.
3. Vincula el Wiimote a una maquina.
4. Ejecuta `wiimote_sensor.py`.
5. Sacude/golpea el Wiimote para crear una falla.
6. Presiona A en el Wiimote para marcar la falla como reparada.

## Base de datos

Por defecto el proyecto usa `db.sqlite3`, para que jale rapido en Linux y Windows sin configurar nada.

Para usar MySQL/XAMPP en Windows, primero crea la base con:

```powershell
mysql -u root < database/mysql_xampp_init.sql
```

Si no tienes `mysql` en el PATH, importa `database/mysql_xampp_init.sql` desde phpMyAdmin.

Luego arranca Django con estas variables en PowerShell:

```powershell
$env:CMMS_DB = "mysql"
$env:CMMS_MYSQL_NAME = "cmms_wii"
$env:CMMS_MYSQL_USER = "root"
$env:CMMS_MYSQL_PASSWORD = ""
$env:CMMS_MYSQL_HOST = "127.0.0.1"
$env:CMMS_MYSQL_PORT = "3306"
py manage.py migrate
py manage.py seed_equipos
py manage.py runserver
```

En Linux/macOS el equivalente es:

```bash
export CMMS_DB=mysql
export CMMS_MYSQL_NAME=cmms_wii
export CMMS_MYSQL_USER=root
export CMMS_MYSQL_PASSWORD=''
export CMMS_MYSQL_HOST=127.0.0.1
export CMMS_MYSQL_PORT=3306
python3 manage.py migrate
python3 manage.py seed_equipos
python3 manage.py runserver
```

## Instalacion en Windows

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements-windows.txt
py manage.py migrate
py manage.py seed_equipos
py manage.py runserver
```

En otra terminal, con el Wiimote ya emparejado por Bluetooth:

```powershell
.\venv\Scripts\Activate.ps1
py wiimote_sensor.py --url http://127.0.0.1:8000 --audio auto
```

Para forzar la bocina real del Wiimote en Windows:

```powershell
py wiimote_sensor.py --url http://127.0.0.1:8000 --audio speaker
```

`--audio auto` intenta bocina HID y si falla usa rumble. `--audio speaker` fuerza bocina y no cae a rumble, util para probar si Windows esta dejando escribir al speaker. Si `hidapi` no encuentra el control, cierra apps que lo agarren en exclusiva y vuelve a emparejarlo.

## Instalacion en Linux

```bash
python3 -m venv venv
. venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements-linux.txt
python3 manage.py migrate
python3 manage.py seed_equipos
python3 manage.py runserver
```

En otra terminal:

```bash
. venv/bin/activate
sudo venv/bin/python wiimote_sensor.py --url http://127.0.0.1:8000 --audio auto
```

El Wiimote debe aparecer en `/dev/input` como `Nintendo Wii Remote` y `Nintendo Wii Remote Accelerometer`.

## Controles

- Sacudir/golpear: crea falla y sacude el icono en la pagina de detalle.
- A: repara la falla activa del equipo vinculado.
- B: pausa/reanuda envio de lecturas.
- HOME: sale del script.

## Opciones utiles del sensor

```bash
python wiimote_sensor.py --help
```

- `--url`: URL del backend, por defecto `http://localhost:8000`.
- `--intervalo`: segundos entre lecturas normales, por defecto `0.5`.
- `--delta`: sensibilidad del golpe, por defecto `1.5` g.
- `--cooldown`: segundos minimos entre golpes, por defecto `2.0`.
- `--audio`: `auto`, `speaker`, `rumble` u `off`.
- `--plataforma`: fuerza `Linux` o `Windows` solo para pruebas.
