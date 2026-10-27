"""Desenha data/contributions.json como o calendário de contribuições (53 semanas x 7 dias) em SVG animado.

Os quadrados aparecem uma vez, em diagonal, e param (sem loop). Gera assets/contribuicoes.svg.
"""
import json
from datetime import date
from pathlib import Path

from terminal import MONO, janela, salvar

ENTRADA = Path("data/contributions.json")
CORES = ["#161b22", "#0e4441", "#11706a", "#1fa196", "#4fd8cb"]  # nível 0 a 4, no tom do portfólio
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
CEL, GAP = 11.6, 3.2
X0, Y0 = 52, 74  # canto do primeiro quadrado


def data_br(iso: str) -> str:
    d = date.fromisoformat(iso)
    return f"{d.day:02d}/{d.month:02d}/{d.year}"


def svg(dados: dict) -> str:
    dias = dados["dias"]
    primeiro = date.fromisoformat(dias[0]["data"])
    deslocamento = (primeiro.weekday() + 1) % 7  # coluna começa no domingo, como no GitHub
    passo = CEL + GAP
    semanas = (deslocamento + len(dias) + 6) // 7
    largura = X0 + semanas * passo + 22
    css = (
        "<style>"
        ".c{opacity:0;transform:translateY(-6px);transform-box:fill-box;animation:entra .5s cubic-bezier(.2,.8,.2,1) forwards}"
        "@keyframes entra{to{opacity:1;transform:none}}"
        ".t{font-family:" + MONO + ";fill:#8b949e;font-size:11px}"
        ".v{font-family:" + MONO + ";fill:#e6edf3;font-size:12.5px}"
        ".k{font-family:" + MONO + ";fill:#5fd1c7;font-size:12.5px}"
        ".s{opacity:0;animation:aparece .6s ease-out forwards}"
        "@keyframes aparece{to{opacity:1}}"
        "</style>"
    )
    partes = [css]
    # linha de comando
    partes.append(f'<text x="22" y="52" class="k">$</text><text x="36" y="52" class="v">git log --since="1 ano" | contribuicoes</text>')
    mes_anterior = None
    rotulos: list[tuple[int, str]] = []
    for i, d in enumerate(dias):
        pos = deslocamento + i
        col, lin = divmod(pos, 7)
        x, y = X0 + col * passo, Y0 + lin * passo
        dia = date.fromisoformat(d["data"])
        if (lin == 0 or i == 0) and dia.month != mes_anterior:
            mes_anterior = dia.month
            if rotulos and col - rotulos[-1][0] < 3:  # mês que mal aparece no começo: fica só o seguinte
                rotulos.pop()
            if col < semanas - 2:
                rotulos.append((col, f'<text x="{x:.1f}" y="{Y0 - 7}" class="t">{MESES[dia.month - 1]}</text>'))
        atraso = 0.4 + (col + lin) * 0.022
        titulo = f"{d['n']} em {data_br(d['data'])}"
        partes.append(
            f'<rect class="c" style="animation-delay:{atraso:.2f}s" x="{x:.1f}" y="{y:.1f}" width="{CEL}" height="{CEL}" rx="2.6" '
            f'fill="{CORES[min(d["nivel"], 4)]}"><title>{titulo}</title></rect>'
        )
    partes.extend(r for _, r in rotulos)
    for lin, nome in ((1, "seg"), (3, "qua"), (5, "sex")):
        partes.append(f'<text x="22" y="{Y0 + lin * passo + CEL - 2:.1f}" class="t">{nome}</text>')
    fim = Y0 + 7 * passo + 14
    fim_anim = 0.4 + (semanas + 7) * 0.022 + 0.2
    # legenda menos -> mais
    lx = largura - 22 - 5 * (CEL + 3) - 40
    leg = [f'<text x="{lx - 44:.1f}" y="{fim:.1f}" class="t">menos</text>']
    for i, cor in enumerate(CORES):
        leg.append(f'<rect x="{lx + i * (CEL + 3):.1f}" y="{fim - CEL + 1:.1f}" width="{CEL}" height="{CEL}" rx="2.6" fill="{cor}"/>')
    leg.append(f'<text x="{lx + 5 * (CEL + 3) + 6:.1f}" y="{fim:.1f}" class="t">mais</text>')
    melhor = dados["melhor_dia"]
    estat = (
        f'<tspan class="k">{dados["total"]}</tspan> contribuições no último ano · '
        f'<tspan class="k">{dados["dias_ativos"]}</tspan> dias ativos · '
        f'maior sequência <tspan class="k">{dados["maior_sequencia"]}</tspan> dias · '
        f'melhor dia <tspan class="k">{melhor["n"]}</tspan> ({data_br(melhor["data"])})'
    )
    partes.append(f'<g class="s" style="animation-delay:{fim_anim:.2f}s">{"".join(leg)}'
                  f'<text x="22" y="{fim + 26:.1f}" class="v" font-size="12">{estat}</text></g>')
    altura = fim + 40
    return janela(largura, altura, "gabriel@github: ~/contribuicoes", "".join(partes))


if __name__ == "__main__":
    salvar(Path("assets/contribuicoes.svg"), svg(json.loads(ENTRADA.read_text(encoding="utf-8"))))
