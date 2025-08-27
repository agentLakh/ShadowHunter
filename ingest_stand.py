import re

def get_nom():
    while True:
        nom = input("Entrez le nom de la cible : ")
        if nom.isalpha():
            return nom
        print("Le nom doit contenir uniquement des lettres.")

def get_prenom():
    while True:
        prenom = input("Entrez le prénom de la cible : ")
        if prenom.isalpha():
            return prenom
        print("Le prénom doit contenir uniquement des lettres.")

def get_pseudo():
    return input("Entrez le pseudo de la cible : ")

def get_email():
    regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    while True:
        email = input("Entrez l'email de la cible : ")
        if re.match(regex, email):
            return email
        print("Veuillez entrer une adresse email valide.")

def get_numero():
    while True:
        numero = input("Entrez le numéro de téléphone du cible : ")
        if numero.isdigit():
            return numero  # <-- retourne une string
        print("Le numéro doit contenir uniquement des chiffres.")

def get_photo():
    chemin = input("Entrez le chemin vers la photo de la cible : ")
    try:
        with open(chemin, "rb") as f:
            photo = f.read()
        return photo
    except Exception as e:
        print("Erreur lors de la lecture de la photo :", e)
        return None

def get_localisation():
    ville = input("Entrez la ville de la cible : ")
    pays = input("Entrez le pays de la cible : ")
    return {"ville": ville, "pays": pays}

