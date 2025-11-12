from dataclasses import dataclass, field
from datetime import date


@dataclass
class DocumentoAnexo:
    titulo: str
    url: str


@dataclass
class Vereador:
    slug: str  # Ex: 'grazi-oliveira'
    nome: str  # Ex: 'Grazi Oliveira'
    partido: str  # Ex: 'PSOL'


@dataclass
class ProjetoLei:
    id_url: int  # Ex: 140595
    id_processo: str  # Ex: '00005/25'
    id_pl: str  # Ex: 'PLL 001/25'
    titulo_simplificado: str  # Ex: 'Criação de auxílio financeiro para mães...'
    data_abertura: date
    autores: list[Vereador]
    situacao: str  # Ex: 'PARA PARECER'
    situacao_plenaria: str  # Ex: 'EM TRAMITACAO'
    data_ultima_tramitacao: date
    documentos: list[DocumentoAnexo] = field(default_factory=list)
    texto_original: str | None = None
