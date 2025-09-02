import requests
import sqlite3
import time

def setup_database():
    conn = sqlite3.connect('anime_tracker.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS animes (
            id INTEGER PRIMARY KEY,
            title TEXT,
            last_known_status TEXT
        )
    ''')
    conn.commit()
    conn.close()

def check_animes():
    conn = sqlite3.connect('anime_tracker.db')
    cursor = conn.cursor()

    try:
        with open('animes.txt', 'r') as f:
            anime_ids = [line.strip() for line in f]
    except FileNotFoundError:
        print("Erro: Arquivo 'animes.txt' não encontrado. Crie o arquivo com os IDs dos animes.")
        return

    print("--- Iniciando verificação ---")
    for anime_id in anime_ids:
        try:
            response = requests.get(f"https://api.jikan.moe/v4/anime/{anime_id}")
            response.raise_for_status()
            data = response.json()['data']
            
            api_title = data['title']
            api_status = data['status']

            cursor.execute("SELECT last_known_status FROM animes WHERE id = ?", (anime_id,))
            result = cursor.fetchone()

            if result is None:
                print(f"  -> NOVO ANIME ENCONTRADO: '{api_title}' está com o status '{api_status}'.")
                cursor.execute("INSERT INTO animes (id, title, last_known_status) VALUES (?, ?, ?)", 
                               (anime_id, api_title, api_status))
            else:
                db_status = result[0]
                if api_status != db_status:
                    print(f"  -> MUDANÇA DE STATUS! '{api_title}' mudou de '{db_status}' para '{api_status}'.")
                    cursor.execute("UPDATE animes SET last_known_status = ? WHERE id = ?", 
                                   (api_status, anime_id))
                else:
                    print(f"  -> Sem novidades para '{api_title}'. Status continua: '{api_status}'.")
            
            time.sleep(1)
        
        except requests.exceptions.RequestException as e:
            print(f"  -> Erro ao buscar dados para o ID {anime_id}: {e}")

    print("--- Verificação concluída ---")
    conn.commit()
    conn.close()

# Roda o programa
setup_database()
check_animes()