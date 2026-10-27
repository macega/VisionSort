# 🎥 VisionSort

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
<<<<<<< HEAD
```

---

## 🛠️ Requisitos e Configuração

### 1. Requisitos Prévios
*   Python 3.9 ou superior instalado.
*   [Ollama](https://ollama.com) instalado e rodando em sua máquina.

### 2. Configurar o Ollama e Baixar o Modelo
Para rodar a inferência localmente, você precisa do modelo multimodal. Recomendamos o **Llama 3.2 Vision** (padrão do app) ou o **LLaVA**.

Abra o seu terminal/prompt de comando e baixe o modelo desejado utilizando o comando abaixo:

```bash
# Baixar e inicializar o Llama 3.2 Vision (11B)
ollama run llama3.2-vision
```

*Nota: Se o Ollama já estiver instalado, você também pode usar `ollama pull llama3.2-vision` para apenas fazer o download do modelo.*

> [!TIP]
> Caso a sua máquina possua limitações de hardware (como pouca VRAM de GPU dedicada), certifique-se de que o Ollama está configurado para compartilhar a execução entre CPU/GPU de forma estável.

### 3. Instalar Dependências do Python
Com o terminal aberto na raiz do projeto, instale os pacotes listados no `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## 🚀 Como Executar a Aplicação

Para iniciar a organização automática dos vídeos, execute o script passando a pasta de destino:

```bash
python organizador_local.py --path "/caminho/para/sua/pasta/de/videos"
```

Se preferir, você pode rodar o comando sem argumentos, e o script solicitará o caminho de forma interativa no prompt:
```bash
python organizador_local.py
```

### Argumentos opcionais na CLI:
*   `--path` ou `-p`: Caminho absoluto/relativo para a pasta que contém os vídeos a serem organizados.
*   `--model` ou `-m`: Nome do modelo vision local no Ollama (Padrão: `llama3.2-vision`).
*   `--frames` ou `-f`: Quantidade de frames chave extraídos por vídeo para análise da IA (Padrão: `4`, recomendado entre `3` e `5`).

**Exemplo customizado:**
```bash
python organizador_local.py --path "./MeusVideos" --model llava --frames 3
```

---

## 📂 Categorias de Organização
O script criará subpastas correspondentes automaticamente caso elas não existam na pasta alvo e moverá os arquivos para uma delas:
1.  **`Comédia - Entretenimento`**
2.  **`Estudos - Tutoriais - Aulas`**
3.  **`Conteúdo Adulto (+18)`**
4.  **`Propagandas - Comerciais`**
5.  **`Outros`** (Categoria padrão caso a mídia não se enquadre em nenhuma das anteriores ou ocorra algum erro na análise)

---

## 🔒 Privacidade e Automação Sem Filtros
O prompt de sistema do VisionSort foi programado para instruir o modelo vision local a classificar livremente qualquer conteúdo, inclusive **Conteúdo Adulto (+18)**, ignorando as políticas de censura corporativas comerciais usuais da web. Como o modelo roda 100% em hardware local e privado, você tem a garantia de que as mídias nunca serão enviadas para servidores terceiros e que a classificação ocorrerá sem recusas ou julgamento moral por parte do LLM.O prompt de sistema do VisionSort foi programado para instruir o modelo vision local a classificar livremente qualquer conteúdo, inclusive **Conteúdo Adulto (+18)**, ignorando as políticas de censura corporativas comerciais usuais da web. Como o modelo roda 100% em hardware local e privado, você tem a garantia de que as mídias nunca serão enviadas para servidores terceiros e que a classificação ocorrerá sem recusas ou julgamento moral por parte do LLM.
=======
>>>>>>> fd94739df67267d79e360d4881eabf440bd7b868
