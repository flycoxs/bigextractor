import librosa, json

def extract_beats(file_path, top_n=10):
    y, sr = librosa.load(file_path)
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
    times = librosa.frames_to_time(beats, sr=sr)
    best_beats = times[:top_n]
    return {"tempo": tempo, "beats": best_beats.tolist()}

if __name__ == "__main__":
    result = extract_beats("audio.mp3")
    with open("beats.json", "w") as f:
        json.dump(result, f, indent=2)

