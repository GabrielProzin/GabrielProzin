"""Lê o calendário público de contribuições do GitHub (sem token) e salva em data/contributions.json.

Usa a mesma página que o próprio perfil carrega: https://github.com/users/<usuario>/contributions
"""
import json
import re
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

USUARIO = "GabrielProzin"
SAIDA = Path("data/contributions.json")


def ler_html(html: str) -> list[dict]:
    sopa = BeautifulSoup(html, "html.parser")
    dicas = {}
    for t in sopa.find_all("tool-tip"):
        m = re.match(r"\s*(\d[\d,]*|No) contributions?", t.get_text())
        if m and t.get("for"):
            dicas[t["for"]] = 0 if m.group(1) == "No" else int(m.group(1).replace(",", ""))
    dias = []
    for td in sopa.select("td.ContributionCalendar-day[data-date]"):
        nivel = int(td.get("data-level", 0))
        n = dicas.get(td.get("id"))
        dias.append({"data": td["data-date"], "nivel": nivel, "n": n if n is not None else nivel})
    if not dias:
        raise SystemExit("Nenhum dia encontrado: o formato da página do GitHub pode ter mudado.")
    return sorted(dias, key=lambda d: d["data"])


def resumo(dias: list[dict]) -> dict:
    total = sum(d["n"] for d in dias)
    maior = atual = seq = 0
    for d in dias:
        seq = seq + 1 if d["n"] > 0 else 0
        maior = max(maior, seq)
    # sequência atual: hoje ainda pode estar zerado sem quebrar a sequência
    for d in reversed(dias):
        if d["n"] > 0:
            atual += 1
        elif d is dias[-1]:
            continue
        else:
            break
    melhor = max(dias, key=lambda d: d["n"])
    return {"total": total, "maior_sequencia": maior, "sequencia_atual": atual,
            "melhor_dia": {"data": melhor["data"], "n": melhor["n"]},
            "dias_ativos": sum(1 for d in dias if d["n"] > 0)}


def main() -> None:
    usuario = sys.argv[1] if len(sys.argv) > 1 else USUARIO
    r = requests.get(f"https://github.com/users/{usuario}/contributions", timeout=30,
                     headers={"User-Agent": f"{usuario}-profile-readme"})
    r.raise_for_status()
    dias = ler_html(r.text)
    dados = {"usuario": usuario, "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
             **resumo(dias), "dias": dias}
    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    SAIDA.write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(dias)} dias, {dados['total']} contribuições, até {dias[-1]['data']} (hoje {date.today()})")


if __name__ == "__main__":
    main()
