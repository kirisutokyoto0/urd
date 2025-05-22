# Enhanced search detection patterns
SEARCH_ENGINES = [
    'google.com', 'bing.com', 'yahoo.com', 'duckduckgo.com', 'yandex.com',
    'baidu.com', 'ask.com', 'ecosia.org', 'startpage.com', 'searx.org'
]

# Academic/question keywords that suggest searching for answers
ACADEMIC_KEYWORDS = [
    'how to', 'what is', 'define', 'definition', 'explain', 'solve', 'solution',
    'answer', 'formula', 'equation', 'theorem', 'proof', 'calculate', 'find',
    'determine', 'derive', 'show that', 'prove that', 'examples of', 'steps to',
    'tutorial', 'guide', 'homework', 'assignment', 'quiz', 'test', 'exam',
    'study', 'lesson', 'learn', 'understand', 'meaning', 'concept', 'theory',
    'method', 'technique', 'approach', 'strategy', 'tips', 'tricks', 'chatgpt', 'gpt', 'GPT'
]

# Subject-specific terms (add more based on your exam subjects)
SUBJECT_KEYWORDS = {
    'mathematics': ['algebra', 'calculus', 'geometry', 'trigonometry', 'statistics', 
                   'derivative', 'integral', 'matrix', 'vector', 'polynomial', 'logarithm'],
    'science': ['physics', 'chemistry', 'biology', 'molecule', 'atom', 'cell', 
               'reaction', 'equation', 'experiment', 'hypothesis', 'theory'],
    'programming': ['python', 'java', 'javascript', 'algorithm', 'function', 
                   'variable', 'loop', 'array', 'object', 'class', 'method'],
    'general': ['history', 'literature', 'geography', 'economics', 'psychology',
               'philosophy', 'sociology', 'political', 'analysis', 'essay', 'explain', 'summarize', 'summarise', 'interpret', 'discuss']
}

# Question patterns that suggest academic searches
QUESTION_PATTERNS = [
    r'\b(how|what|why|when|where|which|who)\s+(?:is|are|do|does|can|will|would|should)',
    r'\bsolve\s+(?:for|the|this)',
    r'\bfind\s+(?:the|a|an)',
    r'\bcalculate\s+(?:the|a)',
    r'\bprove\s+(?:that|the)',
    r'\bexplain\s+(?:how|why|what|the)',
    r'\bdefine\s+(?:the|a|an)',
    r'\bderive\s+(?:the|a|an)',
    r'\bdetermine\s+(?:the|if|whether)'
]

# Document detection patterns - only dedicated document applications
DOCUMENT_APPLICATIONS = {
    'pdf': ['acrobat', 'foxit', 'sumatra', 'pdfviewer', 'pdfreader', 'adobereader'],
    'word': ['winword', 'msword', 'wordpad', 'writer', 'libreoffice', 'openoffice'],
    'powerpoint': ['powerpnt', 'powerpoint', 'impress', 'presentation'],
    'text': ['notepad', 'notepad++', 'sublime', 'atom', 'vscode', 'vim', 'nano', 'gedit', 'texteditor']
}

DOCUMENT_EXTENSIONS = {
    'pdf': ['.pdf'],
    'word': ['.doc', '.docx', '.rtf', '.odt'],
    'powerpoint': ['.ppt', '.pptx', '.odp'],
    'text': ['.txt', '.log', '.md', '.readme', '.text']
}

# Patterns to detect document files in window titles
DOCUMENT_TITLE_PATTERNS = {
    'pdf': [
        r'\.pdf\b',
        r'Adobe Acrobat',
        r'PDF Reader',
        r'Foxit Reader',
        r'SumatraPDF',
        r'- PDF$'
    ],
    'word': [
        r'\.docx?\b',
        r'Microsoft Word',
        r'\.rtf\b',
        r'\.odt\b',
        r'- Word$',
        r'Document\d* - Word'
    ],
    'powerpoint': [
        r'\.pptx?\b',
        r'Microsoft PowerPoint',
        r'\.odp\b',
        r'- PowerPoint$',
        r'Presentation\d* - PowerPoint',
        r'Slide \d+ of \d+'
    ],
    'text': [
        r'\.txt\b',
        r'Notepad',
        r'\.log\b',
        r'\.md\b',
        r'README',
        r'- Notepad$',
        r'Untitled - Notepad'
    ]
}



