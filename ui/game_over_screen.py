"""
ui/game_over_screen.py
======================
NOTA: Con la integración PyQt6, la pantalla de fin de partida
es ahora un QDialog (GameOverDialog en ui/pyqt_main.py).
Este archivo se mantiene como stub compatible para no romper
importaciones en render/chess_3d.py.
"""


class GameOverScreen:
    """Stub — reemplazado por GameOverDialog en la UI PyQt6."""

    def __init__(self, base=None, result="win", on_main_menu=None):
        self._base = base
        self._result = result
        self._on_main_menu = on_main_menu
        # La notificación de fin de juego es enviada al QMainWindow
        # a través de ChessMainWindow._update_sidebar_state()

    def show(self):
        pass

    def hide(self):
        pass

    def destroy(self):
        pass