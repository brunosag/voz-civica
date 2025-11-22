import json
import logging
import pathlib
import re
import unicodedata
import urllib.parse
import time
import sys

import httpx
from bs4 import BeautifulSoup

BASE_URL = 'https://www.camarapoa.rs.gov.br'
SEARCH_ENDPOINT = 'https://www.camarapoa.rs.gov.br/processos'
REFERER_URL = 'https://www.camarapoa.rs.gov.br/projetos'


DOWNLOAD_PDFS = False 

OUTPUT_DIR = pathlib.Path('data')
PDF_DIR = OUTPUT_DIR / 'pdfs'
JSON_FILE = OUTPUT_DIR / 'projects.json'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
)
logger = logging.getLogger(__name__)

class CamaraScraper:
    def __init__(self):
        self.client = httpx.Client(
            timeout=60.0, 
            follow_redirects=True,
            verify=False, 
            headers={
                'Accept': '*/*;q=0.5, text/javascript, application/javascript, application/ecmascript, application/x-ecmascript',
                'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
                'Connection': 'keep-alive',
                'Referer': REFERER_URL,
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'X-Requested-With': 'XMLHttpRequest',
            },
        )
        self.results: list[dict] = []
        self._setup_directories()
        if JSON_FILE.exists():
            try:
                with open(JSON_FILE, 'r', encoding='utf-8') as f:
                    self.results = json.load(f)
                logger.info(f"Carregados {len(self.results)} projetos já salvos.")
            except:
                pass

    def _setup_directories(self):
        PDF_DIR.mkdir(parents=True, exist_ok=True)

    def _dirty_clean_html(self, text: str) -> str:
        return (text
            .replace("\\'", "'")
            .replace('\\"', '"')
            .replace('\\n', '\n')
            .replace('\\r', '')
            .replace('\\/', '/')
            .replace('\\u003c', '<')
            .replace('\\u003e', '>')
        )

    def _to_snake_case(self, text: str) -> str:
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
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
            
            if "$(" in content or "javascript" in resp.headers.get('content-type', ''):
                content = self._dirty_clean_html(content)

            return BeautifulSoup(content, 'html.parser')
        except Exception as e:
            logger.error(f"Erro de conexão ao buscar Soup: {e}")
            return None

    def get_project_links(self, max_pages: int = 1) -> list[str]:
        logger.info('Searching for PLL projects...')
        links = set()
        
        processed_urls = {p['url'] for p in self.results}

        try:
            self.client.get(REFERER_URL)
        except Exception:
            pass

        for page in range(1, max_pages + 1):
            logger.info(f'Scraping page {page}...')
            
            params = {
                'utf8': '✓',
                'busca': '',
                'tipo': 'PLL',
                'autor': '',
                'andamento': 'todos',
                'aprovados_em': '',
                'button': '',
                'page': str(page)
            }

            soup = self._get_soup(SEARCH_ENDPOINT, params)
            if not soup: continue

            articles = soup.select('article.item')
            if not articles:
                logger.warning(f"Nenhum artigo encontrado na página {page}.")
                break

            page_links_count = 0
            for article in articles:
                is_sidebar = False
                for parent in article.parents:
                    if parent.name == 'div':
                        classes = parent.get('class', [])
                        if 'four' in classes and 'wide' in classes:
                            is_sidebar = True
                            break
                
                if is_sidebar: continue

                header = article.find('h2', class_='header') or article.find('h2', class_='ui small header')

                if header:
                    title_text = header.get_text(strip=True).upper()
                    if 'PLL' in title_text:
                        a_tag = header.find('a', href=re.compile(r'/processos/\d+$'))
                        if a_tag:
                            full_link = urllib.parse.urljoin(BASE_URL, a_tag['href'])
                            
                            if full_link not in links and full_link not in processed_urls:
                                links.add(full_link)
                                page_links_count += 1
                                
            logger.info(f'Found {page_links_count} NEW valid PLL projects on page {page}.')
            
            if page_links_count == 0:              
                
                pass
            
            time.sleep(0.5) 

        all_links = list(links)
        logger.info(f'Total new unique PLL projects found to process: {len(all_links)}')
        return all_links

    def process_project(self, url: str):
        try:
            logger.info(f'Processing: {url}')
            
            page_headers = {
                'User-Agent': self.client.headers['User-Agent'],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Referer': SEARCH_ENDPOINT
            }
            
            resp = self.client.get(url, headers=page_headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')

            data = {'url': url, 'id': url.split('/')[-1], 'metadata': {}}

            if id_container := soup.find('div', attrs={'data-tab': 'dados'}):
                for dt in id_container.select('dl.dados dt'):
                    raw_key = dt.get_text(strip=True)
                    key = self._to_snake_case(raw_key)
                    if dd := dt.find_next_sibling('dd'):
                        data['metadata'][key] = dd.get_text(strip=True)

            data['has_votacoes'] = bool(soup.find('div', attrs={'data-tab': 'votacoes'}))
            data['has_tramitacoes'] = bool(soup.find('div', attrs={'data-tab': 'tramitacoes'}))
            data['files'] = []

            if DOWNLOAD_PDFS and (docs_container := soup.find('div', attrs={'data-tab': 'documentos'})):
                project_pdf_dir = PDF_DIR / data['id']
                project_pdf_dir.mkdir(exist_ok=True)
                
                # limit to 3 PDFs per project to avoid freezing
                pdf_links = docs_container.find_all('a', href=re.compile(r'\.pdf', re.IGNORECASE))
                
                for link in pdf_links:
                    file_url = urllib.parse.urljoin(BASE_URL, link['href'])
                    name_text = link.get_text(strip=True) or 'document'
                    filename = re.sub(r'[\\/*?:"<>|]', '', name_text).strip()
                    if not filename: filename = 'documento'
                    if not filename.lower().endswith('.pdf'): filename += '.pdf'
                    save_path = project_pdf_dir / filename
                    
                    if not save_path.exists():
                        try:
                            with self.client.stream('GET', file_url) as r:
                                r.raise_for_status()
                                with open(save_path, 'wb') as f:
                                    for chunk in r.iter_bytes(): f.write(chunk)
                            logger.info(f"Downloaded: {filename}")
                        except Exception as e:
                            logger.error(f"Failed to download PDF {file_url}: {e}")
                    
                    data['files'].append({'name': name_text, 'local_path': str(save_path), 'remote_url': file_url})

            self.results.append(data)
            
        except Exception as e:
            logger.error(f'Failed to process {url}: {e}')

    def save_json(self):
        # incremental save
        temp_file = OUTPUT_DIR / 'projects_temp.json'
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        # atomic save
        temp_file.replace(JSON_FILE)
        logger.info(f'PROGRESS SAVED: {len(self.results)} projects so far.')

    def close(self):
        self.client.close()

if __name__ == '__main__':
    scraper = CamaraScraper()
    try:
        # pages number definition
        links = scraper.get_project_links(max_pages=500)
        
        for i, link in enumerate(links):
            scraper.process_project(link)
            
            # save progress every 10 projects (maximum safety)
            if (i + 1) % 10 == 0:
                scraper.save_json()
                
            time.sleep(0.2)
            
        scraper.save_json()
    except KeyboardInterrupt:
        logger.warning("Interrompido pelo usuário! Salvando progresso...")
        scraper.save_json()
    finally:
        scraper.close()