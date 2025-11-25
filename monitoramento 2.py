import json
import datetime
import os

DADOS_CIRCUITOS = {}
GLOBAL_LAST_SAVE_TIMESTAMP = "N/A (dados ainda não salvos)"

FAIXAS_SEGURAS = {
    "tensao": {"min": 210, "max": 230},
    "corrente": {"min": 0, "max": 50},
    "fator_potencia": {"min": 0.92, "max": 1.0},
    "frequencia": {"min": 59.5, "max": 60.5},
    "thd": {"min": 0, "max": 8.0}
}

MAPA_PARAMETROS = {
    "V": "tensao",
    "I": "corrente",
    "FP": "fator_potencia",
    "F": "frequencia",
    "THD": "thd"
}

ARQUIVO_DADOS = "circuitos_data.json"

def _verificar_e_registrar_thd(nome_circuito, medicoes):
    """
    Verifica se o THD > 8% e grava no relatório de harmônicas.
    """
    if 'thd' in medicoes:
        valor_thd = medicoes['thd']

        if valor_thd > 8.0:
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
    Lê a linha no formato 'Nome; chave=valor; chave=valor...'
    Aceita qualquer ordem: V, I, fp, f, THD.
    """
    try:
        partes = [p.strip() for p in linha.split(';')]
        nome_circuito = partes[0]
        if not nome_circuito:
            return None, None

        medicoes = {}
        for item in partes[1:]:
            if '=' in item:
                chave_raw, valor_str = item.split('=', 1)
                chave_raw = chave_raw.strip().upper()
                valor_str = valor_str.strip().replace(',', '.')

                chave_interna = MAPA_PARAMETROS.get(chave_raw)

                if chave_interna:
                    try:
                        medicoes[chave_interna] = float(valor_str)
                    except ValueError:
                        print(f"  Aviso: Valor inválido em '{item}' (esperado número, ex: 220 ou 10.5)")
                else:
                    print(f"  Aviso: Chave desconhecida '{chave_raw}' (use V, I, fp, f, THD)")

        if salvar_no_global and medicoes:
            if nome_circuito not in DADOS_CIRCUITOS:
                DADOS_CIRCUITOS[nome_circuito] = {}
            DADOS_CIRCUITOS[nome_circuito].update(medicoes)
            print(f"  Sucesso: Dados atualizados para '{nome_circuito}'.")

        return nome_circuito, medicoes
    except Exception as e:
        print(f"  Erro ao processar linha: {e}")
        return None, None

def registrar_medicao():
    """(Menu 1) Registro geral."""
    print("\n--- Modo de Registro Múltiplo ---")
    print("Formato Padrão: Nome; V=220; I=10; fp=0.95; f=60; THD=9.5")

    print("Digite 'fim' para sair.")

    while True:
        linha = input("Nova Medição: ").strip()
        if linha.lower() in ('fim', 'sair'):
            break
        if linha:
            _processar_linha_medicao(linha)

def salvar_circuitos():
    global GLOBAL_LAST_SAVE_TIMESTAMP
    print("\nSalvando circuitos...")
    timestamp = datetime.datetime.now().isoformat()
    dados = {"ultimo_salvamento": timestamp, "circuitos": DADOS_CIRCUITOS}
    try:
        with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)
        print(f"Salvo em '{ARQUIVO_DADOS}'.")
        GLOBAL_LAST_SAVE_TIMESTAMP = timestamp
    except Exception as e:
        print(f"Erro: {e}")

def gerar_relatorio_nao_conforme(last_save_time):
    """(Menu 3) Relatório padrão (V, I, fp, f)."""
    print("\nGerando relatório de não conformidade (Padrão)...")
    lista = []
    for nome, med in DADOS_CIRCUITOS.items():
        for param, valor in med.items():
            if param == 'thd': continue

            faixa = FAIXAS_SEGURAS.get(param)
            if faixa:
                if valor < faixa["min"]:
                    lista.append([nome, param, valor, "ABAIXO"])
                elif valor > faixa["max"]:
                    lista.append([nome, param, valor, "ACIMA"])

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open("relatorio_nao_conformidade.txt", "w", encoding="utf-8") as f:
            f.write(f"Relatório gerado em: {timestamp}\n")
            f.write(f"Dados baseados em:   {last_save_time}\n")
            f.write("-" * 40 + "\n")
            if not lista:
                f.write("Nenhuma não conformidade nos parâmetros básicos (V, I, fp, f).\n")
            for item in lista:
                f.write(f"Circuito {item[0]} | {item[1]}: {item[2]} -> {item[3]}\n")
        print(f"Relatório salvo. {len(lista)} alertas encontrados.")
    except IOError as e:
        print(f"Erro ao salvar: {e}")

def resumo_eletrico(last_save_time):
    """(Menu 4) Resumo geral."""
    print("\nGerando resumo elétrico...")
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        with open("resumo_eletrico.txt", "w", encoding="utf-8") as f:
            f.write(f"Resumo de {timestamp}\n")
            if not DADOS_CIRCUITOS:
                f.write("Nenhum dado registrado.\n")
            for nome, med in DADOS_CIRCUITOS.items():
                v = med.get("tensao", "N/D")
                i = med.get("corrente", "N/D")
                fp = med.get("fator_potencia", "N/D")
                f_ = med.get("frequencia", "N/D")
                thd = med.get("thd", "N/D")
                linha = f"[V={v}, I={i}, fp={fp}, f={f_}, THD={thd}]"
                f.write(f"{nome}: {linha}\n")
        print("Resumo salvo em 'resumo_eletrico.txt'.")
    except IOError as e:
        print(f"Erro ao salvar: {e}")

def analise_harmonicas():
    """
    (Menu 5) Análise de Harmônicas.
    Verifica dados existentes e permite entrada mantendo formato completo (fp, f, etc).
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
        linha = input("\nDados: ").strip()
        if not linha:
            break

        nome, medicoes = _processar_linha_medicao(linha, salvar_no_global=True)

        if nome and medicoes:
            _verificar_e_registrar_thd(nome, medicoes)

def carregar_dados():
    global DADOS_CIRCUITOS, GLOBAL_LAST_SAVE_TIMESTAMP
    try:
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            dados = json.load(f)
        if "circuitos" in dados:
            DADOS_CIRCUITOS = dados["circuitos"]
            GLOBAL_LAST_SAVE_TIMESTAMP = dados.get("ultimo_salvamento", "N/A")
        else:
            DADOS_CIRCUITOS = dados
    except:
        DADOS_CIRCUITOS = {}

def main():
    carregar_dados()
    while True:
        print("\n" + "=" * 30)
        print(" SISTEMA DE MONITORAMENTO")
        print("=" * 30)
        print("1. Registrar Medição (Geral)")
        print("2. Salvar Circuitos")
        print("3. Relatório de Não Conformidade")
        print("4. Resumo Elétrico")
        print("5. Análise de Harmônicas (THD)")
        print("S. Sair e Salvar")
        print("-" * 30)

        opc = input("Opção: ").lower()

        if opc == '1':
            registrar_medicao()
        elif opc == '2':
            salvar_circuitos()
        elif opc == '3':
            gerar_relatorio_nao_conforme(GLOBAL_LAST_SAVE_TIMESTAMP)
        elif opc == '4':
            resumo_eletrico(GLOBAL_LAST_SAVE_TIMESTAMP)
        elif opc == '5':
            analise_harmonicas()
        elif opc == 's':
            salvar_circuitos()
            break
        else:
            print("Opção inválida.")

if __name__ == "__main__":
    main()
