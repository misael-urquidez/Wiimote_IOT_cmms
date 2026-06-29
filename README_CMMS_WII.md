# CMMS-Wii

Prototipo de CMMS (sistema de mantenimiento) hecho en Django que usa un **Wiimote como sensor IoT**. El control manda lecturas de su acelerómetro al backend; una sacudida o golpe fuerte se interpreta como una falla mecánica y genera automáticamente una orden de mantenimiento. Presionar el botón **A** en el Wiimote marca esa falla como reparada.

Corre en **Windows** y **Linux** desde el mismo script (`wiimote_sensor.py`), detectando el sistema operativo automáticamente y usando el backend de hardware correcto en cada caso (HID en Windows, evdev en Linux).

---

## Cómo funciona (arquitectura en breve)

```
Wiimote (Bluetooth)
   │  acelerómetro + botones
   ▼
wiimote_sensor.py   (cliente Python, corre en tu máquina)
   │  HTTP (requests)
   ▼
API REST de Django  (/api/lecturas/, /api/wiimote/sesion/, /api/wiimote/reparar/)
   │
   ▼
Base de datos (SQLite por defecto, o MySQL/XAMPP opcional)
   │
   ▼
Dashboard web  (http://127.0.0.1:8000/equipos/)
```

El proyecto está dividido en 4 apps de Django:

| App            | Qué hace |
|-----------------|----------|
| `equipos`       | Catálogo de "máquinas" (equipos físicos) que se monitorean. Cada equipo tiene un ícono y umbrales de vibración/inclinación. |
| `iot`           | Recibe las lecturas del sensor, decide si una lectura es una falla, y maneja la "sesión" que vincula el Wiimote a un equipo. |
| `mantenimiento` | Órdenes de mantenimiento (preventivo/correctivo) generadas a partir de las fallas. |
| `cmms`          | Configuración del proyecto Django (settings, urls raíz). |

El cliente `wiimote_sensor.py` **no es parte de Django** — es un script aparte que corres en tu máquina (la misma donde tienes el Wiimote conectado por Bluetooth) y que le habla al servidor por HTTP, como cualquier otro sensor IoT.

---

## Flujo de uso (resumen)

1. Arranca el backend Django.
2. Abre `http://127.0.0.1:8000/equipos/` y vincula el Wiimote a una máquina.
3. Conecta el Wiimote por Bluetooth.
4. Ejecuta `wiimote_sensor.py`.
5. Sacude/golpea el Wiimote → se crea una falla y una orden de mantenimiento.
6. Presiona **A** en el Wiimote → se marca la falla como reparada.

---

## Instalación

### Windows

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
py -m pip install --upgrade pip
py -m pip install -r requirements-windows.txt
py manage.py migrate
py manage.py seed_equipos
py manage.py runserver
```

En otra terminal, con el Wiimote ya emparejado por Bluetooth (Configuración de Windows → Bluetooth y otros dispositivos):

```powershell
.\venv\Scripts\Activate.ps1
py wiimote_sensor.py --url http://127.0.0.1:8000 --audio auto
```

Para forzar la bocina real del Wiimote en vez del rumble:

```powershell
py wiimote_sensor.py --url http://127.0.0.1:8000 --audio speaker
```

`--audio auto` intenta usar la bocina HID y si falla cae a rumble. `--audio speaker` fuerza la bocina y no cae a rumble — útil para probar si Windows está dejando escribir al speaker. Si `hidapi` no encuentra el control, cierra cualquier app que lo esté usando en exclusiva (ej. otro emulador) y vuelve a emparejarlo.

### Linux

```bash
python3 -m venv venv
. venv/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements-linux.txt
python3 manage.py migrate
python3 manage.py seed_equipos
python3 manage.py runserver
```

En otra terminal, con el Wiimote ya **conectado** por Bluetooth (no solo emparejado — debe aparecer como "Connected" en `bluetoothctl`):

```bash
. venv/bin/activate
sudo venv/bin/python wiimote_sensor.py --url http://127.0.0.1:8000 --audio auto
```

> Usa `sudo venv/bin/python` (la ruta completa al intérprete del venv) en vez de `sudo python3`, para asegurar que `sudo` use el Python del entorno virtual con `evdev` y `requests` ya instalados, y no el Python del sistema.

El Wiimote debe aparecer en `/dev/input` como dos dispositivos separados:

```bash
cat /proc/bus/input/devices | grep -A4 'Wii'
```

deberías ver `Nintendo Wii Remote` (botones) y `Nintendo Wii Remote Accelerometer` (acelerómetro).

---

## Base de datos

Por defecto el proyecto usa `db.sqlite3`, para que funcione de inmediato en Windows y Linux sin configurar nada.

### Usar MySQL/XAMPP en vez de SQLite (opcional)

Primero crea la base:

```powershell
mysql -u root < database/mysql_xampp_init.sql
```

Si no tienes `mysql` en el PATH, importa `database/mysql_xampp_init.sql` desde phpMyAdmin.

Luego arranca Django con estas variables de entorno.

**PowerShell (Windows):**

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

**Linux/macOS:**

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

---

## Controles del Wiimote

| Acción | Efecto |
|---|---|
| Sacudir / golpear | Crea una falla y una orden de mantenimiento; el ícono del equipo se sacude en el dashboard. |
| **A** | Repara la falla activa del equipo vinculado. |
| **B** | Pausa/reanuda el envío de lecturas. |
| **HOME** | Sale del script. |

---

## Opciones del cliente (`wiimote_sensor.py`)

```bash
python wiimote_sensor.py --help
```

| Opción | Descripción | Default |
|---|---|---|
| `--url` | URL del backend Django. | `http://localhost:8000` |
| `--intervalo` | Segundos entre lecturas normales (heartbeat). | `0.5` |
| `--delta` | Sensibilidad del golpe, en g's de diferencia entre lecturas. | `1.5` |
| `--cooldown` | Segundos mínimos entre dos golpes detectados. | `2.0` |
| `--audio` | `auto`, `speaker`, `rumble` u `off`. | `auto` |
| `--plataforma` | Fuerza `Linux` o `Windows`; normalmente se autodetecta. | autodetectado |
| `--debug-raw` | Muestra en vivo los valores crudos del acelerómetro y botones. Útil para diagnosticar problemas de conexión. | desactivado |

