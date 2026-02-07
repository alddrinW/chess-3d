# ui/main_menu.py
from direct.gui.DirectGui import DirectFrame, DirectButton, DirectLabel
from panda3d.core import TextNode


class MainMenu:
    def __init__(self, start_classic, start_challenge):
        self.start_classic = start_classic
        self.start_challenge = start_challenge

        # Contenedor principal
        self.frame = DirectFrame(
            frameColor=(0, 0, 0, 0.4),          # fondo semi-transparente opcional
            frameSize=(-1.0, 1.0, -0.8, 0.8),
            pos=(0, 0, 0),
            parent=base.aspect2d                # importante: parent al aspect2d
        )

        # Título
        self.title = DirectLabel(
            text="Bienvenido al Chess 3D",
            parent=self.frame,
            scale=0.2,
            pos=(0, 0, 0.6),
            text_align=TextNode.ACenter,
            frameColor=(0, 0, 0, 0),
            text_fg=(1, 1, 1, 1)
        )

        self.subtitle = DirectLabel(
            text="Controla el juego con tu mano",
            parent=self.frame,
            scale=0.1,
            pos=(0, 0, 0.45),
            text_align=TextNode.ACenter,
            frameColor=(0, 0, 0, 0),
            text_fg=(0.8, 0.8, 0.8, 1)
        )

        self.btn_classic = DirectButton(
            text="Modo Clásico",
            parent=self.frame,
            scale=0.1,
            pos=(0, 0, 0.1),
            command=self._on_classic,
            frameColor=(0.2, 0.6, 0.2, 1),      # verde suave
            text_fg=(1, 1, 1, 1)
        )

        self.btn_challenge = DirectButton(
            text="Modo Desafíos",
            parent=self.frame,
            scale=0.1,
            pos=(0, 0, -0.1),
            command=self._on_challenge,
            frameColor=(0.6, 0.2, 0.2, 1),      # rojo suave
            text_fg=(1, 1, 1, 1)
        )

        # Al crearse, lo mostramos por defecto
        self.show()

    def _on_classic(self):
        self.hide()               # ← solo ocultamos, no destruimos
        self.start_classic()

    def _on_challenge(self):
        self.hide()
        self.start_challenge()

    def show(self):
        if self.frame:
            self.frame.show()

    def hide(self):
        if self.frame:
            self.frame.hide()

    def destroy(self):
        if self.frame:
            self.frame.destroy()
            self.frame = None


class ChallengeMenu:
    def __init__(self, start_with_difficulty):
        self.start_with_difficulty = start_with_difficulty

        self.frame = DirectFrame(
            frameColor=(0, 0, 0, 0.4),
            frameSize=(-1.0, 1.0, -0.8, 0.8),
            pos=(0, 0, 0),
            parent=base.aspect2d
        )

        self.title = DirectLabel(
            text="Elige Dificultad",
            parent=self.frame,
            scale=0.15,
            pos=(0, 0, 0.6),
            text_align=TextNode.ACenter,
            frameColor=(0, 0, 0, 0),
            text_fg=(1, 1, 1, 1)
        )

        self.btn_easy = DirectButton(
            text="Fácil (Mate en 2)",
            parent=self.frame,
            scale=0.08,
            pos=(0, 0, 0.2),
            command=lambda: self._select("easy"),
            frameColor=(0.2, 0.6, 0.2, 1),
            text_fg=(1, 1, 1, 1)
        )

        self.btn_medium = DirectButton(
            text="Medio (Mate en 3)",
            parent=self.frame,
            scale=0.08,
            pos=(0, 0, 0.0),
            command=lambda: self._select("medium"),
            frameColor=(0.6, 0.6, 0.2, 1),
            text_fg=(1, 1, 1, 1)
        )

        self.btn_hard = DirectButton(
            text="Difícil (Mate en 5)",
            parent=self.frame,
            scale=0.08,
            pos=(0, 0, -0.2),
            command=lambda: self._select("hard"),
            frameColor=(0.6, 0.2, 0.2, 1),
            text_fg=(1, 1, 1, 1)
        )

        # Mostrar al crearse
        self.show()

    def _select(self, difficulty):
        self.hide()               # ← ocultamos en vez de destruir
        self.start_with_difficulty(difficulty)

    def show(self):
        if self.frame:
            self.frame.show()

    def hide(self):
        if self.frame:
            self.frame.hide()

    def destroy(self):
        if self.frame:
            self.frame.destroy()
            self.frame = None