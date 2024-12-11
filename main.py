import tkinter as tk  # Bibliothèque pour créer des interfaces graphiques
from tkinter import messagebox  # Pour afficher des boîtes de dialogue dans Tkinter
from collections import Counter  # Utilisé pour compter les occurrences de chaque lettre
import unicodedata  # Fournit des outils pour normaliser et manipuler les caractères Unicode
import requests  # Pour effectuer des requêtes HTTP et télécharger des données depuis une URL
import chardet  # Pour détecter automatiquement l'encodage des fichiers texte


# Fonction pour normaliser un texte (supprimer les accents)
def normalize_text(text: str) -> str:
    """
    Normalise une chaîne de caractères en supprimant les accents et autres diacritiques.

    :param text: Le texte à normaliser.
    :type text: str
    :return: Le texte normalisé, sans accents.
    :rtype: str
    :raises AssertionError: Si l'entrée n'est pas une chaîne de caractères.
    """
    # Vérifie que l'entrée est une chaîne de caractères
    assert isinstance(text, str), "Le texte à normaliser doit être une chaîne de caractères."
    # Décompose les caractères accentués en leur forme de base (par ex., 'é' devient 'e' + accent)
    text = unicodedata.normalize('NFD', text)
    # Supprime les caractères de type "Mn" (marques non-spacées, comme les accents)
    return ''.join(c for c in text if unicodedata.category(c) != 'Mn')


# Fonction pour télécharger une liste de mots depuis une URL
def download_vocabulary(url: str) -> set:
    """
    Télécharge et traite une liste de mots depuis une URL.

    :param url: L'URL contenant la liste de mots.
    :type url: str
    :return: Un ensemble contenant les mots uniques en minuscule.
    :rtype: set
    :raises AssertionError: Si l'entrée n'est pas une chaîne ou si l'URL n'est pas valide.
    :raises requests.exceptions.RequestException: En cas de problème avec la requête HTTP.
    :raises UnicodeDecodeError: Si le contenu ne peut pas être décodé.
    :raises AssertionError: Si la liste téléchargée est vide.
    """
    # Vérifie que l'URL est une chaîne et commence par 'http'
    assert isinstance(url, str), "L'URL doit être une chaîne de caractères."
    assert url.startswith('http'), "L'URL doit commencer par 'http' ou 'https'."

    # Effectue une requête HTTP pour obtenir les données
    response = requests.get(url)
    # Lève une exception si la requête échoue
    response.raise_for_status()
    # Lit le contenu brut des données téléchargées
    content = response.content

    # Détecte l'encodage des données pour pouvoir les décoder correctement
    encoding = chardet.detect(content)['encoding']
    assert encoding is not None, "Impossible de détecter l'encodage du fichier."
    
    # Décode le contenu en fonction de l'encodage détecté
    text = content.decode(encoding)
    # Divise les lignes en mots uniques, élimine les espaces superflus et met en minuscule
    vocabulary = set(word.strip().lower() for word in text.splitlines() if word.strip())
    # Vérifie que la liste de vocabulaire n'est pas vide
    assert vocabulary, "La liste de vocabulaire téléchargée est vide."
    return vocabulary


