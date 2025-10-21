# Python to Moodle XML Generator

Outil pour transformer automatiquement vos fichiers Python (fonctions + tests unittest) en questions Moodle CodeRunner au format XML.

## 🚀 Quick Start

```bash
# Installer les dépendances
pip install -r requirements.txt

# Générer le XML depuis les fichiers d'exemple
python python_to_moodle.py input/test_minimal.py --unittest-file input/test_minimal_unittest.py

# Le fichier XML sera dans output/
```

## 📖 Documentation complète

Consultez [UTILISATION.md](UTILISATION.md) pour le guide d'utilisation détaillé.

## 📁 Structure

```
python_to_moodle/
├── python_to_moodle.py          # Script principal
├── config.yaml                  # Configuration globale
├── requirements.txt             # Dépendances Python
├── UTILISATION.md               # Guide complet
├── src/                         # Code source
│   ├── function_analyzer.py     # Analyse AST des fonctions
│   ├── unittest_analyzer.py     # Analyse des tests unittest
│   ├── assertion_transformer.py # Transformation assertions → Moodle
│   └── moodle_xml_generator.py  # Génération XML
├── input/                       # Fichiers d'exemple
│   ├── test_minimal.py                         # Exemple minimal
│   └── test_minimal_unittest.py                # Tests minimaux
└── output/                      # XML générés
    └── test_minimal_moodle.xml                 # XML généré
```

## ✨ Fonctionnalités

- ✅ Analyse automatique des fonctions Python et leurs docstrings
- ✅ Extraction des dépendances entre fonctions
- ✅ Transformation des tests unittest en test cases Moodle
- ✅ Génération XML conforme au format Moodle CodeRunner
- ✅ Configuration flexible via YAML
- ✅ Système de logging détaillé

## 📝 Exemple minimal

Les fichiers minimaux sont parfaits pour tester rapidement l'import dans Moodle :

### 1. Fichier Python minimal (`input/test_minimal.py`)

```python
def double(x):
    """
    Retourne le double d'un nombre.

    Args:
        x: Un nombre

    Returns:
        Le double de x
    """
    return x * 2
```

### 2. Tests minimaux (`input/test_minimal_unittest.py`)

```python
import unittest
from test_minimal import double

class TestDouble(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(double(5), 10)

    def test_zero(self):
        self.assertEqual(double(0), 0)
```

### 3. Générer le XML minimal

```bash
python python_to_moodle.py input/test_minimal.py
# Génère: output/test_minimal_moodle.xml
```

Ce fichier minimal est idéal pour :
- 🐛 Déboguer les problèmes d'import Moodle
- ✅ Tester rapidement la configuration
- 📚 Apprendre la structure des fichiers

## 🔧 Configuration

Personnalisez la génération en modifiant `config.yaml` :

```yaml
category:
  path: "$course$/top/Ma Catégorie"

coderunner:
  type: "python3"
  allornothing: 1

tags:
  - "python"
  - "2024-2025"
```

## 🧪 Tester les questions générées

Pour tester vos questions avant de les déployer en production, utilisez l'environnement Docker Moodle :

```bash
cd ../moodle_docker
docker-compose up -d
# Importez le XML dans http://localhost:8080
```

## 📚 Ressources

- [UTILISATION.md](UTILISATION.md) - Guide d'utilisation complet
- [Exemples](input/test_minimal.py) - Fichier d'exemple
- [Documentation Moodle CodeRunner](https://coderunner.org.nz/)

## 🐛 Dépannage

### Erreur "No module named 'yaml'"
```bash
pip install -r requirements.txt
```

### Erreur "Fichier unittest non trouvé"
Utilisez l'option `--unittest-file` pour spécifier le fichier :
```bash
python python_to_moodle.py mon_fichier.py --unittest-file mes_tests.py
```

### Erreur lors de l'import XML dans Moodle
Si vous obtenez une erreur `mysqli::real_escape_string(): Argument #1 ($string) must be of type string, array given`, cela signifie que le XML contient des caractères mal échappés.

**Solution :** Le générateur préserve maintenant correctement les caractères `<` et `>` dans les sections CDATA. Régénérez votre XML avec la dernière version du script.

**Pour déboguer :**
1. Testez d'abord avec le fichier minimal : `python python_to_moodle.py input/test_minimal.py`
2. Importez `output/test_minimal_moodle.xml` dans Moodle
3. Si le minimal fonctionne, le problème vient du fichier complexe

### Assertions non transformées
Consultez le guide [UTILISATION.md](UTILISATION.md) pour la liste des assertions supportées.

## 📝 Changelog

### Version 1.0.2 (2025-10-16)
- ✅ Ajout de fichiers d'exemple minimaux pour le débogage
- ✅ Amélioration de la détection des contenus CDATA (HTML échappé)
- ✅ Correction du format des balises vides (`<tag></tag>` au lieu de `<tag/>`)

### Version 1.0.1 (2025-10-16)
- ✅ Correction du bug d'échappement des caractères dans les CDATA
- ✅ Les séparateurs et templates Twig sont maintenant correctement préservés
- ✅ Amélioration du pretty-printing XML

### Version 1.0.0 (2025-10-16)
- 🎉 Version initiale
- ✅ Analyse AST des fonctions Python
- ✅ Transformation des tests unittest
- ✅ Génération XML Moodle CodeRunner

---

⬅️ [Retour au projet principal](../README.md)
