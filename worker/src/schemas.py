from datetime import date, datetime
from enum import StrEnum

from pydantic import BaseModel, Field, HttpUrl


class Categoria(StrEnum):
    SAUDE = 'Saúde'
    EDUCACAO = 'Educação'
    SEGURANCA = 'Segurança'
    TRANSPORTE_MOBILIDADE = 'Transporte e Mobilidade'
    URBANISMO_INFRAESTRUTURA = 'Urbanismo e Infraestrutura'
    MEIO_AMBIENTE = 'Meio Ambiente'
    CAUSA_ANIMAL = 'Causa Animal'
    ASSISTENCIA_SOCIAL = 'Assistência Social e Direitos Humanos'
    CULTURA_TURISMO = 'Cultura e Turismo'
    ESPORTE_LAZER = 'Esporte e Lazer'
    ECONOMIA_FINANCAS = 'Economia e Finanças'
    ADMINISTRACAO_PUBLICA = 'Administração Pública'
    HOMENAGENS = 'Homenagens e Festividades'
    OUTROS = 'Outros'


class TipoProjeto(StrEnum):
    PLL = 'PLL'  # Projeto de Lei do Legislativo
    PLE = 'PLE'  # Projeto de Lei do Executivo
    PLCL = 'PLCL'  # Projeto de Lei Complementar do Legislativo
    PLCE = 'PLCE'  # Projeto de Lei Complementar do Executivo
    PELO = 'PELO'  # Proposta de Emenda à Lei Orgânica


class Classificacao(BaseModel):
    categoria: Categoria = Field(
        description='A categoria temática que melhor descreve o projeto.',
    )
    fontes: list[str] = Field(
        min_length=1,
        description='Lista de trechos exatos do texto original que justificam a escolha desta categoria.',
    )


class PontoAnalise(BaseModel):
    texto: str = Field(
        description='A explicação simplificada do ponto (mudança ou justificativa) em linguagem cidadã, sem juridiquês.',
    )
    fontes: list[str] = Field(
        min_length=1,
        description='Lista de strings contendo os trechos exatos (ipsis litteris) do documento original que comprovam este ponto.',
    )


class AnaliseIA(BaseModel):
    modelo: str = Field(
        description='O identificador do modelo de IA utilizado.',
    )
    titulo: str = Field(
        description="Título curto, chamativo e jornalístico (máx 10 palavras). Ex: 'Proibição de fogos de artifício com ruído'.",
    )
    resumo: str = Field(
        description="Uma única frase simples explicando o objetivo central. Comece com verbo (ex: 'Cria', 'Proíbe').",
    )
    mudancas: list[PontoAnalise] = Field(
        min_length=1,
        description="Lista de mudanças práticas na vida do cidadão. Foco no 'o que muda amanhã'.",
    )
    justificativas: list[PontoAnalise] = Field(
        min_length=1,
        description='Lista dos principais argumentos do autor para propor a lei.',
    )
    classificacao: list[Classificacao] = Field(
        min_length=1,
        description='Classificação temática do projeto baseada em evidências no texto.',
    )


class Autor(BaseModel):
    nome: str
    slug: str | None = None
    partido: str | None = None
    foto_url: HttpUrl | None = None


class Anexo(BaseModel):
    titulo: str
    url: HttpUrl


class Votacao(BaseModel):
    data: date
    titulo: str
    votos_sim: int | None
    votos_nao: int | None
    abstencoes: int | None
    resultado: str
    detalhes_url: HttpUrl | None


class Tramitacao(BaseModel):
    setor: str
    data_chegada: date
    data_saida: date | None = None
    situacao: str


class Projeto(BaseModel):
    id_externo: int = Field(
        gt=0,
        description='ID numérico da URL (.../processos/{id})',
    )
    numero_processo: str = Field(
        pattern=r'^\d{5}/\d{2}$',
        description='Número identificador do processo (ex: 00738/25)',
    )
    numero_projeto: str = Field(
        pattern=r'^\d+/\d{2}$',
        description='Número do projeto (ex: 314/25) sem a sigla do tipo',
    )
    tipo: TipoProjeto
    ementa: str
    autores: list[Autor] = Field(min_length=1)
    data_abertura: date
    data_ultima_tramitacao: datetime
    localizacao_atual: str
    situacao_tramitacao: str
    situacao_plenaria: str | None = None
    analise_ia: AnaliseIA | None = None
    anexos: list[Anexo] = Field(default_factory=list)
    votacoes: list[Votacao] = Field(default_factory=list)
    tramitacoes: list[Tramitacao] = Field(default_factory=list)
