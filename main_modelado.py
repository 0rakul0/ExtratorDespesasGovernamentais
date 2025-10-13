import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import pandas as pd

# ======================================================
# Configura e abre o navegador
# ======================================================
def abrir_pagina(download_dir: str) -> tuple:
    """Abre o site de transparência configurando o diretório de download"""
    options = Options()
    prefs = {
        "download.default_directory": os.path.abspath(download_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(300)  # Aumenta tempo limite de carregamento

    wait = WebDriverWait(driver, 15)

    url = "https://transparencia.ac.gov.br/despesas"
    tentativas = 3

    for i in range(tentativas):
        try:
            print(f"🌐 Acessando página ({i+1}/{tentativas})...")
            driver.get(url)
            print("✅ Página carregada com sucesso.")
            return driver, wait

        except Exception as e:
            print(f"⚠️ Erro ao abrir a página (tentativa {i+1}): {e}")
            time.sleep(5)

    print("❌ Não foi possível abrir a página após várias tentativas.")
    driver.quit()
    raise RuntimeError("Falha ao abrir a página.")


# ======================================================
# Espera modal de processamento
# ======================================================
def esperar_processamento(driver, wait):
    try:
        wait.until(EC.invisibility_of_element_located((By.ID, "table_despesa_processing")))
    except:
        pass


# ======================================================
# Seleciona o ano e o filtro
# ======================================================
def selecionar_filtro(driver, wait, ano: int, filtro: str):
    """Seleciona o ano e o filtro desejado no site"""
    # seleciona ano
    time.sleep(1)
    botao_ano = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ano"]')))
    select_ano = Select(botao_ano)
    select_ano.select_by_value(str(ano))
    time.sleep(1)

    # abre pesquisa avançada
    botao_pesquisa_avancada = wait.until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/div[4]/div[2]/div[3]/div/div/div[1]/div[9]/button'))
    )
    botao_pesquisa_avancada.click()

    time.sleep(1)
    # seleciona filtro
    botao_filtros = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="filtros"]')))
    select = Select(botao_filtros)
    select.select_by_value(filtro.lower())

    esperar_processamento(driver, wait)

    # aguarda a tabela aparecer
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tbody tr")))
    print(f"Filtro '{filtro}' aplicado com sucesso.")

# ======================================================
# Aguarda o download e renomeia o arquivo
# ======================================================
def esperar_e_renomear_arquivo(download_dir, novo_nome, tentativas=5, intervalo=1):
    """
    Verifica se 'despesa.csv' existe e renomeia para o novo nome.
    Faz algumas tentativas rápidas antes de desistir.
    """
    caminho_temp = f"{str(download_dir).replace('\\','/')}/despesas.csv"
    for i in range(tentativas):
        time.sleep(intervalo)
        try:
            if os.path.exists(caminho_temp):
                novo_caminho = os.path.join(download_dir, novo_nome)
                os.rename(caminho_temp, novo_caminho)
                print(f"✅ Arquivo renomeado para {novo_nome}")
                return
        except Exception as e:
            print(f"⚠️ Erro ao renomear tentativa {i+1}: {e}")
    print(f"❌ Não foi possível renomear {novo_nome}")



def valida_arquivo(download_dir, nome_arquivo):
    caminho = os.path.join(download_dir, nome_arquivo)
    if not os.path.exists(caminho):
        return False
    else:
        return True


# ======================================================
# Avança para a próxima página
# ======================================================
def avancar_pagina(driver, wait):
    tentativas = 3
    for tentativa in range(tentativas):
        try:
            botao_proximo = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="table_despesa_next"]/a'))
            )
            # scroll para o centro da tela
            driver.execute_script("arguments[0].scrollIntoView({block:'center'});", botao_proximo)

            try:
                botao_proximo.click()
            except:
                driver.execute_script("arguments[0].click();", botao_proximo)

            # espera o modal de processamento sumir
            wait.until(EC.invisibility_of_element_located((By.ID, "table_despesa_processing")))
            time.sleep(1)
            return True

        except Exception as e:
            print(f"⚠️ Erro ao avançar (tentativa {tentativa + 1}/3): {e}")
            time.sleep(2)
    print("❌ Não foi possível avançar para a próxima página após várias tentativas.")
    return False




