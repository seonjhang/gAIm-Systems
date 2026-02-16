# asap_hockey_A_only.py
import re, time, random, csv, os
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup, NavigableString

BASE = "https://www.asapsports.com"
HOCKEY_ROOT = "https://www.asapsports.com/showcat.php?id=5&event=yes"

session = requests.Session()
session.headers.update({
    "User-Agent": "Academic research bot",
    "Referer": HOCKEY_ROOT,
    "Accept-Language": "en-US,en;q=0.9",
})

# ---- utils -------------------------------------------------------------------
MONTH_RE = r"(January|February|March|April|May|June|July|August|September|October|November|December)"
DATE_RE  = rf"{MONTH_RE}\s+\d{{1,2}},\s+\d{{4}}"
SPEAKER_LABEL = re.compile(r"^\s*([A-Z][A-Z\s\.\-']{2,}):\s", re.M)  # e.g., WYATT AAMODT:

def is_asapsports(url: str) -> bool:
    return urlparse(url).netloc.lower().endswith("asapsports.com")

def get_soup(url: str) -> BeautifulSoup:
    if not is_asapsports(url):
        raise RuntimeError(f"skip non-asapsports domain: {url}")
    for i in range(6):  # Try up to 6 times
        try:
            # Increase timeout progressively
            timeout_val = 45 + (i * 15)  # Start at 45s, increase by 15s each retry
            r = session.get(url, timeout=timeout_val)
            if r.status_code == 200:
                return BeautifulSoup(r.text, "html.parser")
            if r.status_code in (429, 500, 502, 503, 504):
                time.sleep(2**i + random.random())
                continue
            r.raise_for_status()
        except requests.exceptions.ReadTimeout:
            print(f"[Timeout] Attempt {i+1}/6 for {url}, retrying...")
            if i < 5:
                time.sleep(5 + random.random() * 5)  # Wait 5-10 seconds before retry
                continue
            else:
                print(f"[Error] Timeout after 6 attempts: {url}")
                raise
        except requests.exceptions.RequestException as e:
            print(f"[Error] Request failed: {e}")
            if i < 5:
                time.sleep(3 + random.random() * 3)
                continue
            else:
                raise
    
    raise RuntimeError(f"Failed to fetch {url}")

# ---- step 1: A–Z ------------------------------------
def extract_letter_links():
    soup = get_soup(HOCKEY_ROOT)
    h2 = soup.select_one('h2:-soup-contains("Interviewee")')
    if not h2:
        raise RuntimeError("Interviewee header not found")

    links = set()
    tbl = h2.find_next("table")
    # letters may be spread across 1~3 adjacent tables
    for _ in range(3):
        if not tbl: break
        for a in tbl.select("a[href]"):
            t = (a.get_text() or "").strip()
            if len(t) == 1 and t.isalpha():
                full = urljoin(BASE, a["href"])
                if is_asapsports(full):
                    links.add(full)
        tbl = tbl.find_next_sibling("table")
    links = sorted(links)
    print(f"[letters] found: {len(links)}")
    return links

# ---- step 2: players under a letter --------------------------
def extract_player_links(letter_url: str):
    soup = get_soup(letter_url)
    main = soup.find(id="content") or soup
    players = []
    for a in main.select("a[href]"):
        name = a.get_text(" ", strip=True)
        href = urljoin(BASE, a["href"])
        if not is_asapsports(href):
            continue
        if not re.search(r"show_player\.php", href, re.I):
            continue
        if not name or len(name) < 3:
            continue
        players.append((name, href))
    # dedupe by href
    out, seen = [], set()
    for n, u in players:
        if u in seen: continue
        seen.add(u)
        out.append((n, u))
    print(f"[players] {letter_url[-1:].upper()}: {len(out)}")
    return out

# ---- step 3: interview links on a player page --------------------------------
def extract_interview_links(player_url: str):
    soup = get_soup(player_url)
    main = soup.find(id="content") or soup
    h1 = main.find("h1")
    scope = h1.find_all_next(["p","li","table","div"]) if h1 else main.find_all(["p","li","table","div"])

    items = []
    for node in scope:
        # stop before footer
        txt_low = node.get_text(" ", strip=True).lower()
        if any(k in txt_low for k in ["fastscripts transcript by asap sports",
                                      "about asap sports", "asap sports, inc."]):
            break
        for a in node.find_all("a", href=True):
            href = urljoin(BASE, a["href"])
            if not is_asapsports(href):        continue
            if not re.search(r"show_.*interview\.php", href, re.I): continue
            title = a.get_text(" ", strip=True)
            
            # Get the full text from the link's parent context
            # The format is usually "[date] event title" where the link is the title
            line = node.get_text(" ", strip=True)
            
            # First try to find date in the link text itself (sometimes date is in the anchor)
            link_text = a.get_text(" ", strip=True)
            m = re.search(DATE_RE, link_text)
            
            # If not in link, look at parent node text
            if not m:
                m = re.search(DATE_RE, line)
            
            date = m.group(0) if m else ""
            
            # If still no date, look for common date patterns in the surrounding text
            if not date:
                # Look for patterns like "April 6, 2022" in the parent text
                parent_text = node.parent.get_text(" ", strip=True) if node.parent else ""
                m = re.search(DATE_RE, parent_text)
                date = m.group(0) if m else ""
            
            items.append({"title": title, "date": date, "url": href})
    print(f"[interviews] on player page: {len(items)}")
    return items

