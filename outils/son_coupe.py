# -*- coding: utf-8 -*-
"""
Le bruit de la lame qui entaille le cercle -> assets/psyi_coupe.mp3, une
boucle sans couture d environ 3,9 s.
  dessus  : « Flesh Growing (Horror) » (Pixabay 392360, tanweraman), le coeur
            du son (0,4 - 2,6 s), mis deux fois bout a bout en fondu ;
  dessous : « Eating Juicy Meat » (Pixabay 7024), 8 dB plus bas, le mouille.
Pixabay Content License : libre, sans attribution.
"""
import os, subprocess, wave
import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(ICI), 'osamason - psykotic', 'звуки ножа')
FF = r'C:/Users/user/AppData/Local/Programs/Python/Python313/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
SR = 44100


def lire(nom):
    return np.frombuffer(subprocess.run([FF, '-v', 'error', '-i', os.path.join(SRC, nom), '-ac', '1', '-ar', str(SR),
                                         '-f', 'f32le', '-'], capture_output=True).stdout, np.float32).astype(np.float64)


def rms(x):
    return np.sqrt((x ** 2).mean())


def enchainer(a, b, c):
    """a puis b, fondu croise de c echantillons"""
    w = np.linspace(0, 1, c)
    return np.concatenate([a[:-c], a[-c:] * (1 - w) + b[:c] * w, b[c:]])


C = int(.25 * SR)
chair = lire('flesh-growing-horror-392360.mp3')[int(.4 * SR):int(2.6 * SR)]
dessus = enchainer(chair, chair, C)                         # deux fois
n = len(dessus)
viande = lire('eating-juicy-meat-7024.mp3')[int(2.0 * SR):int(2.0 * SR) + n]
dessous = viande * rms(dessus) / rms(viande) * 10 ** (-8 / 20)
s = dessus + dessous
# la boucle : la fin rejoint le debut
w = np.linspace(0, 1, C)
s[:C] = s[:C] * w + s[-C:] * (1 - w)
s = s[:-C]
s *= .85 / np.abs(s).max()
wav = os.path.join(ICI, 'coupe.wav')
with wave.open(wav, 'wb') as f:
    f.setnchannels(1); f.setsampwidth(2); f.setframerate(SR)
    f.writeframes((s * 32000).astype(np.int16).tobytes())
subprocess.run([FF, '-v', 'error', '-y', '-i', wav, '-c:a', 'libmp3lame', '-b:a', '128k',
                os.path.join(os.path.dirname(ICI), 'assets', 'psyi_coupe.mp3')], check=True)
os.remove(wav)
print('ok %.2f s' % (len(s) / SR))
