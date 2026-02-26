from panda3d.core import LineSegs, TextNode, DirectionalLight, AmbientLight, Vec4
from direct.gui.DirectGui import DirectFrame, OnscreenText
import chess
# GameOverScreen es ahora un QDialog en PyQt6 (ui/pyqt_main.py)


# =====================
# CONSTANTES
# =====================
TABLERO_Z = 1
GRID_Z = TABLERO_Z + 0.02
TEXTO_Z = TABLERO_Z + 0.02
PIECE_Z = TABLERO_Z + 0.9
PIECE_CENTER_OFFSET = 0.2


# =====================
# CONFIGURACIÓN DE PIEZAS
# =====================
PIECE_CONFIG = {
    "P": {"model": "models/peon_blanco_prueba.glb", "hpr": (0, 90, 0), "offset": (0.0, -0.2, -0.3)},
    "R": {"model": "models/torre_blanca_prueba.glb", "hpr": (0, 90, 0), "offset": (0.0, 0.0, -0.4)},
    "N": {"model": "models/caballo_blanco_prueba.glb", "hpr": (-90, 90, 0), "offset": (0.0, 0.0, -0.4)},
    "B": {"model": "models/alfil_blanco_prueba.glb", "hpr": (0, 90, 0), "offset": (0.0, 0.2, -0.4)},
    "Q": {"model": "models/reina_blanca_prueba.glb", "hpr": (0, 90, 0), "offset": (0.0, 0.2, -0.4)},
    "K": {"model": "models/rey_blanco_prueba.glb", "hpr": (0, 90, 0), "offset": (0.0, 0.3, -0.4)},

    "p": {"model": "models/peon_madera_prueba.glb", "hpr": (180, 90, 0), "offset": (0.0, -0.2, -0.3)},
    "r": {"model": "models/torre_madera_prueba.glb", "hpr": (0, 90, 0), "offset": (0.0, 0.0, -0.4)},
    "n": {"model": "models/caballo_madera_prueba.glb", "hpr": (-90, 90, 0), "offset": (0.0, 0.0, -0.4)},
    "b": {"model": "models/alfil_madera_prueba.glb", "hpr": (0, 90, 0), "offset": (0.0, 0.0, -0.4)},
    "q": {"model": "models/reina_madera_prueba.glb", "hpr": (0, 90, 0), "offset": (0.0, 0.0, -0.4)},
    "k": {"model": "models/rey_madera_prueba.glb", "hpr": (0, 90, 0), "offset": (0.0, 0.3, -0.4)},
}


def square_to_pos(square):
    col = ord(square[0]) - ord('a')
    row = int(square[1]) - 1
    return col - 3.5, row - 3.5, PIECE_Z


