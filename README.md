# 🎥 VisionSort (ou o nome que escolher)

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org)
[![Ollama](https://img.shields.io/badge/Ollama-Local%20AI-orange.svg)](https://ollama.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

O **VisionSort** é um organizador automático de mídia local que utiliza Inteligência Artificial Multimodal rodando 100% offline. Ele analisa seus vídeos através de Visão Computacional, identifica o contexto do conteúdo e os move automaticamente para pastas categorizadas.

---

## 🎯 Por que usar?

Diferente de soluções baseadas em nuvem (como OpenAI ou Google Gemini), o VisionSort utiliza o **Ollama** com modelos Vision locais (como `llama3.2-vision` ou `llava`). Isso garante:

*   **Privacidade Total:** Nenhum frame, título ou dado do seu vídeo sai da sua máquina ou servidor.
*   **Custo Zero:** Sem cobranças por tokens ou assinaturas de API.
*   **Sem Censura/Filtros:** Perfeito para organizar qualquer tipo de mídia privada e local sem bloqueios corporativos de segurança.

---

## ⚡ Como Funciona?

```text
[Pasta de Vídeos] 
       │
       ▼
[OpenCV] ───► Extrai 3-5 frames estratégicos por vídeo
       │
       ▼
[Ollama API] ───► Analisa os frames + nome do arquivo usando Llama 3.2 Vision
       │
       ▼
[JSON Parser] ───► Retorna estritamente a categoria ideal
       │
       ▼
[Sistema de Arquivos] ───► Cria a pasta (se não existir) e move o vídeo original