from datetime import datetime, date
from sqlalchemy import Integer, String, Date, DateTime, JSON, ForeignKey, Table, Column
from sqlalchemy.orm import relationship, Mapped, mapped_column
from database import Base

projeto_autor = Table(
    "projetos_autores",
    Base.metadata,
    Column("projeto_id", ForeignKey("projetos.id"), primary_key=True),
    Column("autor_id", ForeignKey("autores.id"), primary_key=True),
)

class Autor(Base):
    __tablename__ = "autores"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String, unique=True, index=True)
    slug: Mapped[str | None] = mapped_column(String)      
    partido: Mapped[str | None] = mapped_column(String)
    foto_url: Mapped[str | None] = mapped_column(String)  
    
    projetos = relationship("Projeto", secondary=projeto_autor, back_populates="autores")

class Projeto(Base):
    __tablename__ = "projetos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    id_externo: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    numero_processo: Mapped[str] = mapped_column(String) 
    numero_projeto: Mapped[str] = mapped_column(String)  
    tipo: Mapped[str] = mapped_column(String)            
    ementa: Mapped[str] = mapped_column(String)          
    
    data_abertura: Mapped[date] = mapped_column(Date)    
    
    data_ultima_tramitacao: Mapped[datetime] = mapped_column(DateTime) 
    
    situacao_tramitacao: Mapped[str] = mapped_column(String)
    situacao_plenaria: Mapped[str | None] = mapped_column(String)
    localizacao_atual: Mapped[str] = mapped_column(String)

    autores = relationship("Autor", secondary=projeto_autor, back_populates="projetos")
    anexos = relationship("Anexo", back_populates="projeto", cascade="all, delete-orphan")
    tramitacoes = relationship("Tramitacao", back_populates="projeto", cascade="all, delete-orphan")
    votacoes = relationship("Votacao", back_populates="projeto", cascade="all, delete-orphan")
    analise = relationship("AnaliseIA", back_populates="projeto", uselist=False, cascade="all, delete-orphan")

class Anexo(Base):
    __tablename__ = "anexos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    projeto_id: Mapped[int] = mapped_column(ForeignKey("projetos.id"))
    
    titulo: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    
    projeto = relationship("Projeto", back_populates="anexos")

class Tramitacao(Base):
    __tablename__ = "tramitacoes"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    projeto_id: Mapped[int] = mapped_column(ForeignKey("projetos.id"))
    
    setor: Mapped[str] = mapped_column(String)
    data_chegada: Mapped[date] = mapped_column(Date)
    data_saida: Mapped[date | None] = mapped_column(Date)
    situacao: Mapped[str] = mapped_column(String)
    
    projeto = relationship("Projeto", back_populates="tramitacoes")

class Votacao(Base):
    __tablename__ = "votacoes"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    projeto_id: Mapped[int] = mapped_column(ForeignKey("projetos.id"))
    
    data: Mapped[date] = mapped_column(Date)
    titulo: Mapped[str] = mapped_column(String)
    
    votos_sim: Mapped[int | None] = mapped_column(Integer)
    votos_nao: Mapped[int | None] = mapped_column(Integer)
    abstencoes: Mapped[int | None] = mapped_column(Integer)
    
    resultado: Mapped[str] = mapped_column(String)
    detalhes_url: Mapped[str | None] = mapped_column(String)
    
    projeto = relationship("Projeto", back_populates="votacoes")

class AnaliseIA(Base):
    __tablename__ = "analises_ia"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    projeto_id: Mapped[int] = mapped_column(ForeignKey("projetos.id"), unique=True)
    
    modelo: Mapped[str] = mapped_column(String)
    
    titulo: Mapped[str] = mapped_column(String)
    resumo: Mapped[str] = mapped_column(String)
    
    # Armazena listas de modelos Pydantic como JSON
    mudancas: Mapped[list[dict]] = mapped_column(JSON) 
    justificativas: Mapped[list[dict]] = mapped_column(JSON)
    classificacao: Mapped[list[dict]] = mapped_column(JSON) 

    projeto = relationship("Projeto", back_populates="analise")