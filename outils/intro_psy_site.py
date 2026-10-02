# -*- coding: utf-8 -*-
"""
Les fichiers de l intro psykotic pour le site (assets/psyi_*) :
  psyi_couteau.webp   le couteau n 5, retourne (pointe en bas a gauche, gros
                      de la lame en bas), pointe en (1, 1112) sur 810 x 1115
  psyi_cercle.webp    l anneau de sang de l auteur, sans l etoile, carre ;
                      le milieu du trait est a 200/520 du cote (rayon du disque)
  psyi_sang.webp      le sang plein ecran (16:10)
  psyi_gicl0/1/2.webm les giclees (FX Elements, gratuites), VP9 avec alpha,
                      cadrees pour un ecran 1600 x 1000 centre sur le disque
                      quand le disque a un rayon de 148 px
  psyi_coup1/2.mp3    les coups : le sifflement (75 ms) puis la lame ;
                      l impact tombe a 75 ms du debut du fichier
    python outils/intro_psy_site.py
"""
import math, os, subprocess
import numpy as np
from PIL import Image

ICI = os.path.dirname(os.path.abspath(__file__))
PROJET = os.path.dirname(ICI)
SRC = os.path.join(PROJET, 'osamason - psykotic')
A = os.path.join(PROJET, 'assets')
FF = r'C:/Users/user/AppData/Local/Programs/Python/Python313/Lib/site-packages/imageio_ffmpeg/binaries/ffmpeg-win-x86_64-v7.1.exe'
SR = 44100

# ------------------------------------------------------------- le couteau
c = Image.open(os.path.join(SRC, 'нож 5.png')).convert('RGBA').transpose(Image.TRANSPOSE)
c = c.crop(c.getbbox())
c.resize((c.width // 2, c.height // 2), Image.LANCZOS).save(os.path.join(A, 'psyi_couteau.webp'), quality=90, method=6)
print('couteau', c.size, '-> /2')

# --------------------------------------------------------------- l anneau
src = np.asarray(Image.open(os.path.join(SRC, 'круг со звездой.png')).convert('RGB')).astype(np.float32)
N = 1040                                   # cote ; rayon du trait = 400
k = 200 / 400                              # px source par px sortie
yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
dx, dy = xx - N / 2, yy - N / 2
rs = np.hypot(dx, dy) * k
ang = (np.degrees(np.arctan2(dy, dx)) + 360) % 360
for p in [50, 135, 195, 265, 337]:          # les pointes de l etoile, bouchees
    ecart = (ang - p + 180) % 360 - 180
    ang = np.where(np.abs(ecart) < 14, (ang + 36) % 360, ang)
garde = (rs > 181) & (rs < 224)
sx = 254 + rs * np.cos(np.radians(ang)); sy = 254 + rs * np.sin(np.radians(ang))
x0 = np.clip(np.floor(sx).astype(int), 0, 510); y0 = np.clip(np.floor(sy).astype(int), 0, 510)
fx = (sx - x0)[..., None]; fy = (sy - y0)[..., None]
pix = (src[y0, x0] * (1 - fx) * (1 - fy) + src[y0, x0 + 1] * fx * (1 - fy)
       + src[y0 + 1, x0] * (1 - fx) * fy + src[y0 + 1, x0 + 1] * fx * fy)
pix[~garde] = 0
alpha = np.clip((pix.max(2) - 18) * 3, 0, 255)
coul = np.clip(pix * 255 / np.maximum(alpha[..., None], 1), 0, 255)
Image.fromarray(np.dstack([coul, alpha]).astype(np.uint8), 'RGBA').save(os.path.join(A, 'psyi_cercle.webp'), quality=88, method=6)
print('cercle', N)

# ----------------------------------------------------------------- le sang
s = Image.open(os.environ['INTRO_DIR'] + '/sang.png').convert('RGBA').resize((1600, 1000), Image.LANCZOS)
s.save(os.path.join(A, 'psyi_sang.webp'), quality=82, method=6)
print('sang')

# --------------------------------------------------------------- giclees
# (fichier, debut en s, echelle, centre dans l image 1600 de large)
G = [('FX Elements - Blood Impact - 006/BloodImpact-006.mov', 5 / 24, 2.4, (841, 346)),
     ('FX Elements - CG Blood Hit - 024/CG-BloodHit-024.mov', 3 / 24, 1.6, (793, 553)),
     ('FX Elements - Blood Splatter - 018/BloodSplatter-018.mov', 1 / 24, 1.4, (766, 248))]
K = 4096 / 1600
for n, (f, t0, ech, (gx, gy)) in enumerate(G):
    w, h = 1600 / ech * K, 1000 / ech * K                 # ce qui tombe dans l ecran, en px source
    x, y = gx * K - w / 2, gy * K - h / 2
    # on decoupe dans une toile agrandie (pad) pour ne jamais sortir du clip
    vf = ('pad=iw+%d:ih+%d:%d:%d:color=black@0,crop=%d:%d:%d:%d,scale=960:600,format=yuva420p'
          % (2 * int(w), 2 * int(h), int(w), int(h), int(w), int(h), int(x + w), int(y + h)))
    dest = os.path.join(A, 'psyi_gicl%d.webm' % n)
    subprocess.run([FF, '-v', 'error', '-y', '-ss', '%.3f' % t0, '-t', '1.6', '-i', os.path.join(SRC, 'брызги', f),
                    '-vf', vf, '-r', '24', '-an', '-c:v', 'libvpx-vp9', '-pix_fmt', 'yuva420p', '-b:v', '0', '-crf', '34',
                    '-auto-alt-ref', '0', '-deadline', 'good', '-row-mt', '1', dest], check=True)
    print('giclee', n, os.path.getsize(dest) // 1024, 'Ko')


# ------------------------------------------------------------------ sons
def lire(nom):
    x = np.frombuffer(subprocess.run([FF, '-v', 'error', '-i', os.path.join(SRC, 'звуки ножа', nom), '-ac', '1', '-ar', str(SR),
                                      '-f', 'f32le', '-'], capture_output=True).stdout, np.float32).astype(np.float64)
    return x


def niveau(x, db):
    n = int(.1 * SR)
    f = np.sqrt(np.convolve(x ** 2, np.ones(min(n, len(x))) / min(n, len(x)), 'valid').max())
    return x * 10 ** (db / 20) / f


brut = lire('sensitive-lightning-strike-with-melee-weapons.mp3')
sif = brut[int(.004 * SR):int(.079 * SR)].copy()
sif *= np.minimum(1, np.arange(len(sif))[::-1] / (.008 * SR))
sif = niveau(sif, -14)
for n, nom in enumerate(['sharp-single-stab.mp3', 'merciless-strong-stab-at-the-target.mp3']):
    x = lire(nom)
    on = int(np.argmax(np.abs(x) > np.abs(x).max() * .1))
    x = niveau(x[max(0, on - 40):], -9)
    out = np.concatenate([sif, x])
    out *= .95 / max(.95, np.abs(out).max())
    wav = os.path.join(os.environ['INTRO_DIR'], 'coup%d.wav' % n)
    import wave
    with wave.open(wav, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((out * 32000).astype(np.int16).tobytes())
    subprocess.run([FF, '-v', 'error', '-y', '-i', wav, '-c:a', 'libmp3lame', '-b:a', '128k',
                    os.path.join(A, 'psyi_coup%d.mp3' % (n + 1))], check=True)
    print('coup', n + 1, 'impact a %.3f s' % (len(sif) / SR))