FOOTER_CUES = [
    "fastscripts transcript by asap sports",
    "about asap sports",
    "asap sports, inc."
]

def _footer_hit(text_lower: str) -> bool:
    return any(k in text_lower for k in FOOTER_CUES)

# ---- step 4: parse one interview detail page ---------------------------------
def is_question(text: str) -> bool:
    """Check if a line is a question (ends with ? or starts with interrogative words)."""
    text = text.strip()
    if not text:
        return False
    # Ends with question mark
    if text.endswith('?'):
        return True
    # Starts with common question words
    question_starts = [
        'what', 'how', 'when', 'where', 'who', 'why', 'which', 'can you',
        'could you', 'would you', 'do you', 'did you', 'does he', 'does she',
        'is it', 'are you', 'will you', 'tell us', 'can we'
    ]
    text_lower = text.lower()
    # Check if starts with question word and has limited length (likely a question)
    if any(text_lower.startswith(qw) for qw in question_starts):
        if len(text.split()) <= 15:  # Most questions are relatively short
            return True
    return False

def normalize_name(name: str) -> str:
    """
    Normalize a name for matching (e.g., "Aamodt, Wyatt" -> "WYATT AAMODT")
    """
    # Handle "Last, First" format
    if ',' in name:
        parts = name.split(',')
        if len(parts) == 2:
            last, first = parts[0].strip(), parts[1].strip()
            return f"{first} {last}".upper()
    return name.upper()

def clean_metadata_lines(text: str) -> str:
    """
    Remove metadata lines that are not actual interview content.
    Lines like "NCAA MEN'S FROZEN FOUR: MINNESOTA STATE VS. MINNESOTA"
    """
    lines = text.split('\n')
    cleaned = []
    
    # Find the most common prefix (usually the event name)
    prefix_counts = {}
    for line in lines:
        line = line.strip()
        if ':' in line:
            prefix = line.split(':', 1)[0].strip()
            if prefix and len(prefix) > 5:  # Only count meaningful prefixes
                prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
    
    # Get the most common prefix (metadata lines)
    most_common_prefix = None
    if prefix_counts:
        most_common_prefix = max(prefix_counts, key=prefix_counts.get)
        # Only treat as metadata if it appears multiple times
        if prefix_counts[most_common_prefix] < 3:
            most_common_prefix = None
    
    # Skip lines that are clearly metadata
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip lines with the common event prefix (metadata)
        if most_common_prefix and line.startswith(most_common_prefix + ':'):
            # Check if it's actual content (contains long text) or just metadata
            if ':' in line:
                content_part = line.split(':', 1)[1].strip()
                # If the content is short or looks like metadata (venues, dates, etc), skip it
                if len(content_part.split()) <= 5:
                    continue
        
        # Skip lines that are likely event titles, locations, or scores (all caps, short)
        if line.isupper() and len(line) > 0 and len(line.split()) <= 5:
            # Allow if it's clearly a statement
            if any(word in line.lower() for word in ['the', 'and', 'or', 'but', 'for']):
                pass  # Keep it
            else:
                continue  # Skip it (likely event title, location, etc.)
        
        # Skip lines that look like dates (Month Day, Year format)
        if re.match(DATE_RE, line):
            continue
        
        # Skip lines that look like locations (City, State or City, Country)
        if re.match(r'^[A-Z][a-z]+,\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?$', line):
            continue
        
        # Skip lines that look like scores (Team Name-Number or Number-Team Name)
        if re.match(r'^(?:[A-Z][a-z\s]+\-)?\d+\-?(?:[A-Z][a-z\s]+)?$', line):
            continue
        
        # Skip other metadata patterns
        metadata_patterns = [
            r'^[A-Z\s]+:\s*(?:THE MODERATOR|Q\.|QUESTION)',  # Moderator introductions
        ]
        is_metadata = any(re.match(pattern, line) for pattern in metadata_patterns)
        if not is_metadata:
            cleaned.append(line)
    
    return '\n'.join(cleaned)

