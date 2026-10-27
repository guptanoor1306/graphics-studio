"""Shared: render, safe-zone check, self-contained HTML, pixel verify, contact sheet.
usage: python3 finalize.py <out_dir> <final_dir> <sheet.png> <prefix_len>"""
import sys, re, base64, glob, os, shutil, subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageChops
out, final, sheet = map(os.path.abspath, sys.argv[1:4])
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'render.py')
L = dict(l.split(' ', 1) for l in open(out + '/_lists.txt').read().splitlines() if ' ' in l)
if L.get('T'): subprocess.run(['python3', R, '--t'] + L['T'].split(), check=True)
if L.get('O'): subprocess.run(['python3', R] + L['O'].split(), check=True)
# centred safe area: x 120-960 above y 720, x 200-880 from y 720 down, y 240-1540
UNSAFE = [(0,0,1080,240),(0,1540,1080,1920),(0,240,120,720),(960,240,1080,720),(0,720,200,1540),(880,720,1080,1540)]
os.makedirs(final, exist_ok=True)
for f in glob.glob(final + '/*'): os.remove(f)
report = []
# background-only renders: same page with the <body> content removed (keeps the theme's background fill)
bgdir = out + '/_bg'; os.makedirs(bgdir, exist_ok=True)
bgs = []
for h in sorted(glob.glob(out + '/*.html')):
    s0 = open(h).read(); b = s0.replace('</style>', 'body *{visibility:hidden!important} body .fill,body .panel{visibility:visible!important}</style>', 1)
    p = bgdir + '/' + os.path.basename(h); open(p, 'w').write(b); bgs.append(p)
subprocess.run(['python3', R, '--t'] + bgs, check=True)
for h in sorted(glob.glob(out + '/*.html')):
    png = h[:-5] + '.png'
    a = np.asarray(Image.open(png).convert('RGBA')).astype(int)
    g = np.asarray(Image.open(bgdir + '/' + os.path.basename(png)).convert('RGBA')).astype(int)
    ink = np.abs(a - g).sum(2) > 60
    m = np.zeros(ink.shape, bool)
    for x0, y0, x1, y1 in UNSAFE: m[y0:y1, x0:x1] = True
    v = int((ink & m).sum())
    xs = np.where((ink & ~m).any(0))[0]
    centre_off = int(round((xs.min() + xs.max()) / 2 - 540)) if len(xs) else 0
    s = open(h).read()
    def emb(mm):
        rule = mm.group(0); fam = re.search(r"font-family:'([^']+)'", rule).group(1)
        if f"'{fam}'" not in s.split('</style>')[0].split(':root')[1] and fam not in s.split(':root')[1]: return ''
        path = re.search(r"url\('([^']+)'\)", rule).group(1)
        return rule.replace(f"url('{path}')", "url(data:font/woff2;base64," + base64.b64encode(open(path, 'rb').read()).decode() + ") format('woff2')")
    rest = re.sub(r"@font-face\{[^}]+\}", '', s)
    used = {fam for fam in set(re.findall(r"@font-face\{font-family:'([^']+)'", s)) if f"'{fam}'" in rest}
    s = re.sub(r"@font-face\{[^}]+\}\n?", lambda mm: emb(mm) if re.search(r"font-family:'([^']+)'", mm.group(0)).group(1) in used else '', s)
    s = re.sub(r"url\('(/home/[^']+\.png)'\)", lambda mm: "url(data:image/png;base64," + base64.b64encode(open(mm.group(1),'rb').read()).decode() + ")", s)
    s = re.sub(r'src="(/home/[^"]+\.png)"', lambda mm: 'src="data:image/png;base64,' + base64.b64encode(open(mm.group(1),'rb').read()).decode() + '"', s)
    assert '/home/' not in s, h
    name = os.path.basename(h)
    open(f'{final}/{name}', 'w').write(s)
    shutil.copy(png, f'{final}/{name[:-5]}.png')
    report.append((name[:-5], v, centre_off))
# pixel verify from a clean folder
tmp = '/tmp/claude-0/-home-claude/f917a154-6a13-5715-8ce2-fee9302a85f7/scratchpad/verify'
shutil.rmtree(tmp, ignore_errors=True); os.makedirs(tmp)
tl = [os.path.basename(x) for x in L.get('T', '').split()]; ol = [os.path.basename(x) for x in L.get('O', '').split()]
for n in tl + ol: shutil.copy(f'{final}/{n}', tmp)
for n in tl: subprocess.run(['python3', R, '--t', f'{tmp}/{n}'], check=True)
for n in ol: subprocess.run(['python3', R, f'{tmp}/{n}'], check=True)
for name, v, co in report:
    d = ImageChops.difference(Image.open(f'{tmp}/{name}.png').convert('RGBA'), Image.open(f'{out}/{name}.png').convert('RGBA')).getbbox()
    print(f'{name}: safe-zone ink px={v}  centre offset={co:+d}px  self-contained render={"identical" if d is None else "DIFF"}')
# JPG export (quality 95). JPG has no transparency: overlays are flattened on white, so their transparent PNG is kept as well
for name, v, co in report:
    im = Image.open(f'{final}/{name}.png').convert('RGBA')
    flat = Image.new('RGBA', im.size, (255, 255, 255, 255)); flat.alpha_composite(im)
    flat.convert('RGB').save(f'{final}/{name}.jpg', quality=95, subsampling=0)
    if im.getextrema()[3][0] == 255: os.remove(f'{final}/{name}.png')   # opaque: JPG replaces PNG
# contact sheet + safe-zone row
PS = os.environ.get('PS_SAMPLE'); ps = Image.open(PS).convert('RGB').resize((1080, 1920)) if PS and os.path.exists(PS) else Image.new('RGB', (1080, 1920), (120, 110, 105))
ps.paste((214, 222, 230), (0, 0, 1080, 640))
ov = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0)); dd = ImageDraw.Draw(ov)
for r in UNSAFE: dd.rectangle(r, fill=(255, 0, 0, 70))
fs = sorted(glob.glob(final + '/*.jpg')); W, H = 300, 533
c = Image.new('RGB', (len(fs) * (W + 8) + 8, 2 * H + 60), '#f2f2f2'); d = ImageDraw.Draw(c)
F = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 14)
for i, f in enumerate(fs):
    src = f[:-4] + '.png' if os.path.exists(f[:-4] + '.png') else f
    comp = Image.alpha_composite(ps.convert('RGBA'), Image.open(src).convert('RGBA')); x = 8 + i * (W + 8)
    c.paste(comp.convert('RGB').resize((W, H)), (x, 8)); c.paste(Image.alpha_composite(comp, ov).convert('RGB').resize((W, H)), (x, H + 40))
    d.text((x, H + 14), os.path.basename(f)[:-4][-38:], fill='black', font=F)
c.save(sheet)
