from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from robot.api.deco import keyword
from robot.libraries.BuiltIn import BuiltIn
import time
import re

LEAGUE_URL_MAP = {
    'PKO BP Ekstraklasa': ('poland', 'ekstraklasa'),
    'Ekstraklasa': ('poland', 'ekstraklasa'),
    'Premier League': ('england', 'premier-league'),
    'English Premier League': ('england', 'premier-league'),
}

_HEADER_KEYWORDS = {'pos', 'club', 'team', 'games', 'points', 'pozycja', 'drużyna', 'mecze', 'punkty', 'mp', 'pts'}
_CLEAN_CHARS = str.maketrans('', '', '+:-.')

def _clean_text(text):
    """Remove common non-numeric characters from text"""
    return text.translate(_CLEAN_CHARS)

def _parse_position(text):
    """Extract position number from text"""
    try:
        cleaned = _clean_text(text.strip())
        return int(cleaned) if cleaned.isdigit() and 1 <= int(cleaned) <= 30 else None
    except:
        return None

def _safe_int(text, min_val=0, max_val=None):
    """Safely convert text to integer with optional range check"""
    try:
        num = int(text.strip())
        if min_val <= num and (max_val is None or num <= max_val):
            return num
    except:
        pass
    return None

@keyword
def get_league_table(league_name):
    """
    Scrapes league table from flashscore.com
    
    Args:
        league_name: Name of the league to search for (e.g., "PKO BP Ekstraklasa", "Premier League")
    
    Returns:
        List of dictionaries with keys: 'Club', 'Games', 'Points'
    """
    selenium_lib = BuiltIn().get_library_instance('SeleniumLibrary')
    driver = selenium_lib.driver
    
    try:
        _search_for_league(driver, league_name)
        _navigate_to_standings(driver)
        table_data = _extract_table_data(driver)
        return table_data
        
    except Exception as e:
        BuiltIn().log(f"Error scraping league table: {str(e)}", level='ERROR')
        raise

def _try_url(driver, wait, url, league_name):
    """Try to navigate to URL and check if it's the correct league page"""
    try:
        driver.get(url)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        return _check_if_league_page(driver, league_name)
    except:
        return False

def _try_selectors(wait, selectors, timeout=5):
    """Try multiple selectors and return first match"""
    for selector in selectors:
        try:
            return wait.until(EC.presence_of_element_located((By.XPATH, selector)))
        except:
            continue
    return None

def _search_for_league(driver, league_name):
    """Search for league on flashscore.com - tries direct URL first, then search"""
    wait = WebDriverWait(driver, 10)
    domains = ['flashscore.com', 'flashscore.pl']
    
    if league_name in LEAGUE_URL_MAP:
        country, slug = LEAGUE_URL_MAP[league_name]
        for domain in domains:
            if _try_url(driver, wait, f"https://www.{domain}/football/{country}/{slug}/", league_name):
                return
    
    league_slug = _create_league_slug(league_name)
    for country in ['poland', 'england', 'spain', 'germany', 'italy', 'france']:
        for domain in domains:
            if _try_url(driver, wait, f"https://www.{domain}/football/{country}/{league_slug}/", league_name):
                return

    search_input = _try_selectors(wait, [
        "//input[@type='search']",
        "//input[contains(@class, 'search')]",
        "//input[@placeholder='Search' or contains(@placeholder, 'Szukaj')]"
    ])
    
    if search_input:
        try:
            driver.execute_script("arguments[0].click(); arguments[0].value = '';", search_input)
            search_input.send_keys(league_name)
            time.sleep(1)
            
            result_link = wait.until(EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(), '{league_name}')]")))
            result_link.click()
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
            if _check_if_league_page(driver, league_name):
                return
        except:
            pass
    
    raise Exception(f"Could not find league: {league_name}")

def _create_league_slug(league_name):
    """Create URL slug from league name"""
    slug = re.sub(r'^(pko\s*bp|english)\s*', '', league_name.lower())
    slug = re.sub(r'[^\w\s-]', '', slug)
    return re.sub(r'\s+', '-', slug).strip('-')

