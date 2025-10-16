# Guide d'utilisation - Python to Moodle XML Generator

## Installation

### 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

Les dépendances requises :
- `PyYAML>=6.0` : Pour lire le fichier de configuration

## Utilisation

### Commande de base

```bash
python python_to_moodle.py <fichier_fonctions.py> [options]
```

### Exemple avec les fichiers de démonstration

```bash
python python_to_moodle.py input/partiel_In211_2526_with_comment.py --unittest-file input/partiel_In211_2526_unittest.py
```

### Options disponibles

- `--config <fichier>` : Fichier de configuration YAML (défaut: `config.yaml`)
- `--unittest-file <fichier>` : Fichier unittest (auto-détecté si non fourni)
- `--output <fichier>` : Fichier XML de sortie (auto-généré si non fourni dans `output/`)

### Exemples

#### Utilisation simple
```bash
python python_to_moodle.py mon_fichier.py
```
Le script cherchera automatiquement `mon_fichier_unittest.py` dans le même répertoire.

#### Spécifier le fichier de sortie
```bash
python python_to_moodle.py input/exercices.py --output mes_questions.xml
```

#### Utiliser une configuration personnalisée
```bash
python python_to_moodle.py input/exercices.py --config ma_config.yaml
```

## Structure des fichiers d'entrée

### Fichier de fonctions (ex: `partiel_In211_2526_with_comment.py`)

```python
"""
Docstring du module - devient la description de la catégorie Moodle
"""

def ma_fonction(param1, param2):
    '''
    Docstring de la fonction - sera affiché comme consigne dans Moodle

    Cette fonction fait ceci et cela...
    '''
    # Implémentation
    return result
```

**Points importants :**
- Une fonction = Une question Moodle
- Le nom de la fonction devient le nom de la question
- Le docstring de la fonction devient l'énoncé
- Le docstring du module devient la description de la catégorie

### Fichier unittest (ex: `partiel_In211_2526_unittest.py`)

```python
import unittest

class TestMaFonction(unittest.TestCase):
    """Tests pour ma_fonction"""

    def setUp(self):
        """Optionnel: code exécuté avant chaque test"""
        self.valeur = 42

    def test_cas_simple(self):
        """Le premier test devient l'exemple visible par les étudiants"""
        self.assertEqual(ma_fonction(1, 2), 3)

    def test_cas_complexe(self):
        """Tests supplémentaires"""
        self.assertEqual(ma_fonction(10, 20), 30)
        self.assertTrue(ma_fonction(0, 0) == 0)

    def test_exception(self):
        """Test des exceptions"""
        with self.assertRaises(ValueError):
            ma_fonction(-1, -1)
```

**Points importants :**
- Nom de la classe : `Test{NomFonction}` (ex: `TestMaFonction` pour tester `ma_fonction`)
- Convention CamelCase → snake_case : `TestFeetToMeter` → `feet_to_meter`
- Le premier test a `useasexample="1"` (affiché aux étudiants)
- Chaque méthode `test_*` devient un test case Moodle

### Transformations des assertions

Le script transforme automatiquement les assertions unittest :

| Assertion unittest | Code Moodle généré |
|-------------------|-------------------|
| `self.assertEqual(a, b)` | `print(a)` avec `expected=b` |
| `self.assertTrue(expr)` | `print(expr)` avec `expected=True` |
| `self.assertFalse(expr)` | `print(expr)` avec `expected=False` |
| `self.assertIn(a, container)` | `print(a in container)` avec `expected=True` |
| `with self.assertRaises(ValueError):` | `try/except` avec `print("OK"/"KO")` |

## Configuration (config.yaml)

Le fichier `config.yaml` permet de personnaliser la génération :

### Catégorie Moodle
```yaml
category:
  path: "$course$/top/Ma Catégorie/Sous-Catégorie"
  info: "Description de la banque de questions"
  info_format: "html"
```

### Paramètres CodeRunner
```yaml
coderunner:
  type: "python3"  # Type de question
  allornothing: 1  # 1 = tout ou rien, 0 = points partiels
  answerboxlines: 18  # Nombre de lignes dans l'éditeur
  defaultgrade: 1.0  # Note par défaut
  penalty: 0.0  # Pénalité par tentative
```

### Tags
```yaml
tags:
  - "python"
  - "partiel"
  - "2024-2025"
```

### Logging
```yaml
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR
  format: "%(asctime)s - %(levelname)s - %(message)s"
  file: null  # ou chemin vers un fichier de log
```

## Dépannage

### Erreur : "Fichier unittest non trouvé"
Le script cherche automatiquement un fichier avec le suffixe `_unittest.py`. Si votre fichier a un nom différent, utilisez l'option `--unittest-file` :
```bash
python python_to_moodle.py fichier.py --unittest-file mes_tests.py
```

### Erreur : "Fonctions sans classe de test"
Chaque fonction dans le fichier Python doit avoir sa classe de test correspondante avec le nom `Test{NomFonction}`.

### Problème de transformation d'assertion
Si une assertion n'est pas correctement transformée, vérifiez :
- Que vous utilisez les assertions supportées (voir tableau ci-dessus)
- Que le code est valide Python
- Consultez les logs avec `--config` et `logging.level: DEBUG`

### Caractères spéciaux dans le XML
Le générateur gère automatiquement :
- Les caractères HTML (`<`, `>`, `&`)
- Les CDATA pour le code Python
- L'encodage UTF-8

## Workflow recommandé

1. **Développer les fonctions** dans un fichier Python avec docstrings
2. **Écrire les tests unittest** dans un fichier séparé
3. **Tester localement** que les tests passent : `python -m unittest fichier_unittest.py`
4. **Générer le XML** : `python python_to_moodle.py fichier.py`
5. **Importer dans Moodle** le fichier XML généré dans `output/`
6. **Vérifier dans Moodle** que les questions s'affichent correctement
7. **Tester une question** manuellement dans Moodle

## Exemples de fichiers

Des exemples complets sont fournis dans le répertoire `input/` :
- `input/partiel_In211_2526_with_comment.py` : Fichier de fonctions
- `input/partiel_In211_2526_unittest.py` : Fichier de tests
- `input/questions-25-Mi21-In1-Partiel -20251015-2313.xml` : Exemple de XML Moodle (référence)

## Limites connues

- Les boucles `for` avec `subTest` ne sont pas encore complètement transformées
- Les assertions complexes peuvent nécessiter un ajustement manuel
- Les classes dans le fichier de fonctions ne sont pas encore supportées comme questions

## Support

Pour signaler un bug ou demander une fonctionnalité, consultez le README principal du projet.