---

## API REST

El cliente del Wiimote (o cualquier otro sensor/app que quieras conectar, como una app móvil) habla con estos endpoints:

| Método | Endpoint | Para qué |
|---|---|---|
| `GET` | `/api/wiimote/sesion/` | Devuelve qué equipo tiene el Wiimote vinculado actualmente (o `activa: false` si no hay ninguno). |
| `POST` | `/api/wiimote/sesion/` | Vincula el Wiimote a un equipo. Body: `{"equipo_id": 2}`. |
| `DELETE` | `/api/wiimote/sesion/` | Desvincula (cierra la sesión activa). |
| `POST` | `/api/lecturas/` | Manda una lectura nueva. Body: `{"equipo", "vibracion", "inclinacion", "temperatura", "movimiento", "magnitud", "golpe"}`. Si `golpe: true` y no hay ya una falla activa, se crea una `Falla` + `OrdenMantenimiento` automáticamente. |
| `GET` | `/api/equipos/<id>/ultima/` | Última lectura registrada de un equipo. |
| `GET` | `/api/equipos/<id>/estado/` | Si el equipo tiene una falla sin resolver actualmente. |
| `POST` | `/api/wiimote/reparar/` | Resuelve la falla activa del equipo vinculado en la sesión actual (lo que dispara el botón A). |

Esto es lo que hace posible, por ejemplo, mandar lecturas desde una app de celular en vez del Wiimote: solo necesita hablar el mismo protocolo HTTP/JSON contra `/api/lecturas/`.

---

## Solución de problemas

### En Linux, el acelerómetro manda todo en 0 (o en `512,512,512` fijo) aunque el Wiimote esté conectado

Esto casi siempre es un tema de la **conexión Bluetooth en mal estado**, no del código:

1. Desconecta el control limpio: `bluetoothctl disconnect <MAC>`
2. Vuélvelo a conectar (o presiona un botón en el Wiimote para reactivarlo).
3. Vuelve a correr el script.

Puedes diagnosticar a bajo nivel, sin tu script, con:

```bash
sudo evtest /dev/input/event<N>   # usa el número del dispositivo "Accelerometer"
```

y mover el control. Si ahí tampoco cambian los valores, el problema es 100% de la conexión Bluetooth/kernel, no de `wiimote_sensor.py`. Reconectar el control suele arreglarlo.

### `evdev no esta instalado` en Linux

Asegúrate de estar usando el Python del venv, no el del sistema:

```bash
sudo venv/bin/python wiimote_sensor.py ...
```

en vez de `sudo python3 wiimote_sensor.py ...`.

### `hidapi no esta instalado` en Windows

```powershell
py -m pip install hidapi requests
```

### La bocina no suena (cae siempre a rumble)

Usa `--audio speaker` para forzar la bocina HID y ver el error específico en consola. Causas comunes: otra app tiene el Wiimote agarrado en exclusiva, o el control necesita re-emparejarse.

---

## Próximos pasos / ideas

- App móvil (Flutter) que mande lecturas del acelerómetro del celular al mismo endpoint `/api/lecturas/`, como sensor alterno al Wiimote.
- Dashboard con histórico de lecturas y gráficas de vibración por equipo.
- Notificaciones (push/email) cuando se genera una falla.
