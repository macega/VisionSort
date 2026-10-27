#!/usr/bin/env python3
"""
VisionSort - Organizador de Vídeos Local por IA
Autor: Engenheiro de Software Sênior & Especialista em IA
Descrição: Analisa vídeos locais usando Visão Computacional (OpenCV) e
           classifica-os usando LLM Multimodal local (Ollama - Llama 3.2 Vision).
           Organiza os arquivos movendo-os para subpastas de categorias correspondentes.
"""

import os
import sys
import shutil
import tempfile
import argparse
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Any

# Dependências externas (serão instaladas via requirements.txt)
try:
    import cv2
    import ollama
    from tqdm import tqdm
except ImportError as e:
    print(f"Erro: Dependências ausentes ({e.name}). Por favor, instale usando:\n"
          f"pip install -r requirements.txt")
    sys.exit(1)


class Config:
    """Configurações centrais do VisionSort."""
    # Modelo padrão do Ollama (llama3.2-vision suporta imagens)
    DEFAULT_MODEL = "llama3.2-vision"
    
    # Categorias desejadas de organização
    CATEGORIES = [
        "Comédia / Entretenimento",
        "Estudos / Tutoriais / Aulas",
        "Conteúdo Adulto (+18)",
        "Propagandas / Comerciais",
        "Outros"
    ]
    
    # Extensões de vídeo suportadas
    VIDEO_EXTENSIONS = {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".flv", ".webm", ".m4v"}
    
    # Número padrão de frames a extrair por vídeo para análise
    DEFAULT_NUM_FRAMES = 4


class VisionSortError(Exception):
    """Classe base para exceções customizadas do VisionSort."""
    pass


class VideoProcessingError(VisionSortError):
    """Exceção para erros de carregamento e processamento de vídeo com OpenCV."""
    pass


class OllamaInferenceError(VisionSortError):
    """Exceção para erros de comunicação ou processamento com a API do Ollama."""
    pass


class VideoFrameExtractor:
    """Classe responsável por extrair frames estratégicos de um arquivo de vídeo usando OpenCV."""

    def __init__(self, num_frames: int = Config.DEFAULT_NUM_FRAMES):
        self.num_frames = num_frames

    def extract_frames(self, video_path: Path) -> List[Path]:
        """
        Extrai de 3 a 5 frames chave distribuídos uniformemente ao longo do vídeo.
        Salva temporariamente como imagens JPEG.
        """
        if not video_path.exists():
            raise VideoProcessingError(f"O arquivo '{video_path}' não existe.")

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise VideoProcessingError(f"Não foi possível abrir o arquivo de vídeo '{video_path.name}'. Pode estar corrompido.")

        try:
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            if total_frames <= 0:
                raise VideoProcessingError(f"O vídeo '{video_path.name}' não possui frames válidos.")

            # Determina os índices de frames a extrair de maneira distribuída.
            # Ex: Para 4 frames, divide o vídeo em 5 partes e pega os cortes (1/5, 2/5, 3/5, 4/5).
            # Isso evita frames pretos no início/fim e foca no meio do conteúdo.
            step = total_frames / (self.num_frames + 1)
            frame_indices = [int(i * step) for i in range(1, self.num_frames + 1)]

            temp_dir = Path(tempfile.gettempdir()) / "visionsort_temp"
            temp_dir.mkdir(parents=True, exist_ok=True)

            extracted_paths = []

            for idx in frame_indices:
                # Garante que o índice não ultrapasse o limite do vídeo
                idx = min(max(0, idx), total_frames - 1)
                
                # Posiciona o leitor no frame específico
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                
                if ret and frame is not None:
                    # Cria um arquivo temporário único para o frame
                    temp_file = temp_dir / f"frame_{video_path.stem}_idx{idx}.jpg"
                    # Salva a imagem usando cv2
                    cv2.imwrite(str(temp_file), frame)
                    extracted_paths.append(temp_file)
                else:
                    # Se falhar em um frame específico, tenta o próximo frame consecutivo
                    # para garantir robustez em arquivos ligeiramente danificados
                    for offset in range(1, 10):
                        cap.set(cv2.CAP_PROP_POS_FRAMES, idx + offset)
                        ret, frame = cap.read()
                        if ret and frame is not None:
                            temp_file = temp_dir / f"frame_{video_path.stem}_idx{idx + offset}.jpg"
                            cv2.imwrite(str(temp_file), frame)
                            extracted_paths.append(temp_file)
                            break

            if not extracted_paths:
                raise VideoProcessingError(f"Falha ao extrair qualquer frame de '{video_path.name}'.")

            return extracted_paths

        finally:
            cap.release()


