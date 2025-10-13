import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# parâmetros
lista = ["Orgao", "dispesa_orca", "prog_orcam", "fornecedor", "fonte", "numero_empenho"]
UF = "AC"
ano = 2025

# cria as pastas
for i in lista:
    os.makedirs(f"./BASES/{UF}/{ano}/{i}", exist_ok=True)

for item in lista:
    print(f"\n=== Iniciando downloads para: {item} ===")
    download_dir = os.path.abspath(f"./BASES/{UF}/{ano}/{item}")

    # configurações do navegador
    options = Options()
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True,
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)
    wait = WebDriverWait(driver, 15)
    driver.get("https://transparencia.ac.gov.br/despesas")

    # seleciona o ano
    botao_ano = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ano"]')))
    select_ano = Select(botao_ano)
    select_ano.select_by_value(str(ano))
    time.sleep(1)

    # abre pesquisa avançada
    botao_pesquisa_avancada = wait.until(
        EC.element_to_be_clickable((By.XPATH, '/html/body/div[4]/div[2]/div[3]/div/div/div[1]/div[9]/button'))
    )
    botao_pesquisa_avancada.click()

    # seleciona o filtro
    botao_filtros = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="filtros"]')))
    select = Select(botao_filtros)
    select.select_by_value(item.lower())

    # espera carregar a tabela
    wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "tbody tr")))
    links = driver.find_elements(By.CSS_SELECTOR, "a.modal_despesas")

    for idx in range(len(links)):
        # recarrega os elementos a cada iteração
        links = driver.find_elements(By.CSS_SELECTOR, "a.modal_despesas")
        link = links[idx]
        descricao = link.get_attribute("data-descricao")
        print(f"Clicando em: {descricao}")

        # clica para abrir o modal
        link.click()

        # espera o modal abrir
        modal = wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, ".modal.show")))

        # clica no botão dentro do modal (download / detalhes)
        try:
            botao_detalhe = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="table_detalhamento"]/thead/tr[1]/th/div/div/a[2]'))
            )
            botao_detalhe.click()
            print("→ Botão de download clicado com sucesso.")
        except Exception as e:
            print(f"⚠️ Erro ao clicar no botão de download: {e}")

        time.sleep(3)  # aguarda o download começar

        # fecha o modal
        try:
            botao_fechar = wait.until(
                EC.element_to_be_clickable((By.XPATH, '//*[@id="modal-despesa"]/div/div/div[3]/button'))
            )
            botao_fechar.click()
            wait.until(EC.invisibility_of_element(modal))
            print("Modal fechado com sucesso.")
        except Exception as e:
            print(f"⚠️ Não foi possível fechar o modal: {e}")

        time.sleep(1)

    driver.quit()
