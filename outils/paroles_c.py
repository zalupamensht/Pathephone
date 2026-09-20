# -*- coding: utf-8 -*-
"""
Les paroles synchronisees de l album « C », prises sur lrclib.net.

A lancer depuis n importe ou :   python "<chemin>/outils/paroles_c.py"

Rien n est ecrit sans verification. Une reponse n est retenue que si le
titre, l artiste ET la duree du fichier concordent, et que si ses temps
tiennent dans la duree de la piste. Le script peut etre relance sans rien
abimer : il remplace ce qu il a ecrit au lieu de le doubler.
"""
import io, json, os, re, sys, time, urllib.parse, urllib.request
import soundfile as sf

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSSIER = os.path.join(RACINE, 'c lucy bedrooque', 'ТРЕКИ')
ARTISTE = 'lucy bedroque'
UA = 'pathephone-promo/1.0 (site de promotion d album)'


def normal(s):
    return re.sub(r'[^a-z0-9]', '', (s or '').lower())


def titres():
    """le numero et le titre de chaque piste, lus sur les fichiers"""
    out = {}
    for f in os.listdir(DOSSIER):
        m = re.match(r'(\d+)\.lucybedroque - (.+)\.mp3$', f, re.I)
        if m:
            out[int(m.group(1))] = m.group(2)
    return out


TITRES = titres()


def demander(url):
    r = urllib.request.Request(url, headers={'User-Agent': UA})
    for essai in range(4):
        try:
            with urllib.request.urlopen(r, timeout=25) as f:
                return json.load(f)
        except Exception:
            if essai == 3:
                return None
            time.sleep(2 + essai * 2)
    return None


def local(n):
    """un LRC depose a la main : paroles/<numero>.lrc, prioritaire sur le reseau"""
    chemin = os.path.join(RACINE, 'paroles', '%d.lrc' % n)
    if os.path.exists(chemin):
        return io.open(chemin, encoding='utf-8-sig').read()
    return None


def chercher(titre, duree):
    """la bonne reponse, ou rien : on ne devine pas"""
    rep = demander('https://lrclib.net/api/search?q=' + urllib.parse.quote(titre)) or []
    for r in rep:
        if normal(r.get('trackName')) != normal(titre):
            continue
        a = normal(r.get('artistName'))
        if normal(ARTISTE) not in a and a != 'bedroquelucy':
            continue
        if abs((r.get('duration') or 0) - duree) > 5:
            continue
        if not r.get('syncedLyrics'):
            continue
        return r
    return None


def decouper(lrc):
    """le LRC devient la liste attendue par le site : t en secondes"""
    lignes = []
    for m in re.finditer(r'\[(\d+):(\d+(?:\.\d+)?)\]\s*(.*)', lrc):
        t = round(int(m.group(1)) * 60 + float(m.group(2)), 2)
        txt = m.group(3).strip()
        lignes.append({'t': t, 'text': txt} if txt else {'t': t, 'music': True})
    return lignes


def ecrire(trouve, durees):
    """Remplit les paroles piste par piste.

    Chaque piste est reperee par ses propres bornes dans le tableau A4, et
    l ecriture va de la derniere vers la premiere : une insertion ne
    deplace donc jamais les suivantes. C est ce qui manquait a la premiere
    version, qui faisait glisser les textes d une piste a l autre.
    """
    chemin = os.path.join(RACINE, 'index.html')
    h = io.open(chemin, encoding='utf-8').read()
    debut = h.index('var A4 = [')
    fin = h.index('\n];', debut)
    bloc = h[debut:fin]

    bornes = [m.start() for m in re.finditer(r'\{ name:"', bloc)] + [len(bloc)]
    ecrites, refusees = 0, []
    for k in range(len(bornes) - 2, -1, -1):
        a, b = bornes[k], bornes[k + 1]
        piste = bloc[a:b]
        m = re.search(r'audio:"assets/b4_(\d+)\.mp3"', piste)
        if not m:
            continue
        n = int(m.group(1))
        lignes = trouve.get(n) or []
        if not lignes:
            continue
        # garde fou : un texte qui deborde la piste vient d une autre version
        if lignes[-1]['t'] > durees.get(n, 1e9) + 1:
            refusees.append(n)
            continue
        corps = ',\n'.join(
            '        { t: %.2f, %s }' % (
                l['t'],
                'music: true' if l.get('music') else 'text: %s' % json.dumps(l['text'], ensure_ascii=False))
            for l in lignes)
        champ = 'lyrics:[\n' + corps + '\n    ]'
        piste2 = re.sub(r'lyrics:\[.*?\]', lambda _: champ, piste, count=1, flags=re.S)
        if piste2 == piste:
            refusees.append(n)
            continue
        bloc = bloc[:a] + piste2 + bloc[b:]
        ecrites += 1

    reste = len(re.findall(r'audio:"assets/b4_\d+\.mp3"', bloc))
    if reste != len(TITRES):
        print('ARRET : le tableau aurait perdu des pistes (%d au lieu de %d), rien n est ecrit'
              % (reste, len(TITRES)))
        return
    io.open(chemin, 'w', encoding='utf-8', newline='').write(h[:debut] + bloc + h[fin:])
    print('%d pistes ecrites dans index.html' % ecrites)
    if refusees:
        print('laissees vides (texte d une autre version) :', ', '.join(map(str, sorted(refusees))))
    print('pistes presentes apres ecriture : %d' % reste)


if __name__ == '__main__':
    trouve, durees = {}, {}
    for i in sorted(TITRES):
        titre = TITRES[i]
        duree = sf.info(os.path.join(RACINE, 'assets', 'b4_%d.mp3' % i)).duration
        durees[i] = duree
        pose = local(i)
        if pose:
            trouve[i] = decouper(pose)
            print('%2d  %-34s %3d lignes  (fichier depose a la main)' % (i, titre[:34], len(trouve[i])))
            continue
        r = chercher(titre, duree)
        if r:
            trouve[i] = decouper(r['syncedLyrics'])
            print('%2d  %-34s %3d lignes  (%.0f s vs %.0f s)'
                  % (i, titre[:34], len(trouve[i]), r['duration'], duree))
        else:
            trouve[i] = []
            print('%2d  %-34s rien de sur' % (i, titre[:34]))
        sys.stdout.flush()
        time.sleep(1.2)
    print('trouve : %d / %d' % (sum(1 for v in trouve.values() if v), len(TITRES)))
    ecrire(trouve, durees)
