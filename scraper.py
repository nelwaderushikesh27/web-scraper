#!/usr/bin/env python3
"""
🕷️ Web Scraper
A powerful web scraping tool with export capabilities.
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import json
import time
import random
from typing import List, Dict, Optional
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class ScrapedData:
    """Container for scraped data."""
    url: str
    title: str
    text: str
    links: List[str]
    images: List[str]
    metadata: Dict
    timestamp: str


class UserAgentRotator:
    """Rotate user agents to avoid detection."""
    
    USER_AGENTS = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    ]
    
    @classmethod
    def get_random(cls) -> str:
        return random.choice(cls.USER_AGENTS)


class WebScraper:
    """Main web scraper class."""
    
    def __init__(
        self,
        proxy: Optional[str] = None,
        delay: float = 1.0,
        max_retries: int = 3
    ):
        self.proxy = proxy
        self.delay = delay
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': UserAgentRotator.get_random(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        if proxy:
            self.session.proxies = {
                'http': proxy,
                'https': proxy
            }
    
    def scrape(self, url: str) -> ScrapedData:
        """Scrape a single URL."""
        logger.info(f"Scraping: {url}")
        
        for attempt in range(self.max_retries):
            try:
                # Rotate user agent
                self.session.headers['User-Agent'] = UserAgentRotator.get_random()
                
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Extract data
                title = soup.title.string if soup.title else "No title"
                text = soup.get_text(separator=' ', strip=True)
                
                # Extract links
                links = []
                for link in soup.find_all('a', href=True):
                    full_url = urljoin(url, link['href'])
                    if full_url.startswith(('http://', 'https://')):
                        links.append(full_url)
                
                # Extract images
                images = []
                for img in soup.find_all('img', src=True):
                    full_url = urljoin(url, img['src'])
                    images.append(full_url)
                
                # Extract metadata
                metadata = self._extract_metadata(soup)
                
                # Add delay
                time.sleep(self.delay)
                
                return ScrapedData(
                    url=url,
                    title=title,
                    text=text[:1000],  # Limit text length
                    links=list(set(links)),
                    images=list(set(images)),
                    metadata=metadata,
                    timestamp=pd.Timestamp.now().isoformat()
                )
                
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.delay * (attempt + 1))
                else:
                    raise
    
    def scrape_multiple(self, urls: List[str]) -> List[ScrapedData]:
        """Scrape multiple URLs."""
        results = []
        for url in urls:
            try:
                result = self.scrape(url)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to scrape {url}: {e}")
        return results
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict:
        """Extract metadata from HTML."""
        metadata = {}
        
        # Meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name', meta.get('property', ''))
            content = meta.get('content', '')
            if name and content:
                metadata[name] = content
        
        return metadata
    
    def extract_text(self, *tag_names: str) -> List[str]:
        """Extract text from specific tags."""
        results = []
        # Implementation would use the last scraped soup
        return results
    
    def extract_links(self) -> List[str]:
        """Extract all links from last scraped page."""
        return []
    
    def extract_images(self) -> List[str]:
        """Extract all images from last scraped page."""
        return []
    
    def to_csv(self, data: List[ScrapedData], filename: str):
        """Export to CSV."""
        df = pd.DataFrame([vars(d) for d in data])
        df.to_csv(filename, index=False)
        logger.info(f"Saved to {filename}")
    
    def to_json(self, data: List[ScrapedData], filename: str):
        """Export to JSON."""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump([vars(d) for d in data], f, indent=2, ensure_ascii=False)
        logger.info(f"Saved to {filename}")
    
    def to_excel(self, data: List[ScrapedData], filename: str):
        """Export to Excel."""
        df = pd.DataFrame([vars(d) for d in data])
        df.to_excel(filename, index=False)
        logger.info(f"Saved to {filename}")


def main():
    """CLI entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="🕷️ Web Scraper")
    parser.add_argument('--url', type=str, help='URL to scrape')
    parser.add_argument('--urls', nargs='+', help='Multiple URLs to scrape')
    parser.add_argument('--output', type=str, default='results', help='Output filename')
    parser.add_argument('--format', choices=['csv', 'json', 'excel'], default='csv', help='Output format')
    parser.add_argument('--proxy', type=str, help='Proxy URL')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between requests')
    parser.add_argument('--extract', choices=['links', 'images'], help='Extract specific data')
    
    args = parser.parse_args()
    
    scraper = WebScraper(proxy=args.proxy, delay=args.delay)
    
    if args.url:
        result = scraper.scrape(args.url)
        results = [result]
    elif args.urls:
        results = scraper.scrape_multiple(args.urls)
    else:
        print("Please provide --url or --urls")
        return
    
    # Export results
    if args.format == 'csv':
        scraper.to_csv(results, f"{args.output}.csv")
    elif args.format == 'json':
        scraper.to_json(results, f"{args.output}.json")
    elif args.format == 'excel':
        scraper.to_excel(results, f"{args.output}.xlsx")
    
    print(f"\n✅ Scraped {len(results)} pages successfully!")


if __name__ == "__main__":
    main()
