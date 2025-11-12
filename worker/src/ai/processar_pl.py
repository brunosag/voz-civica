import getpass
import json
from io import StringIO

import google.generativeai as genai

# Importações necessárias para ler PDFs
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfinterp import PDFPageInterpreter, PDFResourceManager
from pdfminer.pdfpage import PDFPage


def setup_api_key():
    """Configura a API Key do Google de forma segura."""
    try:
        api_key = 'AIzaSyAazCtcklZxQNNpzi6F_9YINp615IQ_zYw'
        print('API Key carregada da variável de ambiente.')
    except KeyError:
        print('GOOGLE_API_KEY não encontrada no ambiente.')
        api_key = getpass.getpass('Digite sua Google API Key: ')

    genai.configure(api_key=api_key)


def extrair_texto_do_pdf(caminho_do_pdf: str) -> str | None:
    """Extrai o texto de um arquivo PDF usando pdfminer.six."""
    resource_manager = PDFResourceManager()
    fake_file_handle = StringIO()
    converter = TextConverter(resource_manager, fake_file_handle, laparams=LAParams())
    page_interpreter = PDFPageInterpreter(resource_manager, converter)

    print(f'Iniciando leitura do PDF: {caminho_do_pdf}...')
    try:
        with open(caminho_do_pdf, 'rb') as fh:
            for page in PDFPage.get_pages(fh, caching=True, check_extractable=True):
                page_interpreter.process_page(page)
        text = fake_file_handle.getvalue()
    except FileNotFoundError:
        print(f"Erro: O arquivo '{caminho_do_pdf}' não foi encontrado.")
        return None
    except Exception as e:
        print(f'Erro ao processar o PDF: {e}')
        return None

    converter.close()
    fake_file_handle.close()

    if text:
        print('Texto extraído do PDF com sucesso.')
        return text
    else:
        print('Não foi possível extrair texto do PDF.')
        return None


