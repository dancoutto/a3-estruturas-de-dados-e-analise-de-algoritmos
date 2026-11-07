import csv, json, os

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def ler(nome):
    with open(os.path.join(RAIZ, "saida", nome), encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter=";"))

n2 = [[int(r["posicao"]), r["fazenda_id"], r["tanque_id"], round(float(r["ccs_atual"]), 1),
       float(r["ganho_liquido"]), float(r["ganho_acumulado"]), r["faixa_antes"], r["faixa_depois"]]
      for r in ler("nivel2_ranking.csv")[:40]]
n3 = [[int(r["passo"]), r["fazenda_id"], r["tanque_id"], round(float(r["ccs_atual"]), 1),
       float(r["ganho_marginal"]), float(r["ganho_acumulado_real"]),
       r["faixa_tanque_antes"], r["faixa_tanque_depois"]] for r in ler("nivel3_sequencial.csv")[:40]]
dados = json.dumps({"n2": n2, "n3": n3, "custo": 850}, separators=(",", ":"))
with open(os.path.join(RAIZ, "public", "data.js"), "w", encoding="utf-8") as f:
    f.write("window.DATA=" + dados + ";\n")
print("public/data.js gerado")
