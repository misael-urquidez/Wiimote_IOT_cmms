#!/usr/bin/env python3
"""
Cliente Wiimote para CMMS-Wii, Linux + Windows.

Linux:
    sudo python3 wiimote_sensor.py --url http://127.0.0.1:8000
    Usa evdev con el Wiimote ya conectado por Bluetooth.

Windows:
    py -m pip install hidapi requests
    py wiimote_sensor.py --url http://127.0.0.1:8000
    Usa HID para leer acelerometro/botones y, cuando sea posible,
    reproducir tonos por la bocina del Wiimote.
"""

import argparse
import os
import math
import platform
import socket
import sys
import threading
import time

import requests

try:
    import evdev
    from evdev import ecodes
except Exception:
    evdev = None
    ecodes = None

try:
    import hid
except Exception:
    hid = None

NEUTRO = 512
ESCALA = 204.0
DELTA_GOLPE = 1.5
COOLDOWN_SEG = 2.0

BTN_A = 'A'
BTN_B = 'B'
BTN_HOME = 'HOME'


def acc_a_g(x, y, z):
    ax = (x - NEUTRO) / ESCALA
    ay = (y - NEUTRO) / ESCALA
    az = (z - NEUTRO) / ESCALA
    return ax, ay, az, math.sqrt(ax**2 + ay**2 + az**2)


def _normalizar_eje(valor, info=None):
    if info is None:
        return valor
    try:
        minimo = info.min
        maximo = info.max
    except AttributeError:
        return valor
    if maximo <= minimo:
        return valor
    return int(round((valor - minimo) * 1023 / (maximo - minimo)))


def acc_a_vibracion(x, y, z):
    _, _, _, mag = acc_a_g(x, y, z)
    return round(max(0.0, mag - 1.0), 3)


def acc_a_inclinacion(x, y, z):
    _, _, az, mag = acc_a_g(x, y, z)
    if mag == 0:
        return 0.0
    return round(math.degrees(math.acos(max(-1.0, min(1.0, az / mag)))), 2)


class DetectorGolpe:
    def __init__(self, delta=DELTA_GOLPE, cooldown=COOLDOWN_SEG):
        self.delta = delta
        self.cooldown = cooldown
        self._mag_prev = 1.0
        self._ultimo = 0.0

    def evaluar(self, x, y, z):
        _, _, _, mag = acc_a_g(x, y, z)
        delta = abs(mag - self._mag_prev)
        self._mag_prev = mag
        ahora = time.time()
        if delta >= self.delta and (ahora - self._ultimo) >= self.cooldown:
            self._ultimo = ahora
            return True, round(delta, 3), round(mag, 3)
        return False, round(delta, 3), round(mag, 3)


class ClienteCMMS:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()

    def sesion_activa(self):
        try:
            r = self.session.get(f"{self.base_url}/api/wiimote/sesion/", timeout=3)
            data = r.json()
            return data if data.get('activa') else None
        except Exception as e:
            print(f"[ERROR] No se pudo contactar el servidor: {e}")
            return None

    def enviar_lectura(self, equipo_id, vibracion, inclinacion, movimiento, magnitud, golpe=False):
        payload = {
            'equipo': equipo_id,
            'vibracion': vibracion,
            'inclinacion': inclinacion,
            'temperatura': None,
            'movimiento': movimiento,
            'magnitud': magnitud,
            'golpe': golpe,
        }
        try:
            r = self.session.post(f"{self.base_url}/api/lecturas/", json=payload, timeout=3)
            return r.status_code == 201
        except Exception as e:
            print(f"\n[ERROR] enviar_lectura: {e}")
            return False

    def reparar(self):
        try:
            r = self.session.post(f"{self.base_url}/api/wiimote/reparar/", timeout=3)
            return r.json()
        except Exception as e:
            print(f"\n[ERROR] reparar: {e}")
            return None

    def desvincular(self):
        try:
            self.session.delete(f"{self.base_url}/api/wiimote/sesion/", timeout=3)
        except Exception:
            pass


# IMA ADPCM para la bocina del Wiimote.
_STEP_TABLE = [
    7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31,
    34, 37, 41, 45, 50, 55, 60, 66, 73, 80, 88, 97, 107, 118, 130,
    143, 157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408,
    449, 494, 544, 598, 658, 724, 796, 876, 963, 1060, 1166, 1282,
    1411, 1552,
]
_INDEX_TABLE = [-1, -1, -1, -1, 2, 4, 6, 8, -1, -1, -1, -1, 2, 4, 6, 8]


