import contextlib
import logging
import re
import sqlite3
import time
import unicodedata
import urllib.parse
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
from bs4 import BeautifulSoup, Tag

from db import init_db

DOWNLOAD_PDFS = True

DB_FILE = Path('voz_civica.db')
OUTPUT_DIR = Path('data')
PDF_DIR = OUTPUT_DIR / 'pdfs'

BASE_URL = 'https://www.camarapoa.rs.gov.br'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger(__name__)


class CamaraScraper:
    def __init__(self) -> None:
        self.client = httpx.Client(headers={'X-Requested-With': 'XMLHttpRequest'})

        if not DB_FILE.exists():
            init_db(DB_FILE)

        self.conn = sqlite3.connect(DB_FILE)
        self.cursor = self.conn.cursor()

        self.processed_links = set()
        try:
            self.cursor.execute('SELECT id_externo FROM projetos')
            rows = self.cursor.fetchall()
            for row in rows:
                self.processed_links.add(f'{BASE_URL}/processos/{row[0]}')
            logger.info(
                'Carregados %d projetos já salvos do banco.',
                len(self.processed_links),
            )
        except sqlite3.OperationalError:
            logger.exception('Erro ao ler banco de dados. As tabelas existem?')
            raise

    def _dirty_clean_html(self, text: str) -> str:
        return (
            text.replace("\\'", "'")
            .replace('\\"', '"')
            .replace('\\n', '\n')
            .replace('\\r', '')
            .replace('\\/', '/')
            .replace('\\u003c', '<')
            .replace('\\u003e', '>')
        )

    def _to_snake_case(self, text: str) -> str:
        text = (
            unicodedata.normalize('NFKD', text)
            .encode('ascii', 'ignore')
            .decode('utf-8')
        )
        text = re.sub(r'[^a-z0-9]', '_', text.lower())
        return re.sub(r'_+', '_', text).strip('_')

    def _get_soup(self, url: str, params: dict | None = None) -> BeautifulSoup:
        if params:
            params['_'] = int(time.time() * 1000)
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
                if 'four' in classes and 'wide' in classes:
                    return True
        return False

    def _extract_link_from_article(self, article: Tag) -> str | None:
        header = article.find('h2', class_='header') or article.find(
            'h2',
            class_='ui small header',
        )
        if not header:
            return None

        title_text = header.get_text(strip=True).upper()
        if 'PLL' not in title_text:
            return None

        if not (a_tag := header.find('a')):
            return None

        return urllib.parse.urljoin(BASE_URL, str(a_tag['href']))

    def get_project_links(self, max_pages: int = 1) -> list[str]:
        logger.info('Searching for PLL projects...')
        links = set()
        processed_urls = self.processed_links

        for page in range(1, max_pages + 1):
            logger.info('Scraping page %d...', page)

            params = {
                'utf8': '✓',
                'busca': '',
                'tipo': 'PLL',
                'autor': '',
                'andamento': 'todos',
                'aprovados_em': '',
                'button': '',
                'page': str(page),
            }
            soup = self._get_soup(f'{BASE_URL}/processos', params)
            if not soup:
                continue

            articles = soup.select('article.item')
            if not articles:
                logger.warning('Nenhum artigo encontrado na página %d.', page)
                break

            page_links_count = 0
            for article in articles:
                if self._is_sidebar_article(article):
                    continue

                full_link = self._extract_link_from_article(article)
                if (
                    full_link
                    and full_link not in links
                    and full_link not in processed_urls
                ):
                    links.add(full_link)
                    page_links_count += 1

            logger.info(
                'Found %d NEW valid PLL projects on page %d.',
                page_links_count,
                page,
            )

            if page_links_count == 0:
                pass

            time.sleep(0.5)

        all_links = list(links)
        logger.info(
            'Total new unique PLL projects found to process: %d',
            len(all_links),
        )
        return all_links

    def _extract_metadata(self, soup: BeautifulSoup) -> dict:
        metadata = {}
        if id_container := soup.find('div', attrs={'data-tab': 'dados'}):
            for dt in id_container.select('dl.dados dt'):
                raw_key = dt.get_text(strip=True)
                key = self._to_snake_case(raw_key)
                if dd := dt.find_next_sibling('dd'):
                    metadata[key] = dd.get_text(strip=True)
        return metadata

    def _process_files(self, soup: BeautifulSoup, project_id: str) -> list[dict]:
        files = []
        if not DOWNLOAD_PDFS:
            return files

        docs_container = soup.find('div', attrs={'data-tab': 'documentos'})
        if not docs_container:
            return files

        project_pdf_dir = PDF_DIR / project_id
        pdf_links = docs_container.find_all(
            'a',
            href=re.compile(r'\.pdf', re.IGNORECASE),
        )

        for link in pdf_links:
            if not project_pdf_dir.exists():
                project_pdf_dir.mkdir(parents=True, exist_ok=True)

            file_url = urllib.parse.urljoin(BASE_URL, str(link['href']))
            name_text = link.get_text(strip=True) or 'document'
            filename = re.sub(r'[\\/*?:"<>|]', '', name_text).strip()
            if not filename.lower().endswith('.pdf'):
                filename += '.pdf'
            save_path = project_pdf_dir / filename

            if not save_path.exists():
                try:
                    with self.client.stream('GET', file_url) as r:
                        r.raise_for_status()
                        with save_path.open('wb') as f:
                            f.writelines(r.iter_bytes())
                    logger.info('Downloaded: %s', filename)
                except Exception:
                    logger.exception('Failed to download PDF %s', file_url)

            files.append(
                {
                    'name': name_text,
                    'local_path': str(save_path),
                    'remote_url': file_url,
                },
            )
        return files

    def save_project_to_db(self, data: dict):
        try:
            metadata = data.get('metadata', {})
            data_abertura = None
            if raw_data := metadata.get('data_da_abertura'):
                with contextlib.suppress(ValueError):
                    data_abertura = (
                        datetime.strptime(raw_data, '%d/%m/%Y')
                        .replace(tzinfo=UTC)
                        .date()
                    )

            link_pdf = None
            if data['files']:
                link_pdf = data['files'][0].get('local_path')

            # Inserir projeto
            self.cursor.execute(
                """
                INSERT OR IGNORE INTO projetos (
                    id_externo, numero_processo, tipo, ementa,
                    data_abertura, situacao_tramitacao, situacao_plenaria,
                    link_pdf_principal, data_ultima_tramitacao
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    data['id'],
                    metadata.get('processo'),
                    'PLL',
                    None,  # O scraper atual não obtém a ementa nos metadados
                    data_abertura,
                    metadata.get('situacao'),
                    metadata.get('situacao_plenaria'),
                    link_pdf,
                    datetime.strptime(
                        metadata.get('ultima_tramitacao'),
                        '%d/%m/%Y',
                    )
                    .replace(
                        tzinfo=UTC,
                    )
                    .date()
                    if metadata.get('ultima_tramitacao')
                    else None,
                ),
            )

            projeto_db_id = self.cursor.lastrowid

            # Inserir autor e relacionamento
            if projeto_db_id:
                autores_raw = metadata.get('autores', '')
                if autores_raw:
                    nome_autor = autores_raw.strip().upper()
                    self.cursor.execute(
                        'INSERT OR IGNORE INTO autores (nome) VALUES (?)',
                        (nome_autor,),
                    )
                    self.cursor.execute(
                        'SELECT id FROM autores WHERE nome = ?',
                        (nome_autor,),
                    )
                    res = self.cursor.fetchone()
                    if res:
                        autor_id = res[0]
                        self.cursor.execute(
                            'INSERT OR IGNORE INTO projetos_autores (projeto_id, autor_id) VALUES (?, ?)',
                            (projeto_db_id, autor_id),
                        )

            self.conn.commit()
            logger.info('Projeto %s salvo no banco.', data['id'])

        except Exception:
            logger.exception('Erro ao salvar no banco')
            self.conn.rollback()

    def process_project(self, url: str):
        if url in self.processed_links:
            logger.info('Skipping %s (already in DB)', url)
            return

        try:
            logger.info('Processing: %s', url)
            resp = self.client.get(url)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            data: dict[str, Any] = {'url': url, 'id': url.split('/')[-1]}
            data['metadata'] = self._extract_metadata(soup)
            data['has_votacoes'] = bool(
                soup.find('div', attrs={'data-tab': 'votacoes'}),
            )
            data['has_tramitacoes'] = bool(
                soup.find('div', attrs={'data-tab': 'tramitacoes'}),
            )
            data['files'] = self._process_files(soup, data['id'])

            self.save_project_to_db(data)

        except Exception:
            logger.exception('Failed to process %s', url)

    def close(self):
        self.client.close()
        self.conn.close()


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
