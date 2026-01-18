"""
ContentExtractor for God Mode Recon Crawler.
Extracts textual and structural content, meta, headings, forms, scripts, links, and more from a Playwright async page.
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

class Content:
    def __init__(self):
        self.title = ""
        self.meta_tags = {}
        self.keywords = []
        self.headings = {}
        self.forms = []
        self.buttons = []
        self.inputs = []
        self.text = ""
        self.paragraphs = []
        self.scripts = []
        self.description = ""
        self.links = []
        self.tables = []

class ContentExtractor:
    def __init__(self, logger=None):
        self.logger = logger

    async def extract_content(self, page, url) -> Content:
        content = Content()
        try:
            text = await page.evaluate('() => document.body.innerText')
            html = await page.content()
            content.title = await page.title()
            content.text = text[:5000]
            content.links = await page.evaluate("() => Array.from(document.querySelectorAll('a[href]')).map(a => a.href)")
            if HAS_BS4:
                soup = BeautifulSoup(html, 'html.parser')
                # Meta tags
                for meta in soup.find_all('meta'):
                    name = meta.get('name') or meta.get('property')
                    if name:
                        content.meta_tags[name] = meta.get('content', '')
                meta_desc = soup.find('meta', attrs={'name':'description'})
                if meta_desc:
                    content.description = meta_desc.get('content','')
                meta_kw = soup.find('meta', attrs={'name':'keywords'})
                if meta_kw:
                    content.keywords = [k.strip() for k in meta_kw.get('content','').split(',')]
                # Headings
                for tag in ('h1','h2','h3'):
                    content.headings[tag] = [h.get_text(strip=True) for h in soup.find_all(tag)][:5]
                # Inputs and forms
                for f in soup.find_all('form'):
                    fields = [i.get('name') for i in f.find_all('input') if i.get('name')]
                    content.forms.append({'action': f.get('action'), 'fields': fields})
                # Buttons
                content.buttons = [{'text': b.get_text(strip=True)} for b in soup.find_all('button')]
                # Inputs
                content.inputs = [{'name': i.get('name'), 'type': i.get('type','text')} for i in soup.find_all('input')]
                # Scripts
                content.scripts = [s.get('src') for s in soup.find_all('script') if s.get('src')]
                # Paragraphs
                content.paragraphs = [p.get_text(strip=True) for p in soup.find_all('p')]
                # Tables
                for table in soup.find_all('table')[:3]:
                    rows = []
                    for tr in table.find_all('tr'):
                        cells = [td.get_text(strip=True) for td in tr.find_all(['td','th'])]
                        rows.append(cells)
                    content.tables.append({'rows': rows})
            return content
        except Exception as e:
            if self.logger:
                self.logger.error(f"Content extraction error: {e}")
            content.text = "ERROR"
            return content

    async def extract_links(self, page, url, scope_manager):
        """Return (in_scope_links, out_of_scope_links) using scope_manager."""
        in_scope = []
        out_scope = []
        try:
            links = await page.evaluate("""
                () => Array.from(document.querySelectorAll('a[href]'))
                    .map(a => a.href)
                    .filter(href => href && !href.startsWith('javascript:') && !href.startsWith('mailto:') && !href.startsWith('tel:'))
            """)
            for link in set(links):
                normalized = scope_manager.normalize_url(link, url)
                if normalized:
                    if normalized not in in_scope:
                        in_scope.append(normalized)
                else:
                    if link not in out_scope:
                        out_scope.append(link)
            return in_scope, out_scope
        except Exception as e:
            if self.logger:
                self.logger.error(f"Link extraction error: {e}")
            return [], []
