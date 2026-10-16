"""Verificação do portfólio antes de publicar.

Uso (na raiz do repositório):
    python tools/verificar.py            checagens estáticas + navegador
    python tools/verificar.py --links    também testa os links externos
    python tools/verificar.py --fotos D  salva capturas de tela na pasta D
    python tools/verificar.py --servir   só abre a prévia no navegador (Ctrl+C encerra)

O site é servido localmente em http://127.0.0.1:8765/Portfolio/, o mesmo
caminho do GitHub Pages, para pegar erro de caminho relativo.
Precisa de Playwright (pip install playwright; python -m playwright install chromium).
"""
import argparse
import functools
import http.server
import re
import sys
import threading
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PAGINAS = {"pt": RAIZ / "index.html", "en": RAIZ / "en" / "index.html"}
LARGURAS = [360, 390, 768, 1024, 1280, 1440]
PORTA = 8765
BASE = f"http://127.0.0.1:{PORTA}/Portfolio/"

falhas = []


def falha(msg):
    falhas.append(msg)
    print("  FALHA", msg)


# ------------------------------------------------------------------ estático

class Leitor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.texto = []
        self.refs = []
        self.ids = []
        self.classes = []
        self.imgs_sem_alt = 0
        self.h1 = 0
        self.pilha = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag not in ("meta", "link", "img", "source", "br", "input", "circle", "path", "rect"):
            self.pilha.append(tag)
        if tag == "h1":
            self.h1 += 1
        if tag == "img" and not a.get("alt"):
            self.imgs_sem_alt += 1
        if "id" in a:
            self.ids.append(a["id"])
        for c in (a.get("class") or "").split():
            self.classes.append(c)
        for k in ("href", "src"):
            if a.get(k):
                self.refs.append(a[k])
        for k in ("srcset", "imagesrcset"):
            if a.get(k):
                self.refs += [p.strip().split()[0] for p in a[k].split(",")]

    def handle_endtag(self, tag):
        if tag in self.pilha:
            while self.pilha and self.pilha.pop() != tag:
                pass

    def handle_data(self, data):
        if not any(t in ("script", "style") for t in self.pilha):
            self.texto.append(data)


def estatico():
    print("Checagens estáticas")
    lidos = {}
    for lang, arq in PAGINAS.items():
        html = arq.read_text(encoding="utf-8")
        L = Leitor()
        L.feed(html)
        lidos[lang] = L
        texto = " ".join(L.texto)
        visivel_e_meta = texto + " " + " ".join(re.findall(r'content="([^"]*)"', html))

        if re.search(r"[—–]", visivel_e_meta):
            falha(f"{lang}: travessão no texto: {re.findall(r'.{30}[—–].{30}', visivel_e_meta)[:3]}")
        for termo in ("TODO", "Lorem", "lorem", "placeholder", "Varad", "Accomplishments", "XXX"):
            if termo in texto:
                falha(f"{lang}: termo proibido no texto visível: {termo}")
        if L.h1 != 1:
            falha(f"{lang}: {L.h1} elementos h1")
        if L.imgs_sem_alt:
            falha(f"{lang}: {L.imgs_sem_alt} imagens sem alt")
        if len(L.ids) != len(set(L.ids)):
            falha(f"{lang}: id repetido")
        for ref in L.refs:
            if ref.startswith(("http://",)):
                falha(f"{lang}: link sem https: {ref}")
            if ref.startswith(("https://", "mailto:", "#", "data:")):
                continue
            alvo = (arq.parent / ref.split("#")[0]).resolve()
            if alvo.is_dir():
                alvo = alvo / "index.html"
            if not alvo.exists():
                falha(f"{lang}: caminho local inexistente: {ref}")
        print(f"  {lang}: {len(L.refs)} referências, {len(texto.split())} palavras")

    # as duas versões precisam ter a mesma estrutura
    pt, en = lidos["pt"], lidos["en"]
    if pt.ids != en.ids:
        falha(f"ids diferentes entre pt e en: {set(pt.ids) ^ set(en.ids)}")
    for c in ("case", "card", "job", "role", "skill", "principles", "chips", "arrow-link", "tag"):
        a, b = pt.classes.count(c), en.classes.count(c)
        if a != b:
            falha(f"quantidade de .{c} difere: pt={a} en={b}")
    externos = sorted({r for r in pt.refs + en.refs if r.startswith("https://") and "fonts.g" not in r})
    return externos


