"""Moldura de janela de terminal usada pelos SVGs do perfil (mesmo visual nos três)."""
from pathlib import Path

FUNDO = "#0d1117"
BORDA = "#30363d"
BARRA = "#161b22"
TEXTO_BARRA = "#8b949e"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,'Liberation Mono',monospace"


def janela(largura: float, altura: float, titulo: str, conteudo: str) -> str:
    """SVG completo: janela escura com cantos arredondados, barra com os três botões e o título."""
    w, h = round(largura), round(altura)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{titulo}">'
        f'<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="10" fill="{FUNDO}" stroke="{BORDA}"/>'
        f'<path d="M0.5 10.5a10 10 0 0 1 10-10h{w - 21}a10 10 0 0 1 10 10v20h-{w - 1}z" fill="{BARRA}"/>'
        f'<line x1="0.5" y1="30.5" x2="{w - 0.5}" y2="30.5" stroke="{BORDA}"/>'
        '<circle cx="18" cy="15.5" r="5" fill="#ff5f57"/><circle cx="34" cy="15.5" r="5" fill="#febc2e"/><circle cx="50" cy="15.5" r="5" fill="#28c840"/>'
        f'<text x="{w / 2:.1f}" y="19.5" text-anchor="middle" font-family="{MONO}" font-size="11" fill="{TEXTO_BARRA}">{titulo}</text>'
        f"{conteudo}</svg>"
    )


def salvar(caminho: Path, svg: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(svg, encoding="utf-8")
    print(f"gerado: {caminho} ({len(svg) / 1024:.0f} KB)")
