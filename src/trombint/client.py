import os
import re
import logging
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from bs4 import BeautifulSoup
from cas_connector import CASClient
from dotenv import load_dotenv

load_dotenv()

CAS_USERNAME = os.getenv("CAS_USERNAME")
CAS_PASSWORD = os.getenv("CAS_PASSWORD")

ETUDIANTS_URL = "https://trombi.imtbs-tsp.eu/etudiants.php"

logger = logging.getLogger("trombint")

_cas_client = None

def _get_cas_client() -> CASClient:
    global _cas_client
    if _cas_client is None:
        if not CAS_USERNAME or not CAS_PASSWORD:
            raise ValueError("CAS_USERNAME or CAS_PASSWORD environment variables are not set. Check your .env file.")

        logger.info("Initialisation de la connexion CAS...")
        login_url = "https://cas6.imtbs-tsp.eu/cas/login"
        _cas_client = CASClient(service_url=login_url)
        
        _cas_client.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        
        logger.info(f"Authentification avec l'utilisateur: {CAS_USERNAME}...")
        _cas_client.login(username=CAS_USERNAME, password=CAS_PASSWORD)
        
        logger.info("Authentification réussie. Initialisation de la session sur l'annuaire...")
        _cas_client.session.get(ETUDIANTS_URL)
        logger.info("Session prête.")
        
    return _cas_client

def fetch_students_html(name: str | None = None) -> str:
    """Fetches the HTML from the trombi etudiants.php page using CAS authentication."""
    client = _get_cas_client()
    
    # Now the session is authenticated and initialized for searching
    if name is not None:
        logger.info(f"Recherche de l'étudiant: {name}...")
        data = {"etu[user]": name, "etu[ecole]": "", "etu[annee]": ""}
        response = client.session.post(ETUDIANTS_URL, data=data)
    else:
        logger.info("Récupération de tous les étudiants...")
        # Empty POST gets all students
        data = {"etu[user]": "", "etu[ecole]": "", "etu[annee]": ""}
        response = client.session.post(ETUDIANTS_URL, data=data)
        
    response.raise_for_status()
    return response.text

def parse_students(html_content: str) -> list[dict]:
    """Parses the etudiants HTML and returns a list of dictionaries containing student data."""
    soup = BeautifulSoup(html_content, 'html.parser')
    fiches = soup.find_all('div', class_='ldapFiche')
    
    etudiants = []
    
    for fiche in fiches:
        etudiant = {}
        
        # 1. Nom complet
        nom_div = fiche.find('div', class_='ldapNom')
        if nom_div:
            etudiant['nom_complet'] = nom_div.get_text(strip=True)
            
        # 2. Photo URL and UID
        photo_div = fiche.find('div', class_='ldapPhoto')
        if photo_div:
            link = photo_div.find('a')
            if link and link.get('href'):
                original_url = link['href']
                
                parsed_url = urlparse(original_url)
                query_params = parse_qs(parsed_url.query)
                
                uid = query_params.get('uid', [None])[0]
                if uid:
                    etudiant['uid'] = uid
                    
                # Force parameters for high-res photo
                query_params['h'] = ['320']
                query_params['w'] = ['240']
                
                new_query = urlencode(query_params, doseq=True)
                new_url = urlunparse((
                    parsed_url.scheme, 
                    parsed_url.netloc, 
                    parsed_url.path, 
                    parsed_url.params, 
                    new_query, 
                    parsed_url.fragment
                ))
                # Add domain if url is relative
                if not new_url.startswith('http'):
                    new_url = f"https://trombi.imtbs-tsp.eu/{new_url.lstrip('/')}"
                etudiant['photo_url'] = new_url
                
        # 3. Informations supplémentaires
        info_div = fiche.find('div', class_='ldapInfo')
        if info_div:
            email_link = info_div.find('a', href=re.compile(r'^mailto:'))
            if email_link:
                etudiant['email'] = email_link.get_text(strip=True)
                
            ul = info_div.find('ul')
            if ul:
                details = [li.get_text(strip=True) for li in ul.find_all('li')]
                if details:
                    etudiant['details'] = details

        if 'nom_complet' in etudiant:
            etudiants.append(etudiant)
            
    return etudiants

def get_all_students() -> list[dict]:
    """Fetches and parses all students from the trombi."""
    html = fetch_students_html()
    return parse_students(html)

def get_students_by_name(name: str) -> list[dict]:
    """Finds students by using the search form on the server."""
    html = fetch_students_html(name=name)
    return parse_students(html)

def get_pfp_by_name(name: str) -> list[str]:
    """Returns the profile picture URLs for specific student(s) matching the name."""
    students = get_students_by_name(name)
    return [student.get('photo_url') for student in students if student.get('photo_url')]

def get_all_pfps() -> dict[str, str]:
    """Returns a dictionary mapping student names to profile picture URLs."""
    students = get_all_students()
    return {s['nom_complet']: s['photo_url'] for s in students if 'nom_complet' in s and 'photo_url' in s}

def download_image(url: str, output_path: str):
    """Downloads an image using the authenticated CAS session."""
    client = _get_cas_client()
    logger.info(f"Téléchargement de l'image depuis {url}...")
    
    headers = {'Referer': 'https://trombi.imtbs-tsp.eu/etudiants.php'}
    response = client.session.get(url, headers=headers)
    response.raise_for_status()
    
    with open(output_path, 'wb') as f:
        f.write(response.content)
    logger.info(f"Image sauvegardée sous {output_path}")
