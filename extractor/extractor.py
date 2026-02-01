#!/usr/bin/env python3
"""
extractor.py
Prototipo: extrae los mejores bits de un tema usando onset + RMS.

Dependencias: librosa, numpy, soundfile, pydub (opcional)
Uso:
  python extractor/extractor.py input.mp3 --n 5 --seg 6 --out-dir out
"""
import argparse
import os
import json
import numpy as np
import librosa
import soundfile as sf
from pydub import AudioSegment

def detect_candidates(y, sr, hop_length=512):
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop_length)
    peaks = librosa.util.peak_pick(onset_env, pre_max=3, post_max=3, pre_avg=3, post_avg=3, delta=0.2, wait=10)
    times = librosa.frames_to_time(peaks, sr=sr, hop_length=hop_length)
    return peaks, times, onset_env

def score_segments(y, sr, times, onset_env, seg_len_sec=6):
    scores = []
    seg_samples = int(seg_len_sec * sr)
    half = seg_samples // 2
    for t in times:
        center = int(round(t * sr))
        start = max(0, center - half)
        end = min(len(y), start + seg_samples)
        seg = y[start:end]
        if seg.size == 0:
            continue
        rms = float(np.mean(librosa.feature.rms(y=seg)))
        scores.append({'start': int(start), 'end': int(end), 'rms': rms})
    if not scores:
        return []
    for s in scores:
        s['score'] = s['rms']
    scores_sorted = sorted(scores, key=lambda x: x['score'], reverse=True)
    return scores_sorted

def save_segments(y, sr, segments, out_dir, prefix='seg'):
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for i, seg in enumerate(segments):
        start = seg['start']
        end = seg['end']
        fname = os.path.join(out_dir, f"{prefix}_{i+1:02d}.wav")
        sf.write(fname, y[start:end], sr)
        paths.append(fname)
    return paths

def concat_with_crossfade(paths, out_path, crossfade_ms=50):
    if not paths:
        return None
    combined = None
    for p in paths:
        a = AudioSegment.from_file(p)
        if combined is None:
            combined = a
        else:
            combined = combined.append(a, crossfade=crossfade_ms)
    combined.export(out_path, format="wav")
    return out_path

def extract_best_bits(input_path, n=5, seg_len=6, out_dir='out'):
    y, sr = librosa.load(input_path, sr=None, mono=True)
    peaks, times, onset_env = detect_candidates(y, sr)
    scored = score_segments(y, sr, times, onset_env, seg_len_sec=seg_len)
    top = scored[:n]
    if not top:
        print("No se detectaron segmentos.")
        return {'segments': [], 'mix': None}
    base = os.path.splitext(os.path.basename(input_path))[0]
    paths = save_segments(y, sr, top, out_dir, prefix=base)
    out_mix = os.path.join(out_dir, base + "_best_bits.wav")
    concat_with_crossfade(paths, out_mix)
    return {'segments': paths, 'mix': out_mix}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('input', help='archivo de entrada (mp3/wav)')
    ap.add_argument('--n', type=int, default=5, help='numero de segmentos')
    ap.add_argument('--seg', type=float, default=6.0, help='duracion de cada segmento (s)')
    ap.add_argument('--out-dir', default='out', help='directorio de salida')
    ap.add_argument('--json', help='guardar metadata JSON a PATH', default=None)
    args = ap.parse_args()

    res = extract_best_bits(args.input, n=args.n, seg_len=args.seg, out_dir=args.out_dir)
    print("Resultado:", res)
    if args.json:
        with open(args.json, 'w') as f:
            json.dump(res, f, indent=2)

if __name__ == '__main__':
    main()
