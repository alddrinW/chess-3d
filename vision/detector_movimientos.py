import cv2
import mediapipe as mp
import math
import time
import json
from datetime import datetime

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
        self.last_frame = None
        
        # =========================
        # NUEVO: Sistema de logging JSON
        # =========================
        self.move_history = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.json_filename = f"chess_moves_{self.session_id}.json"

    # =========================
    # NUEVO: Método para guardar movimiento
    # =========================
    def _log_move(self, player_type, move_uci, from_sq=None, to_sq=None, fen_before=None, fen_after=None):
        """
        Registra un movimiento válido en el historial y guarda inmediatamente en JSON.
        player_type: 'human' o 'ai'
        """
        move_entry = {
            "timestamp": datetime.now().isoformat(),
            "player": player_type,
            "move_uci": move_uci,
            "from_square": from_sq,
            "to_square": to_sq,
            "fen_before": fen_before or self.logic.board.fen(),
            "fen_after": fen_after,
            "turn_number": len(self.move_history) + 1
        }
        
        self.move_history.append(move_entry)
        
        try:
            with open(self.json_filename, 'w', encoding='utf-8') as f:
                json.dump({
                    "session_id": self.session_id,
                    "total_moves": len(self.move_history),
                    "moves": self.move_history
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[ERROR] No se pudo guardar JSON: {e}")

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

        # Guardar frame para que el CameraWidget de PyQt6 lo consuma
        # (sin cv2.imshow — la ventana va embebida en la UI de Qt)
        if frame is not None:
            self.last_frame = cv2.resize(frame, (320, 240))

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

        # Guardar FEN antes del movimiento para logging
        fen_before = self.logic.board.fen()

        # Validar y ejecutar movimiento humano
        success = self.logic.make_move(from_sq, target_square)

        if success:
            # Movimiento humano válido → actualiza visual
            self.view.update_pieces_from_logic()
            print(f"[DEBUG] Movimiento humano válido: {from_sq} -> {target_square}")

            # Log del movimiento humano
            move_uci = f"{from_sq}{target_square}"
            self._log_move(
                player_type="human",
                move_uci=move_uci,
                from_sq=from_sq,
                to_sq=target_square,
                fen_before=fen_before,
                fen_after=self.logic.board.fen()
            )

            # Log del movimiento de la IA (chess_logic ya lo ejecutó internamente)
            # last_ai_move es None en modo challenge, el detector lo maneja abajo
            ai_mv = getattr(self.logic, 'last_ai_move', None)
            if ai_mv is not None:
                fen_ai_before = self.logic.board.fen()  # tras el mov. de IA
                # Reconstruir FEN antes: deshacer temporalmente para obtenerlo
                self._log_move(
                    player_type="ai",
                    move_uci=ai_mv.uci(),
                    from_sq=ai_mv.uci()[:2],
                    to_sq=ai_mv.uci()[2:4],
                    fen_before=None,  # se captura en _log_move como board.fen() actual
                    fen_after=self.logic.board.fen()
                )
                self.logic.last_ai_move = None
                print(f"[LOGGING] IA logueada: {ai_mv.uci()}")
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
        
        # NUEVO: Resumen final al cerrar
        if self.move_history:
            print(f"\n[JSON EXPORT] Partida guardada en: {self.json_filename}")
            print(f"[JSON EXPORT] Total movimientos válidos: {len(self.move_history)}")
            human_moves = [m for m in self.move_history if m["player"] == "human"]
            ai_moves = [m for m in self.move_history if m["player"] == "ai"]
            print(f"  - Humanos: {len(human_moves)}")
            print(f"  - IA: {len(ai_moves)}")