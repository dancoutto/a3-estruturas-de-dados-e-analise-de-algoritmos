"""
Criterios de aceite da squad 3. Rodar:  BASE_DIR=./base python -m unittest -v

CA1  Os tres casos abertos do enunciado batem (N = 1, 5 e 10; junho).
CA2  Os defeitos da base (D3, D4, D5) nao mudam o resultado: dados sujos = dados limpos.
CA3  Limite de faixa: 250 mil entra na faixa B (inferior inclusivo, superior exclusivo).
CA4  Fazenda abaixo de 250 mil nao reduz CCS e o ganho dela e -R$ 850.
CA5  Duas fazendas do mesmo tanque: o Nivel 2 soma duas vezes, o Nivel 3 nao.
CA6  Desempate deterministico e N invalido gera erro claro.
CA7  Na base real, o tratamento descarta/converte o que o dicionario lista.
"""
import os
import shutil
import tempfile
import unittest

import treinamento as t

BASE_REAL = os.environ.get("BASE_DIR", "base")
TEM_BASE = os.path.exists(os.path.join(BASE_REAL, "coletas.csv"))

FAIXAS = "faixa;ccs_min_mil;ccs_max_mil;bonus_reais_por_litro\nA;0;250;0.12\nB;250;400;0.06\nC;400;600;0.00\nD;600;10000;-0.05\n"
EFEITO = "ccs_min_mil;ccs_max_mil;reducao_esperada_pct;custo_reais\n0;250;0;850\n250;400;12;850\n400;600;22;850\n600;10000;30;850\n"
PARAM = ("parametro;valor;unidade\ncusto_treinamento;850;R$/fazenda\nperiodo_inicio;2026-03-01;data\n"
         "periodo_fim;2026-06-30;data\nmes_referencia_simulacao;6;mes\n")


def escrever_base(pasta, fazendas, coletas, analises):
    def w(nome, texto):
        with open(os.path.join(pasta, nome), "w", encoding="utf-8") as f:
            f.write(texto)
    w("faixas_bonificacao.csv", FAIXAS)
    w("efeito_treinamento.csv", EFEITO)
    w("parametros.csv", PARAM)
    w("fazendas.csv", "fazenda_id;tanque_id\n" + "".join(f"{a};{b}\n" for a, b in fazendas))
    w("coletas.csv", "coleta_id;data;fazenda_id;tanque_id;volume;unidade\n" +
      "".join(f"K{i};{d};{fz};T;{v};{u}\n" for i, (d, fz, v, u) in enumerate(coletas)))
    w("analises.csv", "analise_id;data;origem_tipo;origem_id;ccs;ccs_unidade\n" +
      "".join(f"A{i};{d};fazenda;{fz};{c};{u}\n" for i, (d, fz, c, u) in enumerate(analises)))


# Tanque TX: A e B identicas (50.000 + 50.000 L cada, CCS 650 -> faixa D).
# Treinar uma sobe o tanque para a faixa C (+0,05/L x 200.000 L = R$ 10.000).
# Treinar a outra depois nao muda a faixa (C continua C).
FAZ = [("A", "TX"), ("B", "TX"), ("C", "TY")]
COL_LIMPAS = [("2026-06-10", "A", 50000, "L"), ("2026-06-20", "A", 50000, "L"),
              ("2026-06-10", "B", 50000, "L"), ("2026-06-20", "B", 50000, "L"),
              ("2026-06-15", "C", 1000, "L")]
ANA_LIMPAS = [("2026-06-05", "A", 650, "mil_cel_ml"), ("2026-06-05", "B", 650, "mil_cel_ml"),
              ("2026-06-05", "C", 100, "mil_cel_ml")]


