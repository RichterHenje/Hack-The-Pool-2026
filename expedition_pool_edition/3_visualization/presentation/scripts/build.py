import os
d = os.path.dirname(os.path.abspath(__file__))
t = open(os.path.join(d, "tpl.html"), encoding="utf-8").read()
m = open(os.path.join(d, "map.svgfrag"), encoding="utf-8").read()
open(os.path.join(d, "datenfluss.html"), "w", encoding="utf-8").write(t.replace("<!--MAP-->", m))
