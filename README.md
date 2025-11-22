## Diagrama de fluxo de dados

```mermaid
graph
    Camara@{ shape: lin-cyl, label: "<pre>camarapoa.rs.gov.br</pre>" }
    CronJob@{ shape: event, label: "Cron Job" }
    ListaProjetos@{ shape: docs, label: "<pre>Projeto[]</pre>" }
    DB@{ shape: db, label: "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; Database &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;" }
    Projeto@{ shape: doc, label: "<pre>Projeto</pre>" }
    PDF@{ shape: lin-doc, label: "<pre>Projeto.pdf</pre>" }
    AnaliseIA@{ shape: doc, label: "<pre>AnaliseIA</pre>" }
    PaginaListagem@{ shape: div-rect, label: "Página de Listagem" }
    FrontDetalhes@{ shape: div-rect, label: "Página de Detalhes" }

    Camara --> Scraper
    CronJob e1@--- Scraper
    Scraper --> ListaProjetos
    ListaProjetos <--> DB
    ListaProjetos -------> PaginaListagem
    DB --> Projeto
    Projeto --> PDF
    Projeto --> FrontDetalhes
    PDF --> Simplificador
    Simplificador --> AnaliseIA
    AnaliseIA --> DB
    AnaliseIA --> FrontDetalhes

    e1@{ animate: true }
    classDef text-sm font-size:0.875rem
    classDef text-lg font-size:0.875rem
    class Camara,PDF text-sm
```

## Diagrama de classes

```mermaid
classDiagram
    class Categoria {
        <<enumeration>>
        SAUDE
        EDUCACAO
        SEGURANCA
        TRANSPORTE_MOBILIDADE
        URBANISMO_INFRAESTRUTURA
        MEIO_AMBIENTE
        CAUSA_ANIMAL
        ASSISTENCIA_SOCIAL
        CULTURA_TURISMO
        ESPORTE_LAZER
        ECONOMIA_FINANCAS
        ADMINISTRACAO_PUBLICA
        HOMENAGENS
        OUTROS
    }

    class TipoProjeto {
        <<enumeration>>
        PLL
        PLE
        PLCL
        PLCE
        PELO
    }

    class Classificacao {
        +categoria: Categoria
        +fontes: list[str]
    }

    class PontoAnalise {
        +texto: str
        +fontes: list[str]
    }

    class AnaliseIA {
        +modelo: str
        +titulo: str
        +resumo: str
        +mudancas: list[PontoAnalise]
        +justificativas: list[PontoAnalise]
        +classificacao: list[Classificacao]
    }

    class Anexo {
        +titulo: str
        +url: HttpUrl
    }

    class Autor {
        +nome: str
        +slug: str | None
        +partido: str | None
        +foto_url: HttpUrl | None
    }

    class Votacao {
        +data: date
        +titulo: str
        +votos_sim: int
        +votos_nao: int
        +abstencoes: int
        +resultado: str
        +detalhes_url: HttpUrl
    }

    class Tramitacao {
        +setor: str
        +data_chegada: date
        +data_saida: date
        +situacao: str
    }

    class Projeto {
        +id_externo: int
        +numero_processo: str
        +numero_projeto: str
        +tipo: TipoProjeto
        +ementa: str
        +autores: list[Autor]
        +data_abertura: date
        +data_ultima_tramitacao: datetime
        +localizacao_atual: str
        +situacao_tramitacao: str
        +situacao_plenaria: str | None
        +analise_ia: AnaliseIA | None
        +anexos: list[Anexo]
        +votacoes: list[Votacao]
        +tramitacoes: list[Tramitacao]
    }

    Classificacao ..> Categoria : usa
    AnaliseIA *-- Classificacao : contém
    AnaliseIA *-- PontoAnalise : contém
    Projeto *-- AnaliseIA : contém
    Projeto *-- Anexo : contém
    Projeto *-- Autor : contém
    Projeto *-- Votacao : contém
    Projeto *-- Tramitacao : contém
    Projeto ..> TipoProjeto : usa
```