class BaseSintetica(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def rodar(self, col=COL_LIMPAS, ana=ANA_LIMPAS):
        escrever_base(self.tmp, FAZ, col, ana)
        d = t.carregar(self.tmp)
        return d, t.nivel2(d), t.nivel3(d, 3)


class TestRegras(BaseSintetica):
    def test_ca2_defeitos_nao_mudam_o_resultado(self):
        _, limpo, _ = self.rodar()
        sujas = [("2026-06-10", "A", 51600, "KG"),               # D5: 51600 kg = 50000 L
                 ("2026-06-20", "A", 50000, "L"),
                 ("2026-06-10", "B", 50000, "L"), ("2026-06-20", "B", 50000, "L"),
                 ("2026-06-15", "C", 1000, "L"),
                 ("2026-02-30", "A", 999999, "L"),                # D3: data impossivel
                 ("0000-00-00", "B", 999999, "L"),                # D3
                 ("2027-13-05", "B", 999999, "L"),                # D3
                 ("2026-06-12", "F9999", 999999, "L")]            # D4: fazenda inexistente
        ana = [("2026-06-05", "A", 650000, "cel_ml"),             # D5: 650000 cel/ml = 650 mil
               ("2026-06-05", "B", 650, "mil_cel_ml"), ("2026-06-05", "C", 100, "mil_cel_ml")]
        d, sujo, _ = self.rodar(sujas, ana)
        self.assertEqual([x["fazenda_id"] for x in sujo], [x["fazenda_id"] for x in limpo])
        self.assertEqual([x["ganho_liquido"] for x in sujo], [x["ganho_liquido"] for x in limpo])
        self.assertEqual((d.defeitos.datas_invalidas, d.defeitos.coletas_orfas,
                          d.defeitos.coletas_em_kg, d.defeitos.analises_em_cel_ml), (3, 1, 1, 1))

    def test_ca3_limite_da_faixa_e_inclusivo(self):
        faixas = [(0, 250, .12, "A"), (250, 400, .06, "B")]
        self.assertEqual(t.linha_da_tabela(faixas, 250)[3], "B")
        self.assertEqual(t.linha_da_tabela(faixas, 249.999)[3], "A")

    def test_ca4_abaixo_de_250_nao_reduz_e_custa_850(self):
        _, n2, _ = self.rodar()
        c = next(x for x in n2 if x["fazenda_id"] == "C")
        self.assertEqual(c["ccs_apos_treinamento"], c["ccs_atual"])
        self.assertEqual(c["ganho_liquido"], -850.0)

    def test_ca5_dupla_contagem(self):
        _, n2, n3 = self.rodar()
        self.assertEqual(n2[0]["ganho_liquido"], 9150.0)   # 0,05 x 200.000 - 850
        self.assertEqual(n2[1]["ganho_liquido"], 9150.0)   # isolado, parece igual
        self.assertEqual(n2[1]["ganho_acumulado"], 18300.0)
        self.assertEqual(n3[0]["ganho_marginal"], 9150.0)
        self.assertEqual(n3[1]["ganho_marginal"], -850.0)  # tanque ja subiu: so paga o custo
        self.assertEqual(n3[1]["ganho_acumulado_real"], 8300.0)

    def test_ca6_desempate_e_n_invalido(self):
        _, n2, _ = self.rodar()
        self.assertEqual([x["fazenda_id"] for x in n2[:2]], ["A", "B"])  # empate -> id
        for n in (0, -1, 4, 2.5):
            with self.assertRaises(ValueError):
                t.validar_n(n, 3)


@unittest.skipUnless(TEM_BASE, "defina BASE_DIR com a pasta dos CSVs")
class TestBaseReal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dados = t.carregar(BASE_REAL)
        cls.n2 = t.nivel2(cls.dados)
        cls.n3 = t.nivel3(cls.dados, 40)

    def test_ca1_casos_abertos(self):
        for n, esperado in {1: 9010.40, 5: 42046.84, 10: 78196.16}.items():
            self.assertEqual(self.n2[n - 1]["ganho_acumulado"], esperado, f"N={n}")

    def test_ca7_defeitos_da_base_real(self):
        d = self.dados.defeitos
        self.assertEqual(d.datas_invalidas, 160)       # D3
        self.assertEqual(d.coletas_orfas, 140)         # D4
        self.assertEqual(d.coletas_em_kg, 380)         # D5
        self.assertEqual(len(self.dados.fazendas), 950)
        self.assertEqual(d.fazendas_sem_dados, 12)     # as F9xxx

    def test_nivel3_nunca_passa_do_nivel2(self):
        for a, b in zip(self.n2[:40], self.n3):
            self.assertLessEqual(b["ganho_acumulado_real"], a["ganho_acumulado"])

    def test_sem_fazenda_repetida(self):
        ids = [x["fazenda_id"] for x in self.n3]
        self.assertEqual(len(ids), len(set(ids)))


if __name__ == "__main__":
    unittest.main()
