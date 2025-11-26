import datetime
import json
import os

# --- 1. CONFIGURAÇÕES E DADOS GLOBAIS ---

# Dicionário principal que armazena o estado dos circuitos.
DADOS_CIRCUITOS = {}

# Timestamp do último salvamento/carregamento.
GLOBAL_LAST_SAVE_TIMESTAMP = "N/A (dados ainda não salvos)"

# Limites de operação segura por parâmetro.
FAIXAS_SEGURAS = {
    "tensao": {"min": 210, "max": 230},
    "corrente": {"min": 0, "max": 50},
    "fator_potencia": {"min": 0.92, "max": 1.0},
    "frequencia": {"min": 59.5, "max": 60.5},
    "thd": {"min": 0, "max": 8.0}  # Limite de 8% para THD
}

# Mapa de abreviações -> chaves internas
MAPA_PARAMETROS = {
    "V": "tensao",
    "I": "corrente",
    "FP": "fator_potencia",
    "F": "frequencia",
    "THD": "thd"
}

# Arquivo de persistência
ARQUIVO_DADOS = "circuitos_data.json"


# --- 2. FUNÇÕES AUXILIARES ---

def _verificar_e_registrar_thd(nome_circuito, medicoes):
    """Verifica se o THD > 8% e grava no relatório de harmônicas."""
    if 'thd' in medicoes:
        valor_thd = medicoes['thd']
        if valor_thd > FAIXAS_SEGURAS["thd"]["max"]:
            print(f"  [ALERTA] {nome_circuito}: THD de {valor_thd}% excede limite de 8%!")
            nome_arquivo_thd = "relatorio_harmonicas.txt"
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try:
                with open(nome_arquivo_thd, "a", encoding="utf-8") as f:
                    f.write(f"[{timestamp}] ALERTA CRÍTICO - HARMÔNICAS\n")
                    f.write(f"  Circuito: {nome_circuito}\n")
                    f.write(f"  THD Medido: {valor_thd}%\n")
                    f.write(f"  Dados Completos: {medicoes}\n")
                    f.write("-" * 40 + "\n")
                return True
            except IOError as e:
                print(f"  Erro ao gravar relatório: {e}")
        else:
            print(f"  [OK] {nome_circuito}: THD {valor_thd}% (Normal)")
    return False


def _processar_linha_medicao(linha, salvar_no_global=True):
    """
    Lê uma linha no formato:
      Nome; V=220; I=10; fp=0.95; f=60; THD=9.5
    Aceita ordem livre e vírgula decimal.
    """
    try:
        partes = [p.strip() for p in linha.split(';')]
        nome_circuito = partes[0]
        if not nome_circuito:
            print("Erro: Nome do circuito não pode ser vazio.")
            return None, None

        medicoes = {}
        for item in partes[1:]:
            if '=' not in item:
                print(f"  Aviso: item sem '=' ignorado: '{item}'")
                continue
            chave_raw, valor_str = item.split('=', 1)
            chave_raw = chave_raw.strip().upper()
            valor_str = valor_str.strip().replace(',', '.')
            chave_interna = MAPA_PARAMETROS.get(chave_raw)
            if not chave_interna:
                print(f"  Aviso: Chave desconhecida '{chave_raw}' (use V, I, FP, F, THD)")
                continue
            try:
                medicoes[chave_interna] = float(valor_str)
            except ValueError:
                print(f"  Aviso: Valor inválido em '{item}' (ex.: 220 ou 10.5)")

        if salvar_no_global and medicoes:
            if nome_circuito not in DADOS_CIRCUITOS:
                DADOS_CIRCUITOS[nome_circuito] = {}
            DADOS_CIRCUITOS[nome_circuito].update(medicoes)
            print(f"  Sucesso: Dados atualizados para '{nome_circuito}'.")

        return nome_circuito, medicoes
    except Exception as e:
        print(f"  Erro ao processar linha: {e}")
        return None, None


# --- 3. FUNÇÕES DE MENU ---

def registrar_medicao():
    """Permite registrar múltiplas medições em loop."""
    print("\n--- Modo de Registro Múltiplo ---")
    print("Formato: Nome; V=220; I=10; fp=0.95; f=60; THD=9.5")
    print("Digite 'fim' ou 'sair' para voltar ao menu principal.")
    while True:
        linha = input("Nova Medição: ").strip()
        if linha.lower() in ('fim', 'sair'):
            print("Saindo do modo de registro.")
            break
        if linha:
            _processar_linha_medicao(linha, salvar_no_global=True)


def salvar_circuitos():
    """Salva os dados com timestamp e atualiza a variável global."""
    global GLOBAL_LAST_SAVE_TIMESTAMP
    print("\nSalvando circuitos...")
    timestamp = datetime.datetime.now().isoformat()
    dados_para_salvar = {
        "ultimo_salvamento": timestamp,
        "circuitos": DADOS_CIRCUITOS
    }
    try:
        with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
            json.dump(dados_para_salvar, f, indent=4, ensure_ascii=False)
        GLOBAL_LAST_SAVE_TIMESTAMP = timestamp
        print(f"Sucesso: Dados salvos em '{ARQUIVO_DADOS}'.")
        print(f"Horário do salvamento: {timestamp}")
    except IOError as e:
        print(f"Erro de E/S ao salvar arquivo: {e}")
    except Exception as e:
        print(f"Erro inesperado ao salvar: {e}")


