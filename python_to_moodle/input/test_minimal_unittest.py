"""
Tests pour test_minimal.py

Exemples de différents types d'assertions unittest :
- assertEqual : teste l'égalité
- assertIn : teste l'appartenance
- assertRaises : teste qu'une exception est levée
"""

import unittest
from test_minimal import double, somme_doubles, moyenne_doubles, Calculatrice


class TestDouble(unittest.TestCase):
    """Tests pour la fonction double"""

    def test_positif(self):
        """Test avec un nombre positif"""
        self.assertEqual(double(5), 10)

    def test_zero(self):
        """Test avec zéro"""
        self.assertEqual(double(0), 0)

    def test_negatif(self):
        """Test avec un nombre négatif"""
        self.assertEqual(double(-3), -6)

    def test_decimal(self):
        """Test avec un nombre décimal"""
        self.assertEqual(double(2.5), 5.0)


class TestSommeDoubles(unittest.TestCase):
    """Tests pour la fonction somme_doubles"""

    def test_liste_simple(self):
        """Test avec une liste de nombres positifs"""
        self.assertEqual(somme_doubles([1, 2, 3]), 12)

    def test_liste_vide(self):
        """Test avec une liste vide"""
        self.assertEqual(somme_doubles([]), 0)

    def test_resultats_possibles(self):
        """Test avec assertIn - vérifie que le résultat est parmi les valeurs attendues"""
        resultat = somme_doubles([1, 2])
        self.assertIn(resultat, [6, 12, 18])  # 6 est le bon résultat (2+4)

    def test_exception_element_non_numerique(self):
        """Test qu'une exception est levée si un élément n'est pas un nombre"""
        with self.assertRaises(TypeError):
            somme_doubles([1, "deux", 3])


class TestMoyenneDoubles(unittest.TestCase):
    """Tests pour la fonction moyenne_doubles (niveau 3 - récursif)"""

    def test_liste_simple(self):
        """Test avec une liste simple"""
        self.assertEqual(moyenne_doubles([1, 2, 3]), 4.0)

    def test_un_element(self):
        """Test avec un seul élément"""
        self.assertEqual(moyenne_doubles([5]), 10.0)

    def test_nombres_pairs(self):
        """Test avec des nombres pairs"""
        self.assertEqual(moyenne_doubles([2, 4, 6]), 8.0)

    def test_resultat_decimal(self):
        """Test que le résultat est bien un float"""
        resultat = moyenne_doubles([1, 2])
        self.assertIsInstance(resultat, float)
        self.assertEqual(resultat, 3.0)

    def test_exception_liste_vide(self):
        """Test qu'une exception est levée si la liste est vide"""
        with self.assertRaises(ValueError):
            moyenne_doubles([])

    def test_exception_message_liste_vide(self):
        """Test que le message d'erreur est correct pour une liste vide"""
        with self.assertRaises(ValueError) as context:
            moyenne_doubles([])
        self.assertIn("vide", str(context.exception))

    def test_exception_non_liste(self):
        """Test qu'une exception est levée si l'argument n'est pas une liste"""
        with self.assertRaises(TypeError):
            moyenne_doubles("pas une liste")

    def test_exception_element_non_numerique(self):
        """Test qu'une exception est levée si un élément n'est pas un nombre"""
        with self.assertRaises(TypeError):
            moyenne_doubles([1, "deux", 3])


class Test_Calculatrice(unittest.TestCase):
    """Tests pour la classe Calculatrice - démontre le support des classes"""

    def setUp(self):
        """Initialise une calculatrice pour chaque test"""
        self.calc = Calculatrice(10)

    def test_initialisation(self):
        """Test que la calculatrice est correctement initialisée"""
        self.assertEqual(self.calc.resultat, 10)

    def test_initialisation_defaut(self):
        """Test de l'initialisation avec valeur par défaut"""
        calc_vide = Calculatrice()
        self.assertEqual(calc_vide.resultat, 0)

    def test_ajouter(self):
        """Test de la méthode ajouter"""
        self.calc.ajouter(5)
        self.assertEqual(self.calc.resultat, 15)

    def test_doubler(self):
        """Test de la méthode doubler (utilise la fonction double())"""
        self.calc.doubler()
        self.assertEqual(self.calc.resultat, 20)

    def test_operations_chainees(self):
        """Test d'une séquence d'opérations"""
        self.calc.ajouter(5)      # 10 + 5 = 15
        self.calc.doubler()        # 15 * 2 = 30
        self.calc.ajouter(10)      # 30 + 10 = 40
        self.assertEqual(self.calc.resultat, 40)

    def test_reinitialiser(self):
        """Test de la méthode reinitialiser"""
        self.calc.ajouter(100)
        self.calc.reinitialiser()
        self.assertEqual(self.calc.resultat, 0)

    def test_exception_init_non_numerique(self):
        """Test qu'une exception est levée si la valeur initiale n'est pas un nombre"""
        with self.assertRaises(TypeError):
            Calculatrice("dix")

    def test_exception_ajouter_non_numerique(self):
        """Test qu'une exception est levée si on ajoute une valeur non numérique"""
        with self.assertRaises(TypeError):
            self.calc.ajouter("cinq")


if __name__ == '__main__':
    unittest.main()
