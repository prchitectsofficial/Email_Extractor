import requests
from bs4 import BeautifulSoup
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse, urlunparse
import logging
from xml.etree import ElementTree as ET
import threading
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger(__name__)

class EmailExtractor:
    def __init__(self, max_workers=8, timeout=5, site_timeout=30, rate_limit=0.2, max_retries=2):
        """
        Initialize the EmailExtractor
        
        Args:
            max_workers (int): Maximum number of concurrent threads (increased to 8 for faster processing)
            timeout (int): Request timeout in seconds per page (reduced to 5 for speed)
            site_timeout (int): Maximum time to spend on entire website (reduced to 30 for speed)
            rate_limit (float): Minimum delay between requests in seconds (reduced to 0.2 for speed)
            max_retries (int): Maximum number of retry attempts for failed requests (reduced to 2 for speed)
        """
        self.max_workers = max_workers
        self.timeout = timeout
        self.site_timeout = site_timeout
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        
        # Thread-safe rate limiting
        self._last_request_time = {}
        self._request_lock = threading.Lock()
        
        # Create session with retry strategy
        self.session = self._create_session_with_retries()
        
        # Set a user agent to avoid being blocked
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # Improved email regex pattern (from your code)
        self.email_pattern = re.compile(
            r"""(?<![\w.+-])
            [A-Za-z0-9._%+-]+ @ [A-Za-z0-9.-]+ \. [A-Za-z]{2,}
            (?![\w.-])
            """,
            re.VERBOSE | re.IGNORECASE,
        )
        
        # Email de-obfuscation mappings - expanded to catch more patterns
        self.obfuscation_map = (
            # @ symbol replacements (case insensitive variations)
            ("[at]", "@"), ("(at)", "@"), ("{at}", "@"), ("<at>", "@"), 
            (" at ", "@"), (" [at] ", "@"), (" (at) ", "@"), (" {at} ", "@"),
            ("[AT]", "@"), ("(AT)", "@"), ("{AT}", "@"), ("<AT>", "@"),
            (" AT ", "@"), (" [AT] ", "@"), (" (AT) ", "@"), (" {AT} ", "@"),
            ("[At]", "@"), ("(At)", "@"), ("{At}", "@"), ("<At>", "@"),
            # . symbol replacements (case insensitive variations)
            ("[dot]", "."), ("(dot)", "."), ("{dot}", "."), ("<dot>", "."),
            (" dot ", "."), (" [dot] ", "."), (" (dot) ", "."), (" {dot} ", "."),
            ("[DOT]", "."), ("(DOT)", "."), ("{DOT}", "."), ("<DOT>", "."),
            (" DOT ", "."), (" [DOT] ", "."), (" (DOT) ", "."), (" {DOT} ", "."),
            ("[Dot]", "."), ("(Dot)", "."), ("{Dot}", "."), ("<Dot>", "."),
        )
        
        # Priority keywords for page filtering
        self.priority_keywords = (
            "contact", "about", "services", "company"
        )
    
    def _create_session_with_retries(self):
        """
        Create a requests session with built-in retry strategy
        
        Returns:
            requests.Session: Configured session with retry mechanism
        """
        session = requests.Session()
        
        # Define retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1,  # Wait 1, 2, 4 seconds between retries
            raise_on_redirect=False,
            raise_on_status=False
        )
        
        # Create HTTP adapter with retry strategy
        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=100,
            pool_maxsize=100
        )
        
        # Mount adapter for both HTTP and HTTPS
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _apply_rate_limit(self, domain):
        """
        Apply rate limiting per domain to be respectful to websites
        
        Args:
            domain (str): The domain to apply rate limiting to
        """
        with self._request_lock:
            current_time = time.time()
            last_time = self._last_request_time.get(domain, 0)
            time_since_last = current_time - last_time
            
            if time_since_last < self.rate_limit:
                sleep_time = self.rate_limit - time_since_last
                # Add small random jitter to avoid thundering herd
                sleep_time += random.uniform(0, 0.1)
                time.sleep(sleep_time)
            
            self._last_request_time[domain] = time.time()
    
    def _make_request_with_retries(self, url, custom_timeout=None):
        """
        Make HTTP request with rate limiting and custom retry logic
        
        Args:
            url (str): URL to request
            custom_timeout (int): Custom timeout for this request
            
        Returns:
            requests.Response or None: Response object or None if failed
        """
        domain = urlparse(url).netloc
        timeout = custom_timeout or self.timeout
        
        # Apply rate limiting
        self._apply_rate_limit(domain)
        
        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(
                    url,
                    timeout=timeout,
                    allow_redirects=True
                )
                
                # Check if response is successful
                if response.status_code == 200:
                    return response
                elif response.status_code in [429, 503, 520, 521, 522, 523, 524]:
                    # Rate limited or server issues - wait longer
                    if attempt < self.max_retries:
                        wait_time = (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(f"Rate limited/Server error for {url}, waiting {wait_time:.1f}s (attempt {attempt + 1}/{self.max_retries + 1})")
                        time.sleep(wait_time)
                        continue
                else:
                    # Other HTTP errors
                    logger.warning(f"HTTP {response.status_code} for {url} on attempt {attempt + 1}")
                    if attempt < self.max_retries:
                        time.sleep(1 + random.uniform(0, 1))
                        continue
                    return response  # Return even if not 200 for final attempt
                
            except requests.exceptions.Timeout:
                if attempt < self.max_retries:
                    logger.warning(f"Timeout for {url}, retrying (attempt {attempt + 1}/{self.max_retries + 1})")
                    time.sleep(1 + random.uniform(0, 1))
                    continue
                else:
                    logger.warning(f"Final timeout for {url}")
                    return None
                    
            except requests.exceptions.ConnectionError:
                if attempt < self.max_retries:
                    logger.warning(f"Connection error for {url}, retrying (attempt {attempt + 1}/{self.max_retries + 1})")
                    time.sleep(2 + random.uniform(0, 1))
                    continue
                else:
                    logger.warning(f"Final connection error for {url}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                if attempt < self.max_retries:
                    logger.warning(f"Request error for {url}: {e}, retrying (attempt {attempt + 1}/{self.max_retries + 1})")
                    time.sleep(1 + random.uniform(0, 1))
                    continue
                else:
                    logger.warning(f"Final request error for {url}: {e}")
                    return None
        
        return None
        
        # Common pages that often contain contact information
        self.contact_pages = [
            'contact', 'contact-us', 'contactus', 'contact_us',
            'about', 'about-us', 'aboutus', 'about_us',
            'team', 'staff', 'people', 'leadership',
            'support', 'help', 'info', 'information',
            'reach-us', 'get-in-touch', 'connect', 'services'
        ]
    
    def normalize_url(self, url):
        """
        Normalize URL by adding protocol if missing
        
        Args:
            url (str): URL to normalize
            
        Returns:
            str: Normalized URL
        """
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        return url
    
    def extract_emails_from_text(self, text):
        """
        Extract email addresses from text using multiple patterns and de-obfuscation
        
        Args:
            text (str): Text to search for emails
            
        Returns:
            set: Set of unique email addresses found
        """
        if not text:
            return set()
        
        candidates = set()
        
        # 1) Direct regex extraction with current pattern
        candidates.update(re.findall(self.email_pattern, text))
        
        # 2) Additional email pattern with parentheses format: abc@domain.com (more flexible)
        additional_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\s*\.\s*[A-Za-z]{2,}\b',
            re.IGNORECASE
        )
        candidates.update(re.findall(additional_pattern, text))
        
        # 2b) More aggressive pattern - allows for various separators and formats
        aggressive_pattern = re.compile(
            r'[A-Za-z0-9._%+-]+[@\s]+[A-Za-z0-9.-]+[.\s]+[A-Za-z]{2,}',
            re.IGNORECASE
        )
        aggressive_matches = aggressive_pattern.findall(text)
        for match in aggressive_matches:
            # Clean up the match
            cleaned = re.sub(r'\s+', '', match.replace(' ', '').replace('\n', '').replace('\t', ''))
            if '@' in cleaned and '.' in cleaned:
                candidates.add(cleaned)
        
        # 2c) Pattern for emails without word boundaries (more aggressive)
        loose_pattern = re.compile(
            r'[A-Za-z0-9._%+-]{1,64}@[A-Za-z0-9.-]{1,253}\.[A-Za-z]{2,}',
            re.IGNORECASE
        )
        candidates.update(re.findall(loose_pattern, text))
        
        # 3) Look for emails in HTML attributes (like href="mailto:email@domain.com")
        mailto_pattern = re.compile(
            r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})',
            re.IGNORECASE
        )
        mailto_matches = re.findall(mailto_pattern, text)
        candidates.update(mailto_matches)
        
        # 4) Look for emails in common formats like "Email: abc@domain.com" or "Contact: abc@domain.com"
        context_pattern = re.compile(
            r'(?:email|e-mail|contact|mail|reach)\s*:?\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})',
            re.IGNORECASE
        )
        context_matches = re.findall(context_pattern, text)
        candidates.update(context_matches)
        
        # 5) Advanced de-obfuscation - try this regardless of whether we found emails
        deobfuscated_text = text
        
        # Apply basic obfuscation replacements
        for obfuscated, replacement in self.obfuscation_map:
            deobfuscated_text = deobfuscated_text.replace(obfuscated, replacement)
        
        # Additional pattern-based de-obfuscation for complex cases
        # These patterns match obfuscated emails BEFORE replacement (check original text)
        
        # Pattern for: word [at] word [dot] word (case insensitive)
        pattern1 = re.compile(r'\b([a-zA-Z0-9._+-]+)\s*\[at\]\s*([a-zA-Z0-9.-]+)\s*\[dot\]\s*([a-zA-Z]{2,})\b', re.IGNORECASE)
        matches = pattern1.findall(text)
        for match in matches:
            email = f"{match[0]}@{match[1]}.{match[2]}"
            candidates.add(email)
        
        # Pattern for: word (at) word (dot) word
        pattern2 = re.compile(r'\b([a-zA-Z0-9._+-]+)\s*\(at\)\s*([a-zA-Z0-9.-]+)\s*\(dot\)\s*([a-zA-Z]{2,})\b', re.IGNORECASE)
        matches = pattern2.findall(text)
        for match in matches:
            email = f"{match[0]}@{match[1]}.{match[2]}"
            candidates.add(email)
        
        # Pattern for: word {at} word {dot} word
        pattern3 = re.compile(r'\b([a-zA-Z0-9._+-]+)\s*\{at\}\s*([a-zA-Z0-9.-]+)\s*\{dot\}\s*([a-zA-Z]{2,})\b', re.IGNORECASE)
        matches = pattern3.findall(text)
        for match in matches:
            email = f"{match[0]}@{match[1]}.{match[2]}"
            candidates.add(email)
        
        # Pattern for: word <at> word <dot> word
        pattern3b = re.compile(r'\b([a-zA-Z0-9._+-]+)\s*<at>\s*([a-zA-Z0-9.-]+)\s*<dot>\s*([a-zA-Z]{2,})\b', re.IGNORECASE)
        matches = pattern3b.findall(text)
        for match in matches:
            email = f"{match[0]}@{match[1]}.{match[2]}"
            candidates.add(email)
        
        # Pattern for: word at word dot word (with spaces)
        pattern4 = re.compile(r'\b([a-zA-Z0-9._+-]+)\s+at\s+([a-zA-Z0-9.-]+)\s+dot\s+([a-zA-Z]{2,})\b', re.IGNORECASE)
        matches = pattern4.findall(text)
        for match in matches:
            email = f"{match[0]}@{match[1]}.{match[2]}"
            candidates.add(email)
        
        # Pattern for: word AT word DOT word (uppercase)
        pattern5 = re.compile(r'\b([a-zA-Z0-9._+-]+)\s+AT\s+([a-zA-Z0-9.-]+)\s+DOT\s+([a-zA-Z]{2,})\b')
        matches = pattern5.findall(text)
        for match in matches:
            email = f"{match[0]}@{match[1]}.{match[2]}"
            candidates.add(email)
        
        # Pattern for: word [at] word . word (mixed format)
        pattern6 = re.compile(r'\b([a-zA-Z0-9._+-]+)\s*\[at\]\s*([a-zA-Z0-9.-]+)\s*\.\s*([a-zA-Z]{2,})\b', re.IGNORECASE)
        matches = pattern6.findall(text)
        for match in matches:
            email = f"{match[0]}@{match[1]}.{match[2]}"
            candidates.add(email)
        
        # Pattern for: word (at) word . word (mixed format)
        pattern7 = re.compile(r'\b([a-zA-Z0-9._+-]+)\s*\(at\)\s*([a-zA-Z0-9.-]+)\s*\.\s*([a-zA-Z]{2,})\b', re.IGNORECASE)
        matches = pattern7.findall(text)
        for match in matches:
            email = f"{match[0]}@{match[1]}.{match[2]}"
            candidates.add(email)
        
        # Apply all patterns to deobfuscated text
        candidates.update(re.findall(self.email_pattern, deobfuscated_text))
        candidates.update(re.findall(additional_pattern, deobfuscated_text))
        context_matches_deob = re.findall(context_pattern, deobfuscated_text)
        candidates.update(context_matches_deob)
        mailto_matches_deob = re.findall(mailto_pattern, deobfuscated_text)
        candidates.update(mailto_matches_deob)
        
        # 6) Clean and filter emails with proper TLD validation
        cleaned_emails = set()
        
        # Valid top-level domains (common ones)
        valid_tlds = {
            # Generic TLDs
            'com', 'org', 'net', 'edu', 'gov', 'mil', 'int', 'info', 'biz', 'name',
            'pro', 'museum', 'coop', 'aero', 'xxx', 'jobs', 'mobi', 'travel', 'tel',
            # Country code TLDs (major ones)
            'ac', 'ad', 'ae', 'af', 'ag', 'ai', 'al', 'am', 'an', 'ao', 'aq', 'ar', 'as', 'at',
            'au', 'aw', 'ax', 'az', 'ba', 'bb', 'bd', 'be', 'bf', 'bg', 'bh', 'bi', 'bj', 'bm',
            'bn', 'bo', 'br', 'bs', 'bt', 'bv', 'bw', 'by', 'bz', 'ca', 'cc', 'cd', 'cf', 'cg',
            'ch', 'ci', 'ck', 'cl', 'cm', 'cn', 'co', 'cr', 'cs', 'cu', 'cv', 'cx', 'cy', 'cz',
            'de', 'dj', 'dk', 'dm', 'do', 'dz', 'ec', 'ee', 'eg', 'eh', 'er', 'es', 'et', 'eu',
            'fi', 'fj', 'fk', 'fm', 'fo', 'fr', 'ga', 'gb', 'gd', 'ge', 'gf', 'gg', 'gh', 'gi',
            'gl', 'gm', 'gn', 'gp', 'gq', 'gr', 'gs', 'gt', 'gu', 'gw', 'gy', 'hk', 'hm', 'hn',
            'hr', 'ht', 'hu', 'id', 'ie', 'il', 'im', 'in', 'io', 'iq', 'ir', 'is', 'it', 'je',
            'jm', 'jo', 'jp', 'ke', 'kg', 'kh', 'ki', 'km', 'kn', 'kp', 'kr', 'kw', 'ky', 'kz',
            'la', 'lb', 'lc', 'li', 'lk', 'lr', 'ls', 'lt', 'lu', 'lv', 'ly', 'ma', 'mc', 'md',
            'me', 'mg', 'mh', 'mk', 'ml', 'mm', 'mn', 'mo', 'mp', 'mq', 'mr', 'ms', 'mt', 'mu',
            'mv', 'mw', 'mx', 'my', 'mz', 'na', 'nc', 'ne', 'nf', 'ng', 'ni', 'nl', 'no', 'np',
            'nr', 'nu', 'nz', 'om', 'pa', 'pe', 'pf', 'pg', 'ph', 'pk', 'pl', 'pm', 'pn', 'pr',
            'ps', 'pt', 'pw', 'py', 'qa', 're', 'ro', 'rs', 'ru', 'rw', 'sa', 'sb', 'sc', 'sd',
            'se', 'sg', 'sh', 'si', 'sj', 'sk', 'sl', 'sm', 'sn', 'so', 'sr', 'st', 'su', 'sv',
            'sy', 'sz', 'tc', 'td', 'tf', 'tg', 'th', 'tj', 'tk', 'tl', 'tm', 'tn', 'to', 'tp',
            'tr', 'tt', 'tv', 'tw', 'tz', 'ua', 'ug', 'uk', 'um', 'us', 'uy', 'uz', 'va', 'vc',
            've', 'vg', 'vi', 'vn', 'vu', 'wf', 'ws', 'ye', 'yt', 'za', 'zm', 'zw'
        }
        
        for email in candidates:
            # Clean up whitespace and punctuation
            clean_email = re.sub(r'\s+', '', email.strip(".,;:()<>[]{}\"'")).lower()
            
            # Length check and basic validation
            if 5 <= len(clean_email) <= 254 and '@' in clean_email and '.' in clean_email:
                # Skip common false positives - file extensions and common patterns
                file_extensions = [
                    '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.bmp', '.ico',  # Images
                    '.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.mpeg', '.mpg',  # Video
                    '.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a',  # Audio
                    '.css', '.js', '.json', '.xml', '.html', '.htm',  # Web files
                    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',  # Documents
                    '.zip', '.rar', '.tar', '.gz', '.7z',  # Archives
                    '.exe', '.dll', '.bin', '.iso',  # Executables
                ]
                if not any(pattern in clean_email for pattern in file_extensions + [
                    'example.com', 'test.com', 'domain.com', 'yoursite.com',
                    'sampleemail', 'youremail', 'example@'
                ]):
                    # Extract and validate TLD
                    domain_part = clean_email.split('@')[-1] if '@' in clean_email else ''
                    if '.' in domain_part:
                        # Handle multi-part TLDs like co.uk
                        domain_parts = domain_part.split('.')
                        
                        # Check if the last part is a valid TLD
                        last_tld = domain_parts[-1]
                        
                        # For multi-part TLDs, check combinations
                        valid_tld = False
                        if last_tld in valid_tlds:
                            valid_tld = True
                        elif len(domain_parts) >= 2:
                            # Check for two-part TLDs like co.uk, com.au
                            two_part_tld = '.'.join(domain_parts[-2:])
                            common_two_part_tlds = [
                                'co.uk', 'org.uk', 'ac.uk', 'gov.uk', 'com.au', 'org.au',
                                'net.au', 'edu.au', 'co.nz', 'org.nz', 'net.nz', 'co.in',
                                'org.in', 'net.in', 'co.za', 'org.za', 'net.za', 'com.br',
                                'org.br', 'net.br', 'com.mx', 'org.mx', 'net.mx'
                            ]
                            if two_part_tld in common_two_part_tlds:
                                valid_tld = True
                        
                        if valid_tld:
                            cleaned_emails.add(clean_email)
        
        return cleaned_emails
    
    def get_sitemap_urls(self, base_url):
        """
        Try to get URLs from sitemap.xml for better page discovery
        
        Args:
            base_url (str): Base website URL
            
        Returns:
            list: List of URLs from sitemap, prioritized by keywords
        """
        sitemap_urls = []
        parsed_url = urlparse(base_url)
        base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Try common sitemap locations
        sitemap_candidates = [
            f"{base_domain}/page-sitemap.xml",
            f"{base_domain}/sitemap.xml"
        ]
        
        for sitemap_url in sitemap_candidates:
            try:
                response = self._make_request_with_retries(sitemap_url)
                if response and response.status_code == 200:
                    urls = self.parse_sitemap(response.text)
                    if urls:
                        # Filter for priority pages with proper URL structure
                        priority_urls = []
                        for url in urls:
                            url_lower = url.lower()
                            parsed = urlparse(url_lower)
                            path = parsed.path.strip('/')
                            
                            # Only consider if keyword appears early in the path (first 2 segments)
                            path_segments = path.split('/') if path else []
                            
                            # Check if any priority keyword appears in the first 2 path segments
                            for keyword in self.priority_keywords:
                                if len(path_segments) <= 2 and any(keyword in segment for segment in path_segments[:2]):
                                    priority_urls.append(url)
                                    break
                                # Also include exact matches like domain.com/about
                                elif path == keyword or path == f"{keyword}/":
                                    priority_urls.append(url)
                                    break
                        
                        if priority_urls:
                            sitemap_urls.extend(priority_urls[:12])  # Limit to 12 priority pages
                            break
            except Exception as e:
                logger.debug(f"Failed to fetch sitemap {sitemap_url}: {e}")
                continue
        
        return sitemap_urls
    
    def parse_sitemap(self, xml_text):
        """
        Parse sitemap XML and extract URLs
        
        Args:
            xml_text (str): XML content of sitemap
            
        Returns:
            list: List of URLs found in sitemap
        """
        urls = []
        try:
            root = ET.fromstring(xml_text.encode("utf-8", errors="ignore"))
        except ET.ParseError:
            return urls
        
        # Try with namespace
        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        
        # Look for URL locations
        for loc in root.findall(".//sm:url/sm:loc", ns):
            if loc.text:
                urls.append(loc.text.strip())
        
        # Fallback without namespace
        if not urls:
            for loc in root.findall(".//{*}url/{*}loc"):
                if loc.text:
                    urls.append(loc.text.strip())
        
        # Check for sitemap index (child sitemaps)
        for loc in root.findall(".//sm:sitemap/sm:loc", ns):
            if loc.text:
                urls.append(loc.text.strip())
        
        if not urls:
            for loc in root.findall(".//{*}sitemap/{*}loc"):
                if loc.text:
                    urls.append(loc.text.strip())
        
        return urls
    
    def get_page_urls_to_crawl(self, base_url):
        """
        Generate list of URLs to crawl, prioritizing sitemap discovery
        
        Args:
            base_url (str): Base website URL
            
        Returns:
            list: List of URLs to crawl
        """
        urls_to_crawl = [base_url]  # Always include the main page
        
        # Try to get URLs from sitemap first
        sitemap_urls = self.get_sitemap_urls(base_url)
        if sitemap_urls:
            urls_to_crawl.extend(sitemap_urls)
            logger.info(f"Found {len(sitemap_urls)} priority pages from sitemap for {base_url}")
        
        # Also try to discover contact pages by checking homepage links
        try:
            homepage_response = self._make_request_with_retries(base_url)
            if homepage_response and homepage_response.status_code == 200:
                homepage_soup = BeautifulSoup(homepage_response.content, 'html.parser')
                # Find all links on homepage
                all_links = homepage_soup.find_all('a', href=True)
                contact_keywords = ['contact', 'about', 'team', 'support', 'help', 'reach', 'location', 'office']
                
                for link in all_links:
                    href = link.get('href', '')
                    if href:
                        # Convert relative URLs to absolute
                        absolute_url = urljoin(base_url, href)
                        parsed_link = urlparse(absolute_url)
                        
                        # Only include if it's from the same domain
                        if parsed_link.netloc == urlparse(base_url).netloc:
                            href_lower = href.lower()
                            # Check if link text or href contains contact-related keywords
                            link_text = link.get_text().lower() if link.get_text() else ''
                            
                            if any(keyword in href_lower or keyword in link_text for keyword in contact_keywords):
                                if absolute_url not in urls_to_crawl:
                                    urls_to_crawl.append(absolute_url)
                                    logger.info(f"Discovered contact page from homepage: {absolute_url}")
        except Exception as e:
            logger.debug(f"Could not discover links from homepage: {e}")
        
        if not sitemap_urls:
            # Fallback to manual page construction
            parsed_url = urlparse(base_url)
            base_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
            
            # Add common contact page variations (expanded list)
            contact_pages = [
                'contact', 'contact-us', 'contactus', 'contact_us', 'contactus.html', 'contact.html',
                'about', 'about-us', 'aboutus', 'about_us', 'about.html', 'aboutus.html',
                'team', 'staff', 'people', 'leadership', 'team.html', 'our-team',
                'support', 'help', 'info', 'information', 'support.html',
                'reach-us', 'get-in-touch', 'connect', 'services', 'service',
                'location', 'locations', 'office', 'offices', 'address',
                'phone', 'tel', 'call', 'reach', 'find-us'
            ]
            
            for page in contact_pages:
                # Try different URL patterns including trailing slash
                potential_urls = [
                    f"{base_domain}/{page}/",
                    f"{base_domain}/{page}",
                    f"{base_domain}/{page}.html",
                    f"{base_domain}/{page}.php"
                ]
                urls_to_crawl.extend(potential_urls)
        
        # Remove duplicates while preserving order
        seen = set()
        deduped_urls = []
        for url in urls_to_crawl:
            if url not in seen:
                seen.add(url)
                deduped_urls.append(url)
        
        # Limit total pages per site
        return deduped_urls[:15]
    
    def detect_contact_form(self, soup):
        """
        Detect if a page has a contact form with both name and email fields
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            bool: True if contact form is detected (must have name + email fields)
        """
        # Look for forms with common contact-related attributes
        forms = soup.find_all('form')
        
        for form in forms:
            # Check if form has both name and email fields
            has_email_field = bool(
                form.find(['input', 'textarea'], {'type': 'email'}) or 
                form.find(['input', 'textarea'], {'name': re.compile(r'email', re.I)}) or
                form.find(['input', 'textarea'], {'placeholder': re.compile(r'email', re.I)})
            )
            
            has_name_field = bool(
                form.find(['input', 'textarea'], {'name': re.compile(r'name|first|last|full.*name', re.I)}) or
                form.find(['input', 'textarea'], {'placeholder': re.compile(r'name|first|last|full.*name', re.I)}) or
                form.find(['input', 'textarea'], {'id': re.compile(r'name|first|last|full.*name', re.I)})
            )
            
            # Optional: Check for message/subject field (common in contact forms)
            has_message_field = bool(
                form.find(['textarea', 'input'], {'name': re.compile(r'message|subject|comment|inquiry', re.I)}) or
                form.find(['textarea', 'input'], {'placeholder': re.compile(r'message|subject|comment|inquiry', re.I)})
            )
            
            # Must have both name and email fields to be considered a contact form
            if has_email_field and has_name_field:
                return True
        
        return False
    
    def is_valid_contact_page(self, url):
        """
        Check if a URL is a valid contact/about page (not a long blog post or article)
        Made less restrictive to catch more pages with contact information
        
        Args:
            url (str): URL to check
            
        Returns:
            bool: True if URL seems like a proper contact/about page
        """
        parsed = urlparse(url.lower())
        path = parsed.path.strip('/')
        
        # Homepage is always valid
        if path == '' or path == 'index.html' or path == 'index.php':
            return True
        
        # If path is extremely long or has too many segments, it's probably not a contact page
        if len(path) > 100 or path.count('/') > 5:
            return False
            
        # Check for obvious blog post patterns (but allow contact-related blog posts)
        blog_patterns = ['/posts/', '/articles/', '/news/', '/stories/', '/archive/']
        if any(pattern in path for pattern in blog_patterns):
            # But allow if it contains contact-related keywords
            contact_keywords = ['contact', 'about', 'team', 'support']
            if not any(keyword in path for keyword in contact_keywords):
                return False
            
        # Check for date patterns that indicate blog posts (but be less strict)
        import re
        date_pattern = r'/\d{4}/\d{1,2}/\d{1,2}'
        if re.search(date_pattern, path):
            # Allow if it's a contact or about page with date
            contact_keywords = ['contact', 'about', 'team']
            if not any(keyword in path for keyword in contact_keywords):
                return False
            
        return True
    
    def scrape_single_page(self, url):
        """
        Scrape a single page and extract emails
        
        Args:
            url (str): URL to scrape
            
        Returns:
            dict: Dictionary containing URL, emails found, status, and contact form info
        """
        result = {
            'url': url,
            'emails': set(),
            'status': 'Unknown',
            'error': None,
            'has_contact_form': False
        }
        
        # Skip URLs that don't look like proper contact pages (but be less restrictive for homepage)
        parsed_url = urlparse(url)
        is_homepage = parsed_url.path in ['', '/'] or parsed_url.path == '/index.html'
        if not is_homepage and not self.is_valid_contact_page(url):
            result['status'] = 'Skipped - Not a proper contact/about page'
            return result
        
        try:
            # Make the request with retries and rate limiting
            response = self._make_request_with_retries(url)
            if not response:
                result['status'] = 'Error - Request failed after retries'
                result['error'] = 'Request failed after all retry attempts'
                return result
            
            if response.status_code != 200:
                result['status'] = f'Error - HTTP {response.status_code}'
                result['error'] = f'HTTP {response.status_code}'
                return result
            
            # First, extract emails from raw HTML (before parsing) to catch emails in comments, etc.
            # This is the most important step - check the raw page source thoroughly
            raw_html = response.text
            
            # Extract emails from raw HTML multiple times with different approaches
            raw_emails = self.extract_emails_from_text(raw_html)
            result['emails'].update(raw_emails)
            
            # Also check HTML comments specifically
            comment_pattern = re.compile(r'<!--.*?-->', re.DOTALL)
            comments = comment_pattern.findall(raw_html)
            for comment in comments:
                comment_emails = self.extract_emails_from_text(comment)
                result['emails'].update(comment_emails)
            
            # Check for emails in JavaScript strings and variables
            js_string_pattern = re.compile(r'["\']([^"\']*@[^"\']*\.[^"\']*)["\']', re.IGNORECASE)
            js_matches = js_string_pattern.findall(raw_html)
            for match in js_matches:
                js_emails = self.extract_emails_from_text(match)
                result['emails'].update(js_emails)
            
            # Check for emails in data attributes and JSON-like structures
            json_like_pattern = re.compile(r'["\']email["\']\s*:\s*["\']([^"\']*@[^"\']*\.[^"\']*)["\']', re.IGNORECASE)
            json_matches = json_like_pattern.findall(raw_html)
            for match in json_matches:
                json_emails = self.extract_emails_from_text(match)
                result['emails'].update(json_emails)
            
            # Parse the HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check for contact form before removing scripts
            result['has_contact_form'] = self.detect_contact_form(soup)
            
            # Extract emails from script tags BEFORE removing them (some sites obfuscate emails in JS)
            script_tags = soup.find_all('script')
            for script in script_tags:
                if script.string:
                    script_emails = self.extract_emails_from_text(script.string)
                    result['emails'].update(script_emails)
            
            # Extract emails from data attributes (some sites store emails in data-* attributes)
            for element in soup.find_all(attrs={'data-email': True}):
                data_email = element.get('data-email', '')
                if data_email:
                    email_set = self.extract_emails_from_text(data_email)
                    result['emails'].update(email_set)
            
            # Extract emails from meta tags
            meta_tags = soup.find_all('meta')
            for meta in meta_tags:
                content = meta.get('content', '')
                if content:
                    meta_emails = self.extract_emails_from_text(content)
                    result['emails'].update(meta_emails)
            
            # Extract emails from all link tags (not just mailto)
            all_links = soup.find_all('a')
            for link in all_links:
                href = link.get('href', '')
                if href:
                    # Check href for emails
                    href_emails = self.extract_emails_from_text(href)
                    result['emails'].update(href_emails)
                
                # Check link text
                if link.string:
                    link_text_emails = self.extract_emails_from_text(link.string)
                    result['emails'].update(link_text_emails)
            
            # Extract emails from all input fields (type="email" or with email in name/placeholder)
            input_fields = soup.find_all(['input', 'textarea'])
            for field in input_fields:
                # Check value attribute
                value = field.get('value', '')
                if value:
                    value_emails = self.extract_emails_from_text(value)
                    result['emails'].update(value_emails)
                
                # Check placeholder attribute
                placeholder = field.get('placeholder', '')
                if placeholder:
                    placeholder_emails = self.extract_emails_from_text(placeholder)
                    result['emails'].update(placeholder_emails)
            
            # Now remove script and style elements for text extraction
            soup_copy = BeautifulSoup(response.content, 'html.parser')
            for script in soup_copy(["script", "style"]):
                script.decompose()
            
            # Get text content
            text_content = soup_copy.get_text()
            
            # Also get HTML content for mailto links and other patterns
            html_content = str(soup_copy)
            
            # Extract emails from both text and HTML content
            emails_from_text = self.extract_emails_from_text(text_content)
            emails_from_html = self.extract_emails_from_text(html_content)
            
            # Combine all found emails
            result['emails'].update(emails_from_text)
            result['emails'].update(emails_from_html)
            
            # Additional mailto link extraction for extra safety
            mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.I))
            for link in mailto_links:
                href = link.get('href', '') if hasattr(link, 'get') else ''
                if href and isinstance(href, str):
                    # Handle mailto: links (case insensitive)
                    email = href.replace('mailto:', '').replace('MAILTO:', '').split('?')[0].split('&')[0].strip()
                    # Apply same TLD validation as in extract_emails_from_text
                    email_set = self.extract_emails_from_text(email)
                    result['emails'].update(email_set)
            
            result['status'] = f'Success - Found {len(result["emails"])} emails'
            
        except Exception as e:
            result['status'] = 'Error - Parsing error'
            result['error'] = f'Error parsing page content: {str(e)}'
            logger.warning(f"Error parsing {url}: {e}")
        
        return result
    
    def scrape_website(self, url):
        """
        Scrape a website and extract emails from multiple pages with timeout handling
        
        Args:
            url (str): URL to scrape
            
        Returns:
            dict: Dictionary containing URL, emails found, and status
        """
        result = {
            'url': url,
            'emails': set(),
            'status': 'Unknown',
            'error': None,
            'pages_crawled': [],
            'successful_pages': 0,
            'email_sources': [],  # Track which pages actually found emails
            'has_contact_form': False
        }
        
        # Start timing the entire website processing
        site_start_time = time.time()
        
        try:
            # Normalize the URL
            normalized_url = self.normalize_url(url)
            result['url'] = normalized_url
            
            # Get all pages to crawl
            urls_to_crawl = self.get_page_urls_to_crawl(normalized_url)
            
            # Track which pages were successfully crawled
            all_emails = set()
            successful_pages = 0
            pages_crawled = []
            
            # Crawl each page with timeout checking
            for page_url in urls_to_crawl:
                # Check if we've exceeded the site timeout
                elapsed_time = time.time() - site_start_time
                if elapsed_time > self.site_timeout:
                    logger.warning(f"Site timeout exceeded for {normalized_url} after {elapsed_time:.1f}s")
                    result['status'] = f'Skipped - Taking longer than usual ({elapsed_time:.1f}s timeout)'
                    result['error'] = f'Site processing timeout after {elapsed_time:.1f} seconds'
                    break
                
                try:
                    page_result = self.scrape_single_page(page_url)
                    pages_crawled.append({
                        'url': page_url,
                        'emails_found': len(page_result['emails']),
                        'status': page_result['status'],
                        'has_contact_form': page_result.get('has_contact_form', False)
                    })
                    
                    # Track contact form detection at site level
                    if page_result.get('has_contact_form', False):
                        result['has_contact_form'] = True
                    
                    if page_result['emails']:
                        all_emails.update(page_result['emails'])
                        # Track which page found emails
                        email_sources = result.get('email_sources', [])
                        email_sources.append(page_url)
                        result['email_sources'] = email_sources
                        logger.info(f"Found {len(page_result['emails'])} emails on {page_url}")
                    
                    # Don't log every 404 or failed page to reduce noise
                    if 'Success' in page_result['status']:
                        successful_pages += 1
                        
                except Exception as e:
                    # Continue with other pages even if one fails
                    logger.debug(f"Failed to crawl {page_url}: {e}")
                    continue
            
            # Limit to maximum 5 emails per website
            all_emails_list = list(all_emails)
            limited_emails = all_emails_list[:5]
            
            # Only update status if we haven't already set a timeout status
            if 'Skipped' not in result['status']:
                result['emails'] = limited_emails
                result['pages_crawled'] = pages_crawled
                result['successful_pages'] = successful_pages
                processing_time = time.time() - site_start_time
                total_found = len(all_emails_list)
                displayed = len(limited_emails)
                if total_found > displayed:
                    result['status'] = f'Success - Found {total_found} emails (showing {displayed}) from {len(result.get("email_sources", []))} pages ({processing_time:.1f}s)'
                else:
                    result['status'] = f'Success - Found {displayed} emails from {len(result.get("email_sources", []))} pages ({processing_time:.1f}s)'
            else:
                # For timeout cases, still return what we found
                result['emails'] = limited_emails
                result['pages_crawled'] = pages_crawled
                result['successful_pages'] = successful_pages
            
        except Exception as e:
            elapsed_time = time.time() - site_start_time
            if elapsed_time > self.site_timeout:
                result['status'] = f'Skipped - Taking longer than usual ({elapsed_time:.1f}s timeout)'
                result['error'] = f'Site processing timeout after {elapsed_time:.1f} seconds'
            else:
                result['status'] = f'Error - {str(e)}'
                result['error'] = str(e)
            logger.warning(f"Error crawling {url}: {e}")
        
        # Ensure emails are a list (already limited to 5)
        if isinstance(result['emails'], set):
            result['emails'] = list(result['emails'])[:5]
        elif isinstance(result['emails'], list):
            result['emails'] = result['emails'][:5]
        
        return result
    
    def extract_emails_from_urls(self, urls, progress_callback=None):
        """
        Extract emails from multiple URLs concurrently with proper timeout handling
        
        Args:
            urls (list): List of URLs to process
            progress_callback (function): Optional callback function for progress updates
            
        Returns:
            list: List of dictionaries containing results for each URL
        """
        results = []
        completed = 0
        
        # Use ThreadPoolExecutor for concurrent processing
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_url = {
                executor.submit(self.scrape_website, url): url 
                for url in urls
            }
            
            # Process completed tasks without global timeout
            for future in as_completed(future_to_url):
                try:
                    # Individual websites handle their own timeouts internally
                    result = future.result()
                    results.append(result)
                    completed += 1
                    
                    # Call progress callback if provided
                    if progress_callback:
                        progress_callback(completed, len(urls))
                        
                    logger.info(f"Processed {result['url']}: {result['status']}")
                    
                except Exception as e:
                    url = future_to_url[future]
                    
                    # Create error result for any unhandled exceptions
                    error_result = {
                        'url': url,
                        'emails': [],
                        'status': 'Skipped - Processing error',
                        'error': f'Unexpected error: {str(e)}',
                        'pages_crawled': [],
                        'successful_pages': 0
                    }
                    
                    results.append(error_result)
                    completed += 1
                    
                    if progress_callback:
                        progress_callback(completed, len(urls))
                        
                    logger.warning(f"Failed to process {url}: {e}")
        
        return results
    
    def close(self):
        """Close the session"""
        self.session.close()
