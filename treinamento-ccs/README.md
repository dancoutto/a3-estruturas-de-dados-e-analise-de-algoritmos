# Onde o treinamento rende mais

Squad 3 · A3 · Estruturas de Dados e Análise de Algoritmos · UC HUB

Com N treinamentos no orçamento, quais fazendas treinar e quanto a cooperativa ganha, já descontado o custo? O bônus é pago por tanque (CCS ponderado pelo volume), então treinar uma fazenda pode mudar a faixa de todas as que dividem o tanque.

## Estrutura

```
public/        site de apresentação com rolagem + painel (index.html, style.css, app.js, data.js)
public/entregaveis/   arquivos para download (código, relatório em rascunho, decisões, pré-projeto, Canvas, CSVs)
python/        treinamento.py (algoritmo), test_treinamento.py, gerar_dados.py
saida/         resultados do algoritmo em CSV (alimentam o painel)
base/          CSVs da cooperativa (não versionados; coloque aqui)
vercel.json    publica a pasta public/
```

## Rodar o algoritmo

```
python python/treinamento.py --base base --saida saida --n 10
python python/gerar_dados.py        # atualiza public/data.js
BASE_DIR=base python -m unittest discover -s python -v
```

Só biblioteca padrão do Python (3.9 ou mais novo).

## Ver o painel

Abra `public/index.html` no navegador, ou rode `python -m http.server -d public 8000` e acesse http://localhost:8000.

## Publicar na Vercel

1. Suba o repositório no GitHub.
2. Na Vercel: Add New → Project → importe o repositório.
3. Framework Preset: Other. Sem Build Command e sem Install Command. O Output Directory (`public`) já vem do `vercel.json`.
4. Deploy. Cada `git push` publica de novo.

Se mudar os dados, rode o algoritmo e `gerar_dados.py`, e faça commit de `saida/` e `public/data.js`.

## Decisões de requisito

Elegíveis: fazendas com volume e análise em junho. CCS em mil células/ml e volume em litros (kg ÷ 1,032). Faixa com limite inferior inclusivo. Ganho = (bônus novo − bônus atual) × volume do tanque − R$ 850, arredondado a centavos por fazenda. Desempate: maior queda do CCS do tanque, depois maior CCS da fazenda, depois código. O painel segue o enunciado (N de 1 a 40) e pode ser ampliado até 950. Nível 2 soma ganhos isolados; Nível 3 escolhe uma de cada vez e recalcula o tanque (guloso, não garante o ótimo global).
