"""Converte a foto preparada (source-prepped.png) num retrato ASCII em SVG que se digita linha por linha.

Uso: python scripts/make_ascii_svg.py [source-prepped.png]   (gera assets/retrato.svg)
A animação é SMIL dentro do próprio SVG: o GitHub não roda JavaScript no README, mas toca a animação do SVG.
"""
import os
import sys
from pathlib import Path

import numpy as np
from PIL import Image

from terminal import janela, salvar

RAMPA = " .`:-=+*cs#%@"  # vazio -> denso; num fundo escuro, denso = claro
COLUNAS = 96
FONTE = 7.2  # px
LARGURA_CHAR = FONTE * 0.6  # monoespaçada
ALTURA_LINHA = FONTE * 1.0
COR = "#d7dee6"
ESTATICO = os.environ.get("STATIC") == "1"


def grade(caminho: str) -> list[str]:
    img = Image.open(caminho).convert("LA")
    w, h = img.size
    linhas = round(COLUNAS * LARGURA_CHAR / ALTURA_LINHA * h / w)
    pequeno = np.asarray(img.resize((COLUNAS, linhas), Image.LANCZOS), dtype=np.float32) / 255.0
    luz, alfa = pequeno[:, :, 0], pequeno[:, :, 1]
    # espalha os tons da pessoa por toda a rampa (sem isso o rosto vira uma mancha de um ou dois caracteres)
    dentro = luz[alfa > 0.5]
    lo, hi = np.percentile(dentro, [3, 97])
    luz = np.clip((luz - lo) / max(hi - lo, 1e-3), 0, 1)
    # o ombro some aos poucos na parte de baixo
    queda = np.clip((linhas - 1 - np.arange(linhas)) / (linhas * 0.22), 0, 1)[:, None]
    densidade = (luz ** 0.85) * alfa * (0.35 + 0.65 * queda)
    idx = np.clip((densidade * (len(RAMPA) - 1)).round().astype(int), 0, len(RAMPA) - 1)
    idx[alfa < 0.5] = 0
    return ["".join(RAMPA[i] for i in linha).rstrip() for linha in idx]


def svg(linhas: list[str]) -> str:
    larg = COLUNAS * LARGURA_CHAR
    x0, y0 = 22, 54
    passo, dur = 0.055, 0.32
    corpo = []
    defs = []
    for i, texto in enumerate(linhas):
        if not texto.strip():
            continue
        y = y0 + i * ALTURA_LINHA
        comp = len(texto) * LARGURA_CHAR
        esc = texto.replace("&", "&amp;").replace("<", "&lt;")
        t = f'<text x="{x0}" y="{y:.1f}" textLength="{comp:.1f}" lengthAdjust="spacingAndGlyphs" xml:space="preserve">{esc}</text>'
        if ESTATICO:
            corpo.append(t)
            continue
        ini = 0.6 + i * passo
        defs.append(
            f'<clipPath id="l{i}"><rect x="{x0}" y="{y - ALTURA_LINHA:.1f}" width="0" height="{ALTURA_LINHA + 2:.1f}">'
            f'<animate attributeName="width" from="0" to="{comp + 2:.1f}" begin="{ini:.3f}s" dur="{dur}s" fill="freeze"/></rect></clipPath>'
        )
        corpo.append(f'<g clip-path="url(#l{i})">{t}</g>')
        # cursor em bloco que acompanha a borda da linha enquanto ela é escrita
        corpo.append(
            f'<rect x="{x0}" y="{y - ALTURA_LINHA + 1.5:.1f}" width="{LARGURA_CHAR:.1f}" height="{ALTURA_LINHA - 1:.1f}" fill="#5fd1c7" opacity="0">'
            f'<set attributeName="opacity" to="0.9" begin="{ini:.3f}s"/>'
            f'<animate attributeName="x" from="{x0}" to="{x0 + comp:.1f}" begin="{ini:.3f}s" dur="{dur}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{ini + dur:.3f}s"/></rect>'
        )
    largura = larg + 2 * x0
    altura = y0 + len(linhas) * ALTURA_LINHA + 8
    conteudo = (
        f"<defs>{''.join(defs)}</defs>"
        f'<g font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,\'Liberation Mono\',monospace" font-size="{FONTE}" fill="{COR}">'
        + "".join(corpo)
        + "</g>"
    )
    return janela(largura, altura, "gabriel@github: ~/retrato", conteudo)


if __name__ == "__main__":
    origem = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    salvar(Path("assets/retrato.svg"), svg(grade(origem)))
