from database import SessionLocal
from models import Projeto

def verificar_banco():
    session = SessionLocal()
    try:
        # 1. Contar quantos projetos foram salvos
        total = session.query(Projeto).count()
        print(f"\n=== RELATÓRIO DO BANCO DE DADOS ===")
        print(f"Total de Projetos salvos: {total}")
        
        if total == 0:
            print("Algo estranho: O scraper disse que salvou, mas o banco está vazio.")
            return

        # 2. Listar os 3 primeiros para conferir
        print("\n--- Amostra dos 3 primeiros Projetos ---")
        projetos = session.query(Projeto).limit(3).all()
        
        for p in projetos:
            print(f"ID Externo: {p.id_externo}")
            print(f"Processo:   {p.numero_processo}")
            print(f"Autor(es):  {[a.nome for a in p.autores]}")
            print(f"Ementa:     {p.ementa[:100]}...") # Corta em 100 caracteres
            print(f"PDFs:       {len(p.anexos)} anexos encontrados")
            print("-" * 40)

    except Exception as e:
        print(f"Erro ao ler: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    verificar_banco()