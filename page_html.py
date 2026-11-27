"""A frame made editable as a fixed design keeps its whole page as HTML (frame["page"]). Edit layers points at an
element by its child-index path under <body> ("page>2.0.1"), the same numbering the browser uses (elements only).

locate()   -> where that element sits in the page text
outer()    -> its markup (context for the AI)
set_picture() -> its picture swapped for another file, without the AI (Replace with an image)
detach_js  -> run in the rendered preview: the page as static HTML (scripts gone, marked data-page)"""
from html.parser import HTMLParser
import re

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class _Finder(HTMLParser):
    def __init__(self, steps):
        super().__init__(convert_charrefs=False)
        self.steps, self.stack, self.found = steps, [], None   # stack: [tag, path, child_count]
        self.in_body = False
        self.lines = None

    def _off(self):
        line, col = self.getpos()
        return self.lines[line - 1] + col

    def handle_starttag(self, tag, attrs):
        self._start(tag, self.get_starttag_text() or "", False)

    def handle_startendtag(self, tag, attrs):
        self._start(tag, self.get_starttag_text() or "", True)

    def _start(self, tag, text, selfclose):
        off = self._off()
        if not self.in_body:
            if tag == "body":
                self.in_body = True
                self.stack = [["body", [], 0]]
            return
        par = self.stack[-1]
        path = par[1] + [par[2]]
        par[2] += 1
        if self.found is None and path == self.steps:
            self.found = {"tag": tag, "start": off, "tag_end": off + len(text), "end": None}
            if tag in VOID or selfclose:
                self.found["end"] = off + len(text)
        if tag not in VOID and not selfclose:
            self.stack.append([tag, path, 0])

    def handle_endtag(self, tag):
        if not self.in_body or len(self.stack) <= 1:
            return
        off = self._off()
        if tag in ("body", "html"):
            self._pop_to(1, off, None)
            return
        for k in range(len(self.stack) - 1, 0, -1):     # close up to the matching tag (forgiving, like a browser)
            if self.stack[k][0] == tag:
                self._pop_to(k, off, tag)
                return

    def _pop_to(self, k, off, tag):
        while len(self.stack) > k:
            t = self.stack.pop()
            f = self.found
            if f and f["end"] is None and t[1] == self.steps:
                f["end"] = off + len(f"</{tag}>") if tag and t[0] == tag else off


def locate(page: str, path: str):
    """{"tag", "start", "tag_end", "end"} of the element at a body child-index path ("2.0.1"), or None."""
    try:
        steps = [int(x) for x in str(path).split(".") if x != ""]
    except ValueError:
        return None
    if not steps:
        return None
    p = _Finder(steps)
    starts, n = [0], 0
    for ln in page.splitlines(keepends=True):
        n += len(ln)
        starts.append(n)
    p.lines = starts
    try:
        p.feed(page)
        p.close()
    except Exception:
        return None
    f = p.found
    if f and f["end"] is None:          # never closed: runs to where the page ends
        m = re.search(r"</body\s*>", page[f["tag_end"]:], re.I)
        f["end"] = f["tag_end"] + m.start() if m else len(page)
    return f


def outer(page: str, path: str) -> str | None:
    f = locate(page, path)
    return page[f["start"]:f["end"]] if f else None


def set_picture(page: str, path: str, src: str) -> str | None:
    """The picture of that layer becomes `src`: an <img> gets a new src; a box with a background picture gets the
    new url; a block holding one picture swaps that one. None when the layer has no picture to swap."""
    f = locate(page, path)
    if not f:
        return None
    tag_text = page[f["start"]:f["tag_end"]]
    if f["tag"] == "img":
        if re.search(r'\ssrc\s*=\s*("[^"]*"|\'[^\']*\'|[^\s>]+)', tag_text):
            new_tag = re.sub(r'(\ssrc\s*=\s*)("[^"]*"|\'[^\']*\'|[^\s>]+)', lambda m: f'{m.group(1)}"{src}"', tag_text, count=1)
        else:
            new_tag = tag_text.replace("<img", f'<img src="{src}"', 1)
        new_tag = re.sub(r'\s(srcset)\s*=\s*("[^"]*"|\'[^\']*\')', "", new_tag)
        return page[:f["start"]] + new_tag + page[f["tag_end"]:]
    if re.search(r"background(-image)?\s*:[^;\"']*url\(", tag_text):
        new_tag = re.sub(r"url\((['\"]?)[^)'\"]*\1\)", lambda m: f"url({m.group(1)}{src.replace(' ', '%20')}{m.group(1)})", tag_text, count=1)
        return page[:f["start"]] + new_tag + page[f["tag_end"]:]
    inner = page[f["tag_end"]:f["end"]]
    imgs = list(re.finditer(r"<img\b[^>]*>", inner))
    if len(imgs) == 1:
        m = imgs[0]
        t = m.group(0)
        nt = (re.sub(r'(\ssrc\s*=\s*)("[^"]*"|\'[^\']*\'|[^\s>]+)', lambda q: f'{q.group(1)}"{src}"', t, count=1)
              if re.search(r"\ssrc\s*=", t) else t.replace("<img", f'<img src="{src}"', 1))
        a = f["tag_end"] + m.start()
        return page[:a] + nt + page[a + len(t):]
    return None


DETACH_JS = r"""() => {
  document.querySelectorAll('script, base').forEach(e => e.remove());
  document.body.removeAttribute('class');
  document.body.dataset.page = '1';
  return '<!doctype html>\n' + document.documentElement.outerHTML;
}"""


def clean_detached(html: str, origin: str, theme: str) -> str:
    """Links the browser made absolute (to this server) back to the kit's relative paths."""
    html = html.replace(f"{origin}/themes/{theme}/scenes/", "").replace(f"{origin}/themes/{theme}/", "../")
    return html.replace(origin, "")