def gerar_relatorio_nao_conforme(last_save_time):
    """Gera relatório com medições fora das faixas seguras."""
    print("\nGerando relatório de não conformidade...")
    lista_de_alertas = []

    for nome_circuito, medicoes in DADOS_CIRCUITOS.items():
        for parametro, valor_medido in medicoes.items():
            faixa = FAIXAS_SEGURAS.get(parametro)
            if not faixa:
                continue
            status = ""
            if valor_medido < faixa["min"]:
                status = f"ABAIXO do limite (Min: {faixa['min']})"
            elif valor_medido > faixa["max"]:
                status = f"ACIMA do limite (Max: {faixa['max']})"
            if status:
                lista_de_alertas.append([nome_circuito, parametro, valor_medido, status])

    nome_arquivo = "relatorio_nao_conformidade.txt"
    timestamp_geracao = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            f.write("--- RELATÓRIO DE NÃO CONFORMIDADE ---\n")
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
    """Gera um resumo de todos os circuitos e suas medições."""
    print("\nGerando resumo elétrico...")
    nome_arquivo = "resumo_eletrico.txt"
    timestamp_geracao = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        with open(nome_arquivo, "w", encoding="utf-8") as f:
            f.write("--- RESUMO ELÉTRICO DA INSTALAÇÃO ---\n")
            f.write(f"Resumo gerado em: {timestamp_geracao}\n")
            f.write(f"Dados salvos em:  {last_save_time}\n")
            f.write("=" * 45 + "\n\n")

            if not DADOS_CIRCUITOS:
                f.write("Nenhum circuito registrado no sistema.\n")
                print("Nenhum circuito registrado.")
            else:
                for nome_circuito, medicoes in DADOS_CIRCUITOS.items():
                    f.write(f"[Circuito: {nome_circuito}]\n")
                    f.write(f"  - Tensão: {medicoes.get('tensao', 'N/A')} V\n")
                    f.write(f"  - Corrente: {medicoes.get('corrente', 'N/A')} A\n")
                    f.write(f"  - Fator Potência: {medicoes.get('fator_potencia', 'N/A')}\n")
                    f.write(f"  - Frequência: {medicoes.get('frequencia', 'N/A')} Hz\n")
                    f.write(f"  - THD: {medicoes.get('thd', 'N/A')} %\n\n")

            f.write("=" * 45 + "\nFim do Resumo.\n")
        print(f"Sucesso: Resumo salvo em '{nome_arquivo}'.")
    except IOError as e:
        print(f"Erro ao salvar resumo: {e}")


def analise_harmonicas():
    """
    Verifica THD nos dados existentes e permite inserir novas medições
    para validar THD imediatamente.
    """
    print("\n" + "=" * 50)
    print("          MÓDULO DE ANÁLISE DE HARMÔNICAS")
    print("=" * 50)

    print(">> 1. Verificando circuitos já carregados...")
    count = 0
    if DADOS_CIRCUITOS:
        for nome, medicoes in DADOS_CIRCUITOS.items():
            if 'thd' in medicoes:
                if _verificar_e_registrar_thd(nome, medicoes):
                    count += 1
        if count == 0:
            print("   Nenhum THD crítico encontrado nos dados atuais.")
    else:
        print("   (Memória vazia)")

    print("-" * 50)
    print(">> 2. Inserir/Atualizar medição (Formato Completo)")
    print("   Ex: Circuito 1; V=220; I=10; fp=0.92; f=60; THD=9.5")
    print("   (A ordem não importa. Pressione Enter vazio para sair)")

    while True:
        linha = input("Nova Medição: ").strip()
        if not linha:
            break
        nome, medicoes = _processar_linha_medicao(linha, salvar_no_global=True)
        if nome and medicoes:
            _verificar_e_registrar_thd(nome, medicoes)


def modulo_extra():
    """Cálculo da potência aparente total (S = V * I) de todos os circuitos."""
    print("\n--- Módulo Extra: Potência Aparente (S = V * I) ---")
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


# --- 4. CARREGAMENTO DE DADOS ---

def carregar_dados():
    """Carrega os dados do arquivo e atualiza o timestamp global."""
    global DADOS_CIRCUITOS, GLOBAL_LAST_SAVE_TIMESTAMP
    try:
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            dados_carregados = json.load(f)

        if isinstance(dados_carregados, dict) and "circuitos" in dados_carregados:
            DADOS_CIRCUITOS = dados_carregados.get("circuitos", {})
            GLOBAL_LAST_SAVE_TIMESTAMP = dados_carregados.get("ultimo_salvamento", "N/A")
            print(f"Dados carregados. Último salvamento: {GLOBAL_LAST_SAVE_TIMESTAMP}")
        else:
            # Suporte a formato antigo (apenas o dicionário de circuitos)
            DADOS_CIRCUITOS = dados_carregados if isinstance(dados_carregados, dict) else {}
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
    except Exception as e:
        print(f"Erro inesperado ao carregar dados: {e}")
        DADOS_CIRCUITOS = {}
        GLOBAL_LAST_SAVE_TIMESTAMP = "N/A (erro ao carregar)"


# --- 5. EXECUÇÃO PRINCIPAL ---

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
        print("5 - Análise de Harmônicas (THD)")
        print("6 - Módulo Extra (Potência Aparente Total)")
        print("S - Sair e Salvar")
        print("-" * 35)

        opc = input("Escolha: ").strip().lower()

        if opc == "1":
            registrar_medicao()
        elif opc == "2":
            salvar_circuitos()
        elif opc == "3":
            gerar_relatorio_nao_conforme(GLOBAL_LAST_SAVE_TIMESTAMP)
        elif opc == "4":
            resumo_eletrico(GLOBAL_LAST_SAVE_TIMESTAMP)
        elif opc == "5":
            analise_harmonicas()
        elif opc == "6":
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


