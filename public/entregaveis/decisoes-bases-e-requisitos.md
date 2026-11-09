# Decisões sobre as bases e requisitos – Squad 3 (rascunho)

## Critério
Um arquivo entra só se fornece um insumo da conta: CCS por fazenda, volume por fazenda no mês, tanque da fazenda, faixas e bônus, queda esperada e custo, mês de referência. A unidade do treinamento é a fazenda.

## Arquivos
| Arquivo | Decisão | Motivo |
|---|---|---|
| analises | Usado | CCS mensal por fazenda (não existe análise de tanque) |
| coletas | Usado | Volume por fazenda: peso da média ponderada e base do ganho mensal |
| fazendas | Usado | Liga a fazenda ao tanque |
| faixas_bonificacao | Usado | Faixas A a D e bônus por litro |
| efeito_treinamento | Usado | Queda do CCS por faixa e custo de R$ 850 |
| parametros | Usado em parte | Mês de referência (junho) e custo do treinamento |
| tanques | Apoio | Só rotula o tipo do tanque no painel |
| produtores | Descartado | A unidade é a fazenda; D1, D2 e CPF ficam só nele |
| cargas, caminhoes, silos | Descartados | Rota e descarga do leite; não mudam o CCS nem o volume do tanque |
| eventos_antibiotico | Descartado | Eventos de contaminação, fora desta conta |
| requisitos_bpa, avaliacoes_bpa, niveis_bpa_bonus | Descartados | Outro programa, com outro bônus por litro |
| regras_compatibilidade | Descartado | Mistura de espécies e certificações, fora desta conta |
| clima_municipio, precos_insumos | Descartados | Contexto, sem relação com a conta |

Coluna descartada de propósito: `volume_medio_dia_litros` (em junho o volume real varia de 93% a 106% de média × 30; o volume vem das coletas).

## Defeitos tratados
D3: 160 coletas com data impossível, descartadas. D4: 140 coletas com fazenda inexistente, descartadas; 12 fazendas F9xxx sem coleta nem análise ficam de fora. D5: 380 coletas em kg (÷ 1,032) e 603 análises em cel/ml (÷ 1000), convertidas.

## Requisitos adotados (a squad deve confirmar)
1. Elegíveis: fazendas com volume e análise em junho (950).
2. CCS da fazenda: análise do mês, em mil células/ml.
3. Volume da fazenda: soma das coletas válidas do mês, em litros.
4. Tanque de `fazendas.csv`; CCS do tanque por média ponderada pelo volume.
5. Faixa com limite inferior inclusivo e superior exclusivo (regra do dicionário de dados, não é decisão da squad).
6. Ganho = (bônus novo − bônus atual) × volume do tanque − R$ 850, arredondado a centavos por fazenda antes de somar.
7. Desempate: maior queda do CCS do tanque (mais folga dentro da faixa nova), depois maior CCS da fazenda, depois código.
8. N de 1 até o número de elegíveis (950); o painel segue o enunciado (1 a 40) e pode ser ampliado até 950; o ranking não filtra ganho negativo.
9. Nível 2 soma ganhos isolados; Nível 3 escolhe uma de cada vez e recalcula o tanque (guloso).
