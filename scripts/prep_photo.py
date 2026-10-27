"""Prepara a foto para virar ASCII: tira o fundo, aumenta o contraste local e põe sobre branco.

Uso: python scripts/prep_photo.py foto.jpg [destino.png] [x0,y0,x1,y1]   (gera source-prepped.png, que não vai para o repositório)
"""
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import new_session, remove


def preparar(origem: str, destino: str = "source-prepped.png", recorte: str = "") -> None:
    """recorte opcional "x0,y0,x1,y1" em frações da foto, para fechar no rosto e nos ombros."""
    foto = Image.open(origem).convert("RGB")
    if recorte:
        x0, y0, x1, y1 = (float(v) for v in recorte.split(","))
        w, h = foto.size
        foto = foto.crop((round(x0 * w), round(y0 * h), round(x1 * w), round(y1 * h)))
    recorte = remove(foto, session=new_session("u2net_human_seg"))  # RGBA, fundo transparente
    rgba = np.array(recorte)
    cinza = cv2.cvtColor(rgba[:, :, :3], cv2.COLOR_RGB2GRAY)
    # CLAHE: dá luz e sombra a um rosto com iluminação chapada
    cinza = cv2.createCLAHE(clipLimit=2.4, tileGridSize=(6, 6)).apply(cinza)
    alfa = rgba[:, :, 3]
    # fica só a maior região recortada (a pessoa); some com mãos e cabeças de quem estava em volta
    n, rotulos, stats, _ = cv2.connectedComponentsWithStats((alfa > 127).astype(np.uint8))
    if n > 2:
        maior = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        alfa = np.where(rotulos == maior, alfa, 0).astype(np.uint8)
    # cinza + transparência: o fundo vira espaço no ASCII
    Image.fromarray(np.dstack([cinza, alfa]), "LA").save(destino)
    print("gerado:", destino)


if __name__ == "__main__":
    preparar(*sys.argv[1:])
