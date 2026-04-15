"""akrocansim — CAN bus J1939 engine simulator (modified for embedded spec + UDP multicast)"""

__version__ = '0.7.0'
__app_name__ = 'J1939 Engine Simulator'

from . import gui

def main() -> None:
    gui.AkrocansimGui()