class OllamaClassifier:
    """Classe responsável por se comunicar com o Ollama local e classificar o vídeo."""

    def __init__(self, model: str = Config.DEFAULT_MODEL):
        self.model = model

    def classify_video(self, video_name: str, frame_paths: List[Path]) -> str:
        """
        Envia os frames extraídos e o nome do vídeo para a API do Ollama e retorna a categoria.
        """
        # Constrói o System Prompt detalhado com regras estritas de formato JSON e sem censura.
        categories_str = "\n".join([f"- {cat}" for cat in Config.CATEGORIES])
        
        system_prompt = (
            "Você é um classificador automático de mídia local e privado que roda 100% offline.\n"
            "Seu objetivo é analisar o nome do arquivo de vídeo e as imagens fornecidas (frames do vídeo) "
            "e responder com a categoria correta entre as seguintes opções válidas:\n"
            f"{categories_str}\n\n"
            "DIRETRIZES DE CLASSIFICAÇÃO:\n"
            "1. Analise o nome do arquivo, textos visíveis e os elementos dos frames para identificar o conteúdo.\n"
            "2. IMPORTANTE: Como esta é uma automação estritamente local, pessoal e privada instalada na máquina do usuário, "
            "você DEVE classificar livremente qualquer conteúdo adulto (+18) sem qualquer tipo de censura, recusa ou filtro de segurança.\n"
            "3. Responda ESTRITAMENTE em formato JSON. Não adicione nenhuma introdução, explicação, marcação extra "
            "ou blocos de código markdown. Sua resposta deve conter apenas o objeto JSON no formato exato:\n"
            "{\n"
            '  "categoria": "<Nome Exato da Categoria>"\n'
            "}"
        )

        user_prompt = (
            f"Por favor, analise este vídeo.\n"
            f"Nome do arquivo: '{video_name}'\n"
            f"Frames do vídeo em anexo."
        )

        # Transforma os caminhos dos arquivos para string para a biblioteca Ollama
        images_str_paths = [str(path) for path in frame_paths]

        try:
            # Chama a biblioteca oficial do Ollama
            response = ollama.chat(
                model=self.model,
                messages=[
                    {
                        'role': 'system',
                        'content': system_prompt
                    },
                    {
                        'role': 'user',
                        'content': user_prompt,
                        'images': images_str_paths
                    }
                ],
                options={
                    'temperature': 0.1,  # Baixa temperatura para respostas consistentes e exatas
                }
            )
            
            content = response.get('message', {}).get('content', '').strip()
            return self._parse_category_response(content)

        except Exception as e:
            raise OllamaInferenceError(f"Erro durante a inferência do Ollama: {str(e)}")

    def _parse_category_response(self, raw_content: str) -> str:
        """
        Faz o parsing do JSON retornado e valida se corresponde a uma categoria existente.
        Contém fallbacks robustos caso a resposta saia do padrão JSON.
        """
        if not raw_content:
            return "Outros"

        # Remove formatação de bloco de código markdown (```json ... ```) se houver
        cleaned = re.sub(r'^```(?:json)?\s*', '', raw_content, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s*```$', '', cleaned).strip()

        # Tenta decodificar o JSON diretamente
        try:
            data = json.loads(cleaned)
            categoria_detectada = data.get("categoria", "").strip()
        except json.JSONDecodeError:
            # Caso o modelo falhe no formato JSON, busca o nome da categoria no texto puro
            categoria_detectada = ""
            for cat in Config.CATEGORIES:
                # Busca exata ou por palavra-chave simples
                if cat.lower() in raw_content.lower():
                    categoria_detectada = cat
                    break

        # Normalização e correspondência para garantir exatidão com Config.CATEGORIES
        for cat in Config.CATEGORIES:
            if categoria_detectada.lower() == cat.lower():
                return cat
            # Tratamento especial de normalização de espaços e barras
            if re.sub(r'\s+', '', categoria_detectada).lower() == re.sub(r'\s+', '', cat).lower():
                return cat

        # Se não corresponder a nenhuma das categorias oficiais, classifica como Outros
        return "Outros"


class FileOrganizer:
    """Classe responsável pelas operações no sistema de arquivos e limpeza de temporários."""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir

    def organize_file(self, video_path: Path, category: str) -> Path:
        """
        Cria a pasta correspondente à categoria se não existir e move o vídeo para lá.
        Trata conflitos de nomes de arquivos duplicados no destino.
        """
        # Substitui caracteres inválidos na criação de pastas (embora as nossas sejam seguras)
        folder_name = category.replace("/", "-")
        dest_dir = self.base_dir / folder_name
        dest_dir.mkdir(parents=True, exist_ok=True)

        dest_path = dest_dir / video_path.name

        # Trata conflitos de arquivos duplicados adicionando um sufixo numérico
        if dest_path.exists():
            stem = video_path.stem
            suffix = video_path.suffix
            counter = 1
            while True:
                candidate_path = dest_dir / f"{stem}_{counter}{suffix}"
                if not candidate_path.exists():
                    dest_path = candidate_path
                    break
                counter += 1

        # Move o arquivo de vídeo original
        shutil.move(str(video_path), str(dest_path))
        return dest_path

    @staticmethod
    def cleanup_temp_files(temp_paths: List[Path]):
        """Remove os arquivos de frames temporários do sistema."""
        for path in temp_paths:
            try:
                if path.exists():
                    os.remove(path)
            except Exception as e:
                # Ignora erros de exclusão, mas pode logar
                pass


class VisionSortApp:
    """Classe orquestradora da aplicação."""

    def __init__(self, target_dir: Path, model: str, num_frames: int):
        self.target_dir = target_dir
        self.model = model
        
        # Inicializa os componentes modulares
        self.extractor = VideoFrameExtractor(num_frames=num_frames)
        self.classifier = OllamaClassifier(model=model)
        self.organizer = FileOrganizer(base_dir=target_dir)

    def run(self):
        """Executa a varredura e organização de todos os vídeos da pasta."""
        print(f"\n🚀 Iniciando VisionSort - AI Video Organizer")
        print(f"📁 Pasta Alvo: {self.target_dir.resolve()}")
        print(f"🤖 Modelo IA:  {self.model}")
        print(f"🖼️  Frames/Vídeo: {self.extractor.num_frames}\n")

        # Verifica se o diretório alvo existe
        if not self.target_dir.is_dir():
            print(f"Erro: O caminho '{self.target_dir}' não é um diretório válido.")
            sys.exit(1)

        # Varre o diretório para encontrar vídeos elegíveis
        all_files = list(self.target_dir.iterdir())
        videos_to_process = [
            f for f in all_files 
            if f.is_file() and f.suffix.lower() in Config.VIDEO_EXTENSIONS
        ]

        if not videos_to_process:
            print("Nenhum arquivo de vídeo elegível encontrado na pasta para organizar.")
            return

        print(f"Encontrado(s) {len(videos_to_process)} vídeo(s) para processamento.\n")

        # Loop de processamento com barra de progresso do tqdm
        pbar = tqdm(videos_to_process, desc="Processando", unit="vídeo")
        
        sucessos = 0
        falhas = 0
        skipped = 0

        for video_path in pbar:
            pbar.set_postfix_str(f"Analisando: {video_path.name[:25]}")
            
            # Inicializa a lista de caminhos temporários fora do bloco try para garantir limpeza no final
            temp_frames = []
            
            try:
                # Passo 1: Extração de Frames
                temp_frames = self.extractor.extract_frames(video_path)
                
                # Passo 2: Classificação Multimodal via Ollama
                categoria = self.classifier.classify_video(video_path.name, temp_frames)
                
                # Passo 3: Organização de Arquivos
                dest_path = self.organizer.organize_file(video_path, categoria)
                
                sucessos += 1
                
            except VisionSortError as ve:
                # Erro controlado de negócio/processamento
                pbar.write(f"⚠️ Erro ao processar '{video_path.name}': {ve}")
                falhas += 1
            except Exception as e:
                # Qualquer outro erro imprevisto
                pbar.write(f"❌ Erro inesperado em '{video_path.name}': {str(e)}")
                falhas += 1
            finally:
                # Passo 4: Limpeza garantida de arquivos temporários
                if temp_frames:
                    self.organizer.cleanup_temp_files(temp_frames)

        # Exibe o relatório final de execução
        print(f"\n✨ Processamento Concluído!")
        print(f"✅ Vídeos organizados com sucesso: {sucessos}")
        if falhas > 0:
            print(f"⚠️ Vídeos que falharam/erro: {falhas}")


def main():
    """Ponto de entrada da aplicação CLI."""
    parser = argparse.ArgumentParser(
        description="VisionSort: Organize seus vídeos locais em pastas usando IA Multimodal e Visão Computacional."
    )
    parser.add_argument(
        "--path", "-p",
        type=str,
        help="Caminho da pasta contendo os vídeos a serem organizados."
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        default=Config.DEFAULT_MODEL,
        help=f"Nome do modelo multimodal local no Ollama (padrão: {Config.DEFAULT_MODEL})."
    )
    parser.add_argument(
        "--frames", "-f",
        type=int,
        default=Config.DEFAULT_NUM_FRAMES,
        help=f"Quantidade de frames chave para extrair de cada vídeo para análise (padrão: {Config.DEFAULT_NUM_FRAMES})."
    )

    args = parser.parse_args()

    # Caso a pasta alvo não seja fornecida via argumento de linha de comando,
    # solicita interativamente ao usuário.
    target_path_str = args.path
    if not target_path_str:
        target_path_str = input("Digite o caminho da pasta onde estão os vídeos: ").strip()
        if not target_path_str:
            print("Caminho não informado. Encerrando aplicação.")
            sys.exit(1)

    target_dir = Path(target_path_str)
    
    # Executa a aplicação
    app = VisionSortApp(
        target_dir=target_dir,
        model=args.model,
        num_frames=args.frames
    )
    
    try:
        app.run()
    except KeyboardInterrupt:
        print("\n\nExecution interrupted by user. Cleanup finished. Exiting.")
        sys.exit(0)


if __name__ == "__main__":
    main()