def clean_text_artifacts(text: str) -> str:
    """
    Remove web scraping artifacts and unwanted characters.
    - Remove Â characters
    """
    # Remove Â characters (common encoding issue)
    text = text.replace('Â', '').replace('â', '').replace('\xa0', ' ')
    
    return text

def extract_speaker_statements(text: str, target_player_name: str = None) -> str:
    """
    Extract actual statements from speakers, filtering out questions.
    If target_player_name is provided, only extract statements from that player.
    Handles multiple speakers in format: SPEAKER NAME: statement
    """
    # Clean metadata lines first
    text = clean_metadata_lines(text)
    
    lines = text.split('\n')
    statements = []
    current_speaker = None
    
    # Normalize target player name if provided
    target_normalized = normalize_name(target_player_name) if target_player_name else None
    
    for line in lines:
        line = line.strip()
        
        if not line:
            continue
        
        # Remove parenthetical asides like (Inaudible.), (Question regarding ...), (Off microphone)
        line = re.sub(r'\((?:Inaudible|Question|Off\s*mic(?:rophone)?)[^)]*\)\.?', '', line, flags=re.IGNORECASE)
        line = line.strip()
        
        # Skip lines that start with "Q." or are just "Q"
        if re.match(r'^Q\.?\s*', line, re.IGNORECASE):
            current_speaker = None
            continue
        
        # Clean text artifacts (Â, etc.)
        line = clean_text_artifacts(line)
        
        if not line:
            continue
            
        # Check for speaker label (e.g., ":DARRYL SYDOR:" or "DARRYL SYDOR:")
        speaker_match = re.match(r'^:?([A-Z][A-Z\s\.\-\']{2,}):\s*(.*)$', line)
        if speaker_match:
            speaker_name = speaker_match.group(1).strip()
            statement = speaker_match.group(2).strip()
            
            # If we have a target player, only process their statements
            if target_normalized:
                # Check if this speaker matches the target (normalized)
                speaker_normalized = normalize_name(speaker_name)
                if speaker_normalized == target_normalized:
                    # Only add if it's not a question
                    if statement and not is_question(statement):
                        statements.append(statement)
                    current_speaker = speaker_name
                else:
                    # Not the target speaker
                    current_speaker = None
            else:
                # No target player specified, add all speakers
                if statement and not is_question(statement):
                    statements.append(f"{speaker_name}: {statement}")
                current_speaker = speaker_name
            
        elif current_speaker and target_normalized:
            # Continuation of previous speaker's statement (only if it's the target player)
            if not is_question(line):
                statements.append(line)
        elif current_speaker and not target_normalized:
            # Continuation of previous speaker's statement
            if not is_question(line):
                statements.append(f"{current_speaker}: {line}")
        else:
            # No identified speaker yet, check if it's a standalone question
            if not is_question(line) and not target_normalized:
                statements.append(line)
    
    return '\n'.join(statements)

