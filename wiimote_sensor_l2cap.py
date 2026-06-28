#!/usr/bin/env python3
"""
Cliente Wiimote para CMMS-Wii, Linux SOLO (modo L2CAP directo).

A diferencia de wiimote_sensor.py (que en Linux usa evdev + el driver
hid-wiimote del kernel), este script habla DIRECTO con el Wiimote por
Bluetooth usando un socket L2CAP crudo, igual que ya hace la clase
BocinaL2CAP del script original para la bocina.

Por que existe este script:
    En algunos equipos (sobre todo con adaptadores Bluetooth Intel
    integrados) el driver hid-wiimote del kernel nunca activa el modo
    de reporte continuo del acelerometro (reporte 0x31). El resultado es
    que evdev expone el dispositivo "Nintendo Wii Remote Accelerometer"
    pero nunca manda eventos, aunque el control este conectado y los
    botones si funcionen. Se puede confirmar este problema corriendo:
        sudo evtest /dev/input/event<N-del-acelerometro>
    y viendo que nunca cambia nada al mover el control.

    Este script evita el problema por completo: nosotros mismos abrimos
    el canal L2CAP (PSM 0x13, el "Interrupt channel" del perfil HID) y
    mandamos el comando 0x12,0x04,0x31 para forzar el modo de reporte
    continuo (botones + acelerometro), luego leemos los reportes crudos
    directo del socket.

Requisitos:
    - El Wiimote debe estar EMPAREJADO y CONECTADO por Bluetooth antes
      de correr el script (igual que con el original). Puedes verificar
      con: bluetoothctl info <MAC>
    - Necesitas la direccion MAC del Wiimote. Si no la sabes, corre:
        bluetoothctl devices Connected
      o bien:
        sudo evtest  (busca "Nintendo Wii Remote" en la lista, y si el
      campo Uniq no viene vacio, ahi sale la MAC)

Uso:
    sudo python3 wiimote_sensor_l2cap.py --url http://127.0.0.1:8000 --mac 04:E8:B9:25:CB:0E

    Si omites --mac, el script intenta detectarla solo via evdev (si el
    driver del kernel ya registro el dispositivo).
"""

import argparse
import math
import os
import socket
import subprocess
import sys
import threading
import time

import requests

try:
    import evdev
except Exception:
    evdev = None

NEUTRO = 512
ESCALA = 204.0
DELTA_GOLPE = 1.5
COOLDOWN_SEG = 2.0

BTN_A = 'A'
BTN_B = 'B'
BTN_HOME = 'HOME'

BUTTON_BITS = {
    0x0004: BTN_B,
    0x0008: BTN_A,
    0x0080: BTN_HOME,
}

HID_PSM_CONTROL = 0x11    # Control channel del perfil HID Bluetooth.
HID_PSM = 0x13            # Interrupt channel del perfil HID Bluetooth.


# ---------- utilidades de fisica, iguales a wiimote_sensor.py ----------

def acc_a_g(x, y, z):
    ax = (x - NEUTRO) / ESCALA
    ay = (y - NEUTRO) / ESCALA
    az = (z - NEUTRO) / ESCALA
    return ax, ay, az, math.sqrt(ax ** 2 + ay ** 2 + az ** 2)


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


# ---------- cliente HTTP hacia el CMMS, igual a wiimote_sensor.py ----------

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


# ---------- IMA ADPCM / bocina, igual a wiimote_sensor.py ----------

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


class Audio:
    """Solo bocina por L2CAP. Sin rumble (eso lo da evdev y aqui no lo usamos)."""

    def __init__(self, device, mode='auto'):
        self.device = device
        self.mode = mode

    def _run(self, melodia):
        def inner():
            if self.mode == 'off':
                return
            try:
                self.device.tocar_bocina(melodia)
            except Exception as e:
                print(f"\n[bocina] {e}")
        threading.Thread(target=inner, daemon=True).start()

    def conexion(self):
        self._run('conexion')

    def falla(self):
        self._run('falla')

    def reparado(self):
        self._run('reparado')

    def sin_falla(self):
        self._run('sin_falla')


# ---------- deteccion de MAC ----------

def detectar_mac_evdev():
    """Intenta sacar la MAC del Wiimote desde evdev (campo uniq), si esta disponible."""
    if evdev is None:
        return None
    for path in evdev.list_devices():
        try:
            dev = evdev.InputDevice(path)
            if dev.name == 'Nintendo Wii Remote':
                mac = (dev.uniq or '').upper()
                if mac:
                    return mac
        except Exception:
            continue
    return None


def detectar_mac_bluetoothctl():
    """Intenta sacar la MAC de un Wiimote conectado via bluetoothctl."""
    try:
        salida = subprocess.run(
            ['bluetoothctl', 'devices', 'Connected'],
            capture_output=True, text=True, timeout=5,
        ).stdout
    except Exception:
        return None
    for linea in salida.splitlines():
        partes = linea.split()
        if len(partes) >= 3 and 'Wii' in linea:
            return partes[1].upper()
    return None