# Fonction pour déchiffrer un texte chiffré par la méthode de César via analyse fréquentielle
def decrypt_cesar_frequency_analysis(cipher_text: str, target_letter: str = 'e') -> tuple:
    """
    Déchiffre un texte chiffré avec le chiffrement César en utilisant une analyse fréquentielle.

    :param cipher_text: Le texte chiffré à analyser.
    :type cipher_text: str
    :param target_letter: La lettre cible pour l'analyse fréquentielle (par défaut 'e').
    :type target_letter: str, optionnel
    :return: Le texte déchiffré et le décalage utilisé pour déchiffrer.
    :rtype: tuple[str, int]
    :raises AssertionError: Si les entrées ne respectent pas les types attendus.
    """
    # Vérifie que l'entrée est une chaîne et que la lettre cible est un caractère unique
    assert isinstance(cipher_text, str), "Le texte chiffré doit être une chaîne de caractères."
    assert isinstance(target_letter, str) and len(target_letter) == 1, \
        "La lettre cible doit être un caractère unique."

    # Définit l'alphabet utilisé pour le chiffrement
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    # Normalise le texte pour supprimer les accents
    cipher_text = normalize_text(cipher_text)
    # Compte les occurrences de chaque lettre dans le texte
    text_letter_frequency = Counter(char.lower() for char in cipher_text if char.isalpha())

    # Si aucune lettre valide n'est trouvée, retourne None
    if not text_letter_frequency:
        return None, None

    # Identifie la lettre la plus fréquente dans le texte
    most_common_letter = text_letter_frequency.most_common(1)[0][0]
    # Calcule le décalage en supposant que cette lettre correspond à 'e' (par défaut)
    shift = (alphabet.index(most_common_letter) - alphabet.index(target_letter)) % 26

    # Déchiffre le texte en appliquant le décalage calculé
    decrypted_text = ''.join(
        alphabet[(alphabet.index(char.lower()) - shift) % 26].upper() if char.isupper() else
        alphabet[(alphabet.index(char.lower()) - shift) % 26] if char.islower() else
        char
        for char in cipher_text
    )
    # Vérifie que le texte déchiffré n'est pas vide
    assert decrypted_text, "Le texte déchiffré est vide."
    return decrypted_text, shift


# Fonction pour effectuer un bruteforce sur un texte chiffré avec la méthode de César
def bruteforce_cesar(cipher_text: str, vocabulary: set) -> tuple:
    """
    Teste tous les décalages possibles pour déchiffrer un texte chiffré avec le chiffrement César.

    :param cipher_text: Le texte chiffré à analyser.
    :type cipher_text: str
    :param vocabulary: Ensemble de mots valides utilisés pour évaluer les résultats.
    :type vocabulary: set
    :return: Le meilleur texte déchiffré trouvé, le décalage correspondant, et le ratio de mots valides.
    :rtype: tuple[str, int, float]
    :raises AssertionError: Si les entrées ne respectent pas les types attendus.
    """
    # Vérifie que le texte chiffré est une chaîne et que le vocabulaire est un ensemble
    assert isinstance(cipher_text, str), "Le texte chiffré doit être une chaîne de caractères."
    assert isinstance(vocabulary, set), "Le vocabulaire doit être un ensemble (set)."

    # Définit l'alphabet utilisé pour le chiffrement
    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    # Variables pour stocker les meilleurs résultats trouvés
    best_match = None
    best_shift = None
    best_valid_ratio = 0

    # Teste tous les décalages possibles (de 1 à 25)
    for shift in range(1, 26):
        # Déchiffre le texte pour un décalage donné
        decrypted_text = ''.join(
            alphabet[(alphabet.index(char.lower()) - shift) % 26].upper() if char.isupper() else
            alphabet[(alphabet.index(char.lower()) - shift) % 26] if char.islower() else
            char
            for char in cipher_text
        )
        # Divise le texte déchiffré en mots
        words = decrypted_text.split()
        # Filtre les mots qui appartiennent au vocabulaire
        valid_words = [word.lower() for word in words if word.lower() in vocabulary]
        # Calcule le ratio de mots valides
        valid_ratio = len(valid_words) / len(words) if words else 0

        # Si le ratio actuel est meilleur, met à jour les meilleurs résultats
        if valid_ratio > best_valid_ratio:
            best_match = decrypted_text
            best_shift = shift
            best_valid_ratio = valid_ratio

    # Vérifie qu'un résultat valide a été trouvé
    assert best_match, "Aucune correspondance valide trouvée lors du bruteforce."
    return best_match, best_shift, best_valid_ratio


