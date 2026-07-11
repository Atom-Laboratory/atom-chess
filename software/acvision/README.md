# 📷 ATOM Chess — Visão Computacional

## 📋 Sumário

1. [Requisitos de Sistema](#-1-requisitos-de-sistema)  
2. [OpenCV (Windows)](#️-2-opencv-windows)  
3. [Configuração do Ambiente (MSVC)](#️-3-configuração-do-ambiente-msvc)  
4. [Build e Execução via Terminal](#-4-build-e-execução-via-terminal)  
5. [Fluxo Diário de Desenvolvimento](#-5-fluxo-diário-de-desenvolvimento)  
6. [Troubleshooting](#-6-troubleshooting)

---

## 🧩 1. Requisitos de Sistema

### Windows

- Visual Studio Build Tools 2022 (C++)
- CMake instalado no `PATH`
- Ninja (opcional)
- VSCode como editor

**Extensão recomendada:**

- C/C++ (Microsoft)

### Linux

#### Debian Distributions:

```bash
sudo apt update
sudo apt install build-essential cmake ninja-build libopencv-dev
```

#### Arch:

```bash
sudo pacman -Syu
pacman -S --needed base-devel cmake ninja opencv
```


---

## 🛠️ 2. OpenCV (Windows)

Baixe o OpenCV pré-compilado e extraia em:

```text
D:\opencv
```

Verifique se existe:

```text
D:\opencv\build\x64\vc16\lib\OpenCVConfig.cmake
```

### Variável de ambiente (`OpenCV_DIR`)

```bat
setx OpenCV_DIR "D:\opencv\build\x64\vc16"
```

Adicione também ao `PATH`:

```text
D:\opencv\build\x64\vc16\bin
```

> Reinicie o terminal após essas alterações.

---

## ⚙️ 3. Configuração do Ambiente (MSVC)

Antes de compilar, no cmd, execute:

```bat
"C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"
```

Teste com:

```bat
cl
```

Se a versão do compilador aparecer, está correto.

### 📁 Estrutura do projeto

```text
Software/acvision/
├── CMakeLists.txt
├── src/
├── include/
└── build/
```

---

## 🔨 4. Build e Execução via Terminal

Entre no projeto:

```bat
cd Software/acvision
```

Configure:

```bat
cmake --preset debug
```

Compile:

```bat
cmake --build build
```

Localize o executável:

```bat
dir build /s *.exe
```

Execute:

```bat
build\Debug\nome_do_executavel.exe
```

---

## 🚀 5. Fluxo Diário de Desenvolvimento

Sempre que abrir o projeto:

```bat
"C:\Program Files\Microsoft Visual Studio\18\Community\VC\Auxiliary\Build\vcvars64.bat"
cd Software/acvision
cmake --build build
build\Debug\nome_do_executavel.exe
```

---

## 🧪 6. Troubleshooting

### `cl` não reconhecido

MSVC não foi carregado. Execute `vcvars64.bat`.

### `OpenCV_DIR` errado

Deve apontar para a pasta que contém `OpenCVConfig.cmake`.

### Erro de DLL do OpenCV

Adicione ao `PATH`:

```text
D:\opencv\build\x64\vc16\bin
```

### Erro `LNK` / `cv::`

Compilador incorreto. Use **MSVC (`cl.exe`)**, nunca MinGW.

### `cmake` não encontrado

CMake não está no `PATH` do sistema.

---

## ✅ Regra final

Não usar **CMake Tools** do VSCode.  
Todo build deve ser feito via terminal com MSVC ativo.