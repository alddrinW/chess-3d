from direct.gui.DirectGui import DirectFrame, DirectButton, OnscreenText
from panda3d.core import TextNode


class GameOverScreen:
    def __init__(self, base, result="win", on_main_menu=None):
        """
        Pantalla de fin de partida (victoria o derrota)
        
        Parámetros:
            base: instancia principal de ShowBase (ChessApp)
            result: "win" o "lose"
            on_main_menu: callback para volver al menú principal
        """
        self.base = base
        self.on_main_menu = on_main_menu
        
        # Fondo semi-transparente (cubre toda la pantalla)
        self.frame = DirectFrame(
            frameColor=(0, 0, 0, 0.65),          # negro semitransparente
            frameSize=(-2, 2, -1.5, 1.5),        # cubre casi toda la pantalla
            pos=(0, 0, 0),
            sortOrder=100                        # encima de todo
        )
        
        # Título grande
        title_text = "¡GANASTE!" if result == "win" else "¡PERDISTE!"
        title_color = (0.1, 0.8, 0.1, 1) if result == "win" else (0.9, 0.1, 0.1, 1)
        
        self.title = OnscreenText(
            text=title_text,
            pos=(0, 0.45),                       # un poco más arriba
            scale=0.28,
            fg=title_color,
            align=TextNode.ACenter,
            # Fuente opcional - si no existe, usa la por defecto
            font=base.loader.loadFont("models/fonts/DejaVuSans-Bold.ttf") 
                 if hasattr(base.loader, 'loadFont') else None,
            parent=self.frame
        )
        
        # Mensaje secundario
        msg = "¡Excelente partida, maestro!" if result == "win" else "¡Mejor suerte la próxima vez!"
        self.message = OnscreenText(
            text=msg,
            pos=(0, 0.08),
            scale=0.09,
            fg=(1, 1, 1, 1),
            align=TextNode.ACenter,
            parent=self.frame
        )
        
        # Botón "Menú Principal"
        self.main_menu_btn = DirectButton(
            text="Menú Principal",
            scale=0.13,
            pos=(0, 0, -0.45),
            text_scale=0.65,
            text_pos=(0, -0.12),
            frameColor=(0.15, 0.55, 0.95, 1),
            frameSize=(-2.2, 2.2, -0.7, 0.7),
            text_fg=(1, 1, 1, 1),
            command=self._return_to_main,
            parent=self.frame,
            relief="raised",
            rolloverSound=None,
            clickSound=None
        )
        
        # Empieza oculta
        self.frame.hide()


    def show(self):
        """Muestra la pantalla de fin de partida"""
        self.frame.show()


    def hide(self):
        """Oculta la pantalla"""
        self.frame.hide()


    def destroy(self):
        """Destruye completamente la pantalla (opcional)"""
        if self.frame:
            self.frame.destroy()
            self.frame = None


    def _return_to_main(self):
        """Acción al presionar el botón"""
        self.hide()
        if self.on_main_menu:
            self.on_main_menu()
        # Opcional: destruir después de usar
        # self.destroy()