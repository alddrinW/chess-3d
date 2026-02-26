"""
main.py — Chess 3D con interfaz PyQt6
======================================
Arquitectura:
  1. Se lanza QApplication (PyQt6)
  2. Se muestra la ChessMainWindow
  3. Se obtiene el winId() nativo del PandaWidget
  4. Se inicializa Panda3D (ShowBase) embebido en ese widget
  5. Un QTimer de 16ms llama a base.taskMgr.step() (≈60fps)
  6. El detector de manos escribe frames en last_frame
     y la ChessMainWindow los envía al CameraWidget
"""

import sys
import os

# ── Panda3D config ANTES de importar ShowBase ──────────────────────────────────
# "none" evita que Panda3D abra su propia ventana; abrimos la nuestra más adelante
from panda3d.core import loadPrcFileData, WindowProperties

loadPrcFileData("", "window-type none")
loadPrcFileData("", "audio-library-name null")      # evita warnings de audio
loadPrcFileData("", "model-cache-dir ")             # sin caché molesto
loadPrcFileData("", "background-color 0.07 0.09 0.12 1")

# ── PyQt6 ──────────────────────────────────────────────────────────────────────
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTimer

# ── Panda3D ───────────────────────────────────────────────────────────────────
from direct.showbase.ShowBase import ShowBase

# ── Módulos locales ───────────────────────────────────────────────────────────
from render.chess_3d import Chess3D
from logic.chess_logic import ChessLogic
from vision.detector_movimientos import DetectorMovimientos
from ui.pyqt_main import ChessMainWindow


# ==============================================================================
# CLASE PRINCIPAL DE PANDA3D (sin ventana propia)
# ==============================================================================
class ChessApp(ShowBase):
    """
    Subclase de ShowBase que opera SIN ventana propia.
    La ventana real es el PandaWidget de PyQt6.
    """

    def __init__(self, win_id: int, win_width: int, win_height: int, qt_window: "ChessMainWindow"):
        ShowBase.__init__(self)

        self._qt_window = qt_window        # referencia a la ventana Qt

        # ── Abrir la ventana de Panda3D embebida en el widget Qt ──────────────
        props = WindowProperties()
        props.setParentWindow(win_id)
        props.setSize(win_width, win_height)
        props.setForeground(True)
        props.setUndecorated(True)          # sin bordes propios de Panda3D

        self.openDefaultWindow(props=props)

        # ── Estado del juego ────────────────────────────────────────────────
        self.game = None
        self.logic = None
        self.detector = None
        self._current_mode = None
        self._current_difficulty = None

        # Deshabilitar logo y frame-rate meter
        try:
            self.setFrameRateMeter(False)
        except Exception:
            pass

    # ── MODO CLÁSICO ──────────────────────────────────────────────────────────

    def start_classic_internal(self):
        """Llamado desde ChessMainWindow._start_classic()"""
        self._cleanup_game()
        self._current_mode = "classic"
        self._current_difficulty = None

        self.game = Chess3D(self)
        self.game.main_menu_callback = self._on_menu_requested

        self.logic = ChessLogic(difficulty="medium", view=self.game)
        self.game.set_logic(self.logic)

        self.detector = DetectorMovimientos(self.logic, self.game)
        self._qt_window.register_game_refs(self.logic, self.detector)

    # ── MODO DESAFÍO ──────────────────────────────────────────────────────────

    def start_challenge_internal(self, difficulty: str):
        """Llamado desde ChessMainWindow._start_challenge()"""
        self._cleanup_game()
        self._current_mode = "challenge"
        self._current_difficulty = difficulty

        self.game = Chess3D(self)
        self.game.main_menu_callback = self._on_menu_requested

        self.logic = ChessLogic(challenge_mode=True, difficulty=difficulty, view=self.game)
        self.game.set_logic(self.logic)

        self.detector = DetectorMovimientos(self.logic, self.game)
        self._qt_window.register_game_refs(self.logic, self.detector)

    # ── REINICIAR ─────────────────────────────────────────────────────────────

    def restart_current(self):
        """Reinicia la partida actual con el mismo modo y dificultad."""
        if self._current_mode == "classic":
            self.start_classic_internal()
        elif self._current_mode == "challenge" and self._current_difficulty:
            self.start_challenge_internal(self._current_difficulty)

    # ── VOLVER AL MENÚ ────────────────────────────────────────────────────────

    def _on_menu_requested(self):
        """Callback cuando el juego pide volver al menú."""
        self._cleanup_game()
        self._qt_window.clear_game_refs()

    # ── LIMPIEZA ──────────────────────────────────────────────────────────────

    def _cleanup_game(self):
        """Destruye el juego actual antes de iniciar uno nuevo."""
        # Detener tareas
        self.taskMgr.remove("update_status")
        self.taskMgr.remove("reset_after_error")

        if self.detector:
            try:
                self.detector.cleanup()
            except Exception:
                pass
            self.detector = None

        if self.logic:
            try:
                self.logic.close()
            except Exception:
                pass
            self.logic = None

        if self.game:
            try:
                # Limpiar luces para evitar acumulación en reinicio
                if hasattr(self.game, '_ambient_np') and self.game._ambient_np:
                    self.render.clearLight(self.game._ambient_np)
                    self.game._ambient_np.removeNode()
                if hasattr(self.game, '_sun_np') and self.game._sun_np:
                    self.render.clearLight(self.game._sun_np)
                    self.game._sun_np.removeNode()
                # Limpiar elementos del juego
                if hasattr(self.game, 'status_np') and self.game.status_np:
                    self.game.status_np.removeNode()
                    self.game.status_np = None
                if hasattr(self.game, 'main_menu_btn') and self.game.main_menu_btn:
                    self.game.main_menu_btn.destroy()
                if hasattr(self.game, 'game_over_screen') and self.game.game_over_screen:
                    self.game.game_over_screen.destroy()
                if hasattr(self.game, 'board_root') and self.game.board_root:
                    self.game.board_root.removeNode()
            except Exception:
                pass
            self.game = None

        self._qt_window.clear_game_refs()


