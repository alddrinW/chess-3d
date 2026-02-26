"""
ui/pyqt_main.py
Ventana principal PyQt6 que integra:
  - PandaWidget: render 3D de Panda3D embebido
  - CameraWidget: feed de cámara con hand tracking
  - SidebarWidget: controles, tips e información del juego
  - GameOverDialog: diálogo de fin de partida
"""

import sys
import os
import json
import shutil
import tempfile
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QSplitter, QStatusBar, QLabel, QDialog, QPushButton,
    QVBoxLayout as VBox, QApplication, QMessageBox,
    QSizePolicy, QTableWidget, QTableWidgetItem,
    QHeaderView, QFileDialog, QTextBrowser, QProgressDialog,
    QTableWidget, QTableWidgetItem, QAbstractItemView
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QSize, QThread, QObject
from PyQt6.QtGui import QFont, QIcon, QColor, QPalette, QKeySequence, QShortcut

from ui.panda_widget import PandaWidget
from ui.camera_widget import CameraWidget
from ui.sidebar_widget import SidebarWidget


# =====================
# DIÁLOGO FIN DE PARTIDA
# =====================
class GameOverDialog(QDialog):
    """Diálogo modal que muestra el resultado al terminar la partida."""

    def __init__(self, result: str, message: str = "", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Fin de Partida")
        self.setModal(True)
        self.setFixedSize(360, 220)
        self.setStyleSheet("""
            QDialog {
                background: #0d1117;
                border: 2px solid #2d4a7a;
                border-radius: 12px;
            }
            QLabel#titleLabel {
                font-size: 28px;
                font-weight: bold;
                padding: 10px;
            }
            QLabel#msgLabel {
                font-size: 12px;
                color: #a0c0e0;
                padding: 4px;
            }
            QPushButton {
                padding: 10px 24px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
                border: none;
            }
        """)

        layout = VBox(self)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if result == "win":
            title_text = "🏆  ¡GANASTE!"
            title_color = "#4ade80"
        else:
            title_text = "💀  ¡PERDISTE!"
            title_color = "#f87171"

        title_lbl = QLabel(title_text)
        title_lbl.setObjectName("titleLabel")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet(f"color: {title_color}; font-size: 28px; font-weight: bold;")
        layout.addWidget(title_lbl)

        if message:
            msg_lbl = QLabel(message)
            msg_lbl.setObjectName("msgLabel")
            msg_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            msg_lbl.setWordWrap(True)
            layout.addWidget(msg_lbl)

        # Botones
        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)

        btn_restart = QPushButton("🔄 Nueva Partida")
        btn_restart.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #1e4a8a,stop:1 #0f2d5a);
            color: white;
        """)
        btn_restart.clicked.connect(lambda: self.done(1))  # 1 = reiniciar
        btn_row.addWidget(btn_restart)

        btn_menu = QPushButton("🏠 Menú")
        btn_menu.setStyleSheet("""
            background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #3a3a3a,stop:1 #1a1a1a);
            color: white;
        """)
        btn_menu.clicked.connect(lambda: self.done(0))  # 0 = solo cerrar
        btn_row.addWidget(btn_menu)

        layout.addLayout(btn_row)


# =====================
# WORKER DEEPSEEK (hilo separado para no bloquear UI)
# =====================
class DeepSeekWorker(QObject):
    finished = pyqtSignal(str)   # análisis exitoso
    error    = pyqtSignal(str)   # mensaje de error

    DEEPSEEK_API_KEY = "sk-c76f7a44fd974f04ad7593aa6777f170"
    DEEPSEEK_URL     = "https://api.deepseek.com/v1/chat/completions"

    def __init__(self, prompt: str, parent=None):
        super().__init__(parent)
        self.prompt = prompt

    def run(self):
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {self.DEEPSEEK_API_KEY}",
                "Content-Type":  "application/json"
            }
            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": self.prompt}],
                "temperature": 0.7
            }
            response = requests.post(
                self.DEEPSEEK_URL, headers=headers,
                json=payload, timeout=60
            )
            if response.status_code == 200:
                data     = response.json()
                analysis = data["choices"][0]["message"]["content"]
                self.finished.emit(analysis)
            else:
                self.error.emit(
                    f"Error HTTP {response.status_code}: {response.text[:300]}"
                )
        except Exception as exc:
            self.error.emit(str(exc))


# =====================
# DIÁLOGO PLANILLA DE ANOTACIONES (TABLA VISUAL)
# =====================
class ScoreSheetDialog(QDialog):
    """Diálogo que muestra la planilla de anotaciones en una tabla visual con opción de descargar."""
    
    def __init__(self, turnos, info_partida, history, parent=None):
        super().__init__(parent)
        self.turnos = turnos
        self.info_partida = info_partida
        self.history = history
        self.setWindowTitle("📋 Planilla de Anotaciones")
        self.setModal(True)
        self.setMinimumSize(500, 600)
        self.resize(550, 700)
        self._setup_ui()
        self._apply_styles()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Título
        title = QLabel("♟️ PLANILLA DE ANOTACIONES")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet("color: #7ab3f5; margin-bottom: 8px;")
        layout.addWidget(title)
        
        # Info de la partida (solo los campos solicitados)
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        info_layout.setSpacing(4)
        info_layout.setContentsMargins(8, 8, 8, 8)
        info_widget.setStyleSheet("""
            QWidget {
                background: #0a1020;
                border: 1px solid #2d4a7a;
                border-radius: 8px;
            }
            QLabel {
                color: #c8d8f0;
                font-size: 11px;
            }
        """)
        
        info_data = [
            f"📅 Fecha: {self.info_partida.get('fecha', '—')}",
            f"🎮 Modo: {self.info_partida.get('modo', '—')}",
            f"👤 Jugador: Humano (Blancas)",
            f"🤖 Oponente: IA Stockfish (Negras)",
            f"⏱️ Duración: {self.info_partida.get('duracion', '—')}",
            f"📊 Movs. Jugador: {self.info_partida.get('movs_jugador', 0)}  |  Movs. IA: {self.info_partida.get('movs_ia', 0)}"
        ]
        
        for text in info_data:
            lbl = QLabel(text)
            info_layout.addWidget(lbl)
        
        layout.addWidget(info_widget)
        
        # Tabla de movimientos
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["#", "BLANCAS", "NEGRAS"])
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        # Llenar tabla
        self.table.setRowCount(len(self.turnos))
        for i, (num, white, black) in enumerate(self.turnos):
            # Número
            item_num = QTableWidgetItem(str(num))
            item_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_num.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
            self.table.setItem(i, 0, item_num)
            
            # Blancas
            item_white = QTableWidgetItem(white if white else "")
            item_white.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_white.setFont(QFont("Consolas", 11))
            self.table.setItem(i, 1, item_white)
            
            # Negras
            item_black = QTableWidgetItem(black if black else "")
            item_black.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_black.setFont(QFont("Consolas", 11))
            self.table.setItem(i, 2, item_black)
        
        # Ajustar columnas
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 50)
        self.table.verticalHeader().setVisible(False)
        
        layout.addWidget(self.table)
        
        # Botones de descarga
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.btn_excel = QPushButton("📊 Descargar Excel")
        self.btn_excel.setMinimumHeight(44)
        self.btn_excel.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.btn_excel.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #1e6a35,stop:1 #144d27);
                color: white; border: none; border-radius: 8px; padding: 10px;
            }
            QPushButton:hover { background: #27933e; }
        """)
        self.btn_excel.clicked.connect(self._download_excel)
        btn_layout.addWidget(self.btn_excel)
        
        self.btn_txt = QPushButton("📝 Descargar TXT")
        self.btn_txt.setMinimumHeight(44)
        self.btn_txt.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.btn_txt.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,stop:0 #1e4a8a,stop:1 #0f2d5a);
                color: white; border: none; border-radius: 8px; padding: 10px;
            }
            QPushButton:hover { background: #2860b0; }
        """)
        self.btn_txt.clicked.connect(self._download_txt)
        btn_layout.addWidget(self.btn_txt)
        
        layout.addLayout(btn_layout)
        
        # Botón cerrar
        btn_close = QPushButton("❌ Cerrar")
        btn_close.setMinimumHeight(36)
        btn_close.setStyleSheet("""
            QPushButton {
                background: #2a2a2a; color: #888; border: none; 
                border-radius: 6px; padding: 8px;
            }
            QPushButton:hover { background: #3a3a3a; color: #aaa; }
        """)
        btn_close.clicked.connect(self.reject)
        layout.addWidget(btn_close)
    
    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background: #0d1117;
                border: 2px solid #2d4a7a;
                border-radius: 12px;
            }
            QTableWidget {
                background: #0a1020;
                border: 1px solid #2d4a7a;
                border-radius: 8px;
                gridline-color: #1a2d4a;
            }
            QTableWidget::item {
                color: #c8d8f0;
                padding: 6px;
                border-bottom: 1px solid #1a2d4a;
            }
            QTableWidget::item:selected {
                background: #1e3a5f;
            }
            QHeaderView::section {
                background: #1a2d4a;
                color: #7ab3f5;
                font-weight: bold;
                padding: 8px;
                border: none;
            }
            QScrollBar:vertical {
                background: #0a1020; width: 10px; border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #2d4a7a; border-radius: 5px;
            }
        """)
    
    def _download_excel(self):
        """Genera y descarga el archivo Excel."""
        default_name = f"planilla_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar planilla Excel", default_name,
            "Excel Files (*.xlsx)"
        )
        if not path:
            return
        
        try:
            generar_planilla_excel(self.turnos, self.info_partida, path)
            QMessageBox.information(self, "Éxito", f"✅ Planilla Excel guardada en:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"❌ No se pudo generar Excel:\n{str(e)}")
    
    def _download_txt(self):
        """Genera y descarga el archivo TXT."""
        default_name = f"planilla_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path, _ = QFileDialog.getSaveFileName(
            self, "Guardar planilla TXT", default_name,
            "Text Files (*.txt)"
        )
        if not path:
            return
        
        try:
            lines = [
                "=" * 52,
                "       PLANILLA DE ANOTACIÓN DE AJEDREZ",
                "=" * 52,
                f"Fecha    : {self.info_partida.get('fecha', '—')}",
                f"Modo     : {self.info_partida.get('modo', '—')}",
                f"Jugador  : Humano (Blancas)",
                f"Oponente : IA Stockfish (Negras)",
                f"Duración : {self.info_partida.get('duracion', '—')}",
                "",
                f"  Movs. jugador : {self.info_partida.get('movs_jugador', 0)}",
                f"  Movs. IA      : {self.info_partida.get('movs_ia', 0)}",
                "",
                "-" * 52,
                f"  {'#':<4}  {'BLANCAS':<16}  {'NEGRAS':<16}",
                "-" * 52,
            ]
            
            for (num, white, black) in self.turnos:
                w = white if white else "—"
                b = black if black else "—"
                lines.append(f"  {num:<4}  {w:<16}  {b:<16}")

            lines += [
                "-" * 52,
                f"  Total movimientos: {len(self.history)}",
                "=" * 52,
                "",
                "Generado por Chess 3D — YaQbit Team",
            ]

            with open(path, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))
            
            QMessageBox.information(self, "Éxito", f"✅ Planilla TXT guardada en:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"❌ No se pudo guardar:\n{str(e)}")


# =====================
# FUNCIONES PARA GENERAR PLANILLA EXCEL (SIMPLIFICADA)
# =====================
def generar_planilla_excel(turnos, info_partida, ruta_salida):
    """
    Genera una planilla de anotaciones simplificada en Excel.
    Solo incluye: Fecha, Modo, Jugador, Oponente, Duración, Movimientos.
    """
    try:
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
        from openpyxl.utils import get_column_letter
    except ImportError:
        raise ImportError("Se requiere 'openpyxl'. Instálalo con: pip install openpyxl")
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Planilla"
    
    # Estilos
    thin_border = Border(
        left=Side(style='thin', color='CCCCCC'),
        right=Side(style='thin', color='CCCCCC'),
        top=Side(style='thin', color='CCCCCC'),
        bottom=Side(style='thin', color='CCCCCC')
    )
    
    header_fill = PatternFill(start_color="2d4a7a", end_color="2d4a7a", fill_type="solid")
    
    # ===== TÍTULO =====
    ws.merge_cells('A1:C1')
    ws['A1'] = "PLANILLA DE ANOTACIÓN - AJEDREZ"
    ws['A1'].font = Font(bold=True, size=14, color="FFFFFF")
    ws['A1'].fill = header_fill
    ws['A1'].alignment = Alignment(horizontal='center', vertical='center')
    ws.row_dimensions[1].height = 25
    
    # ===== INFO DE LA PARTIDA (solo campos solicitados) =====
    ws['A3'] = "Fecha:"
    ws['B3'] = info_partida.get('fecha', '')
    ws['A4'] = "Modo:"
    ws['B4'] = info_partida.get('modo', '')
    ws['A5'] = "Jugador:"
    ws['B5'] = "Humano (Blancas)"
    ws['A6'] = "Oponente:"
    ws['B6'] = "IA Stockfish (Negras)"
    ws['A7'] = "Duración:"
    ws['B7'] = info_partida.get('duracion', '')
    
    # Estilo para labels
    for row in range(3, 8):
        ws[f'A{row}'].font = Font(bold=True, size=10, color="2d4a7a")
        ws[f'B{row}'].font = Font(size=10)
    
    # Movimientos totales
    ws['A8'] = "Movs. Jugador:"
    ws['B8'] = info_partida.get('movs_jugador', 0)
    ws['C8'] = "Movs. IA:"
    ws['D8'] = info_partida.get('movs_ia', 0)
    ws['A8'].font = Font(bold=True, size=10, color="2d4a7a")
    ws['C8'].font = Font(bold=True, size=10, color="2d4a7a")
    
    # ===== TABLA DE MOVIMIENTOS =====
    header_row = 10
    headers = ["#", "BLANCAS", "NEGRAS"]
    
    for col, header in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col, value=header)
        cell.font = Font(bold=True, size=11, color="FFFFFF")
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center', vertical='center')
        cell.border = thin_border
    
    # Llenar movimientos
    for i, (num, white, black) in enumerate(turnos, 1):
        row = header_row + i
        
        # Número
        cell_num = ws.cell(row=row, column=1, value=num)
        cell_num.alignment = Alignment(horizontal='center')
        cell_num.border = thin_border
        
        # Blancas
        cell_white = ws.cell(row=row, column=2, value=white if white else "")
        cell_white.alignment = Alignment(horizontal='center')
        cell_white.font = Font(name='Consolas', size=11)
        cell_white.border = thin_border
        
        # Negras (CORREGIDO: ahora sí se muestran)
        cell_black = ws.cell(row=row, column=3, value=black if black else "")
        cell_black.alignment = Alignment(horizontal='center')
        cell_black.font = Font(name='Consolas', size=11)
        cell_black.border = thin_border
    
    # Ajustar anchos
    ws.column_dimensions['A'].width = 8
    ws.column_dimensions['B'].width = 15
    ws.column_dimensions['C'].width = 15
    
    # Total
    total_row = header_row + len(turnos) + 1
    ws.merge_cells(f'A{total_row}:C{total_row}')
    ws[f'A{total_row}'] = f"Total movimientos: {len(turnos) * 2 - (1 if turnos and not turnos[-1][2] else 0)}"
    ws[f'A{total_row}'].font = Font(bold=True, size=10)
    ws[f'A{total_row}'].alignment = Alignment(horizontal='center')
    
    wb.save(ruta_salida)


