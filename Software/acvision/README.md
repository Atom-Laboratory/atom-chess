# 📷 ATOM Chess - Visão Computacional

## 📋 Sumário
1. [Requisitos de Sistema](#1-requisitos-de-sistema)
2. [Instalação do OpenCV (sem compilar da fonte)](#2-instalação-do-opencv-sem-compilar-da-fonte)
3. [Configuração do VSCode (Workspace & CMake Tools)](#3-configuração-do-vscode-workspace--cmake-tools)
4. [Build e execução via VSCode](#4-build-e-execução-via-vscode)
5. [Troubleshooting restrito ao VSCode](#5-troubleshooting-restrito-ao-vscode)

---

## 🧩 1. Requisitos de Sistema

### 🪟 Ambiente Windows (sem a IDE do Visual Studio)
- **Compilador:** [Build Tools for Visual Studio 2022](https://visualstudio.microsoft.com/pt-br/visual-cpp-build-tools/)  
   Instale **apenas** o pacote **Desktop development with C++** (MSVC sem a IDE completa).
- **Editor:** VSCode
- **Extensões VSCode:**
   - `C/C++` (Microsoft)
   - `CMake Tools` (Microsoft)
- **Ninja Build** (opcional, recomendado para builds mais rápidos):
   - Baixe o `.exe` de extração nas [releases do Ninja](https://github.com/ninja-build/ninja/releases)

### 🐧 Ambiente Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install build-essential cmake ninja-build libopencv-dev
```

---

## 🛠️ 2. Instalação do OpenCV (sem compilar da fonte)

### 🪟 Windows (binários MSVC)
1. Baixe o `.exe` de extração nas [releases do OpenCV](https://github.com/opencv/opencv/releases).
2. Extraia em um caminho curto, por exemplo: `D:\opencv\`.
3. Verifique se o arquivo abaixo existe:
    `D:\opencv\build\x64\vc16\lib\OpenCVConfig.cmake`

### 🐧 Linux (APT)
```bash
sudo apt install libopencv-dev
```

---

## ⚙️ 3. Configuração do VSCode (Workspace & CMake Tools)

No VSCode, o setup é feito via **CMake Tools** + variável de ambiente.  
Evite hardcode de caminhos no projeto.

### 🔧 3.1 Variável de ambiente (obrigatório)

Cada desenvolvedor deve configurar o caminho do OpenCV localmente.

#### 🪟 Windows (CMD)
```cmd
setx OpenCV_DIR "D:\opencv\build\x64\vc16\lib"
```

Adicione manualmente ao PATH do sistema:

D:\opencv\build\x64\vc16\bin

Reinicie o VSCode após executar o comando.

#### 🐧 Linux (bash)
```bash
echo 'export OpenCV_DIR=/usr/lib/x86_64-linux-gnu/cmake/opencv4' >> ~/.bashrc
source ~/.bashrc
```

### 🧩 3.2 Configuração do VSCode

Crie ou edite `.vscode/settings.json`:

```json
{
   "cmake.sourceDirectory": "${workspaceFolder}/Software/acvision",
   "cmake.generator": "Ninja",
   "cmake.configureOnOpen": true
}
```

### ⚙️ 3.3 Seleção do preset (crítico)

No VSCode:

`Ctrl + Shift + P` → **CMake: Select Configure Preset**

Selecione:
- **Windows:** `x64 Debug (MSVC)`
- **Linux:** `default` / `gcc`

### 🔄 3.4 Reconfiguração

Sempre que mudar ambiente ou compilador:

`Ctrl + Shift + P` → **CMake: Delete Cache and Reconfigure**

> **Nota:** O `cmake.configureEnvironment` pode injetar o path do OpenCV no processo de configuração da extensão, dispensando flags no terminal.

### 🧰 3.5 Seleção do compilador (Kits)

1. `Ctrl + Shift + P` → **CMake: Scan for Kits**
2. `Ctrl + Shift + P` → **CMake: Select a Kit**
3. Escolha:
    - **Windows:** `Visual Studio Build Tools 2022 Release - amd64` (ou `x86_amd64`)
    - **Linux:** `GCC`

---

## 🔨 4. Build e execução via VSCode

1. **Configurar:** `Ctrl + Shift + P` → **CMake: Configure** (gera o diretório `build/`).
2. **Buildar:** `F7` ou clique em **[Build]** na barra inferior.
3. **Executar:** `Shift + F5` ou clique em **[Run]** (ícone de play). O executável abre no terminal integrado.

Se preferir build pelo terminal integrado:
```bash
cmake -G Ninja -S . -B build -A x64
cmake --build build
```
e dentro da pasta acvision:
```bash
./build/acvision
```
---

## 🧪 5. Troubleshooting restrito ao VSCode

| Sintoma | Causa / Resolução |
| :--- | :--- |
| `cl.exe not found` ou erro de Kit | O VSCode não encontrou o MSVC. Confirme a instalação do **Build Tools for C++**, rode **CMake: Scan for Kits** e selecione o kit correto. |
| `undefined reference to cv::...` no Windows | **Erro de ABI:** foi selecionado kit MinGW/GCC (`gcc.exe`). O OpenCV baixado funciona com MSVC (`cl.exe`). Troque o Kit no VSCode. |
| `OpenCV_DIR-NOTFOUND` | `OpenCV_DIR` está incorreto. Aponte para a pasta que contém `OpenCVConfig.cmake`. |
| Erro de DLL (`opencv_world*.dll`) ao clicar em Run | O build ocorreu, mas o Windows não encontra a DLL em runtime. Adicione `D:\opencv\build\x64\vc16\bin` ao **PATH** e reinicie o VSCode. |
