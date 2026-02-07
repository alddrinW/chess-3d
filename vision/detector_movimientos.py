import cv2
import mediapipe as mp
import math
import time

from logic.ai_engine import ChessAI 

# =========================
# MEDIAPIPE UTILS
# =========================
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils


class HandTracker:
    def __init__(self, cam_index=0):
        self.cap = cv2.VideoCapture(cam_index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        self.hands = mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7
        )

    def get_landmarks(self):
        success, frame = self.cap.read()
        if not success:
            return None, None

        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result = self.hands.process(rgb)

        if result.multi_hand_landmarks:
            hand_landmarks = result.multi_hand_landmarks[0]
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp_hands.HAND_CONNECTIONS
            )
            return hand_landmarks.landmark, frame

        return None, frame

    def release(self):
        self.cap.release()
        cv2.destroyAllWindows()


def is_pinching(landmarks, threshold=0.045):
    thumb = landmarks[4]
    index = landmarks[8]
    dist = math.dist((thumb.x, thumb.y), (index.x, index.y))
    return dist < threshold


def hand_to_board(index_tip):
    scale = 14          # mientras más alto, mas alejado la camara del tablero
    x = (index_tip.x - 0.5) * scale
    y = (0.5 - index_tip.y) * scale
    return x, y


class DetectorMovimientos:
    def __init__(self, chess_logic, chess3d):
        self.logic = chess_logic
        self.view = chess3d
        self.hand = HandTracker()

        self.ai = ChessAI(level=6)  # STOCKFISH

        self.selected_square = None
        self.dragging = False
        self.last_square = None
        self.last_pinch = False

    # =========================
    # UPDATE LOOP
    # =========================
    def update(self):
        landmarks, frame = self.hand.get_landmarks()

        if landmarks:
            index_tip = landmarks[8]
            pinch = is_pinching(landmarks)

            x, y = hand_to_board(index_tip)
            square = self.view.pos_to_square(x, y)

            # Siempre actualizar el cursor/mano
            self.view.update_pointer(x, y)

            # Resaltar casilla actual
            if square != self.last_square:
                self.view.clear_highlights()
                if square:
                    self.view.highlight_square(square)
                self.last_square = square

            # -------------------------------
            # LÓGICA DE PINCH INVERTIDA
            # -------------------------------
            if pinch and not self.last_pinch:
                # Pinch DETECTADO (transición de no-pinch → pinch)
                
                if not self.dragging:
                    # Si NO estamos arrastrando → intentamos SELECCIONAR
                    if square and square in self.view.pieces:
                        if self.logic.is_human_piece(square):
                            self.selected_square = square
                            self.dragging = True
                            self.view.start_drag(square)
                            print(f"[DEBUG] Pieza seleccionada: {square}")
                else:
                    # Si YA estamos arrastrando → Pinch = SOLTAR
                    self._handle_drop(square)
                    print(f"[DEBUG] Soltando pieza en: {square or 'fuera del tablero'}")

            if self.dragging:
                # Mientras esté arrastrando, seguir la mano (sin pinch)
                self.view.drag_preview(x, y)

            self.last_pinch = pinch

        if frame is not None:
            small_frame = cv2.resize(frame, (320, 240))
            cv2.imshow("Hand Tracking", small_frame)
            cv2.waitKey(1)

    # =========================
    # DROP LOGIC - CORREGIDO PARA CHALLENGE
    # =========================
    def _handle_drop(self, target_square):
        from_sq = self.selected_square

        # Si soltaste fuera del tablero, cancelar
        if target_square is None:
            self.view.cancel_drag()
            print(f"[DEBUG] Soltado fuera del tablero: {from_sq}")
            self.dragging = False
            self.selected_square = None
            self.view.clear_highlights()
            return

        # Validar y ejecutar movimiento humano
        success = self.logic.make_move(from_sq, target_square)

        if success:
            # Movimiento humano válido → actualiza visual
            self.view.update_pieces_from_logic()
            print(f"[DEBUG] Movimiento humano válido: {from_sq} -> {target_square}")

            # AHORA SÍ: en modo challenge también dejamos que la IA responda
            # (pero sin validación estricta como en tu lógica anterior)
            if not self.logic.is_game_over() and self.logic.board.turn == self.logic.ai_color:
                ai_move = self.ai.get_move(self.logic.board)
                if ai_move and ai_move in self.logic.board.legal_moves:
                    self.logic.board.push(ai_move)
                    print(f"[IA CHALLENGE] Movió: {ai_move.uci()}")
                    self.view.update_pieces_from_logic()  # ← actualiza visual después de IA
                else:
                    print("[IA CHALLENGE] No encontró movimiento válido")
        else:
            # Movimiento inválido → cancela y devuelve pieza
            self.view.cancel_drag()
            print(f"[DEBUG] Movimiento inválido: {from_sq} -> {target_square}")

        # Limpiar estado
        self.dragging = False
        self.selected_square = None
        self.view.clear_highlights()

    def cleanup(self):
        self.ai.close()
        self.hand.release()

