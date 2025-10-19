"""
Exemples de fonctions et classes pour tester la génération de questions Moodle CodeRunner
"""


def double(x):
    """
    Retourne le double d'un nombre.

    Args:
        x: Un nombre

    Returns:
        Le double de x
    """
    return x * 2


def somme_doubles(liste):
    """
    Calcule la somme des doubles de tous les nombres d'une liste.

    Cette fonction utilise la fonction double() pour calculer
    le double de chaque élément, puis retourne la somme totale.

    Args:
        liste: Une liste de nombres

    Returns:
        La somme des doubles de tous les éléments

    Raises:
        TypeError: Si la liste contient des éléments non numériques

    Exemples:
        >>> somme_doubles([1, 2, 3])
        12
        >>> somme_doubles([])
        0
    """
    if not isinstance(liste, list):
        raise TypeError("L'argument doit être une liste")

    total = 0
    for nombre in liste:
        if not isinstance(nombre, (int, float)):
            raise TypeError(f"L'élément {nombre} n'est pas un nombre")
        total += double(nombre)

    return total


def moyenne_doubles(liste):
    """
    Calcule la moyenne des doubles de tous les nombres d'une liste.

    Cette fonction utilise somme_doubles() pour calculer la somme,
    puis divise par le nombre d'éléments pour obtenir la moyenne.

    Chaîne de dépendances (niveau 3) :
    - moyenne_doubles() utilise somme_doubles()
    - somme_doubles() utilise double()
    - double() est une fonction de base

    Args:
        liste: Une liste de nombres (non vide)

    Returns:
        La moyenne des doubles de tous les éléments

    Raises:
        ValueError: Si la liste est vide
        TypeError: Si la liste contient des éléments non numériques

    Exemples:
        >>> moyenne_doubles([1, 2, 3])
        4.0
        >>> moyenne_doubles([5])
        10.0
        >>> moyenne_doubles([2, 4, 6])
        8.0
    """
    if not isinstance(liste, list):
        raise TypeError("L'argument doit être une liste")

    if len(liste) == 0:
        raise ValueError("La liste ne peut pas être vide")

    somme = somme_doubles(liste)
    return somme / len(liste)


class Calculatrice:
    """
    Une calculatrice simple qui stocke un résultat et permet d'effectuer
    des opérations en chaîne.

    Cette classe utilise la fonction double() pour l'opération de doublement.

    Attributes:
        resultat: Le résultat actuel de la calculatrice
    """

    def __init__(self, valeur_initiale=0):
        """
        Initialise la calculatrice avec une valeur de départ.

        Args:
            valeur_initiale: La valeur de départ (par défaut 0)

        Raises:
            TypeError: Si la valeur initiale n'est pas un nombre
        """
        if not isinstance(valeur_initiale, (int, float)):
            raise TypeError("La valeur initiale doit être un nombre")
        self.resultat = valeur_initiale

    def ajouter(self, nombre):
        """
        Ajoute un nombre au résultat actuel.

        Args:
            nombre: Le nombre à ajouter

        Raises:
            TypeError: Si le nombre n'est pas numérique
        """
        if not isinstance(nombre, (int, float)):
            raise TypeError("Le nombre doit être numérique")
        self.resultat += nombre

    def doubler(self):
        """
        Double le résultat actuel en utilisant la fonction double().
        """
        self.resultat = double(self.resultat)

    def reinitialiser(self):
        """
        Remet le résultat à zéro.
        """
        self.resultat = 0