# ======================================================
# Percorre as linhas da tabela e baixa os arquivos
# ======================================================
def baixar_itens_tabela(driver, wait, download_dir, falhas):
    """Percorre as linhas da tabela, abre o modal e baixa os arquivos"""
    esperar_processamento(driver, wait)

    info = driver.find_element(By.ID, "table_despesa_info").text
    total_str = str(info.split("de")[-1].split("registros")[0].strip()).replace('.','')
    total = int(total_str)
    pagina = 10
    limite_loops = (total + pagina - 1) // pagina

    for i in range(limite_loops):
        print(f"➡️ Página {i+1}/{limite_loops}")
        time.sleep(2)
        esperar_processamento(driver, wait)

        links = driver.find_elements(By.CSS_SELECTOR, "a.modal_despesas")
        for idx in range(len(links)):
            sucesso = False
            tentativas_arquivo = 0

            while not sucesso and tentativas_arquivo <= 1:
                tentativas_arquivo += 1
                try:
                    time.sleep(0.2)
                    links = driver.find_elements(By.CSS_SELECTOR, "a.modal_despesas")
                    link = links[idx]

                    descricao = link.get_attribute("data-descricao") or "(sem descrição)"
                    descricao = descricao.replace("/", "-")
                    nome_arquivo = f"{descricao}.csv"

                    # se já existe e é válido, pula
                    if os.path.exists(os.path.join(download_dir, nome_arquivo)) and valida_arquivo(download_dir, nome_arquivo):
                        print(f"✅ Arquivo {nome_arquivo} já existe e é válido.")
                        sucesso = True
                        break

                    print(f"\n🔹 Tentativa {tentativas_arquivo}/2 - Clicando em: {descricao}")

                    # scroll e clique
                    driver.execute_script("arguments[0].scrollIntoView(true);", link)
                    try:
                        link.click()
                    except:
                        driver.execute_script("arguments[0].click();", link)

                    modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal.show")))
                    esperar_processamento(driver, wait)
                    botao_detalhe = wait.until(
                        EC.element_to_be_clickable((By.XPATH, '//*[@id="table_detalhamento"]/thead/tr[1]/th/div/div/a[2]'))
                    )
                    try:
                        botao_detalhe.click()
                    except:
                        driver.execute_script("arguments[0].click();", botao_detalhe)
                    time.sleep(1)

                    botao_fechar = wait.until(
                        EC.element_to_be_clickable((By.XPATH, '//*[@id="modal-despesa"]/div/div/div[3]/button'))
                    )
                    try:
                        botao_fechar.click()
                    except:
                        driver.execute_script("arguments[0].click();", botao_fechar)
                    wait.until(EC.invisibility_of_element(modal))

                    esperar_e_renomear_arquivo(download_dir, f"{descricao}.csv")

                    if valida_arquivo(download_dir, nome_arquivo):
                        print(f"✅ Download validado: {nome_arquivo}")
                        sucesso = True
                    else:
                        print(f"🔁 Arquivo inválido, tentando novamente...")
                        time.sleep(1)

                except StaleElementReferenceException:
                    print("♻️ Elemento ficou 'stale', rebuscando links...")
                    time.sleep(1)
                    continue
                except Exception as e:
                    print(f"❌ Erro inesperado na tentativa {tentativas_arquivo}: {e}")
                    time.sleep(.2)
                    continue

            if not sucesso:
                print(f"❌ Falha ao baixar {descricao} após 2 tentativas.")
                falhas.append(descricao)  # registra a falha

        if i < limite_loops - 1:
            avancar_pagina(driver, wait)
            esperar_processamento(driver, wait)

# ======================================================
# Função principal
# ======================================================
def executar_downloads():
    lista = ["fonte", "despesa", "programa","orgao", "fornecedor", "n_empenho"]
    UF = "AC"
    ano = 2025

    for item in lista:
        pasta = f"./BASES/{UF}/{ano}/{item}"
        os.makedirs(pasta, exist_ok=True)
        print(f"\n=== Iniciando downloads para: {item} ===")

        driver, wait = abrir_pagina(pasta)
        falhas = []

        try:
            selecionar_filtro(driver, wait, ano, item)
            baixar_itens_tabela(driver, wait, pasta, falhas)
        except Exception as e:
            print(f"❌ Erro no filtro '{item}': {e}")
        finally:
            print(f"🔚 Finalizado filtro: {item}")
            driver.quit()

        # ==================================================
        # Salva falhas específicas desse item
        # ==================================================
        if falhas:
            caminho_falhas_item = os.path.join(pasta, f"falhas_{item}_{UF}_{ano}.txt")
            with open(caminho_falhas_item, "w", encoding="utf-8") as f:
                f.write(f"--{item.upper()}--\n")
                for f_item in falhas:
                    f.write(f"{f_item}\n")
            print(f"⚠️ Falhas para '{item}' salvas em: {caminho_falhas_item}")
        else:
            print(f"✅ Nenhuma falha registrada para '{item}'.")



# ======================================================
# Execução
# ======================================================
if __name__ == "__main__":
    executar_downloads()
