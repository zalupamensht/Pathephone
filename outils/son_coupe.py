# -*- coding: utf-8 -*-
"""
Le bruit de la lame qui entaille le cercle (provisoire, synthetise) :
une boucle de 2 s sans couture -> assets/psyi_coupe.mp3
Un raclement aigu par a-coups (la lame qui accroche), un grave sourd dessous.
"""
import os, subprocess, wave
import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
FF = r'C:/Users/user/AppData/Local/Programs/Python/Python313/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
SR = 44100
n = int(2.2 * SR)
r = np.random.default_rng(3)


def bande(x, lo, hi):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, len(x))


aigu = bande(r.normal(0, 1, n), 2200, 8000)
grave = bande(r.normal(0, 1, n), 120, 500)
g = np.zeros(n); k = 0
while k < n:                                  # les accroches, 35 a 60 par seconde
    L = int(SR * r.uniform(.006, .02))
    m = min(L, n - k)
    g[k:k + m] += r.uniform(.4, 1) * np.hanning(L)[:m]
    k += int(SR * r.uniform(.016, .03))
g = np.convolve(g, np.ones(60) / 60, 'same')
s = aigu * (.35 + .9 * g) * .6 + grave * (.5 + .5 * g) * .5
c = int(.2 * SR); w = np.linspace(0, 1, c)    # fondu croise : la fin rejoint le debut
s[:c] = s[:c] * w + s[-c:] * (1 - w)
s = s[:-c]
s *= .8 / np.abs(s).max()
wav = os.path.join(ICI, 'coupe.wav')
with wave.open(wav, 'wb') as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
    f.writeframes((s * 32000).astype(np.int16).tobytes())
subprocess.run([FF, '-v', 'error', '-y', '-i', wav, '-c:a', 'libmp3lame', '-b:a', '128k',
                os.path.join(os.path.dirname(ICI), 'assets', 'psyi_coupe.mp3')], check=True)
os.remove(wav)
print('ok')
