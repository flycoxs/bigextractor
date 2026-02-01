# Big Extractor

Extractor de los mejores "bits" de cada tema (prototipo).

Características
- Detecta onsets/pulsos y selecciona segmentos con mayor energía.
- Guarda segmentos individuales y crea un mix concatenado con crossfades.
- Script en Python usando librosa + soundfile.

Requisitos
- Python 3.8+
- ffmpeg (opcional, para pydub concatenation en local)
- pip packages (ver requirements.txt)

Instalación
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Uso
```bash
python extractor/extractor.py input.mp3 --n 5 --seg 6 --out-dir out
```

Pruebas (local / CI)
```bash
python tests/test_run.py
```

Estructura
- extractor/: script principal
- tests/: prueba automática que genera un WAV sintético y ejecuta el extractor
- .github/workflows/ci.yml: workflow de CI que ejecuta la prueba (si habilitas Actions)


