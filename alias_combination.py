import random

def create_alias(nom: str = "", prenom: str = "") -> str:
    """
    Génère une chaîne de texte contenant plusieurs alias à partir du nom et/ou prénom.
    Les alias sont séparés par des virgules.
    """
    aliases = set() 

    nom = nom.lower() if nom else ""
    prenom = prenom.lower() if prenom else ""

    if nom and prenom:
        aliases.add(f"{prenom[0]}{nom}")      
        aliases.add(f"{prenom}{nom}")         
        aliases.add(f"{nom}{prenom}")         
        aliases.add(f"{nom}_{prenom}")        
        aliases.add(f"{prenom}.{nom}")        
        aliases.add(f"{prenom}{nom[0]}")     
        aliases.add(f"{prenom[0]}{nom[0]}{random.randint(10,99)}")  
        aliases.add(f"{nom}{random.randint(1,99)}")                 
    elif nom: 
        aliases.add(nom)
        aliases.add(f"{nom}{random.randint(1,99)}")
        aliases.add(f"{nom}_{random.randint(1,99)}")
        aliases.add(f"{nom}.{random.randint(1,99)}")
    elif prenom: 
        aliases.add(prenom)
        aliases.add(f"{prenom}{random.randint(1,99)}")
        aliases.add(f"{prenom}_{random.randint(1,99)}")
        aliases.add(f"{prenom}.{random.randint(1,99)}")
    else:
        return "unknown"

    while len(aliases) < 5:
        base = nom if nom else prenom
        aliases.add(f"{base}{random.randint(100,999)}")

    return ", ".join(aliases)
