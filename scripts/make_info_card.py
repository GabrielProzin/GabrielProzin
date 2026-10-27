"""Cartão no estilo neofetch, ao lado do retrato. Gera assets/cartao.svg.

O conteúdo fica aqui: é a parte da história que o gráfico de contribuições não conta.
STATIC=1 gera o cartão já pronto, sem animação (bom para conferir).
"""
import os
from pathlib import Path

from terminal import MONO, janela, salvar

LINHAS = [
    ("Função", "Cientista de Dados"),
    ("Local", "Goiânia, GO · Brasil"),
    ("Formação", "ADS · pós em Ciência de Dados"),
    ("Pipelines", "Python + Airflow → BigQuery"),
    ("Escala", "18 clientes no mesmo pipeline"),
    ("BI", "20+ dashboards de KPIs no Power BI"),
    ("Stack", "Python · SQL · Airflow · BigQuery"),
    ("Também", "Pandas · Scikit-learn · PostgreSQL"),
    ("Projeto", "busca_vagas: ETL + NLP, 5x por dia"),
    ("Portfólio", "gmendes.vercel.app"),
]
PALETA = ["#0e4441", "#11706a", "#1fa196", "#4fd8cb", "#febc2e", "#ff5f57", "#8b949e", "#e6edf3"]
LARGURA, ALTURA = 500, 445
ESTATICO = os.environ.get("STATIC") == "1"


def svg() -> str:
    css = (
        "<style>"
        f".v{{font-family:{MONO};font-size:12.5px;fill:#e6edf3}}"
        f".k{{font-family:{MONO};font-size:12.5px;fill:#5fd1c7;font-weight:600}}"
        f".t{{font-family:{MONO};font-size:12.5px;fill:#8b949e}}"
        + ("" if ESTATICO else
           ".l{opacity:0;transform:translateX(-8px);animation:entra .45s cubic-bezier(.2,.8,.2,1) forwards}"
           "@keyframes entra{to{opacity:1;transform:none}}"
           ".cur{animation:pisca 1s steps(1) infinite}@keyframes pisca{50%{opacity:0}}")
        + "</style>"
    )
    p = [css]
    atraso = 0.5

    def linha(conteudo: str) -> str:
        nonlocal atraso
        g = f'<g class="l" style="animation-delay:{atraso:.2f}s">{conteudo}</g>'
        atraso += 0.13
        return g

    x, y = 24, 60
    p.append(linha(f'<text x="{x}" y="{y}" class="k">$</text><text x="{x + 15}" y="{y}" class="v">neofetch</text>'))
    y += 30
    p.append(linha(f'<text x="{x}" y="{y}" class="k" font-size="14">gabriel<tspan class="t" font-size="14">@</tspan>github</text>'))
    y += 12
    p.append(linha(f'<line x1="{x}" y1="{y}" x2="{x + 121}" y2="{y}" stroke="#30363d" stroke-width="1.5"/>'))
    y += 24
    for chave, valor in LINHAS:
        val = valor.replace("&", "&amp;")
        p.append(linha(f'<text x="{x}" y="{y}" class="k">{chave}</text><text x="{x + 98}" y="{y}" class="v">{val}</text>'))
        y += 24
    y += 6
    blocos = "".join(f'<rect x="{x + i * 26}" y="{y}" width="22" height="14" rx="3" fill="{c}"/>' for i, c in enumerate(PALETA))
    p.append(linha(blocos))
    y += 40
    p.append(linha(f'<text x="{x}" y="{y}" class="k">$</text><rect class="cur" x="{x + 15}" y="{y - 11}" width="8" height="14" fill="#5fd1c7"/>'))
    return janela(LARGURA, ALTURA, "gabriel@github: ~", "".join(p))


if __name__ == "__main__":
    salvar(Path("assets/cartao.svg"), svg())