def _pcm_to_adpcm(samples):
    adpcm, predictor, step_idx = [], 0, 0
    for s in samples:
        step = _STEP_TABLE[step_idx]
        diff = s - predictor
        nib = 8 if diff < 0 else 0
        if diff < 0:
            diff = -diff
        for bit in (4, 2, 1):
            if diff >= step:
                nib |= bit
                diff -= step
            step >>= 1
        step = _STEP_TABLE[step_idx]
        dq = step >> 3
        if nib & 4:
            dq += step
        if nib & 2:
            dq += step >> 1
        if nib & 1:
            dq += step >> 2
        predictor += -dq if (nib & 8) else dq
        predictor = max(-32768, min(32767, predictor))
        step_idx = max(0, min(56, step_idx + _INDEX_TABLE[nib & 7]))
        adpcm.append(nib)
    return bytes((adpcm[i] & 0xF) | ((adpcm[i + 1] & 0xF) << 4) for i in range(0, len(adpcm) - 1, 2))


def _tono_pcm(hz, seg, sr=8000, amp=0.65):
    n = int(seg * sr)
    return [
        int(math.sin(2 * math.pi * hz * i / sr) * amp * 32767 * min(i / n * 10, 1.0, (n - i) / n * 10))
        for i in range(n)
    ]


def _melodia_adpcm(notas, sr=8000):
    pcm = []
    for hz, seg in notas:
        pcm += [0] * int(seg * sr) if hz == 0 else _tono_pcm(hz, seg, sr)
    return _pcm_to_adpcm(pcm)


MELODIAS_BOCINA = {
    'conexion': [(880, 0.08), (0, 0.03), (1047, 0.12)],
    'falla': [(400, 0.15), (0, 0.02), (300, 0.15), (0, 0.02), (200, 0.25)],
    'reparado': [(523, 0.08), (659, 0.08), (784, 0.08), (0, 0.02), (1047, 0.25)],
    'sin_falla': [(440, 0.20)],
}


class BocinaL2CAP:
    HID_OUT = 0xA2
    RPT_EN = 0x14
    RPT_MUTE = 0x19
    RPT_CFG = 0x13
    RPT_DATA = 0x18

    def __init__(self, mac):
        self.mac = mac
        self._sock = None

    def _conectar(self):
        s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)
        s.settimeout(3.0)
        s.connect((self.mac, 0x13))
        self._sock = s

    def _send(self, data):
        self._sock.send(bytes([self.HID_OUT]) + bytes(data))

    def tocar(self, melodia):
        self._conectar()
        try:
            reproducir_bocina(self._send, melodia)
        finally:
            self._sock.close()
            self._sock = None


class BocinaHID:
    def __init__(self, dev):
        self.dev = dev

    def _send(self, data):
        packet = list(data)[:22]
        packet += [0x00] * (22 - len(packet))
        self.dev.write(bytes(packet))

    def tocar(self, melodia):
        reproducir_bocina(self._send, melodia)


def _write_register(send, address, payload):
    data = list(payload)[:16]
    data += [0x00] * (16 - len(data))
    send([
        0x16,
        (address >> 24) & 0xFF,
        (address >> 16) & 0xFF,
        (address >> 8) & 0xFF,
        address & 0xFF,
        len(payload),
        *data,
    ])
    time.sleep(0.015)


