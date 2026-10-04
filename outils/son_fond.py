# -*- coding: utf-8 -*-
"""
Le fond sonore de l intro psykotic -> assets/psyi_fond.mp3 : une boucle de
40 s sans couture. La montee (le volume qui grandit) se fait sur le site.
  devant   : « Horror Ambience 01 » (Pixabay 66708), le fond principal ;
  dessous  : « Dark Horror Ambient 05 » (Pixabay 425468), qui gonfle au debut ;
  au loin  : « Horror Ghost Breath » (Pixabay 392363), un souffle mis en
             profondeur : aigus coupes, une queue de reverberation, 12 dB plus bas.
Pixabay Content License : libre, sans attribution.
"""
import os, subprocess, wave
import numpy as np

ICI = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(ICI), 'osamason - psykotic', 'звуки фона')
FF = r'C:/Users/user/AppData/Local/Programs/Python/Python313/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
SR = 44100
L = 40 * SR                                   # la boucle
C = 2 * SR                                    # le fondu de la couture


def lire(nom):
    return np.frombuffer(subprocess.run([FF, '-v', 'error', '-i', os.path.join(SRC, nom), '-ac', '2', '-ar', str(SR),
                                         '-f', 'f32le', '-'], capture_output=True).stdout, np.float32).astype(np.float64).reshape(-1, 2)


def rms(x):
    return np.sqrt((x ** 2).mean())


def passe_bas(x, fc):
    X = np.fft.rfft(x, axis=0); f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= (1 / np.sqrt(1 + (f / fc) ** 4))[:, None]
    return np.fft.irfft(X, len(x), axis=0)


def reverb(x, duree=2.6, melange=.45):
    """une salle sombre : une reponse de bruit qui decroit, un peu decalee"""
    r = np.random.default_rng(7)
    n = int(duree * SR); t = np.arange(n) / SR
    ir = r.normal(0, 1, (n, 2)) * np.exp(-t * 3.2)[:, None]
    ir = passe_bas(ir, 2500)
    ir[:int(.03 * SR)] = 0                           # le pre-delai : le mur est loin
    ir /= np.sqrt((ir ** 2).sum(0))
    m = len(x) + n
    Y = np.fft.irfft(np.fft.rfft(x, m, axis=0) * np.fft.rfft(ir, m, axis=0), m, axis=0)[:len(x)]
    return x * (1 - melange) + Y * melange * 1.6


devant = lire('horror-ambience-01-66708.mp3')[int(1 * SR):int(1 * SR) + L + C]
dessous = np.zeros_like(devant)
d = lire('dark-horror-ambient-05-425468.mp3')
d = d[:min(len(d), len(dessous))]
dessous[:len(d)] = d
souffle = lire('horror-ghost-breath-392363.mp3')[:L + C]
souffle = reverb(passe_bas(souffle, 1800))

ref = rms(devant)
s = devant + dessous * ref / rms(d) * 10 ** (-7 / 20) + souffle * ref / rms(souffle) * 10 ** (-12 / 20)
# la couture : les 2 s de trop viennent se fondre sur le debut
w = np.linspace(0, 1, C)[:, None]
s[:C] = s[:C] * w + s[L:L + C] * (1 - w)
s = s[:L]
s *= .9 / np.abs(s).max()
wav = os.path.join(ICI, 'fond.wav')
with wave.open(wav, 'wb') as f:
    f.setnchannels(2); f.setsampwidth(2); f.setframerate(SR)
    f.writeframes((s * 32000).astype(np.int16).tobytes())
subprocess.run([FF, '-v', 'error', '-y', '-i', wav, '-c:a', 'libmp3lame', '-b:a', '112k',
                os.path.join(os.path.dirname(ICI), 'assets', 'psyi_fond.mp3')], check=True)
os.remove(wav)
print('ok', os.path.getsize(os.path.join(os.path.dirname(ICI), 'assets', 'psyi_fond.mp3')) // 1024, 'Ko')
