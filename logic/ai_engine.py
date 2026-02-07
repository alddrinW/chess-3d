import chess
import chess.engine

class ChessAI:
    def __init__(self, level=5):
        self.engine = chess.engine.SimpleEngine.popen_uci(r"C:\Users\alddr\Documents\Proyecto ia\chess-3d\stockfish\stockfish\stockfish-windows-x86-64-avx2.exe")
        self.level = level

    def get_move(self, board):
        result = self.engine.play(
            board,
            chess.engine.Limit(depth=self.level)
        )
        return result.move

    def close(self):
        self.engine.quit()
