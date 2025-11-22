import contextlib
import json
import logging
import re
import time
import unicodedata
import urllib.parse
from pathlib import Path

import httpx
from bs4 import BeautifulSoup, Tag

BASE_URL = 'https://www.camarapoa.rs.gov.br'
SEARCH_ENDPOINT = 'https://www.camarapoa.rs.gov.br/processos'
REFERER_URL = 'https://www.camarapoa.rs.gov.br/projetos'

DOWNLOAD_PDFS = False

OUTPUT_DIR = Path('data')
PDF_DIR = OUTPUT_DIR / 'pdfs'
JSON_FILE = OUTPUT_DIR / 'projects_test.json'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger(__name__)


class CamaraScraper:
    def __init__(self) -> None:
        self.client = httpx.Client(headers={'X-Requested-With': 'XMLHttpRequest'})
        self.results: list[dict] = []
        self._setup_directories()
        if JSON_FILE.exists():
            try:
                with JSON_FILE.open(encoding='utf-8') as f:
                    self.results = json.load(f)
                logger.info('Carregados %d projetos já salvos.', len(self.results))
            except Exception:
                logger.exception(
                    'Falha ao carregar arquivo JSON existente. Iniciando do zero.',
                )

    def _setup_directories(self) -> None:
        if DOWNLOAD_PDFS:
            PDF_DIR.mkdir(parents=True, exist_ok=True)

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
            logger.exception('Erro de conexão ao buscar Soup: %s', url)
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

        a_tag = header.find('a', href=re.compile(r'/processos/\d+$'))
        if not a_tag:
            return None

        return urllib.parse.urljoin(BASE_URL, str(a_tag['href']))

    def _process_page(self, page: int, processed_urls: set[str]) -> set[str] | None:
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

        soup = self._get_soup(SEARCH_ENDPOINT, params)
        if not soup:
            return set()

        articles = soup.select('article.item')
        if not articles:
            logger.warning('Nenhum artigo encontrado na página %d.', page)
            return None

        new_links = set()
        for article in articles:
            if self._is_sidebar_article(article):
                continue

            full_link = self._extract_link_from_article(article)
            if full_link and full_link not in processed_urls:
                new_links.add(full_link)

        return new_links

    def get_project_links(self, max_pages: int = 1) -> list[str]:
        logger.info('Searching for PLL projects...')
        links = set()
        processed_urls = {p['url'] for p in self.results}

        with contextlib.suppress(Exception):
            self.client.get(REFERER_URL)

        for page in range(1, max_pages + 1):
            page_links = self._process_page(page, processed_urls.union(links))
            if page_links is None:
                break
            page_links_count = len(page_links)
            links.update(page_links)
            logger.info(
                'Found %d NEW valid PLL projects on page %d.',
                page_links_count,
                page,
            )
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

    def _download_pdfs(self, soup: BeautifulSoup, project_id: str) -> list[dict]:
        files = []
        if not DOWNLOAD_PDFS:
            return files

        docs_container = soup.find('div', attrs={'data-tab': 'documentos'})
        if not docs_container:
            return files

        project_pdf_dir = PDF_DIR / project_id
        project_pdf_dir.mkdir(exist_ok=True)

        pdf_links = docs_container.find_all(
            'a',
            href=re.compile(r'\.pdf', re.IGNORECASE),
        )

        for link in pdf_links:
            file_url = urllib.parse.urljoin(BASE_URL, str(link['href']))
            name_text = link.get_text(strip=True) or 'document'
            filename = re.sub(r'[\\/*?:"<>|]', '', name_text).strip()
            if not filename:
                filename = 'documento'
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
                    logger.exception(
                        'Failed to download PDF %s',
                        file_url,
                    )

            files.append(
                {
                    'name': name_text,
                    'local_path': str(save_path),
                    'remote_url': file_url,
                },
            )
        return files

    def process_project(self, url: str):
        try:
            logger.info('Processing: %s', url)
            page_headers = {
                'User-Agent': self.client.headers['User-Agent'],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Referer': SEARCH_ENDPOINT,
            }
            resp = self.client.get(url, headers=page_headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            data = {'url': url, 'id': url.split('/')[-1], 'metadata': {}}
            data['metadata'] = self._extract_metadata(soup)
            data['has_votacoes'] = bool(
                soup.find('div', attrs={'data-tab': 'votacoes'}),
            )
            data['has_tramitacoes'] = bool(
                soup.find('div', attrs={'data-tab': 'tramitacoes'}),
            )
            data['files'] = self._download_pdfs(soup, data['id'])

            self.results.append(data)

        except Exception:
            logger.exception('Failed to process %s', url)

    def save_json(self):
        # Incremental save
        temp_file = OUTPUT_DIR / 'projects_temp.json'
        with temp_file.open('w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)

        # Atomic save
        temp_file.replace(JSON_FILE)
        logger.info('PROGRESS SAVED: %d projects so far.', len(self.results))

    def close(self):
        self.client.close()


if __name__ == '__main__':
    scraper = CamaraScraper()
    try:
        links = scraper.get_project_links(max_pages=1)
        for i, link in enumerate(links):
            scraper.process_project(link)
            if (i + 1) % 10 == 0:
                scraper.save_json()
            time.sleep(0.2)
        scraper.save_json()
    except KeyboardInterrupt:
        logger.warning('Interrompido pelo usuário. Salvando progresso...')
        scraper.save_json()
    finally:
        scraper.close()