import psutil
import json
import time
import os
import win32gui
import re
from urllib.parse import urlparse, unquote
import difflib

# Load blacklist and search patterns
with open("blacklist.json") as f:
    data = json.load(f)
    blacklist_apps = [app.lower() for app in data["apps"]]
    blacklist_websites = [site.lower() for site in data["websites"]]

class DocumentDetector:
    def __init__(self):
        self.detected_documents = set()
        self.document_history = []
        
    def detect_document_from_process(self, process_name):
        """Detect document type from process name - only dedicated document applications"""
        process_lower = process_name.lower()
        detected_types = []
        
        for doc_type, app_names in DOCUMENT_APPLICATIONS.items():
            for app_name in app_names:
                # More precise matching to avoid false positives
                if (app_name == process_lower.replace('.exe', '') or 
                    process_lower.startswith(app_name) or 
                    process_lower == f"{app_name}.exe"):
                    detected_types.append(doc_type)
                    break
        
        return detected_types
    
    def detect_document_from_title(self, title):
        """Detect document type and filename from window title - enhanced precision"""
        detected_documents = []
        
        # Only detect if there's clear evidence of document viewing
        for doc_type, patterns in DOCUMENT_TITLE_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, title, re.IGNORECASE)
                if match:
                    # Additional validation for browsers - only count if PDF is explicitly in title
                    if doc_type == 'pdf':
                        # Only detect PDF if the title explicitly mentions PDF or has .pdf extension
                        if not (re.search(r'\.pdf\b', title, re.IGNORECASE) or 
                               re.search(r'PDF', title) or 
                               'Adobe Acrobat' in title or 
                               'PDF Reader' in title):
                            continue
                    
                    # Try to extract filename
                    filename = self.extract_filename_from_title(title, doc_type)
                    detected_documents.append({
                        'type': doc_type,
                        'filename': filename,
                        'title': title
                    })
                    break
        
        return detected_documents
    
    def extract_filename_from_title(self, title, doc_type):
        """Extract filename from window title"""
        # Common patterns for extracting filenames from titles
        filename_patterns = [
            r'([^\\/:*?"<>|]+\.(?:pdf|docx?|pptx?|txt|rtf|odt|odp|log|md))',
            r'([^-]+) - (?:Microsoft (?:Word|PowerPoint)|Adobe Acrobat|Notepad)',
            r'^([^-]+) -',
            r'([^\\/:*?"<>|]+) \(',
        ]
        
        for pattern in filename_patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                filename = match.group(1).strip()
                # Validate that it looks like a reasonable filename
                if len(filename) > 0 and not filename.isspace():
                    return filename
        
        return "Unknown file"
    
    def is_suspicious_document(self, doc_info):
        """Check if document might contain exam-related content"""
        title = doc_info.get('title', '').lower()
        filename = doc_info.get('filename', '').lower()
        
        suspicious_keywords = [
            'exam', 'test', 'quiz', 'answer', 'solution', 'cheat', 'sheet',
            'notes', 'study', 'guide', 'homework', 'assignment', 'formula',
            'reference', 'help', 'tutorial', 'hint', 'tip', 'key'
        ]
        
        suspicion_score = 0
        matched_keywords = []
        
        text_to_check = f"{title} {filename}"
        
        for keyword in suspicious_keywords:
            if keyword in text_to_check:
                suspicion_score += 1
                matched_keywords.append(keyword)
        
        return suspicion_score >= 1, suspicion_score, matched_keywords

# Initialize detectors
search_detector = None  # Will be initialized as SearchDetector class
document_detector = DocumentDetector()

