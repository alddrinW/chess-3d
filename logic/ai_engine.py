import chess
import chess.engine

class ChessAI:
    def __init__(self, level=5):
        self.engine = chess.engine.SimpleEngine.popen_uci("/usr/bin/stockfish")
        self.level = level

    def get_move(self, board):
        result = self.engine.play(
            board,
            chess.engine.Limit(depth=self.level)
        )
        return result.move

    def close(self):
        self.engine.quit()
