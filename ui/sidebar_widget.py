"""
ui/sidebar_widget.py
Panel lateral de la interfaz PyQt6 con:
- Selector de modo de juego (Clásico / Desafío)
- Estado del juego y turno
- Botones: Analizar Partida (IA), Descargar Reporte, Reiniciar
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QGroupBox, QComboBox, QSizePolicy, QSpacerItem, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class SidebarWidget(QWidget):
    """Panel lateral con controles de modo, estado y acciones."""

    sig_start_classic   = pyqtSignal()
    sig_start_challenge = pyqtSignal(str)   # difficulty: easy/medium/hard
    sig_restart         = pyqtSignal()
    sig_analyze_game    = pyqtSignal()
    sig_download_report = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(260)
        self.setMaximumWidth(320)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self._current_mode       = None
        self._current_difficulty = "easy"

        self._setup_ui()
        self._apply_styles()

    # ─────────────────────────────────────────
    #  BUILD UI
    # ─────────────────────────────────────────
    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # ── TÍTULO ──────────────────────────────
        title = QLabel("♟  Chess 3D")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("sidebarTitle")
        main_layout.addWidget(title)

        subtitle = QLabel("Control gestual con IA")
        subtitle.setFont(QFont("Segoe UI", 8))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setObjectName("sidebarSubtitle")
        main_layout.addWidget(subtitle)

        main_layout.addSpacing(4)

        # ── SELECTOR DE MODO ────────────────────
        mode_group = QGroupBox("Modo de Juego")
        mode_group.setObjectName("modeGroup")
        mode_layout = QVBoxLayout(mode_group)
        mode_layout.setSpacing(6)

        self._btn_classic = QPushButton("🎮  Modo Clásico")
        self._btn_classic.setObjectName("btnClassic")
        self._btn_classic.setMinimumHeight(40)
        self._btn_classic.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self._btn_classic.clicked.connect(self._on_classic)
        mode_layout.addWidget(self._btn_classic)

        # Desafío + selector de dificultad
        challenge_row = QHBoxLayout()
        challenge_row.setSpacing(4)
        self._btn_challenge = QPushButton("🏆  Desafío")
        self._btn_challenge.setObjectName("btnChallenge")
        self._btn_challenge.setMinimumHeight(40)
        self._btn_challenge.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self._btn_challenge.clicked.connect(self._on_challenge)
        challenge_row.addWidget(self._btn_challenge, stretch=3)

        self._diff_combo = QComboBox()
        self._diff_combo.addItems(["🟢 Fácil", "🟡 Medio", "🔴 Difícil"])
        self._diff_combo.setObjectName("diffCombo")
        self._diff_combo.setMinimumHeight(40)
        self._diff_combo.currentIndexChanged.connect(self._on_difficulty_changed)
        challenge_row.addWidget(self._diff_combo, stretch=2)
        mode_layout.addLayout(challenge_row)

        main_layout.addWidget(mode_group)

        # ── ESTADO DEL JUEGO ────────────────────
        status_group = QGroupBox("Estado")
        status_group.setObjectName("statusGroup")
        status_layout = QVBoxLayout(status_group)
        status_layout.setSpacing(4)

        self._lbl_turn = QLabel("♟ Turno: —")
        self._lbl_turn.setObjectName("lblTurn")
        self._lbl_turn.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_turn.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        status_layout.addWidget(self._lbl_turn)

        self._lbl_status = QLabel("Selecciona un modo para comenzar")
        self._lbl_status.setObjectName("lblStatus")
        self._lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_status.setWordWrap(True)
        self._lbl_status.setFont(QFont("Segoe UI", 9))
        status_layout.addWidget(self._lbl_status)

        self._lbl_attempts = QLabel("")
        self._lbl_attempts.setObjectName("lblAttempts")
        self._lbl_attempts.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_attempts.setVisible(False)
        status_layout.addWidget(self._lbl_attempts)

        main_layout.addWidget(status_group)

        # ── SEPARADOR ───────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setObjectName("separator")
        main_layout.addWidget(sep)

        # ── BOTÓN ANALIZAR PARTIDA (IA) ─────────
        self._btn_analyze = QPushButton("📊  Analizar con IA")
        self._btn_analyze.setObjectName("btnAnalyze")
        self._btn_analyze.setMinimumHeight(36)
        self._btn_analyze.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._btn_analyze.clicked.connect(self._on_analyze)
        self._btn_analyze.setEnabled(False)
        main_layout.addWidget(self._btn_analyze)

        # ── BOTÓN DESCARGAR REPORTE ─────────────
        self._btn_report = QPushButton("📄  Descargar Reporte")
        self._btn_report.setObjectName("btnReport")
        self._btn_report.setMinimumHeight(36)
        self._btn_report.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._btn_report.clicked.connect(self._on_report)
        self._btn_report.setEnabled(False)
        main_layout.addWidget(self._btn_report)

        # Spacer flexible
        main_layout.addItem(
            QSpacerItem(0, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        )

        # ── BOTÓN REINICIAR ─────────────────────
        self._btn_restart = QPushButton("🔄  Reiniciar")
        self._btn_restart.setObjectName("btnRestart")
        self._btn_restart.setMinimumHeight(36)
        self._btn_restart.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._btn_restart.clicked.connect(self._on_restart)
        self._btn_restart.setEnabled(False)
        main_layout.addWidget(self._btn_restart)

        # Créditos
        credit = QLabel("Powered by YaQbit Team")
        credit.setObjectName("creditLabel")
        credit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(credit)

    # ─────────────────────────────────────────
    #  STYLES
    # ─────────────────────────────────────────
    def _apply_styles(self):
        self.setStyleSheet("""
            SidebarWidget {
                background-color: #0d1117;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 10px;
                color: #7ab3f5;
                border: 1px solid #2d4a7a;
                border-radius: 6px;
                margin-top: 6px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 3px;
                color: #7ab3f5;
            }
            #sidebarTitle {
                color: #e8f4ff;
                font-size: 18px;
            }
            #sidebarSubtitle {
                color: #5a7a9a;
                font-size: 8px;
            }
            #btnClassic {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e6a35, stop:1 #144d27);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px;
            }
            #btnClassic:hover  { background: #27933e; }
            #btnClassic:pressed{ background: #0f3d1c; }

            #btnChallenge {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #7a2020, stop:1 #4d1515);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px;
            }
            #btnChallenge:hover  { background: #a32828; }
            #btnChallenge:pressed{ background: #3a0f0f; }

            #diffCombo {
                background: #1a2433;
                color: #c8d8f0;
                border: 1px solid #2d4a7a;
                border-radius: 6px;
                padding: 4px;
                font-size: 9px;
            }
            #diffCombo::drop-down { border: none; }
            #diffCombo QAbstractItemView {
                background: #1a2433;
                color: #c8d8f0;
                selection-background-color: #2d4a7a;
            }

            #lblTurn {
                color: #e8d88a;
                font-weight: bold;
                padding: 2px;
            }
            #lblStatus {
                color: #a0c0e0;
                font-size: 9px;
                padding: 2px;
            }
            #lblAttempts {
                color: #f5a742;
                font-weight: bold;
                font-size: 10px;
            }

            #separator {
                color: #2d4a7a;
                margin: 2px 0;
            }

            #btnAnalyze {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #4a1e8a, stop:1 #2d0f5a);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px;
            }
            #btnAnalyze:hover  { background: #6030b0; }
            #btnAnalyze:pressed{ background: #1d0a3d; }
            #btnAnalyze:disabled {
                background: #1a2030;
                color: #404858;
            }

            #btnReport {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1a5a3a, stop:1 #0f3d27);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px;
            }
            #btnReport:hover  { background: #238c52; }
            #btnReport:pressed{ background: #0a2419; }
            #btnReport:disabled {
                background: #1a2030;
                color: #404858;
            }

            #btnRestart {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1e4a8a, stop:1 #0f2d5a);
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px;
            }
            #btnRestart:hover  { background: #2860b0; }
            #btnRestart:pressed{ background: #0a1d3d; }
            #btnRestart:disabled {
                background: #1a2030;
                color: #404858;
            }

            #creditLabel {
                color: #2d4060;
                font-size: 7px;
            }
        """)

    # ─────────────────────────────────────────
    #  ACCIONES
    # ─────────────────────────────────────────
    def _on_classic(self):
        self._current_mode = "classic"
        self._lbl_attempts.setVisible(False)
        self._btn_restart.setEnabled(True)
        self._btn_analyze.setEnabled(True)
        self._btn_report.setEnabled(True)
        self.set_status("Iniciando modo clásico...")
        self.set_turn("Blancas")
        self.sig_start_classic.emit()

    def _on_challenge(self):
        self._current_mode = "challenge"
        self._lbl_attempts.setVisible(True)
        diff_map = {0: "easy", 1: "medium", 2: "hard"}
        difficulty = diff_map.get(self._diff_combo.currentIndex(), "easy")
        self._current_difficulty = difficulty
        self._btn_restart.setEnabled(True)
        self._btn_analyze.setEnabled(True)
        self._btn_report.setEnabled(True)
        self.set_status(f"Desafío iniciado: {difficulty.capitalize()}")
        self.set_turn("Blancas")
        self.sig_start_challenge.emit(difficulty)

    def _on_difficulty_changed(self, index):
        diff_map = {0: "easy", 1: "medium", 2: "hard"}
        self._current_difficulty = diff_map.get(index, "easy")

    def _on_analyze(self):
        self.sig_analyze_game.emit()

    def _on_report(self):
        self.sig_download_report.emit()

    def _on_restart(self):
        if self._current_mode == "classic":
            self._on_classic()
        elif self._current_mode == "challenge":
            self._on_challenge()
        self.sig_restart.emit()

    # ─────────────────────────────────────────
    #  ACTUALIZACIONES DE ESTADO (API pública)
    # ─────────────────────────────────────────
    def set_turn(self, turn_text: str):
        self._lbl_turn.setText(f"♟ Turno: {turn_text}")

    def set_status(self, text: str):
        self._lbl_status.setText(text)

    def set_attempts(self, attempts: int):
        color = "#f5a742" if attempts > 2 else "#e05050"
        self._lbl_attempts.setText(f"❤️  Intentos restantes: {attempts}")
        self._lbl_attempts.setStyleSheet(
            f"color: {color}; font-weight: bold; font-size: 10px;"
        )
        self._lbl_attempts.setVisible(True)

    def set_game_message(self, message: str):
        if message:
            self._lbl_status.setText(message)

    def show_hint(self, hint_text: str):
        """Muestra una pista en el área de estado."""
        if hint_text:
            self._lbl_status.setText(f"💡 {hint_text}")