def _iniciar_bocina(send):
    # Secuencia HID del Wiimote: habilita speaker, configura ADPCM y desmutea.
    send([0x14, 0x04])
    time.sleep(0.03)
    send([0x19, 0x04])
    time.sleep(0.03)
    _write_register(send, 0x04A20009, [0x01])
    _write_register(send, 0x04A20001, [0x08, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
    _write_register(send, 0x04A20008, [0x01])
    send([0x19, 0x00])
    time.sleep(0.03)


def reproducir_bocina(send, melodia, sr=8000):
    adpcm = _melodia_adpcm(MELODIAS_BOCINA[melodia], sr)
    chunk = 20
    bps = sr / 2
    pausa = chunk / bps

    _iniciar_bocina(send)

    for i in range(0, len(adpcm), chunk):
        bloque = adpcm[i:i + chunk]
        pad = bytes(chunk - len(bloque))
        send([0x18, len(bloque) << 3] + list(bloque) + list(pad))
        time.sleep(pausa * 0.9)

    time.sleep(0.05)
    send([0x19, 0x04])
    send([0x14, 0x00])

def _rumble_evdev(dev, duracion=0.3):
    if not evdev or not ecodes:
        return
    try:
        effect = evdev.ff.Effect(
            ecodes.FF_RUMBLE, -1, 0,
            evdev.ff.Trigger(0, 0),
            evdev.ff.Replay(int(duracion * 1000), 0),
            evdev.ff.EffectType(ff_rumble_effect=evdev.ff.Rumble(strong_magnitude=0xFFFF, weak_magnitude=0x0000)),
        )
        eid = dev.upload_effect(effect)
        dev.write(ecodes.EV_FF, eid, 1)
        time.sleep(duracion)
        dev.write(ecodes.EV_FF, eid, 0)
        dev.erase_effect(eid)
    except Exception:
        pass


class Audio:
    def __init__(self, device, mode='auto'):
        self.device = device
        self.mode = mode
        self._speaker_ok = mode in ('auto', 'speaker')

    def _run(self, melodia, fallback):
        def inner():
            if self.mode == 'off':
                return
            if self.mode == 'rumble':
                fallback()
                return
            if self._speaker_ok:
                try:
                    self.device.tocar_bocina(melodia)
                    return
                except Exception as e:
                    self._speaker_ok = False
                    msg = f"\n[bocina] {e}"
                    if self.mode == 'speaker':
                        print(msg)
                        return
                    print(f"{msg} -> usando rumble")
            fallback()
        threading.Thread(target=inner, daemon=True).start()

    def conexion(self):
        self._run('conexion', lambda: self.device.rumble(0.15))

    def falla(self):
        self._run('falla', lambda: self.device.rumble(0.6))

    def reparado(self):
        self._run('reparado', lambda: (self.device.rumble(0.1), time.sleep(0.08), self.device.rumble(0.2)))

    def sin_falla(self):
        self._run('sin_falla', lambda: self.device.rumble(0.1))


class LinuxWiimote:
    nombre = 'Linux evdev'

    def __init__(self, accel_dev, btn_dev, mac):
        self.accel_dev = accel_dev
        self.btn_dev = btn_dev
        self.mac = mac
        self.x = self.y = self.z = NEUTRO
        self._pressed = set()
        self._last_pressed = set()
        self._stop = False
        self._absinfo = {}

    @classmethod
    def encontrar(cls):
        if evdev is None:
            raise RuntimeError('evdev no esta instalado. En Linux instala python-evdev o usa el venv correcto.')
        accel_dev = None
        btn_dev = None
        mac = None
        for path in evdev.list_devices():
            try:
                dev = evdev.InputDevice(path)
                if 'Nintendo Wii Remote Accelerometer' in dev.name:
                    accel_dev = dev
                elif dev.name == 'Nintendo Wii Remote':
                    btn_dev = dev
                    mac = (dev.uniq or '').upper() or None
            except Exception:
                continue
        if not accel_dev or not btn_dev:
            return None
        return cls(accel_dev, btn_dev, mac)

    def iniciar(self):
        self._cargar_absinfo()
        threading.Thread(target=self._leer_acc, daemon=True).start()
        try:
            self.btn_dev.grab()
        except Exception:
            pass

    def cerrar(self):
        self._stop = True
        try:
            self.btn_dev.ungrab()
        except Exception:
            pass

    def _cargar_absinfo(self):
        for code in (ecodes.ABS_X, ecodes.ABS_Y, ecodes.ABS_Z, ecodes.ABS_RX, ecodes.ABS_RY, ecodes.ABS_RZ):
            try:
                self._absinfo[code] = self.accel_dev.absinfo(code)
            except Exception:
                pass

    def _leer_acc(self):
        eje_por_codigo = {
            ecodes.ABS_X: 'x',
            ecodes.ABS_RX: 'x',
            ecodes.ABS_Y: 'y',
            ecodes.ABS_RY: 'y',
            ecodes.ABS_Z: 'z',
            ecodes.ABS_RZ: 'z',
        }
        try:
            for ev in self.accel_dev.read_loop():
                if self._stop:
                    return
                if ev.type == ecodes.EV_ABS and ev.code in eje_por_codigo:
                    valor = _normalizar_eje(ev.value, self._absinfo.get(ev.code))
                    setattr(self, eje_por_codigo[ev.code], valor)
        except Exception as e:
            print(f"\n[accel] lector detenido: {e}")

    def leer(self):
        current = set()
        try:
            for ev in self.btn_dev.read():
                if ev.type == ecodes.EV_KEY and ev.value:
                    if ev.code in (ecodes.KEY_ENTER, ecodes.BTN_SOUTH):
                        current.add(BTN_A)
                    elif ev.code in (ecodes.KEY_SPACE, ecodes.BTN_THUMBR):
                        current.add(BTN_B)
                    elif ev.code in (ecodes.KEY_ESC, ecodes.BTN_MODE):
                        current.add(BTN_HOME)
        except BlockingIOError:
            pass
        nuevos = current - self._last_pressed
        self._last_pressed = current
        return self.x, self.y, self.z, nuevos

    def tocar_bocina(self, melodia):
        if not self.mac:
            raise RuntimeError('MAC Bluetooth no detectada')
        BocinaL2CAP(self.mac).tocar(melodia)

    def rumble(self, duracion):
        _rumble_evdev(self.btn_dev, duracion)

    def descripcion(self):
        raw_abs = self.accel_dev.capabilities().get(ecodes.EV_ABS, [])
        abs_codes = {item[0] if isinstance(item, tuple) else item for item in raw_abs}
        nombres = []
        for code in (ecodes.ABS_X, ecodes.ABS_Y, ecodes.ABS_Z, ecodes.ABS_RX, ecodes.ABS_RY, ecodes.ABS_RZ):
            if code in abs_codes:
                nombres.append(ecodes.ABS.get(code, str(code)))
        ejes = ','.join(nombres) or 'sin ejes ABS detectados'
        return f"Acelerometro={self.accel_dev.path} Ejes={ejes} Botones={self.btn_dev.path} MAC={self.mac or 'sin MAC'}"


class WindowsWiimote:
    nombre = 'Windows HID'
    VID = 0x057E
    PIDS = {0x0306, 0x0330}
    BUTTONS = {
        0x0004: BTN_B,
        0x0008: BTN_A,
        0x0080: BTN_HOME,
    }

    def __init__(self, dev, info):
        self.dev = dev
        self.info = info
        self.x = self.y = self.z = NEUTRO
        self._last_pressed = set()

    @classmethod
    def encontrar(cls):
        if hid is None:
            raise RuntimeError('hidapi no esta instalado. En Windows ejecuta: py -m pip install hidapi requests')
        candidatos = [d for d in hid.enumerate() if d.get('vendor_id') == cls.VID and d.get('product_id') in cls.PIDS]
        if not candidatos:
            return None
        info = candidatos[0]
        dev = hid.device()
        dev.open_path(info['path'])
        dev.set_nonblocking(1)
        wii = cls(dev, info)
        wii._set_report_mode()
        return wii

    def _write(self, data):
        packet = list(data)[:22]
        packet += [0x00] * (22 - len(packet))
        self.dev.write(bytes(packet))

    def _set_report_mode(self):
        # 0x31 = botones + acelerometro. 0x04 mantiene el reporte continuo.
        self._write([0x12, 0x04, 0x31])
        time.sleep(0.05)

    def iniciar(self):
        pass

    def cerrar(self):
        try:
            self.dev.close()
        except Exception:
            pass

    def leer(self):
        while True:
            data = self.dev.read(32)
            if not data:
                break
            if data[0] in (0x31, 0x33) and len(data) >= 6:
                mask = (data[1] << 8) | data[2]
                self.x = data[3] * 4
                self.y = data[4] * 4
                self.z = data[5] * 4
                current = {nombre for bit, nombre in self.BUTTONS.items() if mask & bit}
                nuevos = current - self._last_pressed
                self._last_pressed = current
                return self.x, self.y, self.z, nuevos
        return self.x, self.y, self.z, set()

    def tocar_bocina(self, melodia):
        BocinaHID(self.dev).tocar(melodia)

    def rumble(self, duracion):
        try:
            self._write([0x11, 0x01])
            time.sleep(duracion)
            self._write([0x11, 0x00])
        except Exception:
            pass

    def descripcion(self):
        product = self.info.get('product_string') or 'Nintendo Wiimote'
        path = self.info.get('path')
        if isinstance(path, bytes):
            path = path.decode(errors='ignore')
        return f"{product} HID={path}"


def encontrar_wiimote(forzar=None):
    sistema = (forzar or platform.system()).lower()
    if sistema.startswith('win'):
        return WindowsWiimote.encontrar()
    return LinuxWiimote.encontrar()


def correr(base_url, intervalo, delta_golpe, cooldown, plataforma=None, audio_mode='auto', debug_raw=False):
    cliente = ClienteCMMS(base_url)
    detector = DetectorGolpe(delta=delta_golpe, cooldown=cooldown)

    print(f"CMMS-Wii | Servidor: {base_url}")
    print(f"Script: {os.path.abspath(__file__)}")
    print(f"Plataforma: {plataforma or platform.system()}")
    print('Buscando Wiimote conectado por Bluetooth...')

    try:
        wiimote = encontrar_wiimote(plataforma)
    except RuntimeError as e:
        print(f"[ERROR] {e}")
        sys.exit(1)

    if wiimote is None:
        print('[ERROR] No se encontro el Wiimote.')
        print('Linux: verifica /dev/input con cat /proc/bus/input/devices.')
        print('Windows: empareja el control por Bluetooth e instala hidapi.')
        sys.exit(1)

    print(f"OK Wiimote: {wiimote.nombre}")
    print(f"   {wiimote.descripcion()}")

    print('\nVerificando sesion activa...')
    sesion = cliente.sesion_activa()
    if not sesion:
        print(f"Sin maquina vinculada. Ve a {base_url}/equipos/")
        sys.exit(0)

    equipo_id = sesion['equipo_id']
    equipo_nombre = sesion['equipo_nombre']
    print(f"OK Maquina: [{equipo_id}] {equipo_nombre}\n")

    audio = Audio(wiimote, mode=audio_mode)
    wiimote.iniciar()
    audio.conexion()

    pausa = False
    ultimo_hb = 0.0
    ultimo_debug = 0.0

    print(f"Umbral golpe: delta {delta_golpe}g | cooldown: {cooldown}s | lectura: {intervalo}s | audio: {audio_mode}")
    print('  Sacudir/Golpe -> genera FALLA y sacude icono')
    print('  A             -> REPARAR')
    print('  B             -> pausa')
    print('  HOME          -> salir\n')

    try:
        while True:
            x, y, z, botones = wiimote.leer()

            if BTN_HOME in botones:
                print('\n[HOME] Saliendo...')
                break

            if BTN_B in botones:
                pausa = not pausa
                print(f"\n{'Pausa' if pausa else 'Reanudado'}")

            if BTN_A in botones:
                print('\n[A] Reparando...', end=' ', flush=True)
                resultado = cliente.reparar()
                if resultado:
                    if resultado.get('resultado') == 'reparado':
                        print(f"OK Falla resuelta en {resultado['equipo']}")
                        audio.reparado()
                    else:
                        print('Sin fallas activas.')
                        audio.sin_falla()
                else:
                    print('Error de comunicacion.')

            if pausa:
                time.sleep(0.08)
                continue

            if debug_raw and time.time() - ultimo_debug >= 0.25:
                print(f"\rRAW x={x} y={y} z={z} botones={','.join(sorted(botones)) or '-'}      ", end='', flush=True)
                ultimo_debug = time.time()

            vib = acc_a_vibracion(x, y, z)
            inc = acc_a_inclinacion(x, y, z)
            golpe, delta, mag = detector.evaluar(x, y, z)

            ahora = time.time()
            if golpe:
                print(f"\nGOLPE delta={delta}g mag={mag}g -> falla...")
                ok = cliente.enviar_lectura(equipo_id, vib, inc, delta, mag, golpe=True)
                if ok:
                    audio.falla()
                    print('   Enviado. Presiona A para reparar.')
                else:
                    print('   Error al enviar.')
                ultimo_hb = ahora
            elif ahora - ultimo_hb >= intervalo:
                ok = cliente.enviar_lectura(equipo_id, vib, inc, delta, mag, golpe=False)
                ultimo_hb = ahora
                print(
                    f"\r{'OK' if ok else 'XX'} [{equipo_nombre}] "
                    f"raw=({x},{y},{z}) mag={mag:.2f}g delta={delta:.2f}g Vib={vib:.3f}g Inc={inc:.1f}   ",
                    end='', flush=True,
                )

            time.sleep(0.03)

    except KeyboardInterrupt:
        print('\n\nInterrumpido.')
    finally:
        wiimote.cerrar()
        print('Desvinculando...')
        cliente.desvincular()
        print('Hasta luego.')


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--url', default='http://localhost:8000')
    ap.add_argument('--intervalo', type=float, default=0.5)
    ap.add_argument('--delta', type=float, default=DELTA_GOLPE)
    ap.add_argument('--cooldown', type=float, default=COOLDOWN_SEG)
    ap.add_argument('--plataforma', choices=['Linux', 'Windows'], default=None, help='Solo para pruebas; normalmente se autodetecta.')
    ap.add_argument('--audio', choices=['auto', 'speaker', 'rumble', 'off'], default='auto', help='auto intenta bocina y cae a rumble; speaker fuerza bocina HID.')
    ap.add_argument('--debug-raw', action='store_true', help='Muestra valores crudos del acelerometro y botones.')
    args = ap.parse_args()
    correr(args.url, args.intervalo, args.delta, args.cooldown, args.plataforma, args.audio, args.debug_raw)
