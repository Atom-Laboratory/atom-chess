# Relatório Final — Desempenho para uso intensivo de visão no braço robótico de xadrez com Banana Pi M5 e OpenCV

---

## 1. Contexto ajustado

O sistema opera sob:

* uso **intensivo de visão computacional**
* processamento contínuo ou quase contínuo de frames
* necessidade de detecção confiável de:

  * tabuleiro
  * ocupação das casas
  * possível identificação de peças

Baseado nos testes:

* alta taxa de sucesso funcional (**~90–100%**)
* falhas concentradas em testes de **desempenho**, não de corretude
* evidência direta de custo elevado em operações geométricas:

```text
TestRemap_remap.remap/191 → ~182 ms
```

* falhas recorrentes em operações paramétricas:

```text
PerfHoughCircles.*
HoughLines (variações de rho/theta/threshold)
```

---

## 2. Impacto do uso intensivo de visão

### Frequência de processamento

* transição de modelo reativo → processamento contínuo

Resultado:

* latência por operação é **aproximadamente estável sob parâmetros fixos**

* porém sensível a:

  * resolução da imagem
  * conteúdo (densidade de bordas/ruído)
  * espaço paramétrico

* carga total passa a ser limitada por:

  * custo por frame
  * throughput efetivo da CPU + memória

---

## 3. Custos dominantes no cenário intensivo

### 3.1 Operações lineares

* **2–8 ms**

Impacto:

* estáveis
* escalam linearmente com resolução
* não representam gargalo relevante

---

### 3.2 Transformações geométricas

* **120–220 ms** (observado ~182 ms)

Evidência:

```text
TestRemap_remap.remap/191 → ~182 ms
```

Impacto:

* principal custo por frame
* acesso irregular à memória → baixa eficiência de cache
* fortemente limitado por bandwidth de memória
* limitador direto de FPS

---

### 3.3 Operações locais

* **1–5 ms**

Impacto:

* desprezível no custo total
* altamente eficientes

---

### 3.4 Classificação leve

* **10–40 ms**

Impacto:

* segundo maior custo no pipeline
* afeta diretamente o throughput em execução contínua

---

### 3.5 Operações paramétricas globais

* **200–500+ ms (ou mais dependendo dos parâmetros)**

Evidência:

```text
PerfHoughCircles.Basic → FAILED
PerfHoughCircles2.ManySmallCircles → FAILED
HoughLines com múltiplas combinações → FAILED
```

Impacto:

* custo cresce com:

  * granularidade de rho/theta
  * threshold
  * densidade de bordas

* comportamento não linear

* múltiplas passagens na imagem → alto custo de memória

Observação:

* não são inviáveis funcionalmente
* são inadequadas para tempo real sem forte restrição de parâmetros

---

## 4. Hierarquia real de custo

1. operações paramétricas globais → pior caso (dependente de parâmetros)
2. transformações geométricas → custo dominante por frame
3. classificação leve → custo relevante
4. operações lineares → custo moderado
5. operações locais → custo baixo

---

## 5. Throughput real sob carga contínua

### Cenário intensivo básico

```text
operações lineares      → ~5 ms
geométrica              → ~120–220 ms
operações locais        → ~2 ms
```

**Total:**
→ **~130–230 ms por frame**

**Resultado:**
→ **~4–7 FPS**

---

### Cenário com classificação leve

```text
base                    → ~130–230 ms
classificação           → +10–40 ms
```

**Total:**
→ **~140–270 ms**

**Resultado:**
→ **~3–6 FPS**

---

### Cenário com múltiplas operações pesadas

```text
base                    → ~130–230 ms
+ geométrica adicional  → +120–220 ms
ou
+ operação global       → +200–500+ ms
```

**Resultado:**

* **2–4 FPS** (geométrica adicional)
* **1–3 FPS** (com operações globais)
* degradação não linear em casos paramétricos

---

## 6. Gargalos estruturais

Principais limitações do hardware:

* acesso irregular à memória (remapeamento)
* baixa eficiência de cache
* múltiplas varreduras em algoritmos globais
* limitação prática de **bandwidth de memória**, não apenas CPU

---

## 7. Sensibilidade de desempenho

### Resolução

* impacto linear direto no tempo total

### Transformações geométricas

* impacto alto e direto no custo por frame

### Espaço de parâmetros

* impacto elevado e não linear
* evidenciado pelas falhas em HoughLines/HoughCircles
* pequenas mudanças podem multiplicar o tempo de execução

---

## 8. Implicações para o braço robótico

### Pontos positivos

* **3–7 FPS** é suficiente para:

  * monitoramento contínuo do tabuleiro
  * detecção de mudanças de estado
  * sincronização com o controle do braço

---

### Limitações reais

* pipeline por frame deve ser curto
* não comporta múltiplas etapas pesadas encadeadas
* sensível a resolução e parâmetros

---

### Risco principal

> O acúmulo de operações com alto custo por frame (especialmente geométricas ou globais) leva à saturação da CPU/memória e perda de responsividade em tempo real.

---

## 9. Condições de viabilidade sob uso intensivo

O sistema permanece viável quando:

* há **no máximo uma transformação geométrica por frame**
* predominam operações **O(N)** e locais
* classificação é leve e controlada
* espaço de parâmetros é restrito

O sistema degrada quando:

* múltiplas transformações geométricas são encadeadas
* algoritmos globais exploram grande espaço paramétrico
* resolução aumenta sem controle

---

## 10. Conclusão final

O Banana Pi M5 suporta uso intensivo de visão computacional com comportamento previsível, porém limitado por memória e operações não locais:

* latência por frame: **130–270 ms**
* throughput contínuo: **~3–7 FPS**

Conclusão objetiva:

> O hardware é viável para o braço robótico de xadrez em regime contínuo, desde que o pipeline de visão seja estritamente controlado. A presença de múltiplas operações de alto custo ou algoritmos com grande espaço paramétrico compromete diretamente o desempenho em tempo real.

---