def _check_if_league_page(driver, league_name):
    """Check if current page is a league page"""
    try:
        page_text = driver.page_source.lower()
        league_lower = league_name.lower()
        league_match = re.sub(r'pko\s*bp\s*', '', league_lower)
        
        if (league_lower in page_text or league_match in page_text) and \
           any(ind in page_text for ind in ["standings", "tabela", "table", "results", "wyniki", "fixtures", "mecze"]):
            return True
        return False
    except:
        return False

def _navigate_to_standings(driver):
    """Navigate to standings/table tab"""
    wait = WebDriverWait(driver, 8)
    
    for selector in ["//button[contains(@class, 'close')]", "//button[@aria-label='Close']"]:
        close_btn = driver.find_elements(By.XPATH, selector)
        if close_btn:
            driver.execute_script("arguments[0].click();", close_btn[0])
            break
    
    standings_tab = _try_selectors(wait, [
        "//a[contains(@href, 'standings') or contains(@href, '/standings/')]",
        "//a[contains(text(), 'Standings') or contains(text(), 'Tabela')]",
        "//div[contains(@class, 'tabs')]//a[contains(@href, 'standings') or contains(text(), 'Standings') or contains(text(), 'Tabela')]"
    ])
    
    if standings_tab:
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'}); arguments[0].click();", standings_tab)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        return
    
    current_url = driver.current_url
    if 'standings' in current_url.lower():
        return
    
    if '/football/' in current_url:
        try:
            driver.get(current_url.rstrip('/') + '/standings/')
            wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        except:
            pass

