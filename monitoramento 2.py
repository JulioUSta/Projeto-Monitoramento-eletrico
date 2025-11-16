from datetime import datetime

# --- Lista inicial de circuitos ---
circuitos = [
    ["Circuito 1", "iluminacao", 220.0, 8.5, 0.95, 60.0, "05/11/2025"],
    ["Motor Bomba", "motor", 220.0, 14.0, 0.78, 60.0, "05/11/2025"],
    ["Alimentador Principal", "alimentador", 220.0, 25.0, 0.92, 60.0, "05/11/2025"],
    ["Banco Tomadas Sala 2", "tomada", 127.0, 9.5, 0.88, 60.0, "03/11/2025"]
]

# --- Limites por tipo de circuito ---
limites = {
    "iluminacao": {"i_max": 10.0, "fp_min": 0.9, "tensao_nom": 220},
    "motor": {"i_max": 20.0, "fp_min": 0.75, "tensao_nom": 220},
    "tomada": {"i_max": 15.0, "fp_min": 0.8, "tensao_nom": 127},
    "alimentador": {"i_max": 40.0, "fp_min": 0.92, "tensao_nom": 220},
}

tolerancia_tensao = 0.10  # 10%

# --- Funções auxiliares ---
def dentro_da_faixa(circuito):
    nome, tipo, v, i, fp, f, data = circuito
    regra = limites.get(tipo, None)
    if not regra:
        return True
    if not (regra["tensao_nom"] * (1 - tolerancia_tensao) <= v <= regra["tensao_nom"] * (1 + tolerancia_tensao)):
        return False
    if i > regra["i_max"]:
        return False
    if fp < regra["fp_min"]:
        return False
    return True

def registrar_medicao(linha):
    partes = linha.split(";")
    nome = partes[0].strip()
    medidas = {}
    for pedaco in partes[1:]:
        pedaco = pedaco.strip()
        if "=" in pedaco:
            kv = pedaco.split("=", 1)
            if len(kv) == 2:
                k, v = kv
                medidas[k.strip().lower()] = v.strip()

    encontrado = False
    for c in circuitos:
        if c[0] == nome:
            if "v" in medidas:
                c[2] = float(medidas["v"])
            if "i" in medidas:
                c[3] = float(medidas["i"])
            if "fp" in medidas:
                c[4] = float(medidas["fp"])
            if "f" in medidas:
                c[5] = float(medidas["f"])
            c[6] = datetime.now().strftime("%d/%m/%Y")
            encontrado = True
            break

    # Se não encontrou, cria um novo circuito
    if not encontrado:
        novo = [
            nome,
            "desconhecido",  # tipo padrão
            float(medidas.get("v", 0)),
            float(medidas.get("i", 0)),
            float(medidas.get("fp", 0)),
            float(medidas.get("f", 0)),
            datetime.now().strftime("%d/%m/%Y")
        ]
        circuitos.append(novo)


from datetime import datetime

def salvar_circuitos(nome_arquivo="circuitos.txt"):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(nome_arquivo, "w") as arq:
        arq.write("--- LISTA DE CIRCUITOS MONITORADOS ---\n")
        arq.write(f"Arquivo gerado em: {agora}\n")
        arq.write("=============================================\n\n")

        for c in circuitos:
            arq.write(f"[Circuito: {c[0]}]\n")
            arq.write(f"  - Tipo: {c[1]}\n")
            arq.write(f"  - Tensão: {c[2]} V\n")
            arq.write(f"  - Corrente: {c[3]} A\n")
            arq.write(f"  - Fator de Potência: {c[4]}\n")
            arq.write(f"  - Frequência: {c[5]} Hz\n")
            arq.write(f"  - Data da Medição: {c[6]}\n")
            arq.write("---------------------------------------------\n")

        arq.write("\nFim da Lista de Circuitos.\n")

    print("Circuitos salvos em", nome_arquivo)

def gerar_relatorio_nao_conforme(nome_arquivo="relatorio_nao_conforme.txt"):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dados_salvos = datetime.now().isoformat()

    menor_fp = min(circuitos, key=lambda x: x[4])
    fora = [c for c in circuitos if not dentro_da_faixa(c)]

    # circuito mais sobrecarregado
    sobrecarga = None
    maior_razao = 0
    for c in circuitos:
        regra = limites.get(c[1], None)
        if regra:
            razao = c[3] / regra["i_max"]
            if razao > maior_razao:
                maior_razao = razao
                sobrecarga = c

    with open(nome_arquivo, "w") as arq:
        arq.write("--- RELATÓRIO DE NÃO CONFORMIDADE ---\n")
        arq.write(f"Relatório gerado em: {agora}\n")
        arq.write(f"Dados salvos em:  {dados_salvos}\n")
        arq.write("=============================================\n\n")

        arq.write(f"Circuito com menor fator de potência: {menor_fp[0]} - {menor_fp[4]}\n")
        if sobrecarga:
            arq.write(f"Circuito mais sobrecarregado: {sobrecarga[0]} - {sobrecarga[3]} A\n")
        arq.write(f"Total de circuitos fora da faixa: {len(fora)}\n")
        if fora:
            arq.write("Lista dos fora da faixa: " + ", ".join([c[0] for c in fora]) + "\n")

        arq.write("\n=============================================\n")
        arq.write("Fim do Relatório.\n")

    print("Relatório de não conformidade salvo em", nome_arquivo)

# --- Análises elétricas ---


def resumo_eletrico(nome_arquivo="resumo_eletrico.txt"):
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    dados_salvos = datetime.now().isoformat()

    with open(nome_arquivo, "w") as arq:
        arq.write("--- RESUMO ELÉTRICO DA INSTALAÇÃO ---\n")
        arq.write(f"Resumo gerado em: {agora}\n")
        arq.write(f"Dados salvos em:  {dados_salvos}\n")
        arq.write("=============================================\n\n")

        for c in circuitos:
            arq.write(f"[Circuito: {c[0]}]\n")
            arq.write(f"  - Tensão: {c[2]} V\n")
            arq.write(f"  - Corrente: {c[3]} A\n")
            arq.write(f"  - Fator Potência: {c[4]}\n")
            arq.write(f"  - Frequência: {c[5]} Hz\n\n")

        arq.write("=============================================\n")
        arq.write("Fim do Resumo.\n")

    print("Resumo elétrico salvo em", nome_arquivo)


# --- Módulo extra (placeholder) ---
def modulo_extra():
    print("Módulo extra ainda não implementado.")

# --- Menu principal em loop ---
def main():
    while True:
        print("\n=== Sistema de Monitoramento Elétrico ===")
        print("1 - Registrar medição")
        print("2 - Salvar circuitos")
        print("3 - Gerar relatório de não conformidade")
        print("4 - Resumo elétrico")
        print("5 - Rodar módulo extra")
        print("0 - Sair")
        opc = input("Escolha: ")
        if opc == "1":
            linha = input("Digite: Nome; V=...; I=...; fp=...; f=...\n")
            registrar_medicao(linha)
        elif opc == "2":
            salvar_circuitos()
        elif opc == "3":
            gerar_relatorio_nao_conforme()
        elif opc == "4":
            resumo_eletrico()
        elif opc == "5":
            modulo_extra()
        elif opc == "0":
            print("Encerrando sistema...")
            break
        else:
            print("Opção inválida")

# Executa o menu
if __name__ == "__main__":
    main()