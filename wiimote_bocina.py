#!/usr/bin/env python3
"""
wiimote_bocina.py — Alertas Wiimote via rumble + LEDs (cwiid)
=============================================================
Usa rumble y LEDs para señalizar eventos ya que el audio del
Wiimote en Linux no tiene soporte estable.

En Windows se puede reemplazar por audio real via WiinUPro.

Patrones:
  conexion  → 2 pulsos cortos  + LED1 encendido
  falla     → 1 rumble largo   + LEDs 1+2 parpadeando
  reparado  → 3 pulsos cortos  + LED1 encendido
  sin_falla → 1 pulso corto    + LED1 encendido

Uso standalone:
    python3 wiimote_bocina.py --sonido falla
    python3 wiimote_bocina.py --sonido reparado --mac 00:22:D7:A3:47:4F

Importar desde wiimote_sensor.py:
    from wiimote_bocina import Audio
    audio = Audio(wiimote=wii)
    audio.falla()
"""

import sys, time, threading, argparse

try:
    import cwiid
    CWIID_OK = True
except ImportError:
    CWIID_OK = False

# ── Patrones de rumble + LED ──────────────────────────────────────────────────

def _pulso(wii, dur):
    wii.rumble = True
    time.sleep(dur)
    wii.rumble = False

def _leds(wii, mascara):
    wii.led = mascara

def _parpadeo_leds(wii, mascara, veces=3, intervalo=0.15):
    for _ in range(veces):
        wii.led = mascara
        time.sleep(intervalo)
        wii.led = 0
        time.sleep(intervalo)
    wii.led = 0

def _patron_conexion(wii):
    _leds(wii, cwiid.LED1_ON)
    _pulso(wii, 0.12)
    time.sleep(0.08)
    _pulso(wii, 0.12)

def _patron_falla(wii):
    _parpadeo_leds(wii, cwiid.LED1_ON | cwiid.LED2_ON, veces=4, intervalo=0.12)
    _pulso(wii, 0.6)
    _parpadeo_leds(wii, cwiid.LED1_ON | cwiid.LED2_ON, veces=2, intervalo=0.12)

def _patron_reparado(wii):
    _leds(wii, cwiid.LED1_ON)
    for _ in range(3):
        _pulso(wii, 0.1)
        time.sleep(0.08)
    _leds(wii, cwiid.LED1_ON)

def _patron_sin_falla(wii):
    _leds(wii, cwiid.LED1_ON)
    _pulso(wii, 0.1)

# ── Fachada Audio ─────────────────────────────────────────────────────────────

class Audio:
    def __init__(self, wiimote=None, mac=None, btn_dev=None):
        """
        wiimote : instancia de cwiid.Wiimote ya conectada (preferido)
        mac     : MAC string para conectar aquí si no se pasa wiimote
        btn_dev : ignorado, compatibilidad con versión anterior
        """
        self._wii = wiimote
        self._mac = mac
        self._ok  = False

        if self._wii is not None:
            self._ok = True
            print("✔ Bocina: rumble+LEDs (wiimote ya conectado)")
        elif mac:
            try:
                self._wii = cwiid.Wiimote(mac)
                self._ok  = True
                print(f"✔ Bocina: rumble+LEDs ({mac})")
            except Exception as e:
                print(f"  Bocina: no se pudo conectar ({e})")
        else:
            print("  Bocina: sin wiimote → sin alerta física")

    def _run(self, fn):
        if not self._ok or self._wii is None:
            return
        def inner():
            try:
                fn(self._wii)
            except Exception as e:
                print(f"[bocina] {e}")
        threading.Thread(target=inner, daemon=True).start()

    def conexion(self):
        self._run(_patron_conexion)

    def falla(self):
        self._run(_patron_falla)

    def reparado(self):
        self._run(_patron_reparado)

    def sin_falla(self):
        self._run(_patron_sin_falla)

# ── Standalone ────────────────────────────────────────────────────────────────

if __name__ == '__main__':
    if not CWIID_OK:
        print("[ERROR] cwiid no está instalado. Activa el venv.")
        sys.exit(1)

    ap = argparse.ArgumentParser()
    ap.add_argument('--sonido', default='conexion',
                    choices=['conexion', 'falla', 'reparado', 'sin_falla'])
    ap.add_argument('--mac', default=None,
                    help='MAC del Wiimote, ej: 00:22:D7:A3:47:4F')
    args = ap.parse_args()

    print("Presiona 1+2 en el Wiimote..." if not args.mac else f"Conectando a {args.mac}...")
    try:
        wii = cwiid.Wiimote(args.mac) if args.mac else cwiid.Wiimote()
    except Exception as e:
        print(f"[ERROR] No se pudo conectar: {e}")
        sys.exit(1)

    print(f"✔ Conectado  |  patrón: {args.sonido}")

    patrones = {
        'conexion' : _patron_conexion,
        'falla'    : _patron_falla,
        'reparado' : _patron_reparado,
        'sin_falla': _patron_sin_falla,
    }
    patrones[args.sonido](wii)

    # Dejar LED1 encendido al terminar (indica conexión activa)
    wii.led = cwiid.LED1_ON
    print("✔ Listo")