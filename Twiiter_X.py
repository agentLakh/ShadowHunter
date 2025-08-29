from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd

class TwitterSeleniumScraper:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.driver = webdriver.Chrome()
        self.wait = WebDriverWait(self.driver, 30)
    
    def login(self):
        """Se connecter à Twitter"""
        self.driver.get("https://x.com/login")
        
        time.sleep(10)
        # Remplir le formulaire de connexion
        username_input = self.wait.until(EC.presence_of_element_located((By.NAME, "text")))
        username_input.send_keys(self.username)
        username_input.send_keys(Keys.RETURN)
        
        time.sleep(10)
        password_input = self.wait.until(EC.presence_of_element_located((By.NAME, "password")))
        password_input.send_keys(self.password)
        password_input.send_keys(Keys.RETURN)
        
        time.sleep(10)
    
    def search_people(self, query, max_results=10):
        """Rechercher des personnes"""
        search_url = f"https://x.com/search?q={query}&src=typed_query&f=user"
        self.driver.get(search_url)
        
        time.sleep(100)
        
        # Collecter les résultats
        results = []
        users = self.driver.find_elements(By.XPATH, '//div[@data-testid="UserCell"]')
        
        for user in users[:max_results]:
            try:
                user_data = {
                    'name': user.find_element(By.XPATH, './/span[contains(@class, "r-1qd0xha")]').text,
                    'username': user.find_element(By.XPATH, './/span[contains(text(), "@")]').text,
                    'description': user.find_element(By.XPATH, './/div[@data-testid="UserDescription"]').text,
                }
                results.append(user_data)
            except:
                continue
        
        return results
    
    def close(self):
        """Fermer le navigateur"""
        self.driver.quit()

# Configuration
TWITTER_USERNAME = "aka_baye_tapha"
TWITTER_PASSWORD = "Mbacke@3545"

# Utilisation (déconseillé à cause des risques de blocage)
scraper = TwitterSeleniumScraper(TWITTER_USERNAME, TWITTER_PASSWORD)
scraper.login()
results = scraper.search_people("Mamoune Faye", max_results=5)


# Sauvegarder les résultats dans un fichier texte
with open("resultat_twitter.txt", "w", encoding="utf-8") as f:
    for user in results:
        f.write(f"Name: {user['name']}\n")
        f.write(f"Username: {user['username']}\n")
        f.write(f"Description: {user['description']}\n")
        f.write("-" * 30 + "\n")    
print("Résultats enregistrés dans resultat_twitter.txt")