def _extract_table_data(driver):
    """Extract table data from the standings page"""
    wait = WebDriverWait(driver, 15)
    table_data = []
    
    try:
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2); window.scrollTo(0, 0);")
        
        _try_selectors(wait, ["//table", "//div[contains(@class, 'table__row')]", "//div[contains(@class, 'ui-table__row')]", "//div[contains(@class, 'detailScore__tableRow')]"])
        
        table_element = _try_selectors(wait, [
            "//table[.//th[contains(text(), 'TEAM') or contains(text(), 'Team') or contains(text(), 'MP') or contains(text(), 'PTS')]]",
            "//table[contains(@class, 'table') or contains(@class, 'standings')]",
            "//div[contains(@class, 'standings') or contains(@class, 'table')]//table",
            "//table"
        ])
        
        if not table_element:
            div_table = _try_selectors(wait, [
                "//div[contains(@class, 'table__body') or contains(@class, 'detailScore__tableBody')]",
                "//div[contains(@class, 'standings') or contains(@class, 'ui-table')]",
                "//div[contains(@class, 'detailScore') or contains(@class, 'tournamentTable')]"
            ])
            if div_table:
                return _extract_from_div_table(driver, div_table)
            
            for selector in ["//div[contains(@class, 'table__row') or contains(@class, 'ui-table__row')]", "//div[contains(@class, 'detailScore__tableRow')]"]:
                try:
                    rows = wait.until(EC.presence_of_all_elements_located((By.XPATH, selector)))
                    if len(rows) > 5:
                        return _extract_from_div_rows(driver, rows)
                except:
                    continue
        
        if not table_element:
            for selector in ["//tr[contains(@class, 'table__row')]", "//tr[.//td[contains(@class, 'team')]]", "//tr"]:
                try:
                    rows = wait.until(EC.presence_of_all_elements_located((By.XPATH, selector)))
                    if len(rows) > 5:
                        table_element = rows[0].find_element(By.XPATH, "./..")
                        break
                except:
                    continue
            if not table_element:
                raise Exception("Could not find standings table")
        
        rows = []
        for selector in [".//tbody//tr[not(contains(@class, 'header'))]", ".//tr[contains(@class, 'table__row')]", ".//tr[position() > 1]"]:
            rows = table_element.find_elements(By.XPATH, selector)
            if len(rows) > 5:
                break
        
        if len(rows) == 0:
            for selector in ["//div[contains(@class, 'table__row')]", "//div[contains(@class, 'ui-table__row')]"]:
                rows = driver.find_elements(By.XPATH, selector)
                if len(rows) > 5:
                    return _extract_from_div_rows(driver, rows)
            all_rows = table_element.find_elements(By.XPATH, ".//tr")
            rows = [r for r in all_rows if r.find_elements(By.XPATH, ".//td[contains(@class, 'team')] | .//td[2]")]
        
        if len(rows) == 0:
            raise Exception("Could not find any table rows")
        
        team_col_idx = mp_col_idx = pts_col_idx = None
        try:
            header_rows = table_element.find_elements(By.XPATH, ".//thead//tr | .//tr[1]")
            if header_rows:
                headers = header_rows[0].find_elements(By.XPATH, ".//th | .//td")
                for idx, header in enumerate(headers):
                    header_text = header.text.strip().upper()
                    if any(k in header_text for k in ('TEAM', 'DRUŻYNA')):
                        team_col_idx = idx
                    elif any(k in header_text for k in ('MP', 'MECZE', 'GAMES')):
                        mp_col_idx = idx
                    elif any(k in header_text for k in ('PTS', 'PUNKTY', 'POINTS')):
                        pts_col_idx = idx
        except:
            pass
        
        for row in rows:
            try:
                all_cells = row.find_elements(By.XPATH, ".//td | .//div[contains(@class, 'cell')]")
                
                if len(all_cells) < 3:
                    continue
                
                club_text = games = points = position = None
                position = _parse_position(all_cells[0].text) if all_cells else None
                
                if team_col_idx is not None and team_col_idx < len(all_cells):
                    club_text = all_cells[team_col_idx].text.strip()
                else:
                    for i in range(1, min(3, len(all_cells))):
                        text = all_cells[i].text.strip()
                        if text and len(text) > 2 and any(c.isalpha() for c in text):
                            club_text = text
                            break
                
                if mp_col_idx is not None and mp_col_idx < len(all_cells):
                    games = _safe_int(all_cells[mp_col_idx].text, 1, 49)
                else:
                    games = next((_safe_int(all_cells[i].text, 1, 49) for i in range(2, min(6, len(all_cells)))), None)
                
                if pts_col_idx is not None and pts_col_idx < len(all_cells):
                    points = _safe_int(all_cells[pts_col_idx].text, 1)
                else:
                    points = next((_safe_int(all_cells[i].text, 1) for i in range(len(all_cells) - 1, max(0, len(all_cells) - 3), -1)), None)
                
                if club_text and games is not None and points is not None:
                    if not club_text[0].isdigit():
                        if position:
                            club_text = f"{position} {club_text}"
                        else:
                            pos_match = re.match(r'^(\d+)\.?\s*(.+)', club_text)
                            if pos_match:
                                position = int(pos_match.group(1))
                                club_text = f"{position} {pos_match.group(2).strip()}"
                    
                    table_data.append({'Club': club_text, 'Games': games, 'Points': points})
            except Exception:
                continue
        
        if len(table_data) == 0:
            all_text_rows = driver.find_elements(By.XPATH, "//tr | //div[contains(@class, 'row')] | //div[contains(@class, 'table')]//div")
            if len(all_text_rows) > 0:
                return _extract_from_visible_text(driver, all_text_rows)
            raise Exception("No data extracted from table")
        
        return table_data
        
    except Exception as e:
        BuiltIn().log(f"Error extracting table data: {str(e)}", level='ERROR')
        raise

def _extract_from_div_table(driver, div_table):
    """Extract data from div-based table structure"""
    for selector in [
        ".//div[contains(@class, 'table__row') or contains(@class, 'ui-table__row')]",
        ".//div[contains(@class, 'detailScore__tableRow')]",
        ".//div[contains(@class, 'row')]"
    ]:
        rows = div_table.find_elements(By.XPATH, selector)
        if len(rows) > 5:
            return _extract_from_div_rows(driver, rows)
    
    for selector in ["//div[contains(@class, 'table__row')]", "//div[contains(@class, 'ui-table__row')]"]:
        rows = driver.find_elements(By.XPATH, selector)
        if len(rows) > 5:
            return _extract_from_div_rows(driver, rows)
    
    return _extract_from_div_rows(driver, [])

