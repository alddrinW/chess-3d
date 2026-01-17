import cv2
import mediapipe as mp
import math
import time

# =========================
# HAND TRACKER
# =========================
print(dir(mp))
class HandTracker:
    def __init__(self, cam_index=0):
        self.cap = cv2.VideoCapture(cam_index)

        mp_hands = mp.solutions.hands
        self.hands = mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

    def get_landmarks(self):
        success, frame = self.cap.read()
        if not success:
            return None

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb)

        if not result.multi_hand_landmarks:
            return None

        return result.multi_hand_landmarks[0].landmark


# =========================
# GESTOS
# =========================
def is_pinching(landmarks, threshold=0.045):
    thumb = landmarks[4]
    index = landmarks[8]

    dist = math.dist(
        (thumb.x, thumb.y),
        (index.x, index.y)
    )
    return dist < threshold


# =========================
# MANO → TABLERO
# =========================
def hand_to_board(index_tip):
    """
    Convierte coordenadas normalizadas (0–1)
    al plano del tablero (-4 a 4)
    """
    x = (index_tip.x - 0.5) * 8
    y = (0.5 - index_tip.y) * 8
    return x, y


# =========================
# DETECTOR DE MOVIMIENTOS
# =========================
class DetectorMovimientos:
    def __init__(self, chess_logic, chess3d):
        """
        chess_logic -> ChessLogic
        chess3d     -> Vista 3D (Panda3D)
        """
        self.logic = chess_logic
        self.view = chess3d
        self.hand = HandTracker()

        self.selected_square = None
        self.dragging = False
        self.last_square = None
        self.last_pinch = False

        self.last_time = time.time()

    # =========================
    # UPDATE (loop principal)
    # =========================
    def update(self):
        landmarks = self.hand.get_landmarks()
        if not landmarks:
            self._release_if_needed()
            return

        index_tip = landmarks[8]
        pinch = is_pinching(landmarks)

        x, y = hand_to_board(index_tip)
        square = self.view.pos_to_square(x, y)

        # Puntero visual
        self.view.update_pointer(x, y)

        # Hover visual
        if square != self.last_square:
            self.view.clear_highlights()
            if square:
                self.view.highlight_square(square)
            self.last_square = square

        # =========================
        # PINCH START
        # =========================
        if pinch and not self.last_pinch:
            if square and square in self.view.pieces:
                # Validar que sea turno del jugador
                if self.logic.is_human_piece(square):
                    self.selected_square = square
                    self.dragging = True
                    self.view.start_drag(square)

        # =========================
        # DRAG
        # =========================
        if self.dragging:
            self.view.drag_preview(x, y)

        # =========================
        # DROP
        # =========================
        if not pinch and self.last_pinch and self.dragging:
            self._handle_drop(square)

        self.last_pinch = pinch

    # =========================
    # DROP LOGIC
    # =========================
    def _handle_drop(self, target_square):
        from_sq = self.selected_square

        if target_square and self.logic.make_move(from_sq, target_square):
            # Movimiento legal
            self.view.commit_drag(from_sq, target_square)
            self.view.clear_highlights()

            # IA
            self.view.after_human_move()

        else:
            # Movimiento ilegal
            self.view.cancel_drag()

        self.dragging = False
        self.selected_square = None

    # =========================
    # SEGURIDAD
    # =========================
    def _release_if_needed(self):
        if self.dragging:
            self.view.cancel_drag()
            self.dragging = False
            self.selected_square = None
