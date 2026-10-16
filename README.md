# Portfólio · Mayara Alves

Código do meu portfólio pessoal, publicado em https://mayara-tech.github.io/Portfolio/ (português) e https://mayara-tech.github.io/Portfolio/en/ (inglês).

Site estático em HTML, CSS e JavaScript puro. Sem framework, sem etapa de build e sem serviço pago. O GitHub Pages publica os arquivos exatamente como estão no repositório.

## Estrutura

```
index.html            versão em português (padrão)
en/index.html         versão em inglês
assets/css/main.css   estilo único das duas versões
assets/js/main.js     menu móvel, seção ativa, revelação ao rolar, copiar e-mail
assets/img/           foto, ícones e imagens de compartilhamento
tools/verificar.py    checagens antes de publicar
tools/gerar_imagens.py  gera ícones e imagens de compartilhamento
sitemap.xml
```

As duas páginas têm a mesma estrutura e os mesmos `id` de seção (`#about`, `#projects`, `#experience`, `#skills`, `#education`, `#contact`). Ao mudar um conteúdo, mude nas duas. O `verificar.py` acusa quando a quantidade de projetos, cargos, competências ou links fica diferente entre elas.

Todos os caminhos são relativos, então o site funciona dentro de `/Portfolio/` sem configuração extra.

## Prévia local

```
python tools/verificar.py --servir
```

Abre http://127.0.0.1:8765/Portfolio/ no navegador, no mesmo caminho do GitHub Pages.

## Verificação

```
pip install playwright pillow
python -m playwright install chromium
python tools/verificar.py --links
```

Confere, nas duas versões:

- travessão e termos de rascunho no texto visível, imagens sem `alt`, `id` repetido, um único `h1`
- caminhos locais quebrados e links externos fora do ar (`--links`)
- mesma estrutura entre português e inglês
- seis larguras de tela (360 a 1440 px) em duas alturas: rolagem horizontal, texto sobreposto, erro no console e recurso que falhou ao carregar
- menu móvel (abre, fecha ao escolher seção e com Esc), âncora não fica atrás do cabeçalho, seção ativa no menu, primeiro Tab no atalho "pular para o conteúdo", troca de idioma e leitura sem JavaScript

`--fotos PASTA` salva capturas de página inteira de cada largura.

## Cores e fontes

As cores ficam no topo de `assets/css/main.css`, em `:root`. Trocar `--accent` e `--accent-ink` repinta destaques, diagramas e foco. Fontes do Google Fonts: Geist (texto), Geist Mono (rótulos) e Instrument Serif (destaques em itálico).

## Versão anterior

A versão 1, baseada em Materialize, está preservada na tag `v1-legado`:

```
git checkout v1-legado
```