def parse_detail(url: str, player_name: str):
    """Extract title/date and parse speaker statements, filtering out questions."""
    # Use get_soup which has retry and timeout handling
    soup = get_soup(url)

    # 메인 컨테이너
    main = soup.find(id="content") or soup.find("td", attrs={"valign":"top"}) or soup

    # 제목/날짜
    h1 = main.find("h1")
    title = h1.get_text(" ", strip=True) if h1 else ""
    # 날짜는 h2에 있으면 그걸 우선 사용
    h2 = main.find("h2")
    date = ""
    if h2:
        dt = h2.get_text(" ", strip=True)
        m = re.search(DATE_RE, dt)
        if m:
            date = m.group(0)

    # h2에서 못 찾았으면, 헤더 인근(상단 몇 개 블록)에서만 탐색하여 페이지 전역의 다른 날짜와 혼동 방지
    if not date:
        anchor = h2 or h1 or main
        top_chunks = []
        count = 0
        for sib in anchor.next_siblings:
            # 상단 5개 블록 정도만 스캔
            if count >= 5:
                break
            txt = ""
            if isinstance(sib, NavigableString):
                txt = str(sib)
            else:
                # 헤더 태그는 스킵
                if getattr(sib, "name", None) in {"h1","h2","h3"}:
                    continue
                txt = sib.get_text(" ", strip=True)
            if txt:
                top_chunks.append(txt)
                count += 1
        local_top = " \n ".join(top_chunks)
        m2 = re.search(DATE_RE, local_top)
        if m2:
            date = m2.group(0)
    # 그래도 없으면 마지막으로 전체에서 탐색(최후의 수단)
    if not date:
        m3 = re.search(DATE_RE, main.get_text(" ", strip=True))
        if m3:
            date = m3.group(0)

    # <br> → 개행 (중요)
    for br in main.find_all("br"):
        br.replace_with("\n")

    # 푸터 요소 제거
    for node in list(main.find_all(text=True)):
        low = node.strip().lower()
        if any(k in low for k in FOOTER_CUES):
            # 푸터 텍스트가 있는 부모 블록을 통째로 제거
            parent = node.parent
            if parent and parent != main:
                parent.decompose()

    # 본문 시작 기준: h3가 있으면 그 이후, 없으면 h2/h1 이후
    start = main.find("h3") or h2 or h1 or main

    # start 이후 블록을 한 번만 텍스트로 추출 (이중수집 방지)
    body_parts = []
    for sib in start.next_siblings:
        if isinstance(sib, NavigableString):
            txt = str(sib)
        else:
            # 헤더 태그는 스킵
            if getattr(sib, "name", None) in {"h1","h2","h3"}:
                continue
            txt = sib.get_text("\n", strip=True)
        if not txt:
            continue
        body_parts.append(txt)

    raw = "\n".join(body_parts)

    # 라인화 + 인접 중복 제거만 수행 (커버리지 유지)
    lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
    dedup = []
    prev = None
    for ln in lines:
        if ln != prev:
            dedup.append(ln)
        prev = ln

    text = "\n".join(dedup).strip()
    
    # Extract speaker statements and filter out questions
    # Pass player_name to extract only this player's statements
    statements = extract_speaker_statements(text, player_name)
    
    # Final cleanup
    statements = statements.replace('Â', '').replace('â', '').replace('\xa0', ' ')
    
    # Remove any remaining parenthetical asides (Inaudible/Question/Off mic)
    statements = re.sub(r'\((?:Inaudible|Question|Off\s*mic(?:rophone)?)[^)]*\)\.?', '', statements, flags=re.IGNORECASE)
    
    # Remove any remaining lines that start with "Q." and footer tails like FastScripts
    statement_lines = statements.split('\n')
    cleaned_statements = []
    for line in statement_lines:
        line = line.strip()
        if not line:
            continue
        # Skip lines that start with "Q."
        if re.match(r'^Q\.?\s*', line, re.IGNORECASE):
            continue
        # Skip footer markers that sometimes appear at the end
        low = line.lower()
        if 'fastscripts' in low or 'asap sports' in low or 'end of fastscripts' in low:
            continue
        cleaned_statements.append(line)
    statements = '\n'.join(cleaned_statements).strip()

    return {
        "event_title": title,
        "interview_date": date,
        "transcript_text": statements
    }

# ---- driver ------------------------------------------------------------------
def crawl(out_csv="data/asap_hockey.csv",
                letters=None,
                 max_players_per_letter=None,
                 max_interviews_per_player=None,
                 min_words=1,
                 year_filter=None):
    # Create 'data' folder if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    all_letter_urls = extract_letter_links()
    if letters:
        target = {L.upper() for L in letters}
        letter_urls = [u for u in all_letter_urls
                       if re.search(r"[?&]letter=([a-z])", u, re.I)
                       and re.search(r"[?&]letter=([a-z])", u, re.I).group(1).upper() in target]
    else:
        letter_urls = all_letter_urls

    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=[
            "player_name","interview_date","event_title","source_url","letter","transcript_text"
        ])
        w.writeheader()

        for letter_url in letter_urls:
            # Extract letter from URL
            letter_match = re.search(r"[?&]letter=([a-z])", letter_url, re.I)
            letter = letter_match.group(1).upper() if letter_match else ""
            
            players = extract_player_links(letter_url)[:max_players_per_letter]
            for pname, purl in players:
                items = extract_interview_links(purl)[:max_interviews_per_player]
                for it in items:
                    if year_filter and not re.search(year_filter, it.get("date","")):
                        continue
                    meta = parse_detail(it["url"], pname)
                    text = meta["transcript_text"]
                    if not text or len(text.split()) < min_words:
                        continue
                    w.writerow({
                        "player_name": pname,
                        "interview_date": meta["interview_date"] or it["date"],
                        "event_title": meta["event_title"] or it["title"],
                        "source_url": it["url"],
                        "letter": letter,
                        "transcript_text": text
                    })
                    print(f"[save] {pname} | {meta['interview_date']} | {len(text.split())} words")
                    time.sleep(1.5 + random.random()*1.0)  # Increased to 1.5-2.5 seconds between interviews
            time.sleep(2.0 + random.random()*1.0)  # Increased to 2.0-3.0 seconds between players

if __name__ == "__main__":
    crawl(
        out_csv="data/asap_hockey.csv",
        letters=None,
        max_players_per_letter=None,
        max_interviews_per_player=None,
        min_words=1,
        year_filter=None  # e.g., r"202[0-5]"
    )