# ==============================================================================
# PUNTO DE ENTRADA
# ==============================================================================
def main():
    # ── 1. Iniciar QApplication ───────────────────────────────────────────────
    app = QApplication(sys.argv)
    app.setApplicationName("Chess 3D")
    app.setOrganizationName("Chess3D")

    # ── 2. Crear y mostrar la ventana Qt ──────────────────────────────────────
    window = ChessMainWindow()
    window.show()

    # ── 3. Forzar la creación del handle nativo (winId) de Qt ─────────────────
    # Es necesario hacerlo ANTES de que Panda3D intente embeberse
    app.processEvents()

    panda_widget = window._panda_widget
    panda_widget.ensurePolished()
    # Procesar eventos extra para garantizar que el winId exista
    for _ in range(5):
        app.processEvents()

    win_id = panda_widget.get_win_id()
    win_w = panda_widget.width()
    win_h = panda_widget.height()

    if win_w <= 0 or win_h <= 0:
        win_w, win_h = 760, 600   # fallback

    # ── 4. Inicializar Panda3D embebido ───────────────────────────────────────
    os.chdir(os.path.dirname(os.path.abspath(__file__)))  # CWD = carpeta del proyecto

    panda_app = ChessApp(
        win_id=win_id,
        win_width=win_w,
        win_height=win_h,
        qt_window=window,
    )

    # Notificar al PandaWidget de la instancia Panda3D
    panda_widget.set_panda_base(panda_app)

    # ── 5. Registrar el chess_app en la ventana Qt ────────────────────────────
    window._panda_base = panda_app
    window._update_timer.start()

    # ── 6. Runloop de Qt (Panda3D se actualiza vía QTimer) ───────────────────
    sys.exit(app.exec())


if __name__ == "__main__":
    main()