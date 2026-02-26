import chess
from .ai_engine import ChessAI

class ChessLogic:
    def __init__(self, challenge_mode=False, difficulty="medium", view=None):
        self.view = view
        self.challenge_mode = challenge_mode
        self.difficulty = difficulty.lower()

        self.human_color = chess.WHITE
        self.ai_color = chess.BLACK

        self.attempts_left = 5 if self.challenge_mode else None
        self.human_moves_made = 0
        self.solved = False
        self.game_over_message = None
        # Último movimiento de la IA — lo lee detector_movimientos para loguearlo
        self.last_ai_move = None

        if self.challenge_mode:
            self.ai = ChessAI(level=20)
            self._setup_challenge()
        else:
            self.board = chess.Board()
            self.set_difficulty(difficulty)
            self.ai = ChessAI(level=10)

    def set_difficulty(self, difficulty):
        self.difficulty = difficulty.lower()
        if difficulty == "easy":
            self.depth = 1
        elif difficulty == "medium":
            self.depth = 3
        elif difficulty == "hard":
            self.depth = 6
        else:
            self.depth = 2

    def _setup_challenge(self):
        if self.difficulty == "easy":
            self.fen_name = "Mate in 2 - Bishop Sacrifice"
            self.original_fen = "r1bq2r1/b4pk1/p1pp1p2/1p2pP2/1P2P1PB/3P4/1PPQ2P1/R3K2R w - - 0 1"
            self.hint = "Pista: Rey blanco a h6, negro captura, alfil captura f6 mate."
            self.max_moves_to_mate = 2
        elif self.difficulty == "medium":
            self.fen_name = "Mate in 3 - Rook Sacrifice"
            self.original_fen = "8/8/8/r6Q/PqkPPPPq/RPPPPPPP/1PPPPPPP/RNBQKBNR w - - 0 1"
            self.hint = "Pista: Usa la torre para jaque y fuerza movimientos."
            self.max_moves_to_mate = 3
        elif self.difficulty == "hard":
            self.fen_name = "Excelsior by Sam Loyd"
            self.original_fen = "n1rb4/1p3p1p/1p6/1R5K/8/p3p1Pn/1PP1R3/N6k w - - 0 1"
            self.hint = "Pista: Avanza el peón de b2 a través del tablero para promoverlo."
            self.max_moves_to_mate = 5
        else:
            raise ValueError("Dificultad no válida en challenge mode")

        self.board = chess.Board(self.original_fen)
        self.human_color = self.board.turn
        self.ai_color = not self.human_color
        self.human_moves_made = 0

    def is_human_piece(self, square):
        try:
            sq = chess.parse_square(square)
        except ValueError:
            return False

        piece = self.board.piece_at(sq)
        if piece is None:
            return False

        return piece.color == self.human_color

    def make_move(self, from_square, to_square):
        # Normalizar a minúsculas
        from_square = from_square.lower()
        to_square = to_square.lower()

        if from_square == to_square:
            print(f"[LOGIC] Movimiento nulo ignorado: {from_square} -> {to_square}")
            return False

        uci = from_square + to_square
        print(f"[LOGIC DEBUG] Intentando UCI: {uci}")  # ← agrega este print

        try:
            move = chess.Move.from_uci(uci)
        except chess.InvalidMoveError as e:
            print(f"[LOGIC ERROR] UCI inválido: {uci} | {e}")
            return False

        if move not in self.board.legal_moves:
            print(f"[LOGIC] Movimiento ilegal: {from_square} -> {to_square}")
            return False

        # MODO CHALLENGE
        if self.challenge_mode and self.board.turn == self.human_color:
            board_copy = self.board.copy()
            board_copy.push(move)
            remaining = self.max_moves_to_mate - self.human_moves_made

            if board_copy.is_checkmate():
                if self.human_moves_made + 1 <= self.max_moves_to_mate:
                    self.board.push(move)
                    self.human_moves_made += 1
                    self.solved = True
                    self.game_over_message = f"¡GANASTE! {self.fen_name} resuelto en {self.human_moves_made} movimientos."
                    if self.view:
                        self.view.update_pieces_from_logic()
                    return True
                else:
                    self.game_over_message = "Mate, pero fuera del límite."
                    self.attempts_left -= 1
                    self.reset_attempt()
                    if self.attempts_left <= 0:
                        self.game_over_message = "¡Perdiste! Se acabaron los intentos."
                    return False

            try:
                info = self.ai.engine.analyse(board_copy, chess.engine.Limit(depth=22))
                score = info["score"].relative
                mate_in = None
                if score.is_mate():
                    mate_in = abs(score.mate()) if score.mate() < 0 else 999

                if mate_in is not None and mate_in <= remaining:
                    self.board.push(move)
                    self.human_moves_made += 1
                    if self.view:
                        self.view.update_pieces_from_logic()
                    return True
                else:
                    self.game_over_message = "Movimiento no fuerza el mate exacto. Intento perdido."
                    self.attempts_left -= 1
                    self.reset_attempt()
                    if self.attempts_left <= 0:
                        self.game_over_message = "¡Perdiste! Se acabaron los intentos."
                    return False
            except Exception as e:
                print(f"Error en Stockfish (challenge): {e}")
                if board_copy.is_check():
                    self.board.push(move)
                    self.human_moves_made += 1
                    if self.view:
                        self.view.update_pieces_from_logic()
                    return True
                else:
                    self.game_over_message = "Error validando. Intento perdido."
                    self.attempts_left -= 1
                    self.reset_attempt()
                    return False

        # MODO CLÁSICO
        else:
            self.last_ai_move = None  # limpiar antes de cada turno
            self.board.push(move)
            if self.view:
                self.view.update_pieces_from_logic()

            if not self.board.is_game_over() and self.board.turn == self.ai_color:
                ai_move = self.ai.get_move(self.board)
                if ai_move and ai_move in self.board.legal_moves:
                    self.last_ai_move = ai_move  # exponer para logging externo
                    self.board.push(ai_move)
                    print(f"[IA CLÁSICA] Movió: {ai_move.uci()}")
                    if self.view:
                        self.view.update_pieces_from_logic()
                else:
                    print("[IA CLÁSICA] No encontró movimiento válido")

            return True

    def reset_attempt(self):
        if self.challenge_mode:
            self.board = chess.Board(self.original_fen)
            self.human_moves_made = 0

    def close(self):
        if self.challenge_mode and hasattr(self.ai, 'close'):
            self.ai.close()

    def is_game_over(self):
        if self.challenge_mode:
            return self.solved or (self.attempts_left is not None and self.attempts_left <= 0)
        return self.board.is_game_over()

    def result(self):
        if self.challenge_mode:
            if self.solved:
                return "1-0" if self.human_color == chess.WHITE else "0-1"
            else:
                return "0-1" if self.human_color == chess.WHITE else "1-0"
        return self.board.result()