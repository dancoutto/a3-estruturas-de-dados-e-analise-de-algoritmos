"""
Squad 3 - Onde o treinamento rende mais
A3 - Estruturas de Dados e Analise de Algoritmos

Pergunta: com N treinamentos no orcamento, quais fazendas treinar e quanto a
cooperativa ganha, ja descontado o custo?

Estruturas de dados escolhidas (justificativa no documento de requisitos):
  - fazendas : dict  fazenda_id -> Fazenda(ccs, volume, tanque)       acesso O(1)
  - tanques  : dict  tanque_id  -> Tanque(volume V, soma S, membros)
               S = soma(volume x CCS). O CCS ponderado do tanque e S / V.
               Guardar (V, S) permite simular um treinamento em O(1): so S muda,
               S' = S - volume_da_fazenda x queda_de_CCS_da_fazenda.
  - faixas / efeitos : listas ordenadas pelo limite inferior (4 linhas)
  - heap (heapq) com invalidacao preguicosa, para o Nivel 3

Apenas biblioteca padrao: csv, heapq, datetime, dataclasses.
"""
import argparse
import csv
import heapq
import itertools
import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

KG_POR_LITRO = 1.032  # 1 L = 1,032 kg (dicionario de dados)
N_MAX_PADRAO = 40     # o painel permite escolher N de 1 a 40


# --------------------------------------------------------------------------
# Estruturas
# --------------------------------------------------------------------------
@dataclass
class Fazenda:
    id: str
    tanque: str
    ccs: float = None      # mil celulas/ml, no mes de referencia
    volume: float = 0.0    # litros, no mes de referencia


@dataclass
class Tanque:
    id: str
    tipo: str = "n/d"
    membros: list = field(default_factory=list)  # ids das fazendas elegiveis
    volume: float = 0.0                          # V
    soma: float = 0.0                            # S = soma(volume x CCS)


@dataclass
class Defeitos:
    """Contagem do que o tratamento descartou ou converteu (criterio de aceite)."""
    datas_invalidas: int = 0       # D3: coleta cuja data nao vira data
    coletas_orfas: int = 0         # D4: coleta com fazenda inexistente
    coletas_em_kg: int = 0         # D5: volume convertido de kg para litros
    analises_em_cel_ml: int = 0    # D5: CCS convertido de cel/ml para mil cel/ml
    fazendas_sem_dados: int = 0    # sem coleta ou sem analise no mes de referencia


@dataclass
class Dados:
    fazendas: dict
    tanques: dict
    faixas: list
    efeitos: list
    defeitos: Defeitos
    mes: int
    aviso_custo: str = ""


@dataclass
class Simulacao:
    reducao: float
    ccs_pos: float
    ccs_tanque_antes: float
    ccs_tanque_depois: float
    faixa_antes: str
    faixa_depois: str
    ganho_bonus: float
    custo: float
    liquido: float
    nova_soma: float


# --------------------------------------------------------------------------
# Leitura e tratamento da base
# --------------------------------------------------------------------------
def ler(base, nome):
    with open(os.path.join(base, nome), encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f, delimiter=";"))


