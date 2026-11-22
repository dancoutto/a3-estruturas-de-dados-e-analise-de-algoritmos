# RendeLeite · Onde o treinamento rende mais

[![Painel Online](https://img.shields.io/badge/Painel_Interativo-rendeleite.vercel.app-1f4d3a?style=flat-square)](https://rendeleite.vercel.app)
[![Pitch no YouTube](https://img.shields.io/badge/Pitch_em_Vídeo-YouTube-b91c1c?style=flat-square)](https://youtu.be/Xfx_Hy3cWc4)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B_(Stdlib)-3d6b57?style=flat-square)](https://www.python.org/)

> **Com $N$ treinamentos no orçamento, quais fazendas treinar e quanto a cooperativa ganha?**

Sistema de apoio à decisão e painel interativo desenvolvido pela **Squad 3** para a **Avaliação A3** de *Estruturas de Dados e Análise de Algoritmos* (Ciência da Computação · Campus UNA Betim · UC HUB).

---

## Links Rápidos

* **Aplicação Web & Entregáveis:** [rendeleite.vercel.app](https://rendeleite.vercel.app)
* **Pitch Gravado (Streaming):** [youtu.be/Xfx_Hy3cWc4](https://youtu.be/Xfx_Hy3cWc4)
* **Pitch Gravado (Download MP4 · 195 MB):** [Release v1.0-final](https://github.com/dancoutto/a3-estruturas-de-dados-e-analise-de-algoritmos/releases/tag/v1.0-final)

---

## O Problema e a Abordagem

Uma cooperativa de leite possui orçamento limitado para contratar treinamentos de ordenha ao custo unitário de **R$ 850,00**. Embora a intuição sugira treinar as fazendas com maior Contagem de Células Somáticas (CCS), o bônus financeiro do laticínio é pago por **tanque** — calculado pela média ponderada pelo volume de todas as fazendas que compartilham aquele tanque.

Para resolver o problema de alocação, o algoritmo compara três estratégias em Python puro:

| Nível | Estratégia | Complexidade | Comportamento |
| :--- | :--- | :---: | :--- |
| **Nível 1** | Linha de base (pior CCS) | $O(F \log F)$ | Seleciona as $N$ fazendas com maior CCS individual, ignorando volume e efeito no tanque. |
| **Nível 2** | Ganho isolado por fazenda | $O(F \log F)$ | Simula cada fazenda sozinha no tanque em $O(1)$ usando volume acumulado ($V$) e soma ponderada ($S = \sum V_i \cdot \text{CCS}_i$). |
| **Nível 3** | Guloso sequencial (*Heap*) | $O(F \log F + N \cdot k \log F)$ | Escolhe uma fazenda por vez com invalidação preguiçosa e atualiza o estado do tanque ($k \le 12$), evitando dupla contagem da mesma subida de faixa. |

### Principais Resultados (Base de Junho · 950 fazendas elegíveis)
* **Validação:** 100% de aderência nos 3 casos abertos do enunciado ($N = 1, 5, 10$) e 10 testes unitários automatizados (incluindo injeção de defeitos na base).
* **Impacto da dupla contagem ($N = 10$):** O Nível 2 projeta **R$ 78.196,16/mês**, enquanto o ganho real (Nível 3) é de **R$ 54.356,36/mês** (superestimativa de 30%).
* **Viabilidade econômica:** Apenas **93 das 950** fazendas geram retorno líquido positivo acima do custo de R$ 850,00.

---

## Estrutura do Repositório

```text
├── public/                 # Painel interativo e apresentação web (index.html, style.css, app.js, data.js)
│   ├── entregaveis/        # PDFs finais (relatório, decisões, banner ExpoUNA, pré-projeto), scripts e CSVs
│   └── img/                # Identidade visual e ícones da aplicação
├── python/                 # Implementação do algoritmo, gerador de dados do painel e testes unitários
│   ├── treinamento.py      # Motor de tratamento de dados e execução dos Níveis 1, 2 e 3
│   ├── gerar_dados.py      # Exporta os resultados processados para public/data.js
│   └── test_treinamento.py # Suíte de 10 testes automatizados (unittest)
├── saida/                  # Saídas geradas em CSV (rankings, curva de ganho e log de saneamento)
├── base/                   # CSVs brutos da cooperativa (não versionados; inserir localmente para reexecutar)
└── vercel.json             # Configuração de publicação estática da pasta public/
```

---

## Como Executar Localmente

O projeto utiliza **apenas a biblioteca padrão do Python (3.9+)**, sem dependências externas.

### 1. Rodar o algoritmo e atualizar o painel
Com os arquivos CSV da cooperativa dentro da pasta `base/`:

```bash
# Executa os Níveis 1, 2 e 3 e gera os CSVs em saida/
python python/treinamento.py --base base --saida saida --n 10

# Atualiza o arquivo public/data.js consumido pelo painel web
python python/gerar_dados.py
```

### 2. Executar os testes automatizados

```bash
# Linux / macOS
BASE_DIR=base python -m unittest discover -s python -v

# Windows (PowerShell)
$env:BASE_DIR="base"; python -m unittest discover -s python -v
```

### 3. Abrir o painel no navegador

```bash
python -m http.server -d public 8000
```
Acesse `http://localhost:8000` no navegador.

---

## Regras de Negócio e Saneamento de Dados

* **Saneamento:** De 18 arquivos disponíveis na base, 6 são utilizados no cálculo (e `tanques` como apoio visual). Foram descartadas 160 coletas com datas inválidas, 140 com fazendas inexistentes e 12 fazendas sem movimentação; 380 coletas em kg ($\div 1{,}032$) e 603 análises em cél/ml ($\div 1000$) foram convertidas para litros e mil cél/ml.
* **Cálculo de ganho:** $\text{Ganho} = (\text{bônus novo} - \text{bônus atual}) \times V_{\text{tanque}} - 850$, arredondado em centavos por fazenda antes da soma acumulada, respeitando limites de faixa com intervalo inferior inclusivo e superior exclusivo.
* **Critério de desempate:** Maior queda de CCS no tanque (maior margem na nova faixa), seguido de maior CCS individual da fazenda e código identificador.

---

## Equipe · Squad 3

* **Daniel Braga Alves do Couto**
* **Diogo Augusto Reis**
* **Yasmim Vitória Soares Pereira**

**Orientação:** Prof. Ted do Prado Amaral · Ciência da Computação · UNA Betim (2026/2)