# bigextractor
un extractor de bits de musica
import librosa
import librosa.display
import matplotlib.pyplot as plt

# Cargar audio
y, sr = librosa.load("tu_audio.mp3")

# Detectar beats
tempo, beats = librosa.beat.beat_track(y=y, sr=sr)

print(f"Tempo estimado: {tempo} BPM")
print("Beats detectados en frames:", beats)

# Visualizar
plt.figure(figsize=(10, 4))
librosa.display.waveshow(y, sr=sr)
plt.vlines(librosa.frames_to_time(beats, sr=sr), -1, 1, color='r')
plt.title("Beats detectados")
plt.show()
python src/extractor.py

sudo apt-get update && sudo apt-get install -y ffmpeg
