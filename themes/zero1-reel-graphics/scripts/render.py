import sys, asyncio
from playwright.async_api import async_playwright
async def main(pairs, w=1080, h=1920, transparent=False):
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={'width':w,'height':h})
        for html,png in pairs:
            await pg.goto('file://'+html); await pg.wait_for_timeout(300)
            await pg.evaluate('document.fonts.ready')
            await pg.screenshot(path=png, omit_background=transparent)
        await b.close()
if __name__=='__main__':
    args=sys.argv[1:]; t='--t' in args; args=[a for a in args if a!='--t']
    w,h=1080,1920
    if args and args[0].startswith('--size='): w,h=map(int,args[0][7:].split('x')); args=args[1:]
    asyncio.run(main([(a, a.replace('.html','.png')) for a in args], w,h,t))
