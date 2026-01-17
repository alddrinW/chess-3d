from render.chess_3d import Chess3D
from logic.chess_logic import ChessLogic
from vision.detector_movimientos import DetectorMovimientos

# =========================
# INICIALIZACIÓN
# =========================
game = Chess3D()
logic = ChessLogic()
detector = DetectorMovimientos(logic, game)

# =========================
# TASK PARA ACTUALIZAR DETECTOR
# =========================
def update_detector(task):
    detector.update()
    return task.cont  # continuar ejecutando cada frame

game.taskMgr.add(update_detector, "update_detector")

# =========================
# RUN
# =========================
game.run()
