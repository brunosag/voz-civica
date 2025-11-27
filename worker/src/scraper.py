import logging
import re
import unicodedata
import urllib.parse
import time
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup, Tag
from sqlalchemy.orm import Session

try:
    from database import SessionLocal, engine, Base
    from models import Projeto, Autor, Anexo
except ImportError:
    from database import SessionLocal, engine, Base
    from models import Projeto, Autor, Anexo

Base.metadata.create_all(bind=engine)

DOWNLOAD_PDFS = False # Colocar True se quiser baixar os PDFs!

OUTPUT_DIR = Path('data')
PDF_DIR = OUTPUT_DIR / 'pdfs'

BASE_URL = 'https://www.camarapoa.rs.gov.br'
REFERER_URL = 'https://www.camarapoa.rs.gov.br/projetos'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger(__name__)

class CamaraScraper:
    def __init__(self) -> None:
        self.client = httpx.Client(headers={'X-Requested-With': 'XMLHttpRequest'})
        
        self.db: Session = SessionLocal()

        self.processed_ids = set()
        try:
            existing = self.db.query(Projeto.id_externo).all()
            self.processed_ids = {row[0] for row in existing}
            logger.info(
                'Carregados %d projetos já salvos do banco.',
                len(self.processed_ids),
            )
        except Exception as e:
            logger.error(f"Erro ao ler banco de dados: {e}")

    def _dirty_clean_html(self, text: str) -> str:
        return (text.replace("\\'", "'").replace('\\"', '"').replace('\\n', '\n')
                .replace('\\r', '').replace('\\/', '/').replace('\\u003c', '<').replace('\\u003e', '>'))

    def _to_snake_case(self, text: str) -> str:
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
        text = re.sub(r'[^a-z0-9]', '_', text.lower())
        return re.sub(r'_+', '_', text).strip('_')

    def _get_soup(self, url: str, params: dict | None = None) -> BeautifulSoup:
        if params: params['_'] = int(time.time() * 1000)
        try:
            resp = self.client.get(url, params=params)
            resp.encoding = 'utf-8'
            resp.raise_for_status()
            content = resp.text
            if '$(' in content or 'javascript' in resp.headers.get('content-type', ''):
                content = self._dirty_clean_html(content)
            return BeautifulSoup(content, 'html.parser')
        except Exception:
            logger.exception('Erro de conexão ao buscar Soup em %s', url)
            raise

    def _is_sidebar_article(self, article: Tag) -> bool:
        for parent in article.parents:
            if parent.name == 'div':
                classes = parent.get('class') or []
                if 'four' in classes and 'wide' in classes: return True
        return False

    def _extract_link_from_article(self, article: Tag) -> str | None:
        header = article.find('h2', class_='header') or article.find('h2', class_='ui small header')
        if not header: return None
        title_text = header.get_text(strip=True).upper()
        if 'PLL' not in title_text: return None
        if not (a_tag := header.find('a')): return None
        return urllib.parse.urljoin(BASE_URL, str(a_tag['href']))

    def get_project_links(self, max_pages: int = 1) -> list[str]:
        logger.info('Searching for PLL projects...')
        links = set()
        
        for page in range(1, max_pages + 1):
            logger.info('Scraping page %d...', page)
            params = {
                'utf8': '✓', 'busca': '', 'tipo': 'PLL', 'autor': '',
                'andamento': 'todos', 'aprovados_em': '', 'button': '', 'page': str(page),
            }
            soup = self._get_soup(f'{BASE_URL}/processos', params)
            if not soup: continue

            articles = soup.select('article.item')
            if not articles: break

            page_links_count = 0
            for article in articles:
                if self._is_sidebar_article(article): continue
                full_link = self._extract_link_from_article(article)
                
                if full_link:
                    try:
                        p_id = int(full_link.split('/')[-1])
                        if p_id not in self.processed_ids and full_link not in links:
                            links.add(full_link)
                            page_links_count += 1
                    except ValueError: pass
            
            logger.info('Found %d NEW valid PLL projects on page %d.', page_links_count, page)
            if page_links_count == 0: pass
            time.sleep(0.5)

        return list(links)

    def _extract_metadata(self, soup: BeautifulSoup) -> dict:
        metadata = {}
        if id_container := soup.find('div', attrs={'data-tab': 'dados'}):
            for dt in id_container.select('dl.dados dt'):
                raw_key = dt.get_text(strip=True)
                key = self._to_snake_case(raw_key)
                if dd := dt.find_next_sibling('dd'):
                    metadata[key] = dd.get_text(strip=True)
        return metadata

    def _process_files_download(self, soup: BeautifulSoup, project_id: str) -> list[dict]:
        """Baixa arquivos e retorna lista de metadados para salvar no banco."""
        files = []
        docs_container = soup.find('div', attrs={'data-tab': 'documentos'})
        if not docs_container: return files

        project_pdf_dir = PDF_DIR / project_id
        pdf_links = docs_container.find_all('a', href=re.compile(r'\.pdf', re.IGNORECASE))

        for link in pdf_links:
            file_url = urllib.parse.urljoin(BASE_URL, str(link['href']))
            name_text = link.get_text(strip=True) or 'documento'
            filename = re.sub(r'[\\/*?:"<>|]', '', name_text).strip()
            if not filename.lower().endswith('.pdf'): filename += '.pdf'
            
            save_path = project_pdf_dir / filename
            local_path_str = None

            if DOWNLOAD_PDFS:
                if not project_pdf_dir.exists():
                    project_pdf_dir.mkdir(parents=True, exist_ok=True)
                
                if not save_path.exists():
                    try:
                        with self.client.stream('GET', file_url) as r:
                            r.raise_for_status()
                            with save_path.open('wb') as f:
                                f.writelines(r.iter_bytes())
                        logger.info('Downloaded: %s', filename)
                    except Exception:
                        logger.exception('Failed to download PDF %s', file_url)
                
                if save_path.exists():
                    local_path_str = str(save_path)

            files.append({
                'titulo': name_text,
                'caminho_local': local_path_str,
                'url_remota': file_url
            })
        return files

    def save_project_to_db(self, data: dict):
        try:
            meta = data.get('metadata', {})
            
            data_abertura = None
            if raw := meta.get('data_da_abertura'):
                try: data_abertura = datetime.strptime(raw, '%d/%m/%Y').date()
                except: pass

            data_tramitacao = None
            if raw := meta.get('ultima_tramitacao'):
                try:
                    data_tramitacao = datetime.strptime(raw, '%d/%m/%Y') 
                except: pass

            existing_proj = self.db.query(Projeto).filter(Projeto.id_externo == int(data['id'])).first()
            
            if existing_proj:
                logger.info('Projeto %s já existe no banco. Pulando inserção.', data['id'])
                return

            novo_projeto = Projeto(
                id_externo=int(data['id']),
                numero_processo=meta.get('processo', 'N/A'), # Obrigatório
                
                # O scraper atual não pega o número do projeto (ex: 123/24) separado do título
                # Usamos o processo ou string vazia para não quebrar o banco
                numero_projeto=meta.get('processo', '').split('/')[0] if meta.get('processo') else '00000', 
                
                tipo='PLL',
                
                ementa=meta.get('ementa', 'Ementa não extraída automaticamente'), 
                
                data_abertura=data_abertura if data_abertura else datetime.now().date(),
                data_ultima_tramitacao=data_tramitacao if data_tramitacao else datetime.now(),
                
                situacao_tramitacao=meta.get('situacao', 'Desconhecida'),
                situacao_plenaria=meta.get('situacao_plenaria'),
                localizacao_atual=meta.get('localizacao_atual', 'Desconhecida')
            )

            # 1. Autores
            autores_raw = meta.get('autores', '')
            if autores_raw:
                nome_autor = autores_raw.strip().upper()
                autor_obj = self.db.query(Autor).filter(Autor.nome == nome_autor).first()
                if not autor_obj:
                    autor_obj = Autor(nome=nome_autor)
                    self.db.add(autor_obj)
                    self.db.flush()
                novo_projeto.autores.append(autor_obj)

            # 2. Anexos (Arquivos)
            for file_info in data.get('files', []):
                anexo = Anexo(
                    titulo=file_info['titulo'],
                    url=file_info['url_remota'],
                    caminho_local=file_info['caminho_local']
                )
                novo_projeto.anexos.append(anexo)

            self.db.add(novo_projeto)
            self.db.commit()
            
            self.processed_ids.add(int(data['id']))
            logger.info('Projeto %s salvo no banco.', data['id'])

        except Exception as e:
            logger.exception('Erro ao salvar no banco: %s', e)
            self.db.rollback()

    def process_project(self, url: str):
        try:
            p_id = int(url.split('/')[-1])
            if p_id in self.processed_ids: return

            logger.info('Processing: %s', url)
            resp = self.client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            data: dict[str, Any] = {'url': url, 'id': str(p_id)}
            data['metadata'] = self._extract_metadata(soup)
            
            # No futuro dá pra adicionar lógica para extrair votações e tramitações
            # data['votacoes'] = self._extract_votacoes(soup)...
            
            data['files'] = self._process_files_download(soup, data['id'])

            self.save_project_to_db(data)

        except Exception:
            logger.exception('Failed to process %s', url)

    def close(self):
        self.client.close()
        self.db.close()

if __name__ == '__main__':
    scraper = CamaraScraper()
    try:
        links = scraper.get_project_links(max_pages=2)
        for link in links:
            scraper.process_project(link)
    except KeyboardInterrupt:
        logger.warning('Interrompido pelo usuário.')
    finally:
        scraper.close()