import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any

import fitz
from google import genai
from google.genai import types

MODEL_NAME = 'gemini-3-pro-preview'
SYSTEM_PROMPT = """
Você é um especialista em Linguagem Simples (Plain Language) e comunicação legislativa voltada ao cidadão comum.
Sua missão é traduzir Projetos de Lei (PLs) da Câmara Municipal de Porto Alegre, removendo todo o "juridiquês" e focando no impacto prático na vida das pessoas.

DIRETRIZES DE REDAÇÃO:
1. Início Direto: JAMAIS comece frases com "O projeto propõe", "A lei visa", "Trata-se de" ou "O texto diz". Comece diretamente com a ação.
   - Errado: "O projeto cria um auxílio..."
   - Certo: "Cria um auxílio financeiro..."
2. Tradução Radical: Nunca use termos como "revoga", "inciso", "dotação" ou "tramitação". Use "cancela", "regra", "dinheiro" e "status".
3. Neutralidade: Você explica, não opina. Atribua a justificativa ao autor ("Segundo o autor...").
4. Foco no Usuário: A pergunta principal a responder é: "O que muda na minha vida amanhã se isso for aprovado?".
5. Rastreabilidade: Para cada ponto levantado, extraia os trechos exatos do texto original que servem de evidência.

Se o projeto for apenas uma homenagem, nome de rua ou data comemorativa, deixe isso claro e seja breve.
"""

LEGISLATION_SCHEMA = {
    'type': 'object',
    'properties': {
        'titulo': {
            'type': 'string',
            'description': "Título curto e chamativo (máx 10 palavras) explicando o projeto. Ex: 'Proibição de fogos de artifício com ruído'.",
        },
        'resumo': {
            'type': 'string',
            'description': "Uma única frase simples explicando o objetivo central. Comece diretamente com o verbo (ex: 'Cria', 'Proíbe', 'Autoriza'), sem citar 'o projeto'.",
        },
        'mudancas': {
            'type': 'array',
            'description': 'Lista de mudanças práticas propostas pelo projeto.',
            'items': {
                'type': 'object',
                'properties': {
                    'texto_simplificado': {
                        'type': 'string',
                        'description': "A mudança explicada em linguagem simples. Ex: 'A multa passa a ser R$ 200'.",
                    },
                    'trechos_originais': {
                        'type': 'array',
                        'description': 'Lista de strings contendo os trechos exatos da lei que fundamentam essa mudança (sem uso de [...]).',
                        'items': {'type': 'string'},
                    },
                },
                'required': ['texto_simplificado', 'trechos_originais'],
            },
        },
        'justificativas': {
            'type': 'array',
            'description': 'Lista dos principais argumentos do autor.',
            'items': {
                'type': 'object',
                'properties': {
                    'texto_simplificado': {
                        'type': 'string',
                        'description': 'O argumento do autor em linguagem simples.',
                    },
                    'trechos_originais': {
                        'type': 'array',
                        'description': 'Lista de strings contendo os trechos exatos da justificativa original que fundamentam esse argumento.',
                        'items': {'type': 'string'},
                    },
                },
                'required': ['texto_simplificado', 'trechos_originais'],
            },
        },
        'categorias': {
            'type': 'array',
            'description': 'Lista de categorias temáticas onde o projeto se encaixa, com suas evidências no texto.',
            'items': {
                'type': 'object',
                'properties': {
                    'nome': {
                        'type': 'string',
                        'enum': [
                            'Saúde',
                            'Educação',
                            'Transporte',
                            'Segurança',
                            'Assistência Social',
                            'Urbanismo',
                            'Meio Ambiente',
                            'Causa Animal',
                            'Cultura e Turismo',
                            'Esporte e Lazer',
                            'Direitos Humanos',
                            'Ciência e Tecnologia',
                            'Orçamento e Finanças',
                            'Servidor Público',
                            'Homenagens/Datas Comemorativas',
                            'Administração Pública',
                        ],
                    },
                    'trechos_originais': {
                        'type': 'array',
                        'description': 'Trechos do texto que justificam por que esta categoria foi escolhida.',
                        'items': {'type': 'string'},
                    },
                },
                'required': ['nome', 'trechos_originais'],
            },
        },
    },
    'required': [
        'titulo',
        'resumo',
        'mudancas',
        'justificativas',
        'categorias',
    ],
}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger(__name__)


class LegislationParser:
    def __init__(self, api_key: str | None = None) -> None:
        """Initialize the Gemini client. Expects API key via arg or env var."""
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

    def parse(self, pdf_path: str) -> dict[str, Any]:
        """Orchestrate extraction and semantic analysis."""
        text = self._extract_text(pdf_path)

        response = self.client.models.generate_content(
            model=MODEL_NAME,
            contents=text,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                response_mime_type='application/json',
                response_schema=LEGISLATION_SCHEMA,
            ),
        )

        # Return parsed object or fallback to raw text parsing if wrapper fails
        return response.parsed if response.parsed else json.loads(response.text)  # type: ignore[attr-defined]


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Extract semantic metadata from legislation PDFs.',
    )
    parser.add_argument('filepath', type=Path, help='Path to the PDF file')
    parser.add_argument(
        '--out',
        type=Path,
        default=Path('analysis.json'),
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
        result = analyzer.parse(args.filepath)

        with args.out.open('w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        logger.info('Success. Data saved to %s', args.out)
    except Exception:
        logger.exception('Error occurred while processing the PDF.')
        raise


if __name__ == '__main__':
    main()
