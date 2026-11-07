# BOM, eletrônica, alimentação e segurança

Fontes E02/E03/E04/E06/E09/E11 no [registro geral](README.md). O levantamento
de componentes é [bom-audit.csv](bom-audit.csv), 38 grupos com identificação,
subsistema, quantidades, fabricante/modelo, especificação, interface, aquisição,
preço/fonte, datasheet, desenho, validação e pendências. Unknowns são explícitos.
Alguns grupos precisam ser desdobrados em part numbers/ocorrências antes de compra.

## Resultado da auditoria da BOM

1. **Identificados:** SBCs, ESP32-S3, câmera/ESP32-CAM, drivers propostos,
   NEMA17, servo MG996R, fonte/bucks, endstops/parada, cabos e elementos CAD.
2. **Incompletos:** modelo de Orange Pi, NEMA17/carrier real, corrente, redução,
   torque, fonte/servo/buck e todos os códigos comerciais definitivos.
3. **Necessários mas não fechados:** proteção dimensionada, intertravamento de
   potência, chicote/conectores, fusíveis, fixação à bancada e alívio de tração;
   necessidade/seleção de dissipação dependem de ensaio e componente.
4. **Quantidades:** quatro motores/drivers no bring-up vs cinco no diagrama;
   fixadores/rolamentos/polias precisam de BOM de ocorrência. Número de arquivos
   CAD não é quantidade de montagem nem estoque.
5. **Datasheets:** não foi localizado conjunto rastreável de fichas dos componentes
   físicos exatos, incluindo carriers, fontes, servo e motores comprados.
6. **Compatibilidades:** lógica ESP32/driver, alimentação de SBCs/câmera/servo,
   corrente de pico, USB/GND e saída de endstops sem validação da fiação real.
7. **Desenhos:** materiais/encaixes/fixadores e processo das peças próprias sem
   pacote dimensionado; STL não fecha especificação de fabricação.
8. **Aquisição:** não há evidência suficiente de estoque ou compras para declarar
   quantidades a adquirir. Não gerar lista “comprar tudo” por ausência de inventário.
9. **A obter:** etiquetas, fotos da fiação, revisão real, estoque e notas acessíveis;
   dimensões/ratings por componente, fontes de compra e medições de bancada.
10. **Manutenção:** BOM-mestre por revisão, separada em comercial/fabricada,
    agregada por subsistema; quantidade requerida, disponível e comprar distintas.
    Cada item deve apontar desenho/datasheet, ocorrência CAD e revisão do chicote.

Nenhum custo total conhecido foi encontrado. Preços da referência/tutorial,
links afiliados ou valores atuais de loja não provariam o custo pago pelo ATOM.
Custos estimados futuros devem ter data/moeda/quantidade/frete/impostos separados.
Consumo e custo de manutenção/fabricação também desconhecidos; não orçados aqui.

## Elétrica: diagrama não é esquema de conexão

E03 mostra fonte 12 V/10 A, dois bucks 12→5 V, rails de lógica/controle, GND,
cinco DRV8825 com capacitores 100 µF, endstops e emergência. É uma arquitetura
documentada, sem pinagem/netlist/conectores/bitolas e ratings completos.
E06 propõe quatro DRV8825, alimentação separada adequada ao servo e ground comum;
referência original usa UNO/CNC Shield/A4988. Não transferir a pinagem da referência
para ESP32-S3. Firmware atual não usa micro-ROS apesar de E03 mostrar essa ligação.

| Tema | Pode concluir | Verificação necessária |
|---|---|---|
| 12 V/10 A | Valor escrito no diagrama | Identificar fonte real e somar cargas/picos por rail com margem e ensaio |
| Drivers | DRV8825 proposto | Carrier/Rsense, corrente por fase, microstep, temperatura e especificação lógica |
| 5 V/servo | Dois rails propostos | Capacidade de buck e servo em pico/travamento, queda de tensão e reset da lógica |
| GND/USB | Nó comum desenhado | Caminhos de retorno, ruído, referência de sinal e circulação de corrente reais |
| Endstops/E-stop | Funções desenhadas e flags no firmware | Contato/polaridade, fail-safe, bounce, fio rompido, desligamento de potência independente |
| Proteções | Intenção de segurança | Fusíveis/proteção por rail, curto/inversão, invólucro e separação AC/baixa tensão com responsável habilitado |
| Térmica/cabos | Sem dimensionamento | Corrente contínua/pico, bitolas, conectores, ventilação e ensaios |

## Riscos e manutenção antes de ampliar autonomia

P0 é gate para operação física: parada e alimentação precisam de validação
independente de o software funcionar. Não foi observado robô energizado nem
ensaio de segurança; não se afirma falha elétrica real ou conformidade normativa.

- Colisão/prensagem: limites físicos, cursos da garra, cabos e alcance devem
  ser conferidos; o perfil visual de simulação não demonstra ausência de contato.
- Movimento após boot/perda de referência: falta homing e estado conhecido
  demonstrados; posição contada de passos não é posição medida.
- Perda de comunicação: executor bloqueante pode continuar o segmento; não foi
  identificado watchdog de comunicação ativo. Validar o comportamento desejado.
- Sobrecorrente/travamento/aquecimento: estabelecer corrente/limites térmicos com
  componentes reais; não elevar potência para compensar modelo errado.
- Falha de fixação/tensão de cabos: inspecionar fixadores, transmissão e chicote
  em todo curso; registrar reposição e nova calibração após alteração.
- Recuperação: parada, remoção de causa, verificação de referência e autorização
  de retomada devem ser explícitas; não reiniciar automaticamente partida após erro.

Ensaios recomendados: inspeção sem energia, continuidade/polaridade e power-off;
medir rails sem carga e com carga, temperatura/queda e lógica; validar E-stop e
endstops sem motor; só depois um eixo por vez e movimento combinado supervisionado.
Resultados e condições devem ser registrados por quem opera a bancada. Esta
auditoria não executou nem autorizou energização ou mudança de configuração.