# =====================
# DIÁLOGO ANÁLISIS CON IA (DeepSeek)
# =====================
class GameAnalysisDialog(QDialog):
    """Muestra el análisis de partida generado por DeepSeek."""

    def __init__(self, move_history: list, mode: str = "clásico", result: str = "en curso", parent=None):
        super().__init__(parent)
        self.move_history = move_history
        self.mode         = mode
        self.result       = result
        self._thread      = None
        self._worker      = None
        self.setWindowTitle("🤖 Análisis con IA")
        self.setModal(True)
        self.setMinimumSize(620, 640)
        self.resize(660, 700)
        self._build_prompt_and_save()
        self._setup_ui()
        self._apply_styles()

    # --- Prompt -----------------------------------------------------------
    def _build_prompt_and_save(self):
        """Construye el prompt PGN + JSON y lo guarda en un archivo temporal."""
        pgn_line = self._build_pgn()
        moves_json = json.dumps(self.move_history, indent=2, ensure_ascii=False)
        human_count = sum(1 for m in self.move_history if m.get("player") == "human")
        ai_count    = sum(1 for m in self.move_history if m.get("player") == "ai")

        self._prompt = f"""Eres un maestro de ajedrez y entrenador experto. \nAnaliza la siguiente partida de ajedrez entre un jugador humano (Blancas) y una IA (Negras).

MODO: {self.mode.capitalize()}
RESULTADO: {self.result.upper()}
FECHA: {datetime.now().strftime('%d/%m/%Y %H:%M')}
MOVIMIENTOS JUGADOR: {human_count}
MOVIMIENTOS IA: {ai_count}

NOTACIÓN PGN compacta:
{pgn_line}

HISTORIAL COMPLETO (JSON con FEN antes/después de cada movimiento):
{moves_json}

Teniendo en cuenta que el jugador humano {self.result}, por favor proporciona un análisis detallado respondiendo estos 4 puntos:
1. ¿En qué ERRORES frecuentes está cayendo el jugador humano? (máximo 4 puntos específicos)
2. ¿En qué FASE del juego falla más? (apertura, medio juego o final)
3. ¿Cómo puede MEJORAR frente a este nivel de IA? (máximo 4 sugerencias concretas)
4. ¿Qué PATRONES POSITIVOS debe conservar?

Escribe en español, de forma clara y amigable para un jugador amateur, IMPORTANTE, ir directo al tema
sin explicaciones innecesarias, saludos, etc."""

        # Guardar prompt en archivo temporal
        tmp_dir = tempfile.gettempdir()
        self._prompt_file = os.path.join(
            tmp_dir, f"chess_prompt_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        )
        try:
            with open(self._prompt_file, "w", encoding="utf-8") as f:
                f.write(self._prompt)
            print(f"[DeepSeek] Prompt guardado en: {self._prompt_file}")
        except Exception as e:
            print(f"[DeepSeek] No se pudo guardar prompt: {e}")

    def _build_pgn(self) -> str:
        parts, i, turn = [], 0, 1
        while i < len(self.move_history):
            m = self.move_history[i]
            if m.get("player") == "human":
                white = m.get("move_uci", "?").upper()
                black = ""
                if i + 1 < len(self.move_history) and self.move_history[i+1].get("player") == "ai":
                    black = self.move_history[i+1].get("move_uci", "?").upper()
                    i += 2
                else:
                    i += 1
                parts.append(f"{turn}. {white} {black}".strip())
                turn += 1
            else:
                parts.append(f"{turn}... {m.get('move_uci','?').upper()}")
                i += 1; turn += 1
        return "  ".join(parts) or "(sin movimientos)"

    # --- UI ---------------------------------------------------------------
    def _setup_ui(self):
        layout = VBox(self)
        layout.setSpacing(10)
        layout.setContentsMargins(18, 18, 18, 18)

        # Título
        title = QLabel("🤖 Análisis de Partida con AI")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        title.setStyleSheet("color: #c8a8ff; margin-bottom:4px;")
        layout.addWidget(title)

        # Info rápida
        human_c = sum(1 for m in self.move_history if m.get("player")=="human")
        ai_c    = sum(1 for m in self.move_history if m.get("player")=="ai")

        # Color según resultado
        result_upper = self.result.upper()
        if "GANÓ" in result_upper:
            result_color = "#5af078"   # verde
        elif "PERDIÓ" in result_upper:
            result_color = "#f07070"   # rojo
        elif "EMPATÓ" in result_upper:
            result_color = "#f0e060"   # amarillo
        else:
            result_color = "#7ab3f5"   # azul (en curso)

        info = QLabel(
            f"📊 Movimientos: {len(self.move_history)}   ♙ Jugador: {human_c}   ♟ IA: {ai_c}   Modo: {self.mode.capitalize()}"
        )
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet(
            "background:#0a1020; border:1px solid #2d4a7a; border-radius:6px;"
            "padding:6px; font-size:10px; color:#7ab3f5;"
        )
        layout.addWidget(info)

        result_lbl = QLabel(f"🏆 Resultado: {self.result}")
        result_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        result_lbl.setStyleSheet(
            f"background:#050d18; border:1px solid {result_color}44; border-radius:6px;"
            f"padding:5px; font-size:11px; font-weight:bold; color:{result_color};"
        )
        layout.addWidget(result_lbl)

        # PGN compacta
        pgn_lbl = QLabel("📖 PGN: " + self._build_pgn())
        pgn_lbl.setWordWrap(True)
        pgn_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        pgn_lbl.setStyleSheet(
            "background:#0a1020; color:#a8f0b0; border:1px solid #1a3a1a;"
            "border-radius:6px; padding:8px; font-family:'Consolas',monospace; font-size:10px;"
        )
        layout.addWidget(pgn_lbl)

        # Área de resultado del análisis
        analysis_lbl = QLabel("🦖 Análisis de IA:")
        analysis_lbl.setStyleSheet("color:#7ab3f5; font-weight:bold; font-size:11px;")
        layout.addWidget(analysis_lbl)

        self._analysis_browser = QTextBrowser()
        self._analysis_browser.setObjectName("analysisBrowser")
        self._analysis_browser.setMinimumHeight(280)
        self._analysis_browser.setPlainText("Presiona \"Analizar\" para analizar su partida con IA...")
        self._analysis_browser.setStyleSheet("""
            QTextBrowser {
                background: #060e1a;
                color: #c8d8f0;
                border: 1px solid #2d4a7a;
                border-radius: 8px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
                padding: 10px;
            }
        """)
        layout.addWidget(self._analysis_browser)

        # Botones
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._btn_analyze = QPushButton("🤖 Analizar con IA")
        self._btn_analyze.setMinimumHeight(42)
        self._btn_analyze.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self._btn_analyze.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #4a1e8a, stop:1 #2d0f5a);
                color: white; border: none; border-radius: 8px; padding: 10px;
            }
            QPushButton:hover  { background: #6030b0; }
            QPushButton:disabled { background: #1a2030; color: #404858; }
        """)
        self._btn_analyze.clicked.connect(self._run_analysis)
        btn_row.addWidget(self._btn_analyze)

        btn_close = QPushButton("❌ Cerrar")
        btn_close.setMinimumHeight(42)
        btn_close.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
                    stop:0 #3a1a1a, stop:1 #200f0f);
                color: #f0a0a0; border: none; border-radius: 8px; padding: 10px;
            }
            QPushButton:hover { background: #5a2020; }
        """)
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)

        layout.addLayout(btn_row)

    # --- DeepSeek call ----------------------------------------------------
    def _run_analysis(self):
        self._btn_analyze.setEnabled(False)
        self._analysis_browser.setPlainText("⏳ Enviando partida a analisis AI...\nEsto puede tardar unos segundos.")

        self._thread = QThread()
        self._worker = DeepSeekWorker(self._prompt)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.finished.connect(self._on_analysis_done)
        self._worker.error.connect(self._on_analysis_error)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.start()

    def _on_analysis_done(self, text: str):
        self._analysis_browser.setMarkdown(text)
        self._btn_analyze.setEnabled(True)
        self._btn_analyze.setText("↺ Volver a analizar")

    def _on_analysis_error(self, err: str):
        self._analysis_browser.setPlainText(
            f"❌ Error al conectar con DeepSeek:\n\n{err}\n\n"
            f"Verifica tu conexión a internet y la API key."
        )
        self._btn_analyze.setEnabled(True)

    def _apply_styles(self):
        self.setStyleSheet("""
            QDialog {
                background: #0d1117;
                border: 2px solid #4a1e8a;
                border-radius: 12px;
            }
            QLabel { color: #c8d8f0; }
            QScrollBar:vertical {
                background: #0a1020; width: 8px; border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #2d4a7a; border-radius: 4px;
            }
        """)









