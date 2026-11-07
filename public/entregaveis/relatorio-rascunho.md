# Relatório – Onde o treinamento rende mais (RASCUNHO PARCIAL)

Seções marcadas com [A COMPLETAR] ainda não foram escritas.

## 1. Problema
Com N treinamentos (R$ 850 cada), quais fazendas treinar e quanto a cooperativa ganha, já descontado o custo? O bônus é pago por tanque, pelo CCS ponderado pelo volume, então treinar uma fazenda pode mudar a faixa de todas as que dividem o tanque. Exemplo: no tanque TC009 (junho), treinar a F0082 leva o tanque de 428,1 para 390,0 mil e rende R$ 9.010,40 por mês.

## 2. Dados e tratamento
Seis dos 18 arquivos são usados. Defeitos tratados: 160 datas impossíveis e 140 fazendas inexistentes (descartadas); 380 coletas em kg e 603 análises em cel/ml (convertidas). Detalhes em `decisoes-bases-e-requisitos.md`.

## 3. Requisitos
Nove decisões adotadas (arredondamento, desempate, limite de faixa, tratamento de N). Ver `decisoes-bases-e-requisitos.md`.

## 4. Estrutura de dados
Dicionários de fazendas e de tanques. Cada tanque guarda o volume V e a soma S de volume × CCS; o CCS é S ÷ V e simular um treinamento só muda S, em O(1). O Nível 3 usa um heap com invalidação preguiçosa e recalcula só o tanque afetado (no máximo 12 fazendas). Custo: Nível 2 em O(F log F) com F = 950; Nível 3 em O(F log F + N·k·log F). Limite: o Nível 3 é guloso e não garante o ótimo global.
[A COMPLETAR: alternativas consideradas (por exemplo, recalcular o tanque do zero a cada simulação) e por que foram descartadas.]

## 5. Verificação
Os três casos abertos batem (N = 1, 5 e 10: R$ 9.010,40; R$ 42.046,84; R$ 78.196,16). Nove testes automáticos, entre eles um que injeta data impossível, fazenda inexistente, kg e cel/ml e exige o mesmo resultado dos dados limpos.

## 6. Resultados
- N = 10: Nível 2 = R$ 78.196,16; ganho real (Nível 3) = R$ 54.356,36. N = 40: R$ 125.402,33 contra R$ 70.138,42.
- O Nível 2 superestima por contar a subida de faixa de um mesmo tanque mais de uma vez.
- Só 93 das 950 fazendas têm ganho positivo.
[A COMPLETAR: análise do painel e da curva de ganho.]

## 7. Pendências
[A COMPLETAR: conclusão, limitações, resultado para o caso retido do professor, medição de tempo de execução.]
