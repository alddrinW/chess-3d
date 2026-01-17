from panda3d.core import loadPrcFileData
# Forzar X11 y configuración estable para GPU Intel integrada
loadPrcFileData("", """
load-display x11
win-size 1280 720
window-title Chess3D
framebuffer-multisample 1
multisamples 4
""")

from direct.showbase.ShowBase import ShowBase
from panda3d.core import LineSegs, TextNode, DirectionalLight, AmbientLight, Vec4


# Tamaño original de las piezas y tablero: 0.17717 o 0.18701

# =====================
# CONSTANTES
# =====================
TABLERO_Z = 1
GRID_Z = TABLERO_Z + 0.02
TEXTO_Z = TABLERO_Z + 0.02
PIECE_Z = TABLERO_Z + 0.9
PIECE_CENTER_OFFSET = 0.2  # prueba entre 0.05 y 0.2

# =====================
# MODELOS DE PIEZAS
# =====================
MODELS = {
    "P": "models/PeonD.glb", #tamaño 0.18701
    "R": "models/PeonD.glb",
    "N": "models/CaballoD_scaled_4.glb", #tamaño 0.19701
    "B": "models/DoradoAlfil_scaled_3.glb", #tamaño 0.19701
    "Q": "models/PeonD.glb", #tamaño 0.17701
    "K": "models/reyD_scaled_2.glb", #tamaño 0.16701

    "p": "models/NegroPeon_scaled.glb",
    "r": "models/PeonN.glb",
    "n": "models/NegroCaballo_scaled_3.glb", #tamaño 0.19701
    "b": "models/NegroAlfil_scaled.glb",
    "q": "models/NegroPeon_scaled.glb", #tamaño 0.17701
    "k": "models/NegroPeon_scaled.glb",
}

# =====================
# POSICIÓN INICIAL
# =====================
INITIAL_POSITION = {
    # Blancas
    "a1": "R", "b1": "N", "c1": "B", "d1": "Q",
    "e1": "K", "f1": "B", "g1": "N", "h1": "R",
    "a2": "P", "b2": "P", "c2": "P", "d2": "P",
    "e2": "P", "f2": "P", "g2": "P", "h2": "P",

    # Negras
    "a8": "r", "b8": "n", "c8": "b", "d8": "q",
    "e8": "k", "f8": "b", "g8": "n", "h8": "r",
    "a7": "p", "b7": "p", "c7": "p", "d7": "p",
    "e7": "p", "f7": "p", "g7": "p", "h7": "p",
}

# =====================
# CONVERSIÓN CASILLA → POSICIÓN 3D
# =====================
def square_to_pos(square):
    col = ord(square[0]) - ord('a')   # a-h → 0-7
    row = int(square[1]) - 1          # 1-8 → 0-7
    x = col - 3.5
    y = row - 3.5
    return x, y, PIECE_Z

# =====================
# CLASE PRINCIPAL
# =====================
class Chess3D(ShowBase):

    def __init__(self):
        ShowBase.__init__(self)

        # =====================
        # LUCES BÁSICAS
        # =====================

        # Luz ambiental
        ambient = AmbientLight("ambient")
        ambient.setColor(Vec4(0.3, 0.3, 0.3, 1))
        ambient_np = self.render.attachNewNode(ambient)
        self.render.setLight(ambient_np)

        # Luz direccional (sol)
        sun = DirectionalLight("sun")
        sun.setColor(Vec4(0.9, 0.9, 0.9, 1))
        sun_np = self.render.attachNewNode(sun)
        sun_np.setHpr(-30, -60, 0)
        self.render.setLight(sun_np)


        self.board_root = self.render.attachNewNode("board_root")

        # Cámara
        #self.disableMouse()
        self.camera.setPos(0, -15, 15)
        self.camera.lookAt(0, 0, 0)

        # Tablero
        self.tablero = self.loader.loadModel("models/tablero_9x9.glb")
        self.tablero.reparentTo(self.board_root)
        min_b, max_b = self.tablero.getTightBounds()
        self.tablero.setZ(TABLERO_Z - min_b.z)

        # Grid + textos
        self.draw_grid()
        self.draw_square_labels()

        # Piezas
        self.pieces = {}
        self.setup_initial_position()

    # =====================
    # COLOCAR PIEZA
    # =====================
    def place_piece(self, model_path, square, piece_code):
        piece_root = self.board_root.attachNewNode("piece_root")

        model = self.loader.loadModel(model_path)
        model.reparentTo(piece_root)

        # Corregir pivote del modelo
        min_b, max_b = model.getTightBounds()
        center_x = (min_b.x + max_b.x) / 2
        center_y = (min_b.y + max_b.y) / 2
        model.setPos(-center_x, -center_y, -min_b.z)

        # Ajuste fino hacia el centro de la casilla (LOCAL)
        model.setZ(14.5)   # ajusta entre 0.05 y 0.2

        # Posicionar en casilla
        piece_root.setPos(*square_to_pos(square))

        # Rotación correcta
        if piece_code.islower():
            piece_root.setHpr(180, 90, 0)
        else:
            piece_root.setHpr(0, 90, 0)

        self.pieces[square] = piece_root

    # =====================
    # POSICIÓN INICIAL
    # =====================
    def setup_initial_position(self):
        for square, piece_code in INITIAL_POSITION.items():
            self.place_piece(MODELS[piece_code], square, piece_code)

    # =====================
    # GRID
    # =====================
    def draw_grid(self):
        lines = LineSegs()
        lines.setColor(1, 1, 1, 1)

        for i in range(-4, 5):
            lines.moveTo(i, -4, GRID_Z)
            lines.drawTo(i, 4, GRID_Z)
            lines.moveTo(-4, i, GRID_Z)
            lines.drawTo(4, i, GRID_Z)

        self.board_root.attachNewNode(lines.create())

    # =====================
    # TEXTOS DE CASILLAS
    # =====================
    def draw_square_labels(self):
        for col in range(8):
            for row in range(8):
                square = f"{chr(ord('a') + col)}{row + 1}"

                text = TextNode(square)
                text.setText(square)
                text.setAlign(TextNode.ACenter)
                text.setTextColor(1, 1, 0, 1)

                text_np = self.board_root.attachNewNode(text)
                text_np.setScale(0.35)
                text_np.setPos(col - 3.5, row - 3.5, TEXTO_Z)
                text_np.setHpr(0, -90, 0)