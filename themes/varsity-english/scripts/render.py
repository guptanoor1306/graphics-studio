#!/usr/bin/env python3
"""Render scene HTML files to 1920x1080 PNGs.
Usage: python3 scripts/render.py scenes/0.47.html [more.html ...] [--out out_dir]
For each scene writes <name>.png (on its plate). Anchor-shot scenes (no class "fss" on <body>)
also get <name>_overlay.png: transparent, graphics only, for the editor to lay over the real footage.
The overlay is made by adding class "overlay" to <body>, which hides .plate."""
import sys, os, asyncio
from playwright.async_api import async_playwright
argv=sys.argv[1:]; out='out'
if '--out' in argv:
    i=argv.index('--out'); out=argv[i+1]; del argv[i:i+2]
args=[a for a in argv if not a.startswith('--')]
os.makedirs(out,exist_ok=True)
async def main():
    async with async_playwright() as p:
        exe=os.environ.get('CHROMIUM_PATH') or next((c for c in ['/opt/pw-browsers/chromium','/usr/bin/chromium','/usr/bin/chromium-browser','/usr/bin/google-chrome'] if os.path.isfile(c)),None)
        try: b=await p.chromium.launch()
        except Exception:
            if not exe: raise
            b=await p.chromium.launch(executable_path=exe)
        pg=await b.new_page(viewport={'width':1920,'height':1080})
        for f in args:
            name=os.path.splitext(os.path.basename(f))[0]
            await pg.goto('file://'+os.path.abspath(f)); await pg.wait_for_timeout(300)
            await pg.evaluate("document.fonts.ready")
            await pg.screenshot(path=f'{out}/{name}.png')
            if await pg.evaluate("document.body.classList.contains('fss')"):
                print('rendered',name,'(FSS: no overlay)'); continue
            await pg.evaluate("document.body.classList.add('overlay');document.querySelectorAll('.plate').forEach(e=>e.style.display='none')")
            await pg.screenshot(path=f'{out}/{name}_overlay.png',omit_background=True)
            print('rendered',name)
        await b.close()
asyncio.run(main())
