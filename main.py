import json
import datetime
import os

# --- 1. CONFIGURAÇÕES E DADOS GLOBAIS (DICIONÁRIO) ---

# DICIONÁRIO principal que armazena o estado dos circuitos.
DADOS_CIRCUITOS = {}

# MELHORIA: Variável global para armazenar o timestamp dos dados carregados/salvos
GLOBAL_LAST_SAVE_TIMESTAMP = "N/A (dados ainda não salvos)"

# DICIONÁRIO de configuração para os limites de segurança.
FAIXAS_SEGURAS = {
    "tensao": {"min": 210, "max": 230},
    "corrente": {"min": 0, "max": 50},
    "fator_potencia": {"min": 0.92, "max": 1.0},
    "frequencia": {"min": 59.5, "max": 60.5}
}

# DICIONÁRIO para mapear as abreviações da 'linha' para chaves internas.
MAPA_PARAMETROS = {
    "V": "tensao",
    "I": "corrente",
    "fp": "fator_potencia",
    "f": "frequencia"
}

# ARQUIVO para persistência de dados
ARQUIVO_DADOS = "circuitos_data.json"


# --- 2. FUNÇÕES DO MENU ---

def _processar_linha_medicao(linha):
    """Função interna auxiliar para processar uma única string de medição."""
    try:
        partes = [p.strip() for p in linha.split(';')]
        nome_circuito = partes[0]
        if not nome_circuito:
            print("Erro: Nome do circuito não pode ser vazio.")
            return

        medicoes = {}
        for item in partes[1:]:
            chave_raw, valor_str = item.split('=')
            chave_interna = MAPA_PARAMETROS.get(chave_raw)
            if chave_interna:
                medicoes[chave_interna] = float(valor_str)
            else:
                print(f"Aviso: Parâmetro desconhecido '{chave_raw}' ignorado.")

        DADOS_CIRCUITOS[nome_circuito] = medicoes
        print(f"Sucesso: Medição registrada para '{nome_circuito}'.")

    except (ValueError, IndexError, TypeError):
        print(f"Erro: Formato de linha inválido. ({linha})")
    except Exception as e:
        print(f"Erro inesperado ao registrar: {e}")


def registrar_medicao():
    """(Menu 1) Permite registrar múltiplas medições em loop."""
    print("\n--- Modo de Registro Múltiplo ---")
    print("Formato: Nome; V=...; I=...; fp=...; f=...")
    print("Digite 'fim' ou 'sair' para voltar ao menu principal.")

    while True:
        linha = input("Nova Medição: ").strip()
        if linha.lower() in ('fim', 'sair'):
            print("Saindo do modo de registro.")
            break
        if linha:
            _processar_linha_medicao(linha)


def salvar_circuitos():
    """(Menu 2) Salva os dados com um timestamp e atualiza a var global."""
    global GLOBAL_LAST_SAVE_TIMESTAMP  # Informa que vamos alterar a var global
    print("\nSalvando circuitos...")

    timestamp = datetime.datetime.now().isoformat()

    dados_para_salvar = {
        "ultimo_salvamento": timestamp,
        "circuitos": DADOS_CIRCUITOS
    }

    try:
        with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
            json.dump(dados_para_salvar, f, indent=4, ensure_ascii=False)

        print(f"Sucesso: Dados salvos em '{ARQUIVO_DADOS}'.")
        print(f"Horário do salvamento: {timestamp}")

        # MELHORIA: Atualiza a variável global com o novo timestamp
        GLOBAL_LAST_SAVE_TIMESTAMP = timestamp

    except IOError as e:
        print(f"Erro de E/S ao salvar arquivo: {e}")
    except Exception as e:
        print(f"Erro inesperado ao salvar: {e}")


def gerar_relatorio_nao_conforme(last_save_time):
    """
    (Menu 3 - MELHORADO) Gera relatório com data de geração E data dos dados.
    """
    print("\nGerando relatório de não conformidade...")

    lista_de_alertas = []
    for nome_circuito, medicoes in DADOS_CIRCUITOS.items():
        for parametro, valor_medido in medicoes.items():
            faixa_segura = FAIXAS_SEGURAS.get(parametro)
            if not faixa_segura: continue

            status = ""
            if valor_medido < faixa_segura["min"]:
                status = f"ABAIXO do limite (Min: {faixa_segura['min']})"
            elif valor_medido > faixa_segura["max"]:
                status = f"ACIMA do limite (Max: {faixa_segura['max']})"

            if status:
                lista_de_alertas.append([nome_circuito, parametro, valor_medido, status])

    nome_arquivo = "relatorio_nao_conformidade.txt"
    timestamp_geracao = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            f.write(f"--- RELATÓRIO DE NÃO CONFORMIDADE ---\n")
            # MELHORIA: Adiciona as duas datas
            f.write(f"Relatório gerado em: {timestamp_geracao}\n")
            f.write(f"Dados salvos em:     {last_save_time}\n")
            f.write("=" * 45 + "\n\n")

            if not lista_de_alertas:
                f.write("Status: OK. Nenhuma não conformidade encontrada.\n")
                print("Status: OK. Nenhuma não conformidade encontrada.")
            else:
                print(f"Encontradas {len(lista_de_alertas)} não conformidades.")
                for nome, param, valor, status_msg in lista_de_alertas:
                    f.write(f"[ALERTA] Circuito: {nome}\n")
                    f.write(f"  - Parâmetro: {param}\n")
                    f.write(f"  - Valor Medido: {valor}\n")
                    f.write(f"  - Status: {status_msg}\n\n")

            f.write("=" * 45 + "\nFim do Relatório.\n")

        print(f"Sucesso: Relatório salvo em '{nome_arquivo}'.")

    except IOError as e:
        print(f"Erro ao salvar relatório: {e}")


