import chess
import chess.engine

class ChessLogic:
    def __init__(self, difficulty="medium"):
        self.board = chess.Board()
        self.set_difficulty(difficulty)

    # =====================
    # DIFICULTAD
    # =====================
    def set_difficulty(self, difficulty):
        self.difficulty = difficulty

        if difficulty == "easy":
            self.depth = 1
        elif difficulty == "medium":
            self.depth = 3
        elif difficulty == "hard":
            self.depth = 6
        else:
            self.depth = 2

    # =====================
    # MOVIMIENTO HUMANO
    # =====================
    def make_move(self, from_square, to_square):
        """
        from_square: 'e2'
        to_square:   'e4'
        """
        move = chess.Move.from_uci(from_square + to_square)

        if move in self.board.legal_moves:
            self.board.push(move)
            return True
        return False

    # =====================
    # IA (SIN MOTOR EXTERNO)
    # =====================
    def ai_move_simple(self):
        """IA básica por profundidad"""
        best_move = None
        best_score = -9999

        for move in self.board.legal_moves:
            self.board.push(move)
            score = self.evaluate_board()
            self.board.pop()

            if score > best_score:
                best_score = score
                best_move = move

        if best_move:
            self.board.push(best_move)
            return best_move.uci()

        return None

    # =====================
    # EVALUACIÓN SIMPLE
    # =====================
    def evaluate_board(self):
        values = {
            chess.PAWN: 1,
            chess.KNIGHT: 3,
            chess.BISHOP: 3,
            chess.ROOK: 5,
            chess.QUEEN: 9,
            chess.KING: 0
        }

        score = 0
        for piece_type in values:
            score += len(self.board.pieces(piece_type, chess.WHITE)) * values[piece_type]
            score -= len(self.board.pieces(piece_type, chess.BLACK)) * values[piece_type]

        return score

    # =====================
    # ESTADO DEL JUEGO
    # =====================
    def is_game_over(self):
        return self.board.is_game_over()

    def result(self):
        return self.board.result()