class SearchDetector:
    def __init__(self):
        self.previous_titles = set()
        self.search_history = []
        self.max_history = 50
        
    def extract_search_query(self, url):
        """Extract search query from URL"""
        try:
            # Common search parameter names
            search_params = ['q', 'query', 'search', 's', 'p', 'text', 'keywords']
            
            from urllib.parse import parse_qs, urlparse
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            
            for param in search_params:
                if param in params and params[param]:
                    query = unquote(params[param][0])
                    return query.strip()
                    
        except Exception:
            pass
        return None
    
    def detect_search_in_title(self, title):
        """Detect if window title suggests searching"""
        title_lower = title.lower()
        
        # Check for search engines in title
        for engine in SEARCH_ENGINES:
            if engine in title_lower:
                # Extract potential search query from title
                query = self.extract_query_from_title(title)
                if query:
                    return True, f"Search detected on {engine}: {query[:50]}..."
                return True, f"Search engine detected: {engine}"
        
        # Check for academic keywords in title
        academic_score = self.calculate_academic_score(title_lower)
        if academic_score >= 2:  # Threshold for suspicious academic content
            return True, f"Academic content detected (score: {academic_score})"
        
        return False, None
    
    def extract_query_from_title(self, title):
        """Extract search query from browser title"""
        # Common patterns for search queries in titles
        patterns = [
            r'(.+?)\s*-\s*Google Search',
            r'(.+?)\s*-\s*Bing',
            r'(.+?)\s*-\s*Yahoo Search',
            r'(.+?)\s*at DuckDuckGo',
            r'Search:\s*(.+)',
            r'(.+?)\s*\|\s*.*search'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title, re.IGNORECASE)
            if match:
                query = match.group(1).strip()
                if len(query) > 3:  # Ignore very short queries
                    return query
        
        return None
    
    def calculate_academic_score(self, text):
        """Calculate how likely the text is academic/educational content"""
        score = 0
        text_words = text.split()
        
        # Check for academic keywords
        for keyword in ACADEMIC_KEYWORDS:
            if keyword in text:
                score += 2
        
        # Check for question patterns
        for pattern in QUESTION_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                score += 3
        
        # Check for subject-specific keywords
        for subject, keywords in SUBJECT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    score += 1
        
        # Check for mathematical symbols/expressions
        math_patterns = [r'\d+\s*[+\-*/=]\s*\d+', r'\b\w+\s*=\s*\w+', r'\b[a-z]\s*=\s*\d+']
        for pattern in math_patterns:
            if re.search(pattern, text):
                score += 2
        
        return score
    
    def is_suspicious_search(self, query):
        """Determine if a search query is suspicious for an exam context"""
        if not query or len(query.strip()) < 3:
            return False, 0
        
        query_lower = query.lower().strip()
        suspicion_score = 0
        reasons = []
        
        # High suspicion indicators
        high_risk_phrases = [
            'homework help', 'assignment help', 'exam answers', 'test answers',
            'solutions manual', 'answer key', 'cheat sheet', 'study guide answers'
        ]
        
        for phrase in high_risk_phrases:
            if phrase in query_lower:
                suspicion_score += 10
                reasons.append(f"High-risk phrase: '{phrase}'")
        
        # Medium suspicion indicators
        academic_score = self.calculate_academic_score(query_lower)
        if academic_score >= 3:
            suspicion_score += academic_score
            reasons.append(f"Academic content (score: {academic_score})")
        
        # Question patterns
        for pattern in QUESTION_PATTERNS:
            if re.search(pattern, query_lower):
                suspicion_score += 2
                reasons.append("Question pattern detected")
                break
        
        # Long queries often indicate specific questions
        if len(query.split()) > 6:
            suspicion_score += 1
            reasons.append("Long query (potentially specific question)")
        
        return suspicion_score >= 3, suspicion_score, reasons

# Initialize search detector
search_detector = SearchDetector()