def resumo_eletrico(last_save_time):
    """
    (Menu 4 - MELHORADO) Gera resumo com data de geração E data dos dados.
    """
    print("\nGerando resumo elétrico...")
    nome_arquivo = "resumo_eletrico.txt"
    timestamp_geracao = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            f.write(f"--- RESUMO ELÉTRICO DA INSTALAÇÃO ---\n")
            # MELHORIA: Adiciona as duas datas
            f.write(f"Resumo gerado em: {timestamp_geracao}\n")
            f.write(f"Dados salvos em:  {last_save_time}\n")
            f.write("=" * 45 + "\n\n")

            if not DADOS_CIRCUITOS:
                f.write("Nenhum circuito registrado no sistema.\n")
                print("Nenhum circuito registrado.")
                return

            for nome_circuito, medicoes in DADOS_CIRCUITOS.items():
                f.write(f"[Circuito: {nome_circuito}]\n")
                f.write(f"  - Tensão: {medicoes.get('tensao', 'N/A')} V\n")
                f.write(f"  - Corrente: {medicoes.get('corrente', 'N/A')} A\n")
                f.write(f"  - Fator Potência: {medicoes.get('fator_potencia', 'N/A')}\n")
                f.write(f"  - Frequência: {medicoes.get('frequencia', 'N/A')} Hz\n\n")

            f.write("=" * 45 + "\nFim do Resumo.\n")

        print(f"Sucesso: Resumo salvo em '{nome_arquivo}'.")

    except IOError as e:
        print(f"Erro ao salvar resumo: {e}")


def modulo_extra():
    """(Menu 5) Roda um módulo extra (Cálculo de Potência Aparente Total)"""
    print("\n--- Módulo Extra: Cálculo de Potência Aparente (S = V * I) ---")
    if not DADOS_CIRCUITOS:
        print("Nenhum circuito registrado para calcular.")
        return

    potencia_total_va = 0.0
    for nome, medicoes in DADOS_CIRCUITOS.items():
        try:
            potencia_aparente = medicoes['tensao'] * medicoes['corrente']
            potencia_total_va += potencia_aparente
            print(f"  - Circuito '{nome}': {potencia_aparente:.2f} VA")
        except KeyError:
            print(f"  - Circuito '{nome}': Dados incompletos (V ou I faltando).")

    print("-" * 30)
    print(f"Potência Aparente Total: {potencia_total_va:.2f} VA ({potencia_total_va / 1000:.2f} kVA)")


# --- 3. FUNÇÕES AUXILIARES (CARREGAR DADOS) ---

def carregar_dados():
    """Carrega os dados e atualiza o timestamp global."""
    global DADOS_CIRCUITOS, GLOBAL_LAST_SAVE_TIMESTAMP  # Altera ambas globais
    try:
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            dados_carregados = json.load(f)

        if isinstance(dados_carregados, dict) and "circuitos" in dados_carregados:
            # Novo formato
            DADOS_CIRCUITOS = dados_carregados.get("circuitos", {})
            # MELHORIA: Atualiza a var global ao carregar
            GLOBAL_LAST_SAVE_TIMESTAMP = dados_carregados.get("ultimo_salvamento", "N/A")
            print(f"Dados carregados. Último salvamento: {GLOBAL_LAST_SAVE_TIMESTAMP}")
        else:
            # Formato antigo
            print("Arquivo de dados em formato antigo detectado. Carregando...")
            DADOS_CIRCUITOS = dados_carregados
            GLOBAL_LAST_SAVE_TIMESTAMP = "N/A (formato antigo, salve para atualizar)"

        print(f"Total de {len(DADOS_CIRCUITOS)} circuitos carregados.")

    except FileNotFoundError:
        print(f"Arquivo '{ARQUIVO_DADOS}' não encontrado. Iniciando com dados vazios.")
        DADOS_CIRCUITOS = {}
        GLOBAL_LAST_SAVE_TIMESTAMP = "N/A (novo arquivo)"
    except json.JSONDecodeError:
        print(f"Erro ao decodificar JSON em '{ARQUIVO_DADOS}'. Iniciando com dados vazios.")
        DADOS_CIRCUITOS = {}
        GLOBAL_LAST_SAVE_TIMESTAMP = "N/A (arquivo corrompido)"


# --- 4. EXECUÇÃO PRINCIPAL (SEU MENU, AGORA EM LOOP) ---

def main():
    carregar_dados()

    while True:
        print("\n" + "=" * 35)
        print("   Sistema de Monitoramento Elétrico")
        print("=" * 35)
        print("1 - Registrar medição (Modo Múltiplo)")
        print("2 - Salvar circuitos (com Timestamp)")
        print("3 - Gerar relatório de não conformidade")
        print("4 - Resumo elétrico")
        print("5 - Rodar módulo extra")
        print("S - Sair e Salvar")
        print("-" * 35)

        opc = input("Escolha: ").strip().lower()

        if opc == "1":
            registrar_medicao()
        elif opc == "2":
            salvar_circuitos()
        elif opc == "3":
            # MELHORIA: Passa o timestamp global para a função
            gerar_relatorio_nao_conforme(GLOBAL_LAST_SAVE_TIMESTAMP)
        elif opc == "4":
            # MELHORIA: Passa o timestamp global para a função
            resumo_eletrico(GLOBAL_LAST_SAVE_TIMESTAMP)
        elif opc == "5":
            modulo_extra()
        elif opc == "s":
            salvar_circuitos()
            print("Sistema finalizado.")
            break
        else:
            print("Opção inválida. Tente novamente.")

        input("\nPressione Enter para continuar...")
        os.system('cls' if os.name == 'nt' else 'clear')


if __name__ == "__main__":
    main()