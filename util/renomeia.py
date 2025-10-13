import os

pasta = r"D:\github\sistema_temporal\BASES\AC\2025\despesa"

for nome in os.listdir(pasta):
    if nome.endswith(".csv.csv"):
        novo_nome = nome[:-4]
        caminho_antigo = os.path.join(pasta, nome)
        caminho_novo = os.path.join(pasta, novo_nome)
        os.rename(caminho_antigo, caminho_novo)
        print(f"✅ Renomeado: {nome} → {novo_nome}")