def _extract_from_div_rows(driver, rows):
    """Extract data from div-based rows"""
    table_data = []
    
    for idx, row in enumerate(rows):
        try:
            row_text = row.text.strip()
            if not row_text or len(row_text) < 5:
                continue
            
            if idx < 3 and any(h in row_text.lower() for h in _HEADER_KEYWORDS):
                continue
            
            parts = row_text.split()
            if len(parts) < 4:
                continue
            
            position = _parse_position(parts[0])
            
            numbers = []
            for i, part in enumerate(parts):
                if '-' in part and part.count('-') == 1:
                    try:
                        g1, g2 = part.split('-')
                        if g1.isdigit() and g2.isdigit():
                            numbers.extend([(i, int(g1)), (i, int(g2))])
                    except:
                        pass
                else:
                    clean_part = _clean_text(part)
                    if clean_part.isdigit():
                        numbers.append((i, int(clean_part)))
            
            if len(numbers) < 3:
                continue
            
            points = numbers[-1][1] if numbers else None
            games = None
            
            team_start_idx = 1 if position else 0
            team_end_idx = team_start_idx + 1
            
            for i in range(team_start_idx, len(parts)):
                clean_part = _clean_text(parts[i])
                if clean_part.isdigit():
                    num = int(clean_part)
                    if 0 < num < 50:
                        team_end_idx = i
                        games = num
                        break
            
            team_parts = [p for p in parts[team_start_idx:team_end_idx] 
                         if not _clean_text(p).isdigit() or int(_clean_text(p)) > 30]
            club_text = ' '.join(team_parts).strip()
            
            if games is None:
                games = next((num_val for _, num_val in numbers if 0 < num_val < 50), None)
            
            if not club_text or len(club_text) < 2:
                continue
            
            if not games or games > 50:
                games = next((num_val for _, num_val in numbers if 1 <= num_val < 50), None)
                if not games:
                    continue
            
            if not points or points < 0:
                continue
            
            if not club_text[0].isdigit():
                if position:
                    club_text = f"{position} {club_text}"
                else:
                    pos_match = re.match(r'^(\d+)\.?\s*(.+)', club_text)
                    if pos_match:
                        position = int(pos_match.group(1))
                        club_text = f"{position} {pos_match.group(2).strip()}"
                    else:
                        club_text = f"{len(table_data) + 1} {club_text}"
            
            table_data.append({'Club': club_text, 'Games': games, 'Points': points})
        except Exception:
            continue
    
    if len(table_data) == 0:
        try:
            body_text = driver.find_element(By.TAG_NAME, "body").text
            lines = [line.strip() for line in body_text.split('\n') if line.strip() and len(line.strip()) > 10]
            
            for line in lines:
                parts = line.split()
                if len(parts) >= 5:
                    pos = _parse_position(parts[0])
                    if pos:
                        clean_parts = [_clean_text(p) for p in parts[1:]]
                        numbers = [int(p) for p in clean_parts if p.isdigit()]
                        
                        if len(numbers) >= 2:
                            points = numbers[-1]
                            games = next((n for n in numbers if 1 <= n < 50), None)
                            
                            if games and points:
                                team_parts = [parts[i+1] for i, cp in enumerate(clean_parts) 
                                             if not (cp.isdigit() and int(cp) < 50)]
                                
                                if team_parts:
                                    club_text = ' '.join(team_parts).strip()
                                    if len(club_text) > 2:
                                        table_data.append({'Club': f"{pos} {club_text}", 'Games': games, 'Points': points})
            
            if len(table_data) >= 5:
                return table_data
        except:
            pass
        
        raise Exception("No data extracted from div-based table")
    
    return table_data

def _extract_from_visible_text(driver, elements):
    """Last resort: extract data from visible text on page"""
    table_data = []
    try:
        body_text = driver.find_element(By.TAG_NAME, "body").text
        lines = [line.strip() for line in body_text.split('\n') if line.strip() and len(line.strip()) >= 10]
        
        for line in lines:
            parts = line.split()
            if len(parts) >= 4:
                try:
                    pos = int(parts[0])
                    if 1 <= pos <= 30:
                        points = int(parts[-1])
                        games = int(parts[-2])
                        if 0 < games < 50 and points > 0:
                            team_name = ' '.join(parts[1:-2])
                            if len(team_name) > 2:
                                table_data.append({
                                    'Club': f"{pos} {team_name}",
                                    'Games': games,
                                    'Points': points
                                })
                except ValueError:
                    continue
        
        if len(table_data) >= 5:
            return table_data
    except:
        pass
    
    raise Exception("Could not extract data from visible text")