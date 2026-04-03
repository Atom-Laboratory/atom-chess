# 📷 ATOM Chess - Visão Computacional: Teste de Câmera

## 📋 Conteúdo

- [1. Instalação do OpenCV (Windows)](#1-instalação-do-opencv-windows)
- [2. Configuração do Ambiente (VSCode + CMake + MSVC)](#2-configuração-do-ambiente-vscode--cmake--msvc)
- [3. Build do Projeto](#3-build-do-projeto)
- [4. Execução](#4-execução)
- [5. Troubleshooting](#5-troubleshooting)

---

## 🛠️ 1. Instalação do OpenCV (Windows)

Versão recomendada: **4.12+ (pré-compilada para MSVC)**

1. Baixe o OpenCV no repositório oficial:  
   https://github.com/opencv/opencv/releases

2. Extraia em um diretório fixo:
   ```
   D:\opencv\
   ```

3. Confirme a existência do arquivo:
   ```
   D:\opencv\build\x64\vc16\lib\OpenCVConfig.cmake
   ```

---

## ⚙️ 2. Configuração do Ambiente (VSCode + CMake + MSVC)

### 2.1 Pré-requisitos

- Visual Studio 2022 com Desktop development with C++
- VSCode com extensões: CMake Tools, C/C++

### 2.2 Configuração no VSCode

Crie/edite `.vscode/settings.json`:

```json
{
  "cmake.sourceDirectory": "${workspaceFolder}/Software/acvision",
  "cmake.generator": "Ninja",
  "cmake.configureSettings": {
    "OpenCV_DIR": "D:/opencv/build/x64/vc16/lib"
  },
  "cmake.configureOnOpen": true
}
```

### 2.3 Seleção do Toolchain (CRÍTICO)

No VSCode: `Ctrl + Shift + P` → CMake: Select Configure Preset → Selecione `x64 Debug (MSVC)`

### 2.4 Reset de Configuração

`Ctrl + Shift + P` → CMake: Delete Cache and Reconfigure

---

## 🔨 3. Build do Projeto

No terminal do VSCode:
```bash
cmake --build build
```

---

## ▶️ 4. Execução

Executável estará em `build/bin/`. Execute diretamente ou via VSCode.

---

## 🧪 5. Troubleshooting

| Erro | Causa | Solução |
|------|-------|---------|
| `undefined reference to cv::...` | MinGW (g++) + OpenCV MSVC | Selecionar preset `x64 Debug (MSVC)` |
| `cl.exe not found` | MSVC não carregado | Instalar Visual Studio com C++ ou rodar: `"C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat"` |
| `OpenCVConfig.cmake not found` | Caminho incorreto | Verificar: `D:/opencv/build/x64/vc16/lib` |
| DLL não encontrada (`opencv_world*.dll`) | PATH ausente | Adicionar ao PATH: `D:\opencv\build\x64\vc16\bin` e reiniciar sistema |

