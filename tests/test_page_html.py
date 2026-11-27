import page_html as ph

PG = ('<!doctype html>\n<html><head><link rel="stylesheet" href="../t.css"></head><body data-page="1">'
      '<div class="bg" style="background-image:url(\'../assets/a.jpg\')"></div>\n'
      '<div class="L"><img src="../x.png"><p>Hi <b>there</b></p></div>'
      '<table><tbody><tr><td>1</td></tr></tbody></table></body></html>')


def test_paths_match_browser_numbering():
    assert ph.outer(PG, "1.0") == '<img src="../x.png">'
    assert ph.outer(PG, "1.1.0") == "<b>there</b>"
    assert ph.outer(PG, "2.0.0.0") == "<td>1</td>"
    assert ph.outer(PG, "9") is None


def test_picture_swap_without_ai():
    assert '<img src="../assets/uploads/n.png">' in ph.set_picture(PG, "1.0", "../assets/uploads/n.png")
    assert "url('../assets/b.jpg')" in ph.set_picture(PG, "0", "../assets/b.jpg")
    assert '<img src="new.png">' in ph.set_picture(PG, "1", "new.png")      # a block with one picture
    assert ph.set_picture(PG, "1.1", "x.png") is None                        # words: nothing to swap


def test_detached_links_made_relative():
    h = ph.clean_detached('<img src="http://127.0.0.1:8000/themes/k/scenes/../assets/a.png">', "http://127.0.0.1:8000", "k")
    assert h == '<img src="../assets/a.png">'