def extract_domain_from_title(title):
    """Extract potential domain names from browser window titles"""
    url_patterns = [
        r'https?://([^\s/]+)',
        r'www\.([^\s/]+)',
        r'([a-zA-Z0-9-]+\.[a-zA-Z]{2,})'
    ]
    
    domains = []
    for pattern in url_patterns:
        matches = re.findall(pattern, title.lower())
        for match in matches:
            if isinstance(match, tuple):
                match = match[0] if match[0] else match[1]
            domain = match.strip().rstrip('/')
            if domain and '.' in domain:
                domains.append(domain)
    
    return domains

def is_blacklisted_website(title):
    """Check if browser title contains blacklisted websites"""
    title_lower = title.lower()
    domains_in_title = extract_domain_from_title(title)
    
    for website in blacklist_websites:
        if website in title_lower:
            return True, website
    
    for domain in domains_in_title:
        for website in blacklist_websites:
            if website in domain or domain in website:
                return True, website
    
    return False, None

def scan_processes():
    print("=== Process Scan ===")
    flagged_processes = []
    detected_documents = []
    
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            pid = proc.info['pid']
            process_name = proc.info['name']
            
            # Skip processes with empty or None names
            if not process_name or process_name.strip() == '':
                continue
                
            name = process_name.lower()
            
            flagged = False
            matched_item = None
            
            # Check for blacklisted apps
            for blacklisted_app in blacklist_apps:
                if blacklisted_app in name or name in blacklisted_app:
                    flagged = True
                    matched_item = blacklisted_app
                    break
            
            # Check for document applications
            doc_types = document_detector.detect_document_from_process(process_name)
            if doc_types:
                detected_documents.append({
                    'pid': pid,
                    'process': process_name,
                    'types': doc_types
                })
            
            status = "⚠️ FLAGGED" if flagged else "📄 DOC" if doc_types else "OK"
            
            if flagged:
                color = "\033[91m"  # Red
            elif doc_types:
                color = "\033[94m"  # Blue
            else:
                color = "\033[92m"  # Green
            
            reset_color = "\033[0m"
            
            print(f"PID {pid:<6} | Process: {process_name:<30} | Status: {color}{status}{reset_color}")
            
            if doc_types:
                print(f"        └─ Document types: {', '.join(doc_types).upper()}")
            
            if flagged:
                flagged_processes.append({
                    'pid': pid,
                    'name': process_name,
                    'matched': matched_item
                })
                
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    
    return flagged_processes, detected_documents

def enum_window_callback(hwnd, window_titles):
    if win32gui.IsWindowVisible(hwnd):
        title = win32gui.GetWindowText(hwnd)
        if title:
            window_titles.append(title)