def parse_data(texto):
    """Devolve a data ou None. Cobre 2026-02-30, 0000-00-00, 2027-13-05, 31/04/2026."""
    try:
        return datetime.strptime(texto.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None


def carregar(base, mes=None):
    # Tabelas de referencia (lidas dos CSVs, nada fixo no codigo)
    faixas = sorted(
        (float(r["ccs_min_mil"]), float(r["ccs_max_mil"]),
         float(r["bonus_reais_por_litro"]), r["faixa"])
        for r in ler(base, "faixas_bonificacao.csv"))
    efeitos = sorted(
        (float(r["ccs_min_mil"]), float(r["ccs_max_mil"]),
         float(r["reducao_esperada_pct"]) / 100, float(r["custo_reais"]))
        for r in ler(base, "efeito_treinamento.csv"))
    par = {r["parametro"]: r["valor"] for r in ler(base, "parametros.csv")}
    mes = int(mes if mes is not None else par["mes_referencia_simulacao"])
    inicio, fim = parse_data(par["periodo_inicio"]), parse_data(par["periodo_fim"])

    aviso = ""
    custos = {linha[3] for linha in efeitos}
    if "custo_treinamento" in par and float(par["custo_treinamento"]) not in custos:
        aviso = "custo_treinamento de parametros.csv difere de efeito_treinamento.csv"

    tipos = {}
    if os.path.exists(os.path.join(base, "tanques.csv")):  # so apoio ao painel
        tipos = {r["tanque_id"]: r["tipo"] for r in ler(base, "tanques.csv")}

    fazendas = {r["fazenda_id"]: Fazenda(r["fazenda_id"], r["tanque_id"])
                for r in ler(base, "fazendas.csv")}
    d = Defeitos()

    # Volume da fazenda no mes: soma das coletas validas, em litros
    for r in ler(base, "coletas.csv"):
        data = parse_data(r["data"])
        if data is None:
            d.datas_invalidas += 1
            continue
        if r["fazenda_id"] not in fazendas:
            d.coletas_orfas += 1
            continue
        litros = float(r["volume"])
        if r["unidade"] == "KG":
            litros /= KG_POR_LITRO
            d.coletas_em_kg += 1
        if inicio <= data <= fim and data.month == mes:
            fazendas[r["fazenda_id"]].volume += litros

    # CCS da fazenda no mes: analise do mes, em mil celulas/ml (a mais recente)
    recente = {}
    for r in ler(base, "analises.csv"):
        data = parse_data(r["data"])
        f = fazendas.get(r["origem_id"])
        if data is None or f is None:
            continue
        ccs = float(r["ccs"])
        if r["ccs_unidade"] == "cel_ml":
            ccs /= 1000
            d.analises_em_cel_ml += 1
        if inicio <= data <= fim and data.month == mes and data >= recente.get(f.id, data):
            recente[f.id] = data
            f.ccs = ccs

    # Elegiveis: tem volume e CCS no mes. Monta os tanques com (V, S).
    elegiveis = {fid: f for fid, f in fazendas.items() if f.volume > 0 and f.ccs is not None}
    d.fazendas_sem_dados = len(fazendas) - len(elegiveis)
    tanques = {}
    for f in elegiveis.values():
        t = tanques.setdefault(f.tanque, Tanque(f.tanque, tipos.get(f.tanque, "n/d")))
        t.membros.append(f.id)
        t.volume += f.volume
        t.soma += f.volume * f.ccs
    return Dados(elegiveis, tanques, faixas, efeitos, d, mes, aviso)


# --------------------------------------------------------------------------
# Regras de negocio
# --------------------------------------------------------------------------
def linha_da_tabela(tabela, ccs):
    """Limite inferior inclusivo e superior exclusivo."""
    if ccs < tabela[0][0]:
        return tabela[0]
    for linha in tabela:
        if linha[0] <= ccs < linha[1]:
            return linha
    return tabela[-1]


def simular(f, V, S, faixas, efeitos):
    """Treina a fazenda f num tanque com volume V e soma S. Nao altera nada."""
    _, _, reducao, custo = linha_da_tabela(efeitos, f.ccs)
    ccs_pos = f.ccs * (1 - reducao)
    S_pos = S - f.volume * (f.ccs - ccs_pos)
    antes, depois = S / V, S_pos / V
    fa, fd = linha_da_tabela(faixas, antes), linha_da_tabela(faixas, depois)
    ganho_bonus = (fd[2] - fa[2]) * V   # R$ por mes: novo bonus por litro x volume do tanque
    return Simulacao(reducao, ccs_pos, antes, depois, fa[3], fd[3],
                     round(ganho_bonus, 2), custo, round(ganho_bonus - custo, 2), S_pos)


def validar_n(n, total):
    if not isinstance(n, int) or n < 1 or n > total:
        raise ValueError(f"N deve ser um inteiro entre 1 e {total} (recebido: {n!r})")


# --------------------------------------------------------------------------
# Nivel 1: CCS, volume, queda esperada e as N de pior CCS
# --------------------------------------------------------------------------
def nivel1(dados):
    linhas = []
    for f in dados.fazendas.values():
        _, _, reducao, _ = linha_da_tabela(dados.efeitos, f.ccs)
        linhas.append({"fazenda_id": f.id, "tanque_id": f.tanque, "ccs_atual": f.ccs,
                       "volume_litros": f.volume, "reducao_pct": reducao * 100,
                       "ccs_apos_treinamento": f.ccs * (1 - reducao)})
    linhas.sort(key=lambda x: (-x["ccs_atual"], x["fazenda_id"]))
    for i, x in enumerate(linhas, 1):
        x["posicao_pior_ccs"] = i
    return linhas


# --------------------------------------------------------------------------
# Nivel 2 (exigido): ganho de cada fazenda treinada sozinha, ordenado
# --------------------------------------------------------------------------
def nivel2(dados):
    linhas = []
    for f in dados.fazendas.values():
        t = dados.tanques[f.tanque]
        s = simular(f, t.volume, t.soma, dados.faixas, dados.efeitos)
        linhas.append((f, t, s))
    # ganho liquido decrescente; desempate: maior CCS, depois id (resultado deterministico)
    linhas.sort(key=lambda x: (-x[2].liquido, -x[0].ccs, x[0].id))
    saida, acumulado = [], 0.0
    for i, (f, t, s) in enumerate(linhas, 1):
        acumulado = round(acumulado + s.liquido, 2)
        saida.append({
            "posicao": i, "fazenda_id": f.id, "tanque_id": t.id, "tipo_tanque": t.tipo,
            "fazendas_no_tanque": len(t.membros), "ccs_atual": f.ccs,
            "volume_litros": f.volume, "ccs_apos_treinamento": s.ccs_pos,
            "ccs_tanque_antes": s.ccs_tanque_antes, "ccs_tanque_depois": s.ccs_tanque_depois,
            "queda_ccs_tanque": s.ccs_tanque_antes - s.ccs_tanque_depois,
            "faixa_antes": s.faixa_antes, "faixa_depois": s.faixa_depois,
            "muda_faixa": s.faixa_antes != s.faixa_depois,
            "volume_tanque_litros": t.volume, "ganho_bonus_mensal": s.ganho_bonus,
            "custo": s.custo, "ganho_liquido": s.liquido, "ganho_acumulado": acumulado})
    return saida


# --------------------------------------------------------------------------
# Nivel 3 (bonus): escolha uma de cada vez, recalculando o tanque a cada passo
# Guloso: a cada passo pega o maior ganho marginal. Nao garante o otimo global
# (duas fazendas que so juntas fazem o tanque subir de faixa nao sao vistas).
# --------------------------------------------------------------------------
def nivel3(dados, n_max=N_MAX_PADRAO):
    fazendas, tanques = dados.fazendas, dados.tanques
    soma = {tid: t.soma for tid, t in tanques.items()}     # estado atualizado
    versao = defaultdict(int)                               # invalida entradas antigas
    treinadas, heap, contador = set(), [], itertools.count()
    isolado = {}

    def empurrar(f):
        t = tanques[f.tanque]
        s = simular(f, t.volume, soma[t.id], dados.faixas, dados.efeitos)
        heapq.heappush(heap, (-s.liquido, -f.ccs, f.id, versao[t.id], next(contador), s))
        return s

    for f in fazendas.values():
        isolado[f.id] = empurrar(f).liquido

    escolhidas, acumulado = [], 0.0
    while heap and len(escolhidas) < n_max:
        _, _, fid, ver, _, s = heapq.heappop(heap)
        f = fazendas[fid]
        if fid in treinadas or ver != versao[f.tanque]:
            continue                       # entrada velha: o tanque mudou depois dela
        treinadas.add(fid)
        soma[f.tanque] = s.nova_soma
        versao[f.tanque] += 1
        acumulado = round(acumulado + s.liquido, 2)
        escolhidas.append({
            "passo": len(escolhidas) + 1, "fazenda_id": fid, "tanque_id": f.tanque,
            "ccs_atual": f.ccs, "ganho_isolado_nivel2": isolado[fid],
            "ganho_marginal": s.liquido, "ganho_acumulado_real": acumulado,
            "faixa_tanque_antes": s.faixa_antes, "faixa_tanque_depois": s.faixa_depois,
            "muda_faixa": s.faixa_antes != s.faixa_depois})
        for outro in tanques[f.tanque].membros:   # so o tanque afetado e recalculado
            if outro not in treinadas:
                empurrar(fazendas[outro])
    return escolhidas


# --------------------------------------------------------------------------
# Saidas para o painel
# --------------------------------------------------------------------------
def _arredondar(v):
    return round(v, 2) if isinstance(v, float) else v


def escrever(caminho, linhas, colunas=None):
    colunas = colunas or list(linhas[0].keys())
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(colunas)
        for x in linhas:
            w.writerow([_arredondar(x[c]) for c in colunas])


def executar(base, saida, n=None, mes=None, n_max=N_MAX_PADRAO):
    dados = carregar(base, mes)
    total = len(dados.fazendas)
    n_max = min(n_max, total)
    if n is not None:
        validar_n(n, total)
    n1, n2, n3 = nivel1(dados), nivel2(dados), nivel3(dados, n_max)
    curva = [{"n": i + 1, "ganho_acumulado_nivel2": n2[i]["ganho_acumulado"],
              "ganho_acumulado_real_nivel3": n3[i]["ganho_acumulado_real"]}
             for i in range(min(n_max, len(n3)))]
    os.makedirs(saida, exist_ok=True)
    escrever(os.path.join(saida, "nivel1_fazendas.csv"), n1)
    escrever(os.path.join(saida, "nivel2_ranking.csv"), n2)
    escrever(os.path.join(saida, "nivel3_sequencial.csv"), n3)
    escrever(os.path.join(saida, "curva_ganho.csv"), curva)
    d = dados.defeitos
    escrever(os.path.join(saida, "log_tratamento.csv"), [
        {"indicador": "mes_referencia", "valor": dados.mes},
        {"indicador": "fazendas_elegiveis", "valor": total},
        {"indicador": "fazendas_sem_dados_no_mes", "valor": d.fazendas_sem_dados},
        {"indicador": "coletas_data_invalida_descartadas", "valor": d.datas_invalidas},
        {"indicador": "coletas_fazenda_inexistente_descartadas", "valor": d.coletas_orfas},
        {"indicador": "coletas_convertidas_de_kg", "valor": d.coletas_em_kg},
        {"indicador": "analises_convertidas_de_cel_ml", "valor": d.analises_em_cel_ml}])
    return dados, n1, n2, n3, curva


def main():
    p = argparse.ArgumentParser(description="Squad 3 - Onde o treinamento rende mais")
    p.add_argument("--base", default="base", help="pasta com os CSVs")
    p.add_argument("--saida", default="saida", help="pasta dos resultados")
    p.add_argument("--n", type=int, default=10, help="numero de treinamentos")
    p.add_argument("--mes", type=int, default=None, help="mes (padrao: parametros.csv)")
    a = p.parse_args()
    dados, n1, n2, n3, curva = executar(a.base, a.saida, a.n, a.mes)
    d = dados.defeitos
    print(f"Mes {dados.mes}: {len(dados.fazendas)} fazendas elegiveis em {len(dados.tanques)} tanques")
    print(f"Tratamento: {d.datas_invalidas} datas invalidas, {d.coletas_orfas} coletas orfas, "
          f"{d.coletas_em_kg} coletas em kg, {d.analises_em_cel_ml} analises em cel/ml")
    if dados.aviso_custo:
        print("AVISO:", dados.aviso_custo)
    print(f"\nN = {a.n}")
    print("Nivel 1 - pior CCS:", ", ".join(x["fazenda_id"] for x in n1[:a.n]))
    print("Nivel 2 - maior ganho:", ", ".join(x["fazenda_id"] for x in n2[:a.n]))
    print(f"  ganho acumulado (soma dos ganhos isolados): R$ {n2[a.n - 1]['ganho_acumulado']:,.2f}")
    if a.n <= len(n3):
        print(f"Nivel 3 - sequencial: ganho real acumulado R$ {n3[a.n - 1]['ganho_acumulado_real']:,.2f}")


if __name__ == "__main__":
    main()
