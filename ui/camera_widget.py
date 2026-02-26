"""
ui/camera_widget.py
Widget que muestra el feed de la cámara OpenCV (con landmarks de MediaPipe)
convertido a QPixmap dentro de la interfaz PyQt6.
"""

import numpy as np
from PyQt6.QtWidgets import QLabel, QSizePolicy, QVBoxLayout, QWidget, QFrame
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap, QColor, QPainter, QFont


class CameraWidget(QFrame):
    """
    Muestra frames de cámara (numpy BGR) como QPixmap.
    Recibe frames a través de update_frame().
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFrameShape(QFrame.Shape.Box)
        self.setFrameShadow(QFrame.Shadow.Sunken)
        self.setLineWidth(2)
        self.setStyleSheet("""
            QFrame {
                border: 2px solid #3a7bd5;
                border-radius: 8px;
                background-color: #0a0a14;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header label
        self._header = QLabel("📷  Cámara — Hand Tracking")
        self._header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._header.setStyleSheet("""
            QLabel {
                background: #1a2a4a;
                color: #7ab3f5;
                font-size: 11px;
                font-weight: bold;
                padding: 4px;
                border-bottom: 1px solid #3a7bd5;
                border-radius: 0px;
            }
        """)
        layout.addWidget(self._header)

        # Área de imagen
        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setMinimumSize(240, 180)
        self._image_label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._image_label.setStyleSheet("background-color: #0a0a14;")
        layout.addWidget(self._image_label)

        # Mostrar placeholder inicial
        self._show_placeholder()

    def _show_placeholder(self):
        """Muestra un placeholder mientras la cámara carga."""
        pm = QPixmap(320, 240)
        pm.fill(QColor(10, 10, 20))
        painter = QPainter(pm)
        painter.setPen(QColor(80, 120, 200))
        font = QFont("Arial", 11)
        painter.setFont(font)
        painter.drawText(pm.rect(), Qt.AlignmentFlag.AlignCenter, "Iniciando cámara...")
        painter.end()
        self._image_label.setPixmap(pm)

    def update_frame(self, frame: np.ndarray):
        """
        Recibe un frame BGR de OpenCV y lo muestra como QPixmap.
        Args:
            frame: numpy array shape (H, W, 3) en formato BGR
        """
        if frame is None:
            return

        try:
            # Convertir BGR → RGB
            rgb = frame[:, :, ::-1].copy()
            h, w, ch = rgb.shape
            bytes_per_line = ch * w
            qt_img = QImage(rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_img)

            # Escalar al tamaño disponible manteniendo aspecto
            available = self._image_label.size()
            scaled = pixmap.scaled(
                available,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self._image_label.setPixmap(scaled)
        except Exception as e:
            pass  # Ignorar errores de frame corrupto

    def set_status(self, text: str):
        """Actualiza el header con texto de estado."""
        self._header.setText(f"📷  {text}")
