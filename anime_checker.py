import requests
import sqlite3
import time

def setup_database():
    """
    Connects to the SQLite database and creates the 'animes' table
    if it doesn't already exist.
    """
    # conn is our connection to the database file.
    conn = sqlite3.connect('anime_tracker.db')
    # cursor is the object we use to execute commands on the database.
    cursor = conn.cursor()
    
    # Execute an SQL command to create our table.
    # The 'animes' table will have 3 columns: id, title, and the last status we saw.
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS animes (
            id INTEGER PRIMARY KEY,
            title TEXT,
            last_known_status TEXT
        )
    ''')
    # Save the changes and close the connection.
    conn.commit()
    conn.close()

def check_animes():
    """
    Main function to check for anime status updates.
    It reads a list of anime IDs, fetches their current status from the Jikan API,
    and compares it against the status stored in the local SQLite database.
    """
    conn = sqlite3.connect('anime_tracker.db')
    cursor = conn.cursor()

    try:
        # Open animes.txt and read all IDs into a list.
        with open('animes.txt', 'r') as f:
            anime_ids = [line.strip() for line in f]
    except FileNotFoundError:
        print("Error: 'animes.txt' file not found. Please create it with the anime IDs.")
        return

    print("--- Starting check ---")
    # Loop: for each ID in the list...
    for anime_id in anime_ids:
        try:
            # Make the API call (same as in Phase 1).
            response = requests.get(f"https://api.jikan.moe/v4/anime/{anime_id}")
            response.raise_for_status() # Raise an exception for bad status codes (4xx or 5xx).
            data = response.json()['data']
            
            api_title = data['title']
            api_status = data['status']

            # Query our database to see if we already know this anime.
            cursor.execute("SELECT last_known_status FROM animes WHERE id = ?", (anime_id,))
            result = cursor.fetchone() # Fetch the first result.

            if result is None:
                # If we didn't find it, it's a new anime!
                print(f"  -> NEW ANIME FOUND: '{api_title}' has status '{api_status}'.")
                # Insert it into the database so we remember it for next time.
                cursor.execute("INSERT INTO animes (id, title, last_known_status) VALUES (?, ?, ?)", 
                               (anime_id, api_title, api_status))
            else:
                # If we already know it, let's compare the status.
                db_status = result[0]
                if api_status != db_status:
                    # The status has changed! (e.g., from "Airing" to "Finished").
                    print(f"  -> STATUS CHANGE! '{api_title}' changed from '{db_status}' to '{api_status}'.")
                    # Update the status in the database.
                    cursor.execute("UPDATE animes SET last_known_status = ? WHERE id = ?", 
                                   (api_status, anime_id))
                else:
                    # No news.
                    print(f"  -> No news for '{api_title}'. Status remains: '{api_status}'.")
            
            # Pause for 1 second to be respectful to the API server.
            time.sleep(1)
        
        except requests.exceptions.RequestException as e:
            print(f"  -> Error fetching data for ID {anime_id}: {e}")

    print("--- Check complete ---")
    # Save all changes made during the loop and close the connection.
    conn.commit()
    conn.close()

# --- Main execution block ---
# This ensures the code runs only when the script is executed directly.
if __name__ == "__main__":
    setup_database()
    check_animes()