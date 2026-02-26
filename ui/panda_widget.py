"""
ui/panda_widget.py
Widget Qt que embebe el render 3D de Panda3D dentro de la ventana PyQt6.
Usa WindowProperties de Panda3D con el winId() nativo de Windows.
"""

from PyQt6.QtWidgets import QWidget, QSizePolicy
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPalette, QColor


class PandaWidget(QWidget):
    """
    Widget que actúa como contenedor para el render de Panda3D.
    Panda3D dibuja su output 3D directamente sobre el área nativa de este widget.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # CRÍTICO: Configuración para que ocupe todo el espacio disponible
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow, True)
        self.setAttribute(Qt.WidgetAttribute.WA_PaintOnScreen, True)
        self.setAttribute(Qt.WidgetAttribute.WA_NoSystemBackground, True)
        
        # Política de tamaño: Expanding en ambas direcciones
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        # Sin tamaño mínimo restrictivo (o uno muy pequeño)
        self.setMinimumSize(200, 150)  # Reducido para permitir flexibilidad
        
        # Fondo oscuro mientras carga
        pal = self.palette()
        pal.setColor(QPalette.ColorRole.Window, QColor(10, 10, 20))
        self.setPalette(pal)
        self.setAutoFillBackground(True)

        self._panda_base = None
        self._resize_timer = None  # Timer para debounce de resize

    def get_win_id(self):
        """Retorna el handle nativo de ventana para que Panda3D se adjunte."""
        self.winId()  # Fuerza la creación del handle nativo
        return int(self.winId())

    def set_panda_base(self, base):
        """Guarda referencia a la instancia ShowBase de Panda3D."""
        self._panda_base = base
        # Forzar un resize inicial después de un breve delay
        QTimer.singleShot(100, self._force_resize)

    def _force_resize(self):
        """Fuerza el redimensionamiento de Panda3D al tamaño actual del widget."""
        if self._panda_base and self._panda_base.win:
            try:
                from panda3d.core import WindowProperties
                props = WindowProperties()
                props.setSize(self.width(), self.height())
                props.setOrigin(0, 0)  # Asegurar origen en esquina superior izquierda
                self._panda_base.win.requestProperties(props)
            except Exception as e:
                print(f"Error en _force_resize: {e}")

    def resizeEvent(self, event):
        """Notifica a Panda3D cuando el widget cambia de tamaño."""
        super().resizeEvent(event)
        
        # Usar un timer para debounce (evitar múltiples llamadas rápidas)
        if self._resize_timer is None:
            self._resize_timer = QTimer(self)
            self._resize_timer.setSingleShot(True)
            self._resize_timer.timeout.connect(self._apply_resize)
        
        self._resize_timer.start(50)  # 50ms de delay

    def _apply_resize(self):
        """Aplica el redimensionamiento a Panda3D."""
        if self._panda_base and self._panda_base.win:
            try:
                from panda3d.core import WindowProperties
                props = WindowProperties()
                props.setSize(self.width(), self.height())
                props.setOrigin(0, 0)
                self._panda_base.win.requestProperties(props)
                
                # Forzar actualización de la ventana
                self._panda_base.graphicsEngine.renderFrame()
            except Exception as e:
                print(f"Error en resize de Panda3D: {e}")

    def paintEngine(self):
        """Necesario para WA_PaintOnScreen — evita que Qt intente pintar sobre Panda3D."""
        return None
        
    def showEvent(self, event):
        """Se llama cuando el widget se muestra."""
        super().showEvent(event)
        # Forzar resize cuando se muestra por primera vez
        QTimer.singleShot(200, self._force_resize)