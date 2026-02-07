# Ajedrez 3D con IA y Control por Gestos

Este proyecto implementa un juego de ajedrez en 3D con inteligencia artificial y control mediante gestos de la mano.

## Características Principales

- **Motor de Ajedrez**: Utiliza la librería `python-chess` para la lógica del juego, validación de movimientos y reglas oficiales.
- **Inteligencia Artificial**: Integra el motor de ajedrez **Stockfish** para desafiar al jugador.
- **Control por Gestos**: Implementa detección de manos y gestos utilizando **MediaPipe**.
- **Interfaz 3D**: Desarrollado con **Panda3D** para una experiencia visual inmersiva.
- **Modos de Juego**:
    - **Clásico**: Jugador vs IA.
    - **Challenge**: Sistema de "captura de piezas" donde la IA intenta capturar tus piezas y tú las suyas.

## Requisitos Previos

- Python 3.8+
- pip

## Instalación

1. **Clona el repositorio** (o descarga el código fuente).

2. **Crea un entorno virtual** (recomendado):
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Instala las dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

Ejecuta el juego desde la terminal:

```bash
python main.py
```

### Controles

- **Seleccionar Pieza**: Apunta a una pieza y realiza un gesto de "pinch" (dedo pulgar e índice juntos).
- **Mover Pieza**: Arrastra la mano hacia la casilla destino (no es necesario hacer "pinch" para mover).
- **Soltar**: Libera el gesto de "pinch" sobre la casilla destino.
- **Salir**: Presiona `Esc` o `Ctrl+C`.

## Estructura del Proyecto

- `main.py`: Punto de entrada principal de la aplicación.
- `logic/`: Contiene la lógica del juego:
    - `chess_logic.py`: Maneja el estado del tablero y las reglas.
    - `ai_engine.py`: Interfaz con Stockfish.
- `vision/`: Módulo de visión por computadora:
    - `detector_movimientos.py`: Detección de manos y gestos.
- `chess3d/`: Interfaz gráfica y visualización 3D:
    - `chess_scene.py`: Escena principal del juego.
    - `menu_scene.py`: Menú principal.
    - `ui_elements.py`: Elementos de interfaz (botones, texto).
- `assets/`: Modelos 3D y texturas de las piezas.
