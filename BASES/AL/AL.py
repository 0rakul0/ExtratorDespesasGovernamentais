import os
import requests
import zipfile

for ano in range(2000, 2026):
    url = f"https://transparencia.al.gov.br/media/arquivo/convenio-{ano}.zip"
    pasta_destino = fr".\convenios\{ano}"
    pasta_extracao = os.path.join(pasta_destino, "extraidos")

    os.makedirs(pasta_destino, exist_ok=True)
    os.makedirs(pasta_extracao, exist_ok=True)

    arquivo_zip = os.path.join(pasta_destino, f"convenio-{ano}.zip")

    print(f"Baixando {url} ...")

    try:
        resposta = requests.get(url, stream=True, timeout=30)
        if resposta.status_code == 200:
            # Salva o arquivo ZIP
            with open(arquivo_zip, "wb") as f:
                for chunk in resposta.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            print(f"✅ Download concluído: {arquivo_zip}")

            # Extrai o conteúdo diretamente em "extraidos/"
            with zipfile.ZipFile(arquivo_zip, 'r') as zip_ref:
                zip_ref.extractall(pasta_extracao)
            print(f"📂 Arquivo extraído em: {pasta_extracao}")

            # (Opcional) Apaga o .zip após a extração
            # os.remove(arquivo_zip)
            # print(f"🗑️ ZIP removido: {arquivo_zip}")

        else:
            print(f"❌ Não encontrado ({resposta.status_code}): {url}")

    except Exception as e:
        print(f"⚠️ Erro ao processar {url}: {e}")
