import datetime
import re
from bs4 import BeautifulSoup
from lxml import etree
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options

def estrai_numero_da_estensione(estensione):
    estensioni_numeriche = {
        None: 0, 'bis': 1, 'tris': 2, 'ter': 3, 'quater': 4, 'quinquies': 5,
        'quinques': 5, 'sexies': 6, 'septies': 7, 'octies': 8, 'novies': 9,
    }
    return estensioni_numeriche.get(estensione, 0)

def estrai_testo_articolo(atto_xml, num_articolo=1, est_articolo=None, comma=None):
    try:
        soup = BeautifulSoup(atto_xml, 'xml')
        
        if isinstance(num_articolo, str) and "-" in num_articolo:
            parts = num_articolo.split('-')
            num_articolo, est_articolo = int(parts[0]), parts[1]
        else:
            num_articolo = int(num_articolo)
        
        # Utilizziamo BeautifulSoup per trovare gli articoli, ignorando gli spazi dei nomi
        articoli = soup.find_all('articolo', {'id': str(num_articolo)})
        
        if not articoli:
            return "Nessun articolo trovato."
        
        # Selezionare l'articolo corretto in presenza di estensioni
        if est_articolo:
            indice_estensione = estrai_numero_da_estensione(est_articolo)
            if indice_estensione >= len(articoli):
                return "Estensione dell'articolo non trovata."
            articolo = articoli[indice_estensione]
        else:
            articolo = articoli[0]
        
        # Gestione specifica del comma
        if comma is not None:
            comma_elements = articolo.find_all('comma', {'id': f'art{num_articolo}-com{comma}'})
            if comma_elements:
                return ''.join([element.get_text() for element in comma_elements])
            else:
                # Cerca nel testo degli elementi p senza considerare gli spazi dei nomi
                p_out = []
                for p in articolo.find_all('p'):
                    if p.get_text(strip=True).startswith(f"{comma}"):
                        p_out.append(p.get_text(strip=True))
                return ' '.join(p_out) if p_out else "Comma specificato non trovato."
        else:
            return articolo.get_text(strip=True)

    except Exception as e:
        return f"Errore generico: {e}"

def parse_date(input_date):
    """
    Converte una stringa di data in formato esteso o YYYY-MM-DD al formato YYYY-MM-DD.
    Supporta mesi in italiano.
    """
    month_map = {
        "gennaio": "01", "febbraio": "02", "marzo": "03", "aprile": "04",
        "maggio": "05", "giugno": "06", "luglio": "07", "agosto": "08",
        "settembre": "09", "ottobre": "10", "novembre": "11", "dicembre": "12"
    }

    # Tenta la conversione per formati con mesi per esteso
    pattern = r"(\d{1,2})\s+([a-zA-Z]+)\s+(\d{4})"
    match = re.search(pattern, input_date)
    if match:
        day, month, year = match.groups()
        month = month_map.get(month.lower())
        if not month:
            raise ValueError("Mese non valido")
        return f"{year}-{month}-{day.zfill(2)}"
    
    # Gestione del formato standard YYYY-MM-DD
    try:
        datetime.datetime.strptime(input_date, "%Y-%m-%d")
        return input_date
    except ValueError:
        raise ValueError("Formato data non valido")

def normalize_act_type(input_type):
    """
    Normalizes the type of legislative act based on a variable input.
    """
    act_types = {
        "decreto legge": "decreto.legge",
        "dl": "decreto.legge",
        "legge": "legge",
        "costituzione": "costituzione"
    }
    
    input_type = input_type.lower().strip()
    # Improved logic to ensure accurate mapping
    for key, value in act_types.items():
        if input_type == key or input_type == key.replace(" ", ""): 
            return value
    raise ValueError("Tipo di atto non riconosciuto")

def generate_urn(act_type, date, act_number, article=None, extension=None, version=None, version_date=None):
    """
    Genera un URL per Normattiva basandosi sui parametri forniti.
    """
    try:
        formatted_date = parse_date(date)
        normalized_type = normalize_act_type(act_type)
    except ValueError as e:
        print(f"Errore nella formattazione dei parametri: {e}")
        return None

    base_url = "https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:"
    urn = f"{normalized_type}:{formatted_date};{act_number}"
        
    if article:
        urn += f"~art{article}"
        if extension:
            urn += extension
            
    if version == "originale":
        urn += "@originale"
    elif version == "vigente":
        urn += "!vig="
        if version_date:
            formatted_version_date = parse_date(version_date)
            urn += formatted_version_date
    
    return base_url + urn

def create_driver(headless=True):
    """
    Crea e restituisce un'istanza del WebDriver di Chrome.
    
    Args:
        headless (bool): Se True, avvia Chrome in modalità headless. Default a True.
    
    Returns:
        webdriver.Chrome: Un'istanza di Chrome WebDriver configurata.
    """
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")  # Imposta la modalità headless
        chrome_options.add_argument("--disable-gpu")  # Raccomandato per eseguire in modalità headless
        chrome_options.add_argument("--window-size=1920x1080")  # Opzionale, imposta la risoluzione del browser

    driver = webdriver.Chrome(options=chrome_options)
        
    return driver

def get_urn_and_extract_data(driver, act_type, date, act_number, article=None, extension=None, comma=None, version=None, version_date=None, timeout=10):
    """
    Funzione principale per generare l'URN, visitare la pagina e, in base all'esigenza, esportare in XML o estrarre testo HTML.
    """
    urn = generate_urn(act_type, date, act_number, article, extension, version, version_date)
    if urn is None:
        print("Errore nella generazione dell'URN.")
        return None

    act_link = urn  
    driver.get(act_link)
    try:
        export_button_selector = "#mySidebarRight > div > div:nth-child(2) > div > div > ul > li:nth-child(2) > a"
        export_xml_selector = "generaXml"
            
        WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.CSS_SELECTOR, export_button_selector))).click()
        driver.switch_to.window(driver.window_handles[-1])
        WebDriverWait(driver, timeout).until(EC.element_to_be_clickable((By.NAME, export_xml_selector))).click()
        driver.switch_to.window(driver.window_handles[-1])
        WebDriverWait(driver, timeout)
        xml_data = driver.page_source
        driver.close()
        xlm_out = estrai_testo_articolo(xml_data, article, extension, comma)
        return xlm_out
    except Exception as e:
        print(f"Errore nell'esportazione XML: {e}")
        return None