def links(externos):
    print(f"Links externos ({len(externos)})")
    for u in externos:
        if u.startswith("https://mayara-tech.github.io/Portfolio/"):
            continue
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
            cod = urllib.request.urlopen(req, timeout=20).status
        except urllib.error.HTTPError as e:
            cod = e.code
        except Exception as e:  # noqa: BLE001
            cod = type(e).__name__
        # o LinkedIn responde 999 para robôs, o que não quer dizer link quebrado
        ok = cod == 200 or (cod == 999 and "linkedin.com" in u)
        print(f"  {'ok   ' if ok else 'FALHA'} {cod} {u}")
        if not ok:
            falhas.append(f"link externo {cod}: {u}")


# ------------------------------------------------------------------ navegador

class Servidor(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        if path.startswith("/Portfolio"):
            path = path[len("/Portfolio"):] or "/"
        else:
            return str(RAIZ / "__nao_existe__")
        return super().translate_path(path)

    def log_message(self, *a):
        pass


SOBREPOSICAO_JS = r"""
() => {
  const sel = 'h1,h2,h3,h4,p,dt,dd,.chips li,.flow li span,.tag,.btn,.icon-link,.arrow-link,.bullets li,.job__when strong,.inst,.when span,.k,.v,.copy,.brand,.lang,.nav__list a,.system-card,.portrait';
  const els = [...document.querySelectorAll(sel)].filter(e => {
    const r = e.getBoundingClientRect(); const s = getComputedStyle(e);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.opacity !== '0' && !e.closest('details:not([open]) > :not(summary)') && !e.closest('.nav:not(.is-open)') ;
  });
  const out = [];
  const R = els.map(e => e.getBoundingClientRect());
  for (let i = 0; i < els.length; i++) for (let j = i + 1; j < els.length; j++) {
    const a = els[i], b = els[j];
    if (a.contains(b) || b.contains(a)) continue;
    // o cartão de áreas fica de propósito sobre a foto
    if ((a.closest('.hero__visual') && b.closest('.hero__visual'))) continue;
    const r1 = R[i], r2 = R[j];
    const w = Math.min(r1.right, r2.right) - Math.max(r1.left, r2.left);
    const h = Math.min(r1.bottom, r2.bottom) - Math.max(r1.top, r2.top);
    if (w > 2 && h > 2) out.push(`${a.tagName}.${a.className} "${(a.textContent||'').trim().slice(0,30)}" x ${b.tagName}.${b.className} "${(b.textContent||'').trim().slice(0,30)}"`);
  }
  // textos do diagrama não podem encostar nos nós nem sair da caixa
  document.querySelectorAll('.system-card svg').forEach(svg => {
    const box = svg.getBoundingClientRect();
    const nos = [...svg.querySelectorAll('circle')].map(c => c.getBoundingClientRect());
    svg.querySelectorAll('text').forEach(t => {
      const r = t.getBoundingClientRect();
      if (r.left < box.left - 1 || r.right > box.right + 1) out.push('texto do diagrama vaza: ' + t.textContent);
      nos.forEach(n => { if (Math.min(r.right,n.right)-Math.max(r.left,n.left) > 0 && Math.min(r.bottom,n.bottom)-Math.max(r.top,n.top) > 0) out.push('texto do diagrama encosta no nó: ' + t.textContent); });
    });
  });
  // título de seção escondido atrás do cabeçalho fixo ao navegar por âncora é checado à parte
  return out;
}
"""


def navegador(pasta_fotos):
    from playwright.sync_api import sync_playwright

    print("Navegador")
    handler = functools.partial(Servidor, directory=str(RAIZ))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORTA), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    with sync_playwright() as p:
        nav = p.chromium.launch()
        for lang in ("pt", "en"):
            url = BASE + ("" if lang == "pt" else "en/")
            for w in LARGURAS:
                for altura in (720, 900):
                    ctx = nav.new_context(viewport={"width": w, "height": altura}, reduced_motion="reduce")
                    pg = ctx.new_page()
                    erros = []
                    pg.on("console", lambda m: erros.append(m.text) if m.type in ("error", "warning") else None)
                    pg.on("pageerror", lambda e: erros.append(str(e)))
                    pg.on("requestfailed", lambda r: erros.append("falhou " + r.url))
                    pg.on("response", lambda r: erros.append(f"{r.status} {r.url}") if r.status >= 400 else None)
                    pg.goto(url, wait_until="networkidle")
                    pg.evaluate("document.fonts.ready")
                    tag = f"{lang} {w}x{altura}"
                    for e in erros:
                        falha(f"{tag}: console/rede: {e}")
                    sw = pg.evaluate("document.documentElement.scrollWidth")
                    if sw > w:
                        largos = pg.evaluate(f"[...document.querySelectorAll('body *')].filter(e=>e.getBoundingClientRect().right>{w}+1).slice(0,5).map(e=>e.tagName+'.'+e.className)")
                        falha(f"{tag}: rolagem horizontal ({sw}px): {largos}")
                    for s in pg.evaluate(SOBREPOSICAO_JS):
                        falha(f"{tag}: sobreposição: {s}")
                    if altura == 900 and pasta_fotos:
                        pg.screenshot(path=str(Path(pasta_fotos) / f"{lang}-{w}.png"), full_page=True)
                    ctx.close()

            # fluxos: menu móvel, âncoras, troca de idioma, revelação ao rolar
            ctx = nav.new_context(viewport={"width": 390, "height": 800})
            pg = ctx.new_page()
            pg.goto(url, wait_until="networkidle")
            btn = pg.locator(".menu-btn")
            btn.click()
            if btn.get_attribute("aria-expanded") != "true" or not pg.locator("#nav").is_visible():
                falha(f"{lang}: menu móvel não abre")
            pg.locator(".nav__list a").nth(1).click()
            pg.wait_for_timeout(900)
            if btn.get_attribute("aria-expanded") != "false":
                falha(f"{lang}: menu móvel não fecha ao escolher seção")
            topo = pg.evaluate("document.getElementById('projects').querySelector('h2').getBoundingClientRect().top")
            if topo < 64:
                falha(f"{lang}: título de Projetos fica atrás do cabeçalho ({topo}px)")
            btn.click()
            pg.keyboard.press("Escape")
            if btn.get_attribute("aria-expanded") != "false":
                falha(f"{lang}: Esc não fecha o menu")
            ctx.close()

            ctx = nav.new_context(viewport={"width": 1280, "height": 800})
            pg = ctx.new_page()
            pg.goto(url, wait_until="networkidle")
            altura_total = pg.evaluate("document.body.scrollHeight")
            for y in range(0, altura_total, 500):
                pg.mouse.wheel(0, 500)
                pg.wait_for_timeout(60)
            pg.wait_for_timeout(900)
            escondidos = pg.evaluate("[...document.querySelectorAll('.reveal:not(.is-in)')].filter(e=>!e.closest('details:not([open])')).length")
            if escondidos:
                falha(f"{lang}: {escondidos} blocos continuam invisíveis depois de rolar")
            ativo = pg.evaluate("document.querySelector('.nav__list a[aria-current]')?.getAttribute('href')")
            if ativo != "#contact":
                falha(f"{lang}: menu não marca a seção atual no fim da página ({ativo})")
            # teclado: o primeiro Tab mostra o atalho para o conteúdo
            pg.evaluate("window.scrollTo(0,0)")
            pg.keyboard.press("Tab")
            if pg.evaluate("document.activeElement.className") != "skip":
                falha(f"{lang}: primeiro Tab não vai para 'pular para o conteúdo'")
            href = pg.locator(".lang").get_attribute("href")
            resp = pg.goto(url + href if not href.startswith("..") else BASE)
            if not resp or resp.status != 200:
                falha(f"{lang}: troca de idioma quebrada ({href})")
            ctx.close()

            # sem JavaScript a página precisa continuar legível
            ctx = nav.new_context(viewport={"width": 390, "height": 800}, java_script_enabled=False)
            pg = ctx.new_page()
            pg.goto(url, wait_until="networkidle")
            if not pg.locator("#projects h2").is_visible() or not pg.locator(".nav__list a").first.is_visible():
                falha(f"{lang}: sem JavaScript o conteúdo ou o menu some")
            ctx.close()
            print(f"  {lang}: {len(LARGURAS) * 2} tamanhos de tela + fluxos")
        nav.close()
    srv.shutdown()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--links", action="store_true")
    ap.add_argument("--fotos")
    ap.add_argument("--servir", action="store_true")
    args = ap.parse_args()
    if args.servir:
        import webbrowser
        handler = functools.partial(Servidor, directory=str(RAIZ))
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", PORTA), handler)
        print(f"Prévia em {BASE}  (Ctrl+C para encerrar)")
        webbrowser.open(BASE)
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            pass
        return
    externos = estatico()
    if args.links:
        links(externos)
    navegador(args.fotos)
    print()
    if falhas:
        print(f"{len(falhas)} problema(s).")
        sys.exit(1)
    print("Tudo certo.")


if __name__ == "__main__":
    main()
