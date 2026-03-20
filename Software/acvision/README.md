# 📷 ATOM Chess - Visão Computacional: Teste de Câmera

## 📋 Conteúdo

- [1. Instalação e Configuração do OpenCV (Windows)](#-1-instalação-e-configuração-do-opencv-windows)
  - [1.1. Configuração de Variáveis de Ambiente (Runtime)](#11-configuração-de-variáveis-de-ambiente-runtime)
- [2. Configuração da Toolchain (Visual Studio)](#-2-configuração-da-toolchain-visual-studio)
  - [2.1. Criação e Setup do Projeto](#21-criação-e-setup-do-projeto)
  - [2.2. Diretórios VC++ (Headers e Libs)](#22-diretórios-vc-headers-e-libs)
  - [2.3. Vinculador (Linker)](#23-vinculador-linker)
- [3. Executando o Teste](#-3-executando-o-teste)

---

## 🛠️ 1. Instalação e Configuração do OpenCV (Windows)

A versão homologada para este teste é a **4.13.0**.

1. Faça o download do executável (`opencv-4.13.0-windows.exe`) diretamente do [repositório oficial de releases no GitHub](https://github.com/opencv/opencv/releases) ou do site oficial do OpenCV.
2. Execute o arquivo e extraia o conteúdo para um diretório raiz de fácil acesso, preferencialmente em um SSD para otimizar o tempo de build.
   > **Recomendação de Path:** `C:\opencv\`

### 1.1. Configuração de Variáveis de Ambiente (Runtime)

Para que o Windows localize as DLLs do OpenCV em tempo de execução (dynamic linking):

1. Pressione `Win`, digite **"Editar as variáveis de ambiente do sistema"** e pressione `Enter`.
2. Clique em **Variáveis de Ambiente...**.
3. Em _Variáveis do sistema_, localize `Path`, selecione-a e clique em **Editar**.
4. Adicione um **Novo** caminho para a pasta `bin`:
   ```
   C:\opencv\build\x64\vc16\bin
   ```

⚠️ **Reinicie o computador** para que a variável seja propagada.

---

## 💻 2. Configuração da Toolchain (Visual Studio)

Certifique-se de ter o **Visual Studio Community** (ou superior) instalado com a carga de trabalho "Desenvolvimento para Desktop com C++".

### 2.1. Criação e Setup do Projeto

1. Crie um Projeto Vazio (Empty Project) em C++.
2. Na barra de ferramentas, defina a plataforma como **x64**.
3. Acesse **Projeto > Propriedades...** (ou `Alt + Enter`).

### 2.2. Diretórios VC++ (Headers e Libs)

Nas Propriedades, navegue até **Diretórios VC++** e configure:

**Diretórios de Inclusão:**

```
C:\opencv\build\include
```

**Diretórios de Biblioteca:**

```
C:\opencv\build\x64\vc16\lib
```

### 2.3. Vinculador (Linker)

1. Expanda **Vinculador > Entrada**.
2. Em **Dependências Adicionais**, adicione:
   ```
   opencv_world4130d.lib
   ```

> **Nota:** O sufixo `d` é para Debug. Para Release, use `opencv_world4130.lib`.

---

## ▶️ 3. Executando o Teste

1. No Gerenciador de Soluções, clique com o botão direito no projeto e abra a pasta no Gerenciador de Arquivos.
2. Copie os diretórios `src`, `include` e `examples` para a pasta do projeto.
3. Adicione os arquivos `.cpp` ao projeto via **Botão direito > Adicionar > Item Existente...**.
4. Execute com `F5` (Depurador Local do Windows).

**Troubleshooting:** Se falhar com erro sobre `opencv_world4130d.dll` não encontrada, revise o passo 1.1 e reinicie o computador.
