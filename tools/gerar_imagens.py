"""Gera as imagens derivadas do portfólio: ícones e imagens de compartilhamento.

Uso (na raiz do repositório):
    python tools/gerar_imagens.py

Precisa de Python com Playwright e Pillow:
    pip install playwright pillow
    python -m playwright install chromium

Saída em assets/img: favicon-32.png, apple-touch-icon.png, og-pt.png, og-en.png.
Rode de novo só quando mudar o título, a foto ou as cores.
"""
import base64
from pathlib import Path

from playwright.sync_api import sync_playwright

RAIZ = Path(__file__).resolve().parent.parent
IMG = RAIZ / "assets" / "img"

FOTO = base64.b64encode((IMG / "mayara-800.jpg").read_bytes()).decode()

OG = {
    "pt": {
        "eyebrow": "Tecnologia / Inteligência Artificial / Automação",
        "titulo": "Desenvolvimento de soluções digitais e otimização de processos.",
        "rodape": "Portfólio",
    },
    "en": {
        "eyebrow": "Technology / Artificial Intelligence / Automation",
        "titulo": "Building digital solutions and making processes work better.",
        "rodape": "Portfolio",
    },
}

MOLDE_OG = """<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Geist+Mono:wght@400&family=Instrument+Serif:ital@1&display=block" rel="stylesheet">
<style>
*{{box-sizing:border-box;margin:0}}
body{{width:1200px;height:630px;background:#f6f5f1;font-family:Geist,sans-serif;color:#15151b;position:relative;overflow:hidden}}
.grid{{position:absolute;inset:0;background-image:linear-gradient(#e2dfd7 1px,transparent 1px),linear-gradient(90deg,#e2dfd7 1px,transparent 1px);background-size:56px 56px;-webkit-mask-image:radial-gradient(ellipse 60% 70% at 80% 30%,#000 10%,transparent 75%);opacity:.6}}
.txt{{position:absolute;left:80px;top:84px;width:640px}}
.eb{{font-family:'Geist Mono',monospace;font-size:20px;color:#464650;display:flex;align-items:center;gap:14px}}
.eb i{{width:12px;height:12px;border-radius:50%;background:#5546d6;box-shadow:0 0 0 6px #ecebfb;display:block}}
h1{{font-size:104px;letter-spacing:-.045em;line-height:.95;font-weight:600;margin-top:44px}}
h1 span{{font-family:'Instrument Serif',serif;font-style:italic;font-weight:400;color:#3f31b5;letter-spacing:0}}
p{{font-size:34px;line-height:1.25;letter-spacing:-.015em;margin-top:30px;font-weight:500}}
.ft{{position:absolute;left:80px;bottom:56px;font-family:'Geist Mono',monospace;font-size:18px;color:#66666f}}
.foto{{position:absolute;right:80px;top:80px;width:336px;height:420px;border-radius:28px;overflow:hidden;box-shadow:0 20px 50px -20px rgba(21,21,27,.35)}}
.foto img{{width:100%;height:100%;object-fit:cover}}
</style></head><body><div class="grid"></div>
<div class="txt"><div class="eb"><i></i>{eyebrow}</div><h1>Mayara <span>Alves</span></h1><p>{titulo}</p></div>
<div class="foto"><img src="data:image/jpeg;base64,{foto}"></div>
<div class="ft">mayara-tech.github.io/Portfolio · {rodape}</div>
</body></html>"""


def main():
    favicon = (IMG / "favicon.svg").read_text(encoding="utf-8")
    with sync_playwright() as p:
        nav = p.chromium.launch()
        pg = nav.new_page()
        for nome, lado in (("favicon-32.png", 32), ("apple-touch-icon.png", 180)):
            pg.set_viewport_size({"width": lado, "height": lado})
            pg.set_content(
                f'<style>*{{margin:0}}svg{{width:{lado}px;height:{lado}px;display:block}}</style>{favicon}'
            )
            pg.screenshot(path=str(IMG / nome), omit_background=True)
        pg.set_viewport_size({"width": 1200, "height": 630})
        for lang, t in OG.items():
            pg.set_content(MOLDE_OG.format(foto=FOTO, **t))
            pg.wait_for_load_state("networkidle")
            pg.evaluate("document.fonts.ready")
            pg.screenshot(path=str(IMG / f"og-{lang}.png"))
        nav.close()
    print("ok")


if __name__ == "__main__":
    main()