def scan_browser_titles():
    print("\n=== Browser Title & Search Detection Scan ===")
    titles = []
    flagged_titles = []
    search_violations = []
    document_windows = []
    suspicious_documents = []
    
    win32gui.EnumWindows(enum_window_callback, titles)
    
    for title in titles:
        # Check for blacklisted websites
        is_blacklisted, matched_website = is_blacklisted_website(title)
        
        # Check for search activity
        is_search, search_info = search_detector.detect_search_in_title(title)
        
        # Check for document files in window titles
        detected_docs = document_detector.detect_document_from_title(title)
        
        # Extract and analyze search queries
        search_query = search_detector.extract_query_from_title(title)
        is_suspicious_search = False
        suspicion_score = 0
        suspicion_reasons = []
        
        if search_query:
            is_suspicious_search, suspicion_score, suspicion_reasons = search_detector.is_suspicious_search(search_query)
        
        # Check for suspicious documents
        for doc in detected_docs:
            is_sus_doc, sus_score, sus_keywords = document_detector.is_suspicious_document(doc)
            if is_sus_doc:
                suspicious_documents.append({
                    'document': doc,
                    'score': sus_score,
                    'keywords': sus_keywords,
                    'title': title
                })
        
        # Determine overall status
        flagged = is_blacklisted or is_search or is_suspicious_search
        has_documents = len(detected_docs) > 0
        has_suspicious_docs = any(document_detector.is_suspicious_document(doc)[0] for doc in detected_docs)
        
        if flagged or has_suspicious_docs:
            status = "🚨 VIOLATION"
            color = "\033[91m"  # Red
        elif has_documents:
            status = "📄 DOCUMENT"
            color = "\033[94m"  # Blue
        elif search_query:
            status = "⚠️ SEARCH"
            color = "\033[93m"  # Yellow
        else:
            status = "OK"
            color = "\033[92m"  # Green
        
        reset_color = "\033[0m"
        display_title = (title[:77] + "...") if len(title) > 80 else title
        
        print(f"Window: {display_title:<80} | Status: {color}{status}{reset_color}")
        
        # Show details for flagged items
        if is_blacklisted:
            flagged_titles.append({
                'title': title,
                'matched': matched_website,
                'type': 'blacklisted'
            })
            print(f"        └─ Blacklisted site: {matched_website}")
        
        if is_search:
            print(f"        └─ Search activity: {search_info}")
        
        if search_query:
            print(f"        └─ Query: \"{search_query[:60]}{'...' if len(search_query) > 60 else ''}\"")
            
            if is_suspicious_search:
                search_violations.append({
                    'title': title,
                    'query': search_query,
                    'score': suspicion_score,
                    'reasons': suspicion_reasons
                })
                print(f"        └─ 🚨 SUSPICIOUS (Score: {suspicion_score})")
                for reason in suspicion_reasons[:2]:  # Show first 2 reasons
                    print(f"            • {reason}")
        
        # Show document details
        if detected_docs:
            document_windows.extend(detected_docs)
            for doc in detected_docs:
                is_sus, sus_score, sus_keywords = document_detector.is_suspicious_document(doc)
                sus_indicator = f" 🚨 SUSPICIOUS (Score: {sus_score})" if is_sus else ""
                print(f"        └─ 📄 {doc['type'].upper()}: {doc['filename']}{sus_indicator}")
                if is_sus and sus_keywords:
                    print(f"            • Keywords: {', '.join(sus_keywords[:3])}")
    
    return flagged_titles, search_violations, document_windows, suspicious_documents

def display_summary(flagged_processes, flagged_titles, search_violations, process_documents, document_windows, suspicious_documents):
    """Display a comprehensive summary of all violations"""
    print("\n" + "="*80)
    print("EXAM SECURITY ALERT SUMMARY")
    print("="*80)
    
    total_violations = len(flagged_processes) + len(flagged_titles) + len(search_violations) + len(suspicious_documents)
    total_documents = len(process_documents) + len(document_windows)
    
    if flagged_processes:
        print(f"\n🚨 FLAGGED PROCESSES ({len(flagged_processes)}):")
        for proc in flagged_processes:
            print(f"   • PID {proc['pid']}: {proc['name']} (matched: {proc['matched']})")
    
    if flagged_titles:
        print(f"\n🚨 BLACKLISTED WEBSITES ({len(flagged_titles)}):")
        for window in flagged_titles:
            print(f"   • {window['title'][:60]}... (matched: {window['matched']})")
    
    if search_violations:
        print(f"\n🚨 SUSPICIOUS SEARCH ACTIVITY ({len(search_violations)}):")
        for violation in search_violations:
            print(f"   • Query: \"{violation['query'][:50]}{'...' if len(violation['query']) > 50 else ''}\"")
            print(f"     Risk Score: {violation['score']} | Reasons: {', '.join(violation['reasons'][:2])}")
    
    if suspicious_documents:
        print(f"\n🚨 SUSPICIOUS DOCUMENTS ({len(suspicious_documents)}):")
        for sus_doc in suspicious_documents:
            doc = sus_doc['document']
            print(f"   • {doc['type'].upper()}: {doc['filename']} (Score: {sus_doc['score']})")
            print(f"     Keywords: {', '.join(sus_doc['keywords'][:3])}")
    
    if total_documents > 0:
        print(f"\n📄 DOCUMENTS DETECTED ({total_documents}):")
        
        # Show process-based documents
        doc_types_from_processes = {}
        for proc_doc in process_documents:
            for doc_type in proc_doc['types']:
                if doc_type not in doc_types_from_processes:
                    doc_types_from_processes[doc_type] = []
                doc_types_from_processes[doc_type].append(proc_doc['process'])
        
        for doc_type, processes in doc_types_from_processes.items():
            print(f"   • {doc_type.upper()} applications: {', '.join(set(processes))}")
        
        # Show window-based documents
        doc_types_from_windows = {}
        for doc in document_windows:
            doc_type = doc['type']
            if doc_type not in doc_types_from_windows:
                doc_types_from_windows[doc_type] = []
            doc_types_from_windows[doc_type].append(doc['filename'])
        
        for doc_type, filenames in doc_types_from_windows.items():
            print(f"   • {doc_type.upper()} files: {', '.join(set(filenames))}")
    
    if total_violations == 0 and total_documents == 0:
        print("\n✅ No violations or documents detected")
    elif total_violations == 0:
        print(f"\n📄 {total_documents} document(s) detected - Review for exam relevance")
    else:
        print(f"\n⚠️  TOTAL VIOLATIONS: {total_violations}")
        if total_documents > 0:
            print(f"📄 TOTAL DOCUMENTS: {total_documents}")
        print("⚠️  RECOMMENDED ACTION: Review student activity immediately")
    
    print("="*80)

