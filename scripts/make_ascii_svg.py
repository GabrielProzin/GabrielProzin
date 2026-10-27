"""Converte a foto preparada (source-prepped.png) num retrato ASCII em SVG que se digita linha por linha.

Uso: python scripts/make_ascii_svg.py [source-prepped.png]   (gera assets/retrato.svg)
A animação é SMIL dentro do próprio SVG: o GitHub não roda JavaScript no README, mas toca a animação do SVG.
"""
import colorsys
import os
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from terminal import MONO, janela, salvar

RAMPA = " .:-=+*cs#%@"  # vazio -> denso; num fundo escuro, denso = claro
COLUNAS = 110
FONTE = 6.0  # px
LARGURA_CHAR = FONTE * 0.6  # monoespaçada
ALTURA_LINHA = FONTE * 1.0
COR = "#d7dee6"
GAMA = 0.75  # < 1 deixa as partes iluminadas mais cheias
BORDA = 0.45  # quanto os contornos pesam
LIMIAR = 0.34  # abaixo disso (sombras, cabelo, barba) fica sem caractere, como um estêncil
ESTATICO = os.environ.get("STATIC") == "1"
MONOCROMATICO = os.environ.get("COLORIDO") != "1"  # preto e branco; COLORIDO=1 puxa um tom da foto


def _tom(rgb: np.ndarray, v: float) -> str:
    """Cor do caractere: o matiz da foto, bem claro e pouco saturado (fica um tom pastel, não arco-íris)."""
    h, s, _ = colorsys.rgb_to_hsv(*rgb)
    r, g, b = colorsys.hsv_to_rgb(h, min(s * 0.55, 0.32), 0.72 + 0.28 * v)
    q = lambda x: min(255, round(x * 255 / 16) * 16)  # poucos tons = SVG menor
    return f"#{q(r):02x}{q(g):02x}{q(b):02x}"


def grade(caminho: str) -> list[list[tuple[str, str]]]:
    """Cada linha é uma lista de (caractere, cor)."""
    img = Image.open(caminho).convert("RGBA")
    w, h = img.size
    linhas = round(COLUNAS * LARGURA_CHAR / ALTURA_LINHA * h / w)
    # contornos (orelha, mandíbula, fios do cabelo) ganham traço mesmo onde é escuro
    cheia = np.asarray(img, dtype=np.float32) / 255.0
    cinza = cv2.GaussianBlur(cheia[:, :, :3] @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32), (0, 0), 1.6)
    borda = np.hypot(cv2.Sobel(cinza, cv2.CV_32F, 1, 0), cv2.Sobel(cinza, cv2.CV_32F, 0, 1)) * (cheia[:, :, 3] > 0.5)
    borda = cv2.resize(borda, (COLUNAS, linhas), interpolation=cv2.INTER_AREA)
    borda = np.clip(borda / max(np.percentile(borda[borda > 0], 97), 1e-3), 0, 1)
    px = np.asarray(img.resize((COLUNAS, linhas), Image.LANCZOS), dtype=np.float32) / 255.0
    rgb, alfa = px[:, :, :3], px[:, :, 3]
    luz = rgb @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    # espalha os tons da pessoa por toda a escala antes de cortar as sombras
    dentro = luz[alfa > 0.5]
    lo, hi = np.percentile(dentro, [2, 98])
    luz = np.clip((luz - lo) / max(hi - lo, 1e-3), 0, 1)
    # a parte de baixo (ombros) some aos poucos
    queda = np.clip((linhas - 1 - np.arange(linhas)) / (linhas * 0.18), 0, 1)[:, None]
    v = np.clip(luz ** GAMA + BORDA * borda, 0, 1) * (0.4 + 0.6 * queda)
    niveis = len(RAMPA) - 1
    idx = np.where(v < LIMIAR, 0, 1 + np.floor((v - LIMIAR) / (1 - LIMIAR) * (niveis - 0.001))).astype(int)
    idx[alfa < 0.5] = 0
    saida = []
    for y in range(linhas):
        linha = [(RAMPA[idx[y, x]], COR if MONOCROMATICO else _tom(rgb[y, x], float(v[y, x]))) for x in range(COLUNAS)]
        while linha and linha[-1][0] == " ":
            linha.pop()
        saida.append(linha)
    return saida


def _tspans(linha: list[tuple[str, str]]) -> str:
    """Junta caracteres seguidos da mesma cor num tspan só."""
    partes, atual, buf = [], None, ""
    for ch, cor in linha:
        cor = None if ch == " " else cor
        if cor != atual and ch != " ":
            if buf:
                partes.append(buf if atual is None else f'<tspan fill="{atual}">{buf}</tspan>')
            atual, buf = cor, ""
        buf += ch.replace("&", "&amp;").replace("<", "&lt;")
    if buf:
        partes.append(buf if atual is None else f'<tspan fill="{atual}">{buf}</tspan>')
    return "".join(partes)


def svg(linhas: list[str]) -> str:
    larg = COLUNAS * LARGURA_CHAR
    x0, y0 = 22, 54
    passo, dur = 0.04, 0.3
    corpo = []
    defs = []
    for i, linha in enumerate(linhas):
        if not linha:
            continue
        y = y0 + i * ALTURA_LINHA
        comp = len(linha) * LARGURA_CHAR
        t = f'<text x="{x0}" y="{y:.1f}" textLength="{comp:.1f}" lengthAdjust="spacingAndGlyphs" xml:space="preserve">{_tspans(linha)}</text>'
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
    fim_retrato = y0 + len(linhas) * ALTURA_LINHA
    altura = fim_retrato + 34
    # linha de prompt no rodapé, como no terminal: aparece quando o retrato termina
    fim_anim = 0.6 + len(linhas) * passo + dur
    prompt = (
        f'<g font-family="{MONO}" font-size="11"{"" if ESTATICO else " opacity=\"0\""}>'
        + ("" if ESTATICO else f'<set attributeName="opacity" to="1" begin="{fim_anim:.2f}s"/>')
        + f'<text x="{x0}" y="{fim_retrato + 22:.1f}"><tspan fill="#5fd1c7">gabriel@github</tspan><tspan fill="#8b949e">:~$</tspan>'
        f'<tspan fill="#8b949e"> whoami </tspan><tspan fill="#e6edf3" font-weight="600">Gabriel Mendes</tspan></text>'
        f'<rect x="{x0 + 261}" y="{fim_retrato + 12:.1f}" width="6.5" height="12" fill="#5fd1c7">'
        + ("" if ESTATICO else '<animate attributeName="opacity" values="1;1;0;0" keyTimes="0;0.5;0.5;1" dur="1s" repeatCount="indefinite"/>')
        + "</rect></g>"
    )
    conteudo = (
        f"<defs>{''.join(defs)}</defs>"
        f'<g font-family="ui-monospace,SFMono-Regular,Menlo,Consolas,\'Liberation Mono\',monospace" font-size="{FONTE}" fill="{COR}">'
        + "".join(corpo)
        + "</g>" + prompt
    )
    return janela(largura, altura, "gabriel@github: ~/retrato", conteudo)


if __name__ == "__main__":
    origem = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    salvar(Path("assets/retrato.svg"), svg(grade(origem)))
