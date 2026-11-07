import argparse
import csv
import heapq
import itertools
import os
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

KG_POR_LITRO = 1.032
N_MAX_PADRAO = 40

@dataclass
class Fazenda:
    id: str
    tanque: str
    ccs: float = None
    volume: float = 0.0


@dataclass
class Tanque:
    id: str
    tipo: str = "n/d"
    membros: list = field(default_factory=list)
    volume: float = 0.0
    soma: float = 0.0


@dataclass
class Defeitos:
    """Contagem do que o tratamento descartou ou converteu (criterio de aceite)."""
    datas_invalidas: int = 0
    coletas_orfas: int = 0
    coletas_em_kg: int = 0
    analises_em_cel_ml: int = 0
    fazendas_sem_dados: int = 0


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
    if os.path.exists(os.path.join(base, "tanques.csv")):
        tipos = {r["tanque_id"]: r["tipo"] for r in ler(base, "tanques.csv")}

    fazendas = {r["fazenda_id"]: Fazenda(r["fazenda_id"], r["tanque_id"])
                for r in ler(base, "fazendas.csv")}
    d = Defeitos()

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

    elegiveis = {fid: f for fid, f in fazendas.items() if f.volume > 0 and f.ccs is not None}
    d.fazendas_sem_dados = len(fazendas) - len(elegiveis)
    tanques = {}
    for f in elegiveis.values():
        t = tanques.setdefault(f.tanque, Tanque(f.tanque, tipos.get(f.tanque, "n/d")))
        t.membros.append(f.id)
        t.volume += f.volume
        t.soma += f.volume * f.ccs
    return Dados(elegiveis, tanques, faixas, efeitos, d, mes, aviso)

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
    ganho_bonus = (fd[2] - fa[2]) * V 
    return Simulacao(reducao, ccs_pos, antes, depois, fa[3], fd[3],
                     round(ganho_bonus, 2), custo, round(ganho_bonus - custo, 2), S_pos)


def validar_n(n, total):
    if not isinstance(n, int) or n < 1 or n > total:
        raise ValueError(f"N deve ser um inteiro entre 1 e {total} (recebido: {n!r})")

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

def nivel2(dados):
    linhas = []
    for f in dados.fazendas.values():
        t = dados.tanques[f.tanque]
        s = simular(f, t.volume, t.soma, dados.faixas, dados.efeitos)
        linhas.append((f, t, s))
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

def nivel3(dados, n_max=N_MAX_PADRAO):
    fazendas, tanques = dados.fazendas, dados.tanques
    soma = {tid: t.soma for tid, t in tanques.items()}
    versao = defaultdict(int)
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
            continue
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
        for outro in tanques[f.tanque].membros:
            if outro not in treinadas:
                empurrar(fazendas[outro])
    return escolhidas

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