def gerar_resumo_explicavel_xsum(texto_original: str) -> dict | None:
    """
    Envia o texto para a API Gemini e solicita o JSON estruturado
    usando ENUMs para normalização (v4).
    """

    # 1. O PROMPT (LIMPO)
    # Instruímos a IA a *selecionar* das categorias fixas.
    prompt_de_sistema = """
    Você é um analista legislativo e especialista em comunicação cívica.
    Sua tarefa é analisar um Projeto de Lei (PL) e extrair metadados semânticos.
    
    Analise o texto completo para extrair as seguintes informações:
    
    1.  'resumo_abstrativo': O que a lei faz.
    2.  'justificativa_resumida': O porquê da lei (baseado na 'Exposição de Motivos').
    3.  'evidencias': O mapeamento (XAI) do resumo aos artigos.
    4.  'entidades_envolvidas': Órgãos da prefeitura ou outros citados como responsáveis.
    5.  'prazo_vigencia': Quando a lei começa a valer ou sua duração.
    
    Para os campos 'verbo_acao', 'impacto_orcamentario', 'areas_tematicas' e 
    'publico_alvo', selecione a(s) categoria(s) mais apropriada(s) 
    da lista de opções (enums) fornecida no schema.
    """

    # 2. O SCHEMA (FIXO) - v4
    # Usamos "enum" para forçar a seleção de categorias fixas.
    schema_json_fixo = {
        'type': 'object',
        'properties': {
            # --- Campos de Texto Livre ---
            'resumo_abstrativo': {
                'type': 'string',
                'description': 'Resumo do que a lei faz (foco nos artigos).',
            },
            'justificativa_resumida': {
                'type': 'string',
                'description': "Resumo do porquê a lei é proposta (foco na 'Exposição de Motivos').",
            },
            'evidencias': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'properties': {
                        'ponto_resumo': {'type': 'string'},
                        'citacao_original': {'type': 'string'},
                    },
                    'required': ['ponto_resumo', 'citacao_original'],
                },
            },
            'entidades_envolvidas': {
                'type': 'array',
                'items': {'type': 'string'},
                'description': "Órgãos ou entidades responsáveis pela execução da lei (ex: 'Sistema de saúde', 'Assistência social').",
            },
            'prazo_vigencia': {
                'type': 'string',
                'description': "Quando a lei entra em vigor ou sua duração (ex: 'Duração permanente', '90 dias após publicação').",
            },
            # --- Campos de Categoria Fixa (ENUM) ---
            'verbo_acao': {
                'type': 'string',
                'description': 'Ação principal do PL.',
                'enum': [
                    'Criação',
                    'Alteração',
                    'Revogação',
                    'Proibição',
                    'Nomeação',
                    'Autorização',
                    'Declaração',
                    'Instituição',
                    'Outro',
                ],
            },
            'impacto_orcamentario': {
                'type': 'string',
                'description': 'Análise do impacto financeiro.',
                'enum': [
                    'Cria Despesa',
                    'Aumenta Arrecadação',
                    'Não Gera Despesa',
                    'Impacto Neutro',
                    'Não Especificado',
                ],
            },
            'areas_tematicas': {
                'type': 'array',
                'description': 'Lista de temas que o PL aborda.',
                'items': {
                    'type': 'string',
                    'enum': [
                        'Saúde',
                        'Educação',
                        'Transporte',
                        'Meio Ambiente',
                        'Urbanismo',
                        'Assistência Social',
                        'Direitos Humanos',
                        'Cultura',
                        'Esporte',
                        'Finanças',
                        'Administração',
                        'Segurança',
                        'Tecnologia',
                        'Habitação',
                    ],
                },
            },
            'publico_alvo': {
                'type': 'array',
                'description': 'Grupo(s) principal(is) afetado(s) pela lei.',
                'items': {
                    'type': 'string',
                    'enum': [
                        'Crianças e Adolescentes',
                        'Idosos',
                        'Pessoas com Deficiência',
                        'Mulheres',
                        'Jovens',
                        'Consumidores',
                        'Servidores Públicos',
                        'Empresas',
                        'Animais',
                        'População de Baixa Renda',
                        'Cidadão em Geral',
                    ],
                },
            },
        },
        'required': [
            'resumo_abstrativo',
            'justificativa_resumida',
            'evidencias',
            'impacto_orcamentario',
            'areas_tematicas',
            'publico_alvo',
            'verbo_acao',
            'entidades_envolvidas',
            'prazo_vigencia',
        ],
    }

    # 3. Configuração do Modelo (Gemini)
    generation_config = {
        'response_mime_type': 'application/json',
        'response_schema': schema_json_fixo,
    }

    model = genai.GenerativeModel(
        model_name='gemini-2.5-pro',
        system_instruction=prompt_de_sistema,
        generation_config=generation_config,
    )

    print('Enviando texto para a API Gemini (X-Sum v4 - Categorias Fixas)...')
    try:
        response = model.generate_content(texto_original)
        output_json = json.loads(response.text)
        print('JSON estruturado (v4) recebido da API.')
        return output_json

    except json.JSONDecodeError:
        print('\n--- ERRO FATAL ---')
        print('A API não retornou um JSON válido, mesmo com o schema fixo.')
        print('Saída recebida:', response.text)
        return None
    except Exception as e:
        print('\n--- ERRO FATAL ---')
        print(f'Erro ao chamar a API Gemini: {e}')
        return None


# --- Função Principal (Orquestrador) ---
def main():
    """Orquestra o pipeline completo."""
    print("--- Pipeline MVP 'Voz Cívica' (Demonstração v4) ---")

    setup_api_key()
    # caminho_pdf = "lei_grazi.pdf"
    caminho_pdf = 'lei_grazi_parecer_previo.pdf'

    texto_do_pl = extrair_texto_do_pdf(caminho_pdf)

    if texto_do_pl:
        resultado_xsum = gerar_resumo_explicavel_xsum(texto_do_pl)

        if resultado_xsum:
            print('\n\n--- SUCESSO! RESULTADO X-SUM v4 (JSON) ---')
            print(json.dumps(resultado_xsum, indent=2, ensure_ascii=False))

            # novo_arquivo = "resultado_xsum_v4.json"
            novo_arquivo = 'resultado_xsum_v4_1.json'
            try:
                with open(novo_arquivo, 'w', encoding='utf-8') as f:
                    json.dump(resultado_xsum, f, indent=2, ensure_ascii=False)
                print(f"\n[i] Resultado também salvo em '{novo_arquivo}'")
            except Exception as e:
                print(f'\nErro ao salvar arquivo JSON: {e}')
    else:
        print('Encerrando o script. Não foi possível ler o PDF.')


if __name__ == '__main__':
    main()
