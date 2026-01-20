import requests
import json
from datetime import date, timedelta
import sys

# --- CONFIGURAZIONE SERVIZI (URL e PORTE) ---
AUTH_URL = "http://localhost:8001/api/v1"       # Authentication Service
DB_URL = "http://localhost:8002/api/v1"         # Database Service (Creazione Utenti/Dati) <--- AGGIUNGI QUESTO
PLANNER_URL = "http://localhost:8004"    # Meal Planner Service
RECIPE_URL = "http://localhost:8005/api/v1"     # Recipe CRUD Service

# Dati di test
USERNAME = "test_chef03"
PASSWORD = "password_sicura_123"
EMAIL = "chef@test.com"

def print_header(step, msg):
    print(f"\n{'-'*60}")
    print(f"🔹 STEP {step}: {msg}")
    print(f"{'-'*60}")

def run_test():
    session = requests.Session()
    
    # ---------------------------------------------------------
    # 1. REGISTRAZIONE UTENTE (PUNTARE A DB_URL :8002)
    # ---------------------------------------------------------
    print_header(1, "Registrazione Utente")
    user_payload = {
        "username": USERNAME,
        "email": EMAIL,
        "password": PASSWORD, 
        "full_name": "Test Chef Runner"
    }
    
    try:
        # MODIFICA QUI SOTTO: Usa DB_URL invece di AUTH_URL
        res = requests.post(f"{AUTH_URL}/auth/register", json=user_payload) 
        
        if res.status_code in [200, 201]:
            print(f"✅ Utente creato con successo: {res.json().get('username')}")
        elif res.status_code == 400 and "already exists" in res.text:
            print("⚠️ L'utente esiste già, procedo al login.")
        else:
            print(f"❌ Errore creazione utente: {res.status_code} - {res.text}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"❌ IMPOSSIBILE CONNETTERSI A: {DB_URL}")
        print("Il servizio Database è giù. Controlla 'docker compose ps'.")
        sys.exit(1)

    # ---------------------------------------------------------
    # 2. LOGIN & RECUPERO TOKEN
    # ---------------------------------------------------------
    print_header(2, "Login & Token JWT")
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    # OAuth2 standard usa form-data per il login
    res = requests.post(f"{AUTH_URL}/auth/login", data=login_data)    
    if res.status_code != 200:
        print(f"❌ Login fallito: {res.text}")
        sys.exit(1)
    
    token_data = res.json()
    access_token = token_data.get("access_token")
    headers = {"Authorization": f"Bearer {access_token}"}
    print(f"✅ Token ottenuto: {access_token[:20]}...")

    # ---------------------------------------------------------
    # 3. CREAZIONE RICETTA (TEST CRITICO INGREDIENTI)
    # ---------------------------------------------------------
    print_header(3, "Creazione Ricetta con Ingredienti")
    
    recipe_payload = {
        "user_id": 1, # Verrà associata all'utente del token o a questo ID
        "name": "Carbonara Test",
        "category": "Main Course",
        "area": "Italian",
        "instructions": "Mix eggs and cheese. Fry guanciale. Cook pasta.",
        "is_custom": True,
        "ingredients": [
            {"name": "Spaghetti", "measure": "100g"},
            {"name": "Guanciale", "measure": "50g"},
            {"name": "Pecorino", "measure": "30g"},
            {"name": "Eggs", "measure": "2"}
        ]
    }

    try:
        res = requests.post(f"{RECIPE_URL}/recipes/", json=recipe_payload, headers=headers)
        
        if res.status_code in [200, 201]:
            recipe_data = res.json()
            print(f"✅ Ricetta creata ID: {recipe_data.get('id')}")
            
            # VERIFICA DEL FIX DEGLI INGREDIENTI
            saved_ingredients = recipe_data.get("ingredients", [])
            print(f"   Ingredienti restituiti: {len(saved_ingredients)}")
            if len(saved_ingredients) > 0 and "name" in saved_ingredients[0]:
                 print(f"   🔍 Verifica ingrediente 1: {saved_ingredients[0]['name']} - {saved_ingredients[0]['measure']}")
            else:
                 print(f"   ⚠️ ATTENZIONE: La lista ingredienti sembra vuota o malformata: {saved_ingredients}")
        else:
            print(f"❌ Errore creazione ricetta: {res.status_code} - {res.text}")
    except requests.exceptions.ConnectionError:
         print(f"❌ IMPOSSIBILE CONNETTERSI A: {RECIPE_URL}")

    # ---------------------------------------------------------
    # 4. GENERAZIONE PIANO ALIMENTARE
    # ---------------------------------------------------------
    print_header(4, "Generazione Meal Plan")
    
    today = date.today()
    plan_payload = {
        "user_id": 1,
        "start_date": today.isoformat(),
        "end_date": (today + timedelta(days=2)).isoformat()
    }

    try:
        # Nota: Endpoint ipotetico, adattalo se hai cambiato le rotte nel planner
        res = requests.post(f"{PLANNER_URL}/meal-plans/", json=plan_payload, headers=headers)

        if res.status_code in [200, 201]:
            plan_data = res.json()
            print(f"✅ Piano creato ID: {plan_data.get('id')}")
            print(f"   Periodo: {plan_data.get('start_date')} -> {plan_data.get('end_date')}")
        else:
            print(f"❌ Errore creazione piano: {res.status_code} - {res.text}")
    except requests.exceptions.ConnectionError:
        print(f"❌ IMPOSSIBILE CONNETTERSI A: {PLANNER_URL}")

if __name__ == "__main__":
    run_test()