import db
import ingest_stand
import alias_combination
import email_search as email_module
import time
import telephone_search as phone_module


def collect_inputs():
    options = {
        1: ("nom", ingest_stand.get_nom),
        2: ("prenom", ingest_stand.get_prenom),
        3: ("pseudo", ingest_stand.get_pseudo),
        4: ("email", ingest_stand.get_email),
        5: ("numero", ingest_stand.get_numero),
        6: ("photo", ingest_stand.get_photo),
        7: ("localisation", ingest_stand.get_localisation)
    }

    print("=== Données disponibles à saisir ===")
    for k, (label, _) in options.items():
        print(f"{k}. {label}")

    choix_raw = input("Entrez les numéros des informations connues (séparés par des virgules, ex: 1,4,5) : ")
    choix = [int(x.strip()) for x in choix_raw.split(",") if x.strip().isdigit()]

    data = {}
    for c in choix:
        if c in options:
            key, func = options[c]
            data[key] = func()
    return data

def wait_for_launch(keyword="launch"):
    print(f"\nQuand tu veux lancer les recherches, tape '{keyword}' puis Entrée.")
    while True:
        cmd = input("> ").strip().lower()
        if cmd == keyword:
            return True
        elif cmd in ("exit", "quit"):
            print("Abandon des recherches.")
            return False
        else:
            print(f"Commande inconnue. Tape '{keyword}' pour lancer ou 'exit' pour annuler.")

def main():
    db.init_db()

    data = collect_inputs()

    # Générer les alias (séparés par virgules)
    nom = data.get("nom", "")
    prenom = data.get("prenom", "")
    if nom or prenom:
        data["alias"] = alias_combination.create_alias(nom, prenom)
    else:
        data["alias"] = "unknown"

    # Sauvegarder la cible et récupérer target_id
    target_id = db.save_target(data)
    print(f"\nTarget créée (id={target_id}). Les données : {data}")

    # Attendre le mot pour lancer toutes les recherches
    if not wait_for_launch("launch"):
        return

    print("Démarrage des modules de recherche ...")

    # === Lancer la recherche email si fournie ===
    email = data.get("email")
    if email:
        print(f"Lancement recherche email pour {email} ...")
        res = email_module.search_email(email, target_id=target_id, save=True)
        print("Résultats email :", res.get("notes", res.get("hibp")))
    else:
        print("Aucun email fourni, recherche email ignorée.")

    numero = data.get("numero") 
    if numero:
        print(f"Lancement recherche téléphone pour {numero} ...")
        phone_res = phone_module.search_phone_and_save(numero, target_id=target_id, save=True)
        if phone_res.get("ok"):
            print("Résultat téléphone sauvegardé :", phone_res["result"])
        else:
            print("Erreur recherche téléphone :", phone_res.get("error"))
    else:
        print("Aucun numéro fourni, recherche téléphone ignorée.")

    # Ici je pourrais appeler d'autres modules (photo, phone, social, etc.)
    
    print("Recherche terminée.")

if __name__ == "__main__":
    main()