# ---------- Wiimote por L2CAP crudo ----------

class L2CAPWiimote:
    nombre = 'Linux L2CAP directo'
    HID_OUT = 0xA2

    def __init__(self, mac):
        self.mac = mac
        self.x = self.y = self.z = NEUTRO
        self._last_pressed = set()
        self._stop = False
        self._send_lock = threading.Lock()

        # El perfil HID Bluetooth exige abrir primero el canal de Control
        # (PSM 0x11). Algunos Wiimote rechazan la conexion al Interrupt
        # channel (0x13) si este paso no se hace antes.
        self.sock_ctrl = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)
        self.sock_ctrl.settimeout(5.0)
        self.sock_ctrl.connect((mac, HID_PSM_CONTROL))

        self.sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_SEQPACKET, socket.BTPROTO_L2CAP)
        self.sock.settimeout(5.0)
        self.sock.connect((mac, HID_PSM))
        self.sock.settimeout(0.5)

    @classmethod
    def encontrar(cls, mac=None):
        mac = mac or detectar_mac_evdev() or detectar_mac_bluetoothctl()
        if not mac:
            return None
        try:
            return cls(mac)
        except OSError as e:
            print(f"[ERROR] No se pudo conectar por L2CAP a {mac}: {e}")
            return None

    def _send(self, data):
        with self._send_lock:
            self.sock.send(bytes([self.HID_OUT]) + bytes(data))

    def iniciar(self):
        # 0x31 = botones + acelerometro, 0x04 = reporte continuo.
        self._send([0x12, 0x04, 0x31])
        time.sleep(0.1)

    def cerrar(self):
        self._stop = True
        try:
            self.sock.close()
        except Exception:
            pass
        try:
            self.sock_ctrl.close()
        except Exception:
            pass

    def leer(self):
        nuevos = set()
        try:
            while True:
                data = self.sock.recv(32)
                if not data:
                    break
                # data[0] == 0xA1 (Input report), data[1] == id del reporte (0x31/0x33).
                if len(data) >= 2 and data[0] == 0xA1 and data[1] in (0x31, 0x33):
                    cuerpo = data[2:]
                    if len(cuerpo) >= 5:
                        mask = (cuerpo[0] << 8) | cuerpo[1]
                        self.x = cuerpo[2] * 4
                        self.y = cuerpo[3] * 4
                        self.z = cuerpo[4] * 4
                        actuales = {nombre for bit, nombre in BUTTON_BITS.items() if mask & bit}
                        nuevos |= actuales - self._last_pressed
                        self._last_pressed = actuales
        except socket.timeout:
            pass
        except OSError:
            pass
        return self.x, self.y, self.z, nuevos

    def tocar_bocina(self, melodia):
        reproducir_bocina(self._send, melodia)

    def rumble(self, duracion):
        try:
            self._send([0x13, 0x01])
            time.sleep(duracion)
            self._send([0x13, 0x00])
        except Exception:
            pass

    def descripcion(self):
        return f"MAC={self.mac} PSM=0x{HID_PSM:02X} (socket L2CAP directo)"


# ---------- loop principal ----------

def correr(base_url, mac, intervalo, delta_golpe, cooldown, audio_mode='auto', debug_raw=False):
    cliente = ClienteCMMS(base_url)
    detector = DetectorGolpe(delta=delta_golpe, cooldown=cooldown)

    print(f"CMMS-Wii (L2CAP) | Servidor: {base_url}")
    print(f"Script: {os.path.abspath(__file__)}")
    print('Buscando Wiimote conectado por Bluetooth (modo L2CAP directo)...')

    wiimote = L2CAPWiimote.encontrar(mac)
    if wiimote is None:
        print('[ERROR] No se encontro/conecto el Wiimote por L2CAP.')
        print('Verifica que este conectado: bluetoothctl info <MAC>')
        print('O pasa la MAC manualmente con --mac AA:BB:CC:DD:EE:FF')
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
    ap.add_argument('--mac', default=None, help='MAC Bluetooth del Wiimote, ej AA:BB:CC:DD:EE:FF. Si se omite, se intenta autodetectar.')
    ap.add_argument('--intervalo', type=float, default=0.5)
    ap.add_argument('--delta', type=float, default=DELTA_GOLPE)
    ap.add_argument('--cooldown', type=float, default=COOLDOWN_SEG)
    ap.add_argument('--audio', choices=['auto', 'off'], default='auto', help='auto reproduce tonos por la bocina; off los desactiva.')
    ap.add_argument('--debug-raw', action='store_true', help='Muestra valores crudos del acelerometro y botones.')
    args = ap.parse_args()
    correr(args.url, args.mac, args.intervalo, args.delta, args.cooldown, args.audio, args.debug_raw)