# Interface graphique avec Tkinter
def create_gui():
    """
    Crée et lance une interface utilisateur graphique (GUI) pour interagir avec les fonctions de déchiffrement.

    La GUI permet d'entrer un texte chiffré et de lancer deux méthodes de déchiffrement :
    1. Analyse Fréquentielle
    2. Bruteforce

    Les résultats sont affichés directement dans la fenêtre. Elle télécharge également un vocabulaire de mots à utiliser
    pour l'analyse bruteforce.

    :raises Exception: Si le téléchargement du vocabulaire échoue.
    """
    # Fonction déclenchée lors du clic sur "Déchiffrer (Analyse Fréquentielle)"
    def on_decrypt_frequency():
        """
        Déchiffre un texte entré par l'utilisateur en utilisant une analyse fréquentielle.

        Cette fonction est appelée lors d'un clic sur le bouton "Déchiffrer (Analyse Fréquentielle)".

        :raises Warning: Affiche un avertissement si aucun texte n'est saisi.
        """
        # Récupère le texte entré par l'utilisateur
        cipher_text = cipher_text_entry.get("1.0", tk.END).strip()
        # Si aucun texte n'est saisi, affiche un avertissement
        if not cipher_text:
            messagebox.showwarning("Erreur", "Veuillez entrer un texte chiffré.")
            return

        # Déchiffre le texte en utilisant l'analyse fréquentielle
        result, shift = decrypt_cesar_frequency_analysis(cipher_text)
        if result:
            # Affiche le texte déchiffré et le décalage
            freq_result_label.config(text=f"Texte déchiffré : {result}\nDécalage : {shift}")
        else:
            freq_result_label.config(text="Aucun résultat trouvé avec l'analyse fréquentielle.")

    # Fonction déclenchée lors du clic sur "Déchiffrer (Bruteforce)"
    def on_decrypt_bruteforce():
        """
        Déchiffre un texte entré par l'utilisateur en testant tous les décalages possibles (bruteforce).

        Cette fonction est appelée lors d'un clic sur le bouton "Déchiffrer (Bruteforce)".

        :raises Warning: Affiche un avertissement si aucun texte n'est saisi.
        :raises AssertionError: Si aucun résultat valide n'est trouvé lors de l'analyse bruteforce.
        """
        # Récupère le texte entré par l'utilisateur
        cipher_text = cipher_text_entry.get("1.0", tk.END).strip()
        # Si aucun texte n'est saisi, affiche un avertissement
        if not cipher_text:
            messagebox.showwarning("Erreur", "Veuillez entrer un texte chiffré.")
            return

        # Déchiffre le texte en utilisant le bruteforce
        result, shift, valid_ratio = bruteforce_cesar(cipher_text, vocabulary)
        if result:
            # Affiche le texte déchiffré, le décalage et le ratio de mots valides
            brute_result_label.config(
                text=f"Texte déchiffré : {result}\nDécalage : {shift}\nRatio de mots valides : {valid_ratio:.0%}"
            )
        else:
            brute_result_label.config(text="Aucun résultat trouvé avec le bruteforce.")

    # Télécharge la liste de vocabulaire au démarrage
    vocabulary_url = "https://raw.githubusercontent.com/Taknok/French-Wordlist/refs/heads/master/francais.txt"
    global vocabulary
    try:
        # Télécharge et charge le vocabulaire
        vocabulary = download_vocabulary(vocabulary_url)
    except Exception as e:
        # En cas d'échec, affiche une erreur et utilise un vocabulaire vide
        vocabulary = set()
        messagebox.showerror("Erreu r", f"Impossible de télécharger le vocabulaire : {e}")

    # Crée la fenêtre principale
    root = tk.Tk()
    root.title("Décryptage César")

    # Widgets pour l'interface utilisateur
    tk.Label(root, text="Entrez le texte chiffré :").pack()
    # Zone de texte pour entrer le texte chiffré
    cipher_text_entry = tk.Text(root, height=10, width=50)
    cipher_text_entry.pack()

    # Bouton pour lancer l'analyse fréquentielle
    tk.Button(root, text="Déchiffrer (Analyse Fréquentielle)", command=on_decrypt_frequency).pack(pady=5)
    # Étiquette pour afficher le résultat de l'analyse fréquentielle
    freq_result_label = tk.Label(root, text="", wraplength=400, justify="left", fg="blue")
    freq_result_label.pack()

    # Bouton pour lancer le bruteforce
    tk.Button(root, text="Déchiffrer (Bruteforce)", command=on_decrypt_bruteforce).pack(pady=5)
    # Étiquette pour afficher le résultat du bruteforce
    brute_result_label = tk.Label(root, text="", wraplength=400, justify="left", fg="green")
    brute_result_label.pack()

    # Lance la boucle principale de Tkinter
    root.mainloop()


# Point d'entrée principal du programme
if __name__ == "__main__":
    create_gui()
