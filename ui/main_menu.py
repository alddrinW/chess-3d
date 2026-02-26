"""
ui/main_menu.py
===============
NOTA: Con la integración PyQt6, el menú principal y el selector de dificultad
ahora viven en SidebarWidget (ui/sidebar_widget.py).
Este archivo se mantiene como stub compatible para no romper importaciones
existentes en el código base.
"""


class MainMenu:
    """Stub — reemplazado por SidebarWidget en la UI PyQt6."""

    def __init__(self, start_classic=None, start_challenge=None):
        self._start_classic = start_classic
        self._start_challenge = start_challenge
        # Sin elementos DirectGui ya que Qt maneja todo el UI

    def show(self):
        pass

    def hide(self):
        pass

    def destroy(self):
        pass


class ChallengeMenu:
    """Stub — reemplazado por SidebarWidget en la UI PyQt6."""

    def __init__(self, start_with_difficulty=None):
        self._start_with_difficulty = start_with_difficulty

    def show(self):
        pass

    def hide(self):
        pass

    def destroy(self):
        pass