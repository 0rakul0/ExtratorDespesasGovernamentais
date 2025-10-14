import os
import re
import pandas as pd
from glob import glob


def limpar_texto(texto):
    """Remove quebras, múltiplos espaços e caracteres indesejados."""
    if not isinstance(texto, str):
        return texto
    texto = texto.replace('\r', ' ').replace('\n', ' ').replace('\t', ' ')
    texto = texto.replace('""', '"')
    texto = re.sub(r' +', ' ', texto)  # remove múltiplos espaços
    return texto.strip()


def concatenar_csv(pasta: str) -> str:
    """
    Lê todos os arquivos CSV em uma pasta, corrige cabeçalhos duplicados e inconsistências,
    e salva um único arquivo concatenado.

    Retorna o caminho do arquivo final salvo.
    """
    nome_csv = os.path.basename(pasta)
    arquivos_csv = glob(os.path.join(pasta, "*.csv"))

    if not arquivos_csv:
        print(f"⚠️ Nenhum arquivo CSV encontrado em {pasta}.")
        return ""

    todos_dfs = []
    colunas = None

    for arquivo in arquivos_csv:
        with open(arquivo, "r", encoding="utf-8-sig") as f:
            primeira_linha = f.readline().strip()
            primeira_linha = re.sub(r'\s*;\s*', ';', primeira_linha.replace('\ufeff', ''))
            headers = [h.strip() for h in primeira_linha.split(';')]

            if colunas is None:
                colunas = headers
            elif headers != colunas:
                print(f"⚠️ Cabeçalho diferente detectado em {os.path.basename(arquivo)} — será ajustado.")

            conteudo = f.read()

        conteudo = conteudo.replace('\r\n', '\n').replace('\r', '\n')
        linhas = conteudo.split('\n')
        linhas_corrigidas = []

        for linha in linhas:
            linha = linha.strip()
            if not linha:
                continue

            # Ignora cabeçalhos duplicados
            if any(linha.startswith(prefixo) for prefixo in ["entidade;", "﻿entidade;"]):
                continue

            campos = re.findall(r'"((?:[^"]|"")*?)"', linha)
            if len(campos) != len(colunas):
                campos = re.split(r';(?=(?:[^"]*"[^"]*")*[^"]*$)', linha)
                campos = [c.strip('"').strip() for c in campos]

            campos = [limpar_texto(c) for c in campos]

            if len(campos) < len(colunas):
                campos += [''] * (len(colunas) - len(campos))
            elif len(campos) > len(colunas):
                campos[len(colunas) - 1] = ' '.join(campos[len(colunas) - 1:])
                campos = campos[:len(colunas)]

            linhas_corrigidas.append(campos)

        if linhas_corrigidas:
            df = pd.DataFrame(linhas_corrigidas, columns=colunas)
            todos_dfs.append(df)

    df_final = pd.concat(todos_dfs, ignore_index=True)

    # Limpa colunas de texto
    colunas_texto = df_final.select_dtypes(include=['object']).columns
    for col in colunas_texto:
        df_final[col] = df_final[col].map(lambda x: " ".join(str(x).split()) if isinstance(x, str) else x)

    # Salva resultado
    arquivo_saida = os.path.join(pasta, f"{nome_csv}_concatenado.csv")
    df_final.to_csv(arquivo_saida, sep=";", index=False, encoding="utf-8-sig")

    print(f"\n💾 Arquivo final salvo em: {arquivo_saida}")
    return arquivo_saida
