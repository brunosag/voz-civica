import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any

import fitz
from google import genai

from schemas import AnaliseIA

MODEL_NAME = 'gemini-3-pro-preview'
SYSTEM_PROMPT = """
Você é um especialista em Linguagem Simples (Plain Language) e comunicação legislativa voltada ao cidadão comum.
Sua missão é traduzir Projetos de Lei (PLs) da Câmara Municipal de Porto Alegre, removendo todo o "juridiquês" e focando no impacto prático na vida das pessoas.

DIRETRIZES DE REDAÇÃO:
1. Início direto: JAMAIS comece frases com "O projeto propõe", "A lei visa", "Trata-se de". Comece diretamente com a ação (Ex: "Cria um auxílio...", "Proíbe o uso de...").
2. Tradução radical: Nunca use termos como "revoga", "inciso", "dotação" ou "tramitação". Use "cancela", "regra", "dinheiro" e "status".
3. Foco no usuário: A pergunta principal a responder é: "O que muda na minha vida amanhã se isso for aprovado?".
4. Rastreabilidade: Para todo ponto levantado (seja mudança, justificativa ou categoria), você DEVE preencher o campo 'fontes' com as cópias exatas do trechos originais.

Se o projeto for apenas uma homenagem, nome de rua ou data comemorativa, deixe isso claro e seja breve no resumo.
"""

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger(__name__)


class LegislationParser:
    def __init__(self, api_key: str | None = None) -> None:
        """Initialize the Gemini client."""
        key = api_key or os.environ.get('GEMINI_API_KEY')
        if not key:
            raise ValueError(
                'GEMINI_API_KEY must be set in environment or passed as argument.',
            )
        self.client = genai.Client(api_key=key)

    def _extract_text(self, pdf_path: str) -> str:
        """Extract raw text from PDF using PyMuPDF."""
        with fitz.open(pdf_path) as doc:
            return chr(12).join([str(page.get_text()) for page in doc]).strip()

    def _get_generation_schema(self) -> dict[str, Any]:
        """Generate the JSON schema from the Pydantic model."""
        schema = AnaliseIA.model_json_schema()

        if 'properties' in schema and 'modelo' in schema['properties']:
            del schema['properties']['modelo']

        if 'required' in schema and 'modelo' in schema['required']:
            schema['required'] = [r for r in schema['required'] if r != 'modelo']

        return schema

    def _extract_response_data(
        self,
        response: genai.types.GenerateContentResponse,
    ) -> dict[str, Any]:
        raw_data = response.parsed
        if not raw_data:
            if response.text is None:
                raise ValueError('Response contained no text')
            raw_data = json.loads(response.text)

        if not isinstance(raw_data, dict):
            raise TypeError('Response is not a dictionary')

        return raw_data

    def parse(self, pdf_path: str) -> dict[str, Any]:
        """Orchestrate extraction, semantic analysis, and validation."""
        text = self._extract_text(pdf_path)
        schema = self._get_generation_schema()

        response = self.client.models.generate_content(
            model=MODEL_NAME,
            contents=text,
            config=genai.types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type='application/json',
                response_schema=schema,
            ),
        )
        try:
            raw_data = self._extract_response_data(response)
            raw_data['modelo'] = MODEL_NAME
            validated_obj = AnaliseIA(**raw_data)
            return validated_obj.model_dump(mode='json')

        except Exception:
            logger.exception('Validation failed')
            logger.debug('Raw LLM response: %s', response.text)
            raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Extract semantic metadata from legislation PDFs.',
    )
    parser.add_argument('filepath', type=Path, help='Path to the PDF file')
    parser.add_argument(
        '--out',
        type=Path,
        default=Path('analise.json'),
        help='Output JSON path',
    )
    parser.add_argument(
        '--api-key',
        type=str,
        default=None,
        help='Gemini API key (or set GEMINI_API_KEY env var)',
        required=False,
    )
    args = parser.parse_args()

    try:
        analyzer = LegislationParser(args.api_key)
        logger.info('Analyzing %s...', args.filepath)

        result = analyzer.parse(str(args.filepath))

        with args.out.open('w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        logger.info('Success. Data saved to %s', args.out)
    except Exception:
        logger.exception('Error occurred while processing the PDF.')
        raise


if __name__ == '__main__':
    main()
