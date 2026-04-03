# 📷 ATOM Chess - Visão Computacional

## 📋 Sumário
1. [Requisitos de Sistema](#1-requisitos-de-sistema)
2. [Instalação do OpenCV (Sem compilar da fonte)](#2-instalação-do-opencv-sem-compilar-da-fonte)
3. [Configuração do VSCode (Workspace & CMake Tools)](#3-configuração-do-vscode-workspace--cmake-tools)
4. [Build e Execução via VSCode](#4-build-e-execução-via-vscode)
5. [Troubleshooting Restrito ao VSCode](#5-troubleshooting-restrito-ao-vscode)

---

## 🧩 1. Requisitos de Sistema

### 🪟 Ambiente Windows (Sem a IDE do Visual Studio)
* **Compilador:** [Build Tools for Visual Studio 2022](https://visualstudio.microsoft.com/pt-br/visual-cpp-build-tools/) (Instale **apenas** o pacote *Desktop development with C++*. Isso instala o MSVC sem a IDE pesada).
* **IDE:** VSCode.
* **Extensões VSCode:** * `C/C++` (Microsoft)
  * `CMake Tools` (Microsoft)

### 🐧 Ambiente Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install build-essential cmake ninja-build libopencv-dev
```

---

## 🛠️ 2. Instalação do OpenCV (Sem compilar da fonte)

### 🪟 Windows (Binários MSVC)
1. Baixe o `.exe` de extração nas [Releases do OpenCV](https://github.com/opencv/opencv/releases).
2. Extraia na raiz para evitar problemas de path. Ex: `D:\opencv\`
3. Garanta que este arquivo existe:
   `D:\opencv\build\x64\vc16\lib\OpenCVConfig.cmake`

### 🐧 Linux (Apt)
```bash
sudo apt install libopencv-dev
```

---

## ⚙️ 3. Configuração do VSCode (Workspace & CMake Tools)

No VSCode, todo o setup é feito via `.vscode/settings.json` e pela interface do CMake Tools. Esqueça terminais externos.

Crie ou edite o arquivo `.vscode/settings.json` na raiz do seu projeto:

```json
{
  "cmake.sourceDirectory": "${workspaceFolder}/Software/acvision",
  "cmake.generator": "Ninja",
  "cmake.configureOnOpen": true,
  "cmake.configureEnvironment": {
    "OpenCV_DIR": "D:/opencv/build/x64/vc16/lib"
  }
}
```
*Nota: O `cmake.configureEnvironment` injeta o path do OpenCV direto no processo de configuração da extensão, dispensando flags no terminal.*

### Seleção do Compilador (Kits)
É aqui que o VSCode assume o controle.
1. Pressione `Ctrl + Shift + P` → digite **CMake: Scan for Kits** (para o VSCode achar o MSVC ou GCC).
2. Pressione `Ctrl + Shift + P` → digite **CMake: Select a Kit**.
3. Escolha:
   * **Windows:** `Visual Studio Build Tools 2022 Release - amd64` (ou `x86_amd64`).
   * **Linux:** `GCC`.

---

## 🔨 4. Build e Execução via VSCode

Toda a interação agora é feita pela barra inferior do VSCode ou por atalhos:

1. **Configurar:** `Ctrl + Shift + P` → **CMake: Configure** (Isso gera o diretório `/build`).
2. **Buildar:** `F7` ou clique em **[Build]** na barra inferior do VSCode.
3. **Executar:** `Shift + F5` ou clique em **[Run]** (ícone de play na barra inferior). O executável será lançado no terminal integrado.

Se preferir o terminal integrado para o build:
```bash
cmake --build build
```

---

## 🧪 5. Troubleshooting Restrito ao VSCode

| Sintoma | Causa / Resolução |
| :--- | :--- |
| `cl.exe not found` ou erro de Kit | O VSCode não achou o MSVC. Certifique-se de que instalou o **Build Tools for C++**. Rode `CMake: Scan for Kits` e selecione o kit correto na barra inferior. |
| `undefined reference to cv::...` no Windows | **Erro fatal de ABI:** Você selecionou o kit do MinGW/GCC (gcc.exe). O OpenCV baixado só funciona com o kit do MSVC (`cl.exe`). Troque o Kit no VSCode. |
| `OpenCV_DIR-NOTFOUND` | O path no `settings.json` está errado. O caminho DEVE usar barras normais `/` e apontar para a pasta que contém o `OpenCVConfig.cmake`. |
| Erro de DLL (`opencv_world*.dll`) ao clicar em Run | O VSCode compilou, mas o Windows não acha a DLL na hora de rodar. Adicione `D:\opencv\build\x64\vc16\bin` na variável de ambiente **PATH** do seu Windows e **reinicie o VSCode**. |