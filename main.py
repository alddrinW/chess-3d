from direct.showbase.ShowBase import ShowBase
from render.chess_3d import Chess3D
from logic.chess_logic import ChessLogic
from vision.detector_movimientos import DetectorMovimientos
from ui.main_menu import MainMenu, ChallengeMenu


class ChessApp(ShowBase):
    def __init__(self):
        ShowBase.__init__(self)  # ← ÚNICA instancia de ShowBase

        self.game = None
        self.logic = None
        self.detector = None
        self.challenge_menu = None

        # Crear el menú principal (puede usar self como base si lo necesita)
        self.menu = MainMenu(
            start_classic=self.start_classic,
            start_challenge=self.start_challenge
        )


    def _initialize_game(self):
        if self.game is not None:
            print("El juego ya está inicializado")
            return

        print("Inicializando escena del juego...")
        self.game = Chess3D(self)  # ← pasamos self (la ShowBase) como parámetro
        self.game.main_menu_callback = self.show_main_menu

        if hasattr(self.game, 'main_menu_btn'):
            self.game.main_menu_btn.show()


    def start_classic(self):
        print("Iniciando Modo Clásico...")
        self.menu.hide()
        self._initialize_game()

        self.logic = ChessLogic(difficulty="medium", view=self.game)
        self.game.set_logic(self.logic)

        self.detector = DetectorMovimientos(self.logic, self.game)
        self.taskMgr.add(self.update_detector, "update_detector")  # ← self.taskMgr, no self.game.taskMgr


    def start_challenge(self):
        print("Abriendo menú de desafíos...")
        self.menu.hide()
        self.challenge_menu = ChallengeMenu(self.start_with_difficulty)


    def start_with_difficulty(self, difficulty):
        print(f"Iniciando desafío {difficulty.capitalize()}...")
        self.menu.hide()
        self._initialize_game()

        self.logic = ChessLogic(challenge_mode=True, difficulty=difficulty, view=self.game)
        self.game.set_logic(self.logic)

        self.detector = DetectorMovimientos(self.logic, self.game)
        self.taskMgr.add(self.update_detector, "update_detector")


    def update_detector(self, task):
        if self.detector:
            self.detector.update()
        return task.cont


    def show_main_menu(self):
        print("Volviendo al menú principal...")

        # 1. Detener detector y tareas relacionadas
        self.taskMgr.remove("update_detector")
        if self.detector:
            self.detector = None

        # 2. Limpiar la UI del juego
        if self.game:
            # Botón de menú principal
            if hasattr(self.game, 'main_menu_btn') and self.game.main_menu_btn:
                self.game.main_menu_btn.destroy()

            # Pantalla de game over (si existe)
            if hasattr(self.game, 'game_over_screen') and self.game.game_over_screen:
                self.game.game_over_screen.destroy()

            # Status text → solo si existe (modo desafío)
            if hasattr(self.game, 'status_np') and self.game.status_np:
                self.game.status_np.removeNode()
                self.game.status_np = None  # opcional, para limpiar

            # Ocultar / destruir tablero
            if hasattr(self.game, 'board_root') and self.game.board_root:
                self.game.board_root.removeNode()   # o .hide() si prefieres conservar

            self.game = None  # liberamos la referencia al juego

        # 3. Mostrar de nuevo el menú principal
        if hasattr(self, 'menu') and self.menu:
            self.menu.show()   # ← asegúrate que MainMenu tenga un método show()
        else:
            print("Advertencia: menú principal no encontrado, recreando...")
            self.menu = MainMenu(
                start_classic=self.start_classic,
                start_challenge=self.start_challenge
            )
            # Si MainMenu no tiene .show(), aquí llamas lo que sea necesario para mostrarlo


# =========================
# PROGRAMA PRINCIPAL
# =========================
if __name__ == "__main__":
    app = ChessApp()
    app.run()  # ← ahora sí funciona, porque app es ShowBase