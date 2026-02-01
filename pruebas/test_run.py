#!/usr/bin/env python3
"""
Test simple:
- genera un WAV sintético con "golpes" rítmicos + fondo
- ejecuta extractor.extract_best_bits sobre ese WAV
- verifica que se generen segmentos
"""
import os
import numpy as np
import soundfile as sf
from extractor.extractor import extract_best_bits

def generate_test_wav(path='tests/test_input.wav', sr=22050, duration=12.0):
    t = np.linspace(0, duration, int(sr*duration), endpoint=False)
    # fondo musical (baja frecuencia)
    background = 0.1 * np.sin(2 * np.pi * 220 * t)
    # golpes (transientes)
    signal = background.copy()
    beat_times = np.arange(0.5, duration, 0.5)  # cada 0.5s
    for bt in beat_times:
        idx = int(bt * sr)
        # pulso corto
        pulse = np.zeros_like(signal)
        length = int(0.02 * sr)
        pulse[idx:idx+length] += 0.9 * np.hanning(length)
        signal[idx:idx+length] += pulse[idx:idx+length]
    # normalizar
    mx = np.max(np.abs(signal))
    if mx > 0:
        signal = signal / mx * 0.9
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sf.write(path, signal, sr)
    return path

def test_run():
    test_wav = generate_test_wav()
    out = extract_best_bits(test_wav, n=3, seg_len=3, out_dir='tests/out')
    print("Test output:", out)
    assert out['segments'], "No segments created"
    assert os.path.exists(out['mix']), "Mix file not created"

if __name__ == '__main__':
    test_run()
    print("OK")