class Chess3D:
    def __init__(self, base, logic=None):
        self.base = base
        self.loader = base.loader
        self.render = base.render
        self.camera = base.camera
        self.taskMgr = base.taskMgr
        self.aspect2d = base.aspect2d

        self.logic = logic
        self.pieces = {}
        self.dragging_piece = None
        self.drag_from = None

        ambient = AmbientLight("ambient")
        ambient.setColor(Vec4(0.3, 0.3, 0.3, 1))
        self._ambient_np = self.render.attachNewNode(ambient)
        self.render.setLight(self._ambient_np)

        sun = DirectionalLight("sun")
        sun.setColor(Vec4(0.9, 0.9, 0.9, 1))
        self._sun_np = self.render.attachNewNode(sun)
        self._sun_np.setHpr(-30, -60, 0)
        self.render.setLight(self._sun_np)

        #desabilita el mouse
        #self.base.disableMouse()
        self.camera.setPos(0, -12, 12)
        self.camera.lookAt(0, 0, 0)

        self.board_root = self.render.attachNewNode("board_root")
        self.board_root.hide()

        self._load_hand()
        self.status_np = None

        self.game_over_screen = None
        self.main_menu_callback = None

        self.create_main_menu_button()


    def create_main_menu_button(self):
        """
        El botón de menú principal ahora es gestionado por el SidebarWidget de PyQt6.
        Se mantiene como stub para compatibilidad.
        """
        self.main_menu_btn = None  # La UI Qt maneja la navegación


    def return_to_main_menu(self):
        if self.main_menu_callback:
            self.main_menu_callback()


    def show_game_over(self, result="win"):
        """
        La pantalla de fin de partida ahora es un QDialog en PyQt6.
        Esta función es un stub para compatibilidad.
        La ChessMainWindow detecta el fin de partida en _update_sidebar_state().
        """
        pass


    def set_logic(self, logic):
        self.logic = logic
        self.setup_board()
        self.board_root.show()

        if self.logic.challenge_mode:
            self.status_np = self.aspect2d.attachNewNode(TextNode("status"))
            self.status_np.node().setAlign(TextNode.ACenter)
            self.status_np.node().setTextColor(1, 1, 1, 1)
            self.status_np.setScale(0.07)
            self.status_np.setPos(0, 0, 0.9)
            self.taskMgr.add(self.update_status, "update_status")


    def update_status(self, task):
        if self.logic.challenge_mode:
            txt = f"Dificultad: {self.logic.difficulty.capitalize()} | Mate en {self.logic.max_moves_to_mate}\n"
            txt += f"Intentos restantes: {self.logic.attempts_left}\n"
            txt += f"{self.logic.hint}\n"

            if self.logic.game_over_message:
                txt += self.logic.game_over_message + "\n"
                if "incorrecto" in self.logic.game_over_message.lower():
                    self.taskMgr.doMethodLater(3, self.reset_board, 'reset_after_error')

            if self.status_np:
                self.status_np.node().setText(txt)
        return task.cont


    def reset_board(self, task=None):
        self.logic.reset_attempt()
        self.update_pieces_from_logic()
        self.logic.game_over_message = None
        return task.done if task else None


    def setup_board(self):
        self.tablero = self.loader.loadModel("models/tablero_9x9.glb")
        self.tablero.reparentTo(self.board_root)

        min_b, _ = self.tablero.getTightBounds()
        self.tablero.setZ(TABLERO_Z - min_b.z)

        self.draw_grid()
        self.draw_square_labels()
        self.setup_initial_position()


    def place_piece(self, piece_config, square):
        root = self.board_root.attachNewNode("piece_root")
        model = self.loader.loadModel(piece_config["model"])
        model.reparentTo(root)

        min_b, max_b = model.getTightBounds()
        center_x = (min_b.x + max_b.x) / 2
        center_y = (min_b.y + max_b.y) / 2
        model.setPos(-center_x, -center_y, -min_b.z)

        offset = piece_config.get("offset", (0.0, 0.0, 0.0))
        model.setX(model.getX() + offset[0])
        model.setY(model.getY() + offset[1])
        model.setZ(model.getZ() + offset[2])

        root.setPos(*square_to_pos(square))
        root.setHpr(*piece_config["hpr"])

        self.pieces[square] = root


    def setup_initial_position(self):
        self.update_pieces_from_logic()  # Limpiar + recrear inicial


    def update_pieces_from_logic(self):
        """Sincroniza el tablero visual con la lógica"""
        # Limpiar todo lo viejo
        for node in list(self.pieces.values()):
            node.removeNode()
        self.pieces.clear()

        if not self.logic or not self.logic.board:
            return

        piece_map = self.logic.board.piece_map()

        for square_int, piece in piece_map.items():
            square_name = chess.square_name(square_int)
            symbol = piece.symbol()
            if symbol in PIECE_CONFIG:
                self.place_piece(PIECE_CONFIG[symbol], square_name)
            else:
                print(f"¡Falta modelo para {symbol} en {square_name}!")


    def commit_drag(self, from_sq, to_sq):
        """Solo valida y deja que la lógica maneje todo"""
        if from_sq == to_sq:
            self.cancel_drag()
            return

        if self.logic and self.logic.make_move(from_sq, to_sq):
            self.update_pieces_from_logic()  # ← actualiza TODO después de lógica
            print(f"[DRAG] Movimiento aceptado: {from_sq} → {to_sq}")
        else:
            self.cancel_drag()
            print(f"[DRAG] Movimiento rechazado: {from_sq} → {to_sq}")

        self.dragging_piece = None
        self.drag_from = None


    def pos_to_square(self, x, y):
        if not (-4 <= x <= 4 and -4 <= y <= 4):
            return None
        col = int(x + 4)
        row = int(y + 4)
        if 0 <= col <= 7 and 0 <= row <= 7:
            return f"{chr(ord('a') + col)}{row + 1}"
        return None


    def is_piece_at(self, square):
        return square in self.pieces


    def start_drag(self, square):
        if square not in self.pieces:
            return
        self.dragging_piece = self.pieces[square]
        self.drag_from = square


    def drag_preview(self, x, y):
        if self.dragging_piece:
            self.dragging_piece.setPos(x, y, PIECE_Z + 0.6)


    def cancel_drag(self):
        if self.dragging_piece:
            self.dragging_piece.setPos(*square_to_pos(self.drag_from))
        self.dragging_piece = None
        self.drag_from = None


    def _load_hand(self):
        self.hand_root = self.board_root.attachNewNode("hand_cursor")
        self.hand_model = self.loader.loadModel("models/mano.glb")
        self.hand_model.reparentTo(self.hand_root)

        min_b, max_b = self.hand_model.getTightBounds()
        self.hand_model.setPos(
            -(min_b.x + max_b.x)/2,
            -(min_b.y + max_b.y)/2,
            -max_b.z
        )

        self.hand_root.setScale(0.015)
        self.hand_root.setHpr(-90, 0, 0)
        self.hand_root.setZ(0.4)


    def update_pointer(self, x, y):
        self.hand_root.setPos(x, y, 3)


    def draw_grid(self):
        lines = LineSegs()
        lines.setColor(1, 1, 1, 1)
        for i in range(-4, 5):
            lines.moveTo(i, -4, GRID_Z)
            lines.drawTo(i, 4, GRID_Z)
            lines.moveTo(-4, i, GRID_Z)
            lines.drawTo(4, i, GRID_Z)
        self.board_root.attachNewNode(lines.create())


    def draw_square_labels(self):
        for c in range(8):
            for r in range(8):
                sq = f"{chr(ord('a') + c)}{r + 1}"
                text = TextNode(sq)
                text.setText(sq)
                text.setAlign(TextNode.ACenter)
                text.setTextColor(1, 1, 0, 1)
                np = self.board_root.attachNewNode(text)
                np.setScale(0.35)
                np.setPos(c - 3.5, r - 3.5, TEXTO_Z)
                np.setHpr(0, -90, 0)


    def highlight_square(self, square):
        self.clear_highlights()
        x, y, _ = square_to_pos(square)
        ls = LineSegs()
        ls.setColor(1, 1, 0, 1)
        s = 0.5
        ls.moveTo(x - s, y - s, GRID_Z)
        ls.drawTo(x + s, y - s, GRID_Z)
        ls.drawTo(x + s, y + s, GRID_Z)
        ls.drawTo(x - s, y + s, GRID_Z)
        ls.drawTo(x - s, y - s, GRID_Z)
        self.highlight = self.board_root.attachNewNode(ls.create())


    def clear_highlights(self):
        if hasattr(self, "highlight") and self.highlight:
            self.highlight.removeNode()
            self.highlight = None