def main_monitor():
    try:
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("🔍 ENHANCED EXAM MONITORING SYSTEM")
        print("Monitoring for:")
        print("• Unauthorized applications and websites")
        print("• Search engine activity")
        print("• Suspicious academic queries")
        print("• Document files (PDF, Word, PowerPoint, Text)")
        print("• Potential answer-seeking behavior")
        print("Press Ctrl+C to stop.\n")
        
        flagged_processes, process_documents = scan_processes()
        flagged_titles, search_violations, document_windows, suspicious_documents = scan_browser_titles()
        
        display_summary(flagged_processes, flagged_titles, search_violations, 
                       process_documents, document_windows, suspicious_documents)
        
        total_violations = len(flagged_processes) + len(flagged_titles) + len(search_violations) + len(suspicious_documents)
        return total_violations > 0
        
    except Exception as e:
        print(f"Error during monitoring: {e}")
        return False

# Main execution
if __name__ == "__main__":
    try:
        print("Starting enhanced monitoring system with document detection...")
        print(f"Loaded {len(blacklist_apps)} applications and {len(blacklist_websites)} websites to monitor")
        print(f"Monitoring {len(SEARCH_ENGINES)} search engines")
        print(f"Loaded {len(ACADEMIC_KEYWORDS)} academic keywords and {sum(len(v) for v in SUBJECT_KEYWORDS.values())} subject-specific terms")
        
        # Show document types being monitored
        total_doc_apps = sum(len(apps) for apps in DOCUMENT_APPLICATIONS.values())
        total_doc_extensions = sum(len(exts) for exts in DOCUMENT_EXTENSIONS.values())
        print(f"Monitoring {total_doc_apps} document applications and {total_doc_extensions} file extensions")
        print("Document types: PDF, Word, PowerPoint, Text files")
        
        time.sleep(3)
        
        while True:
            violations_detected = main_monitor()
            
            if violations_detected:
                # You could add logging, alerts, or automatic actions here
                print("\n🚨 ALERT: Potential exam violations detected!")
            
            time.sleep(5)  # Check every 5 seconds
            
    except KeyboardInterrupt:
        print("\n\n🛑 Monitoring stopped by user.")
    except FileNotFoundError:
        print("❌ Error: blacklist.json file not found!")
        print("Please ensure the JSON file is in the same directory as this script.")
    except json.JSONDecodeError:
        print("❌ Error: Invalid JSON format in blacklist.json!")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")