# =====================
# VENTANA PRINCIPAL
# =====================
class ChessMainWindow(QMainWindow):
    """
    Ventana principal del juego Chess 3D con PyQt6.
    Coordina todos los widgets y la lógica de juego.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chess 3D — Manos Libres")
        self.setMinimumSize(1100, 700)
        self._panda_base = None
        self._game = None
        self._logic = None
        self._detector = None
        self._game_running = False
        self._showing_game_over = False   # ← inicializado aquí para evitar AttributeError

        self._setup_ui()
        self._apply_global_styles()
        self._setup_shortcuts()
        self._setup_update_timer()

    def _setup_ui(self):
        """Construye el layout principal de la ventana."""
        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ── SPLITTER PRINCIPAL (izquierda 3D | derecha panel) ──
        self._main_splitter = QSplitter(Qt.Orientation.Horizontal)
        self._main_splitter.setHandleWidth(4)
        self._main_splitter.setStyleSheet("""
            QSplitter::handle { background: #1a2d4a; }
            QSplitter::handle:hover { background: #3a7bd5; }
        """)
        
        # CRÍTICO: Permitir que el splitter se expanda
        self._main_splitter.setSizePolicy(
            QSizePolicy.Policy.Expanding, 
            QSizePolicy.Policy.Expanding
        )

        # ── PANDA3D WIDGET (izquierda) ──
        self._panda_widget = PandaWidget()
        # Tamaño mínimo razonable pero no restrictivo
        self._panda_widget.setMinimumSize(400, 300)
        self._main_splitter.addWidget(self._panda_widget)

        # ── PANEL DERECHO (cámara + sidebar) ──
        right_widget = QWidget()
        # Tamaño fijo para el panel derecho (no expansivo)
        right_widget.setFixedWidth(340)  # Usar fixed width en lugar de min/max
        right_widget.setSizePolicy(
            QSizePolicy.Policy.Fixed,  # No se expande horizontalmente
            QSizePolicy.Policy.Expanding  # Sí se expande verticalmente
        )
        right_widget.setStyleSheet("background: #0d1117;")
        
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Feed de cámara
        self._camera_widget = CameraWidget()
        self._camera_widget.setFixedHeight(240)  # Altura fija para la cámara
        self._camera_widget.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Fixed
        )
        right_layout.addWidget(self._camera_widget)

        # Sidebar - ocupa el resto del espacio vertical
        self._sidebar = SidebarWidget()
        self._sidebar.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Expanding
        )
        right_layout.addWidget(self._sidebar)

        self._main_splitter.addWidget(right_widget)
        
        # CRÍTICO: Establecer stretch factors (3D expandible, panel fijo)
        self._main_splitter.setStretchFactor(0, 1)  # Índice 0 (PandaWidget) expandible
        self._main_splitter.setStretchFactor(1, 0)  # Índice 1 (right_widget) no expandible
        
        # Proporciones iniciales (el 3D tomará más espacio)
        self._main_splitter.setSizes([800, 340])

        root_layout.addWidget(self._main_splitter)

        # ── STATUS BAR ──
        self._status_bar = QStatusBar()
        self._status_bar.setStyleSheet("""
            QStatusBar {
                background: #0a0f18;
                color: #5a7a9a;
                font-size: 10px;
                border-top: 1px solid #1a2d4a;
            }
        """)
        self._status_bar.showMessage("Chess 3D — Listo. Selecciona un modo de juego.")
        self.setStatusBar(self._status_bar)

        # ── CONECTAR SEÑALES DEL SIDEBAR ──
        self._sidebar.sig_start_classic.connect(self._start_classic)
        self._sidebar.sig_start_challenge.connect(self._start_challenge)
        self._sidebar.sig_restart.connect(self._restart_game)
        self._sidebar.sig_analyze_game.connect(self._show_game_analysis)
        self._sidebar.sig_download_report.connect(self._download_report)

    def _apply_global_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background: #0d1117;
            }
        """)
        # Paleta oscura global
        pal = QApplication.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(13, 17, 23))
        pal.setColor(QPalette.ColorRole.WindowText, QColor(200, 216, 240))
        pal.setColor(QPalette.ColorRole.Base, QColor(10, 16, 26))
        pal.setColor(QPalette.ColorRole.AlternateBase, QColor(20, 30, 46))
        pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(20, 30, 46))
        pal.setColor(QPalette.ColorRole.ToolTipText, QColor(200, 216, 240))
        pal.setColor(QPalette.ColorRole.Text, QColor(200, 216, 240))
        pal.setColor(QPalette.ColorRole.Button, QColor(30, 45, 65))
        pal.setColor(QPalette.ColorRole.ButtonText, QColor(200, 216, 240))
        pal.setColor(QPalette.ColorRole.Highlight, QColor(50, 100, 180))
        pal.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        QApplication.setPalette(pal)

    def _setup_shortcuts(self):
        """Configura atajos de teclado."""
        QShortcut(QKeySequence("Ctrl+R"), self, self._restart_game)
        QShortcut(QKeySequence("F11"), self, self._toggle_fullscreen)
        QShortcut(QKeySequence("Escape"), self, self._escape_handler)

    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _escape_handler(self):
        if self.isFullScreen():
            self.showNormal()

    # ── TIMER PARA EL LOOP DE PANDA3D ──────────────────────

    def _setup_update_timer(self):
        """QTimer a ~60fps que llama base.taskMgr.step() y actualiza la cámara."""
        self._update_timer = QTimer(self)
        self._update_timer.setInterval(16)  # ~60fps
        self._update_timer.timeout.connect(self._tick)

    def _tick(self):
        """Loop principal: actualiza Panda3D, hand-tracking y UI de estado."""
        # 1. Paso del task manager de Panda3D
        if self._panda_base:
            try:
                self._panda_base.taskMgr.step()
            except Exception:
                pass

        # 2. Capturar frame de cámara (detector ya fue actualizado por Panda)
        if self._detector:
            try:
                # Actualizar el detector manualmente (sin ventana OpenCV)
                self._detector.update()
                # Mostrar el frame capturado en el CameraWidget
                frame = getattr(self._detector, 'last_frame', None)
                if frame is not None:
                    self._camera_widget.update_frame(frame)
            except Exception:
                pass

        # 3. Actualizar estado del sidebar (turno, intentos, game over)
        self._update_sidebar_state()

    def _update_sidebar_state(self):
        """Actualiza sidebar con state actual de la lógica de juego."""
        if not self._logic:
            return
        try:
            import chess
            # Turno
            if self._logic.board.turn == chess.WHITE:
                self._sidebar.set_turn("Blancas ♟")
            else:
                self._sidebar.set_turn("Negras ♙")

            # Modo desafío
            if self._logic.challenge_mode:
                if self._logic.attempts_left is not None:
                    self._sidebar.set_attempts(self._logic.attempts_left)
                if self._logic.game_over_message:
                    self._sidebar.set_game_message(self._logic.game_over_message)
                    # Verificar fin de juego
                    if self._logic.is_game_over() and not self._showing_game_over:
                        self._showing_game_over = True
                        result = "win" if self._logic.solved else "lose"
                        QTimer.singleShot(500, lambda: self._show_game_over_dialog(result, self._logic.game_over_message))
            else:
                # Modo clásico
                if self._logic.board.is_game_over() and not self._showing_game_over:
                    self._showing_game_over = True
                    res = self._logic.board.result()
                    if res == "1-0":
                        result, msg = "win", "¡Las blancas ganan!"
                    elif res == "0-1":
                        result, msg = "lose", "¡Las negras ganan!"
                    else:
                        result, msg = "win", "¡Tablas!"
                    QTimer.singleShot(500, lambda: self._show_game_over_dialog(result, msg))
        except Exception:
            pass

    # ── INICIAR MODOS DE JUEGO ──────────────────────────────

    def set_panda_base(self, base):
        """
        Llama desde main.py después de inicializar Panda3D.
        Registra la instancia ShowBase y activa el timer.
        """
        self._panda_base = base
        self._panda_widget.set_panda_base(base)
        self._update_timer.start()
        self._status_bar.showMessage("Chess 3D — Motor 3D inicializado. ¡Selecciona un modo!")

    def _start_classic(self):
        """Inicia el modo clásico."""
        self._cleanup_game()
        self._showing_game_over = False
        self._status_bar.showMessage("Modo Clásico iniciado — ¡Buena suerte!")

        if self._panda_base:
            self._panda_base.start_classic_internal()

    def _start_challenge(self, difficulty: str):
        """Inicia el modo desafío."""
        self._cleanup_game()
        self._showing_game_over = False
        difficulty_names = {"easy": "Fácil (Mate en 2)", "medium": "Medio (Mate en 3)", "hard": "Difícil (Mate en 5)"}
        self._status_bar.showMessage(f"Modo Desafío — {difficulty_names.get(difficulty, difficulty)}")

        if self._panda_base:
            self._panda_base.start_challenge_internal(difficulty)

    def _restart_game(self):
        """Reinicia la partida actual."""
        self._showing_game_over = False
        self._status_bar.showMessage("Partida reiniciada.")
        if self._panda_base:
            self._panda_base.restart_current()

    def _cleanup_game(self):
        """Limpia el estado anterior antes de iniciar uno nuevo."""
        pass

    def _show_game_over_dialog(self, result: str, message: str = ""):
        """Muestra el diálogo de fin de partida."""
        dialog = GameOverDialog(result, message, parent=self)
        code = dialog.exec()
        if code == 1:
            self._restart_game()

    # ── REGISTRAR REFERENCIAS ──────────────────────────────

    def register_game_refs(self, logic, detector):
        """Registra referencias a la lógica y detector desde ChessApp."""
        self._logic = logic
        self._detector = detector
        if logic and logic.challenge_mode and hasattr(logic, 'hint'):
            self._sidebar.show_hint(logic.hint)

    def _show_game_analysis(self):
        """Abre el diálogo de análisis con el historial de movimientos actual."""
        history = []
        if self._detector and hasattr(self._detector, 'move_history'):
            history = self._detector.move_history

        if not history:
            QMessageBox.information(
                self, "Análisis de Partida",
                "⚠️ No hay movimientos registrados todavía.\n\nJuega algunos movimientos primero."
            )
            return

        mode = "clásico"
        result = "partida en curso"

        if self._logic:
            # Determinar modo
            if hasattr(self._logic, 'challenge_mode') and self._logic.challenge_mode:
                mode = "desafío"
                # Resultado modo desafío
                if hasattr(self._logic, 'solved') and self._logic.solved:
                    result = "GANÓ (resolvió el mate)"
                elif hasattr(self._logic, 'attempts_left') and self._logic.attempts_left == 0:
                    result = "PERDIÓ (se quedó sin intentos)"
                elif self._logic.is_game_over():
                    result = "partida terminada"
            else:
                # Resultado modo clásico
                try:
                    import chess as _chess
                    if self._logic.board.is_game_over():
                        res = self._logic.board.result()
                        if res == "1-0":
                            result = "GANÓ (las blancas hicieron jaque mate)"
                        elif res == "0-1":
                            result = "PERDIÓ (la IA hizo jaque mate)"
                        elif res == "1/2-1/2":
                            result = "EMPATÓ (tablas)"
                        else:
                            result = f"partida terminada ({res})"
                    else:
                        result = "partida en curso (análisis parcial)"
                except Exception:
                    result = "partida en curso"

        dialog = GameAnalysisDialog(history, mode=mode, result=result, parent=self)
        dialog.exec()


    def _download_report(self):
        """Abre diálogo con tabla visual de la planilla y opciones de descarga."""
        history = []
        if self._detector and hasattr(self._detector, 'move_history'):
            history = self._detector.move_history

        if not history:
            QMessageBox.information(
                self, "Descargar Reporte",
                "⚠️ No hay movimientos registrados todavía.\n\nJuega algunos movimientos primero."
            )
            return

        # Determinar modo
        modo = "Clásico"
        if self._logic and hasattr(self._logic, 'challenge_mode') and self._logic.challenge_mode:
            modo = "Desafío"

        # CORREGIDO: Procesar turnos correctamente (emparejar blancas y negras)
        turnos = []
        i = 0
        turno_num = 1
        
        while i < len(history):
            m = history[i]
            
            if m.get("player") == "human":
                # Movimiento de blancas
                white = m.get("move_uci", "").upper()
                
                # Buscar siguiente movimiento de negras (IA)
                black = ""
                if i + 1 < len(history) and history[i + 1].get("player") == "ai":
                    black = history[i + 1].get("move_uci", "").upper()
                    i += 2  # Avanzar 2 (blancas + negras)
                else:
                    i += 1  # Solo avanzar 1 si no hay negras
                
                turnos.append((turno_num, white, black))
                turno_num += 1
            else:
                # Si empieza con negras (raro, pero posible)
                white = "..."
                black = m.get("move_uci", "").upper()
                turnos.append((turno_num, white, black))
                i += 1
                turno_num += 1

        # Calcular duración
        duracion_str = "—"
        if len(history) >= 2:
            try:
                t0 = datetime.fromisoformat(history[0]["timestamp"])
                t1 = datetime.fromisoformat(history[-1]["timestamp"])
                secs = int((t1 - t0).total_seconds())
                duracion_str = f"{secs // 60}m {secs % 60}s"
            except Exception:
                pass

        # Contadores
        human_count = sum(1 for m in history if m.get("player") == "human")
        ai_count = sum(1 for m in history if m.get("player") == "ai")

        # Info para la planilla (solo campos solicitados)
        info_partida = {
            'fecha': datetime.now().strftime("%d/%m/%Y %H:%M"),
            'modo': modo,
            'duracion': duracion_str,
            'movs_jugador': human_count,
            'movs_ia': ai_count
        }

        # Mostrar diálogo con tabla visual
        dialog = ScoreSheetDialog(turnos, info_partida, history, parent=self)
        dialog.exec()

    def clear_game_refs(self):
        """Limpia referencias al terminar/reiniciar."""
        self._logic = None
        self._detector = None
        self._showing_game_over = False
        self._sidebar.set_turn("—")
        self._sidebar.set_status("Selecciona un modo para comenzar")

    def closeEvent(self, event):
        """Al cerrar la ventana, detiene Panda3D limpiamente."""
        self._update_timer.stop()
        if self._panda_base:
            try:
                self._panda_base.destroy()
            except Exception:
                pass
        event.accept()