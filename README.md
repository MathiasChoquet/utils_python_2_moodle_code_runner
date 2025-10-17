# Python to Moodle CodeRunner - Projet complet

Outil complet pour créer et tester des questions CodeRunner pour Moodle.

## Structure du projet

```
PYTHON_2_MOODLE_CODE_RUNNER/
├── python_to_moodle/          # 🐍 Outil de transformation Python → XML Moodle
│   ├── python_to_moodle.py    # Script principal
│   ├── config.yaml            # Configuration
│   ├── requirements.txt       # Dépendances Python
│   ├── UTILISATION.md         # Guide d'utilisation détaillé
│   ├── src/                   # Code source
│   │   ├── function_analyzer.py
│   │   ├── unittest_analyzer.py
│   │   ├── assertion_transformer.py
│   │   └── moodle_xml_generator.py
│   ├── input/                 # Fichiers Python d'exemple
│   │   ├── test_minimal.py
│   │   └── test_minimal_unittest.py
│   └── output/                # XML Moodle généré
│
└── moodle_docker/             # 🐳 Environnement Moodle + CodeRunner + Jobe
    ├── docker-compose.yml     # Configuration Docker
    ├── Dockerfile             # Image Moodle personnalisée
    └── docker-entrypoint.sh   # Script de démarrage
```

## 📦 Les deux parties du projet

### 1️⃣ python_to_moodle/ - Transformation Python → XML Moodle

**Objectif :** Transformer automatiquement vos fichiers Python (fonctions + tests unittest) en questions Moodle CodeRunner au format XML.

**Quick Start :**
```bash
cd python_to_moodle
pip install -r requirements.txt
python python_to_moodle.py input/test_minimal.py --unittest-file input/test_minimal_unittest.py
```

➡️ [Voir la documentation complète](python_to_moodle/UTILISATION.md)

**Fonctionnalités :**
- ✅ Analyse automatique des fonctions Python et leurs docstrings
- ✅ Extraction des dépendances entre fonctions
- ✅ Transformation des tests unittest en test cases Moodle
- ✅ Génération XML conforme au format Moodle CodeRunner
- ✅ Configuration flexible via YAML
- ✅ Logging détaillé

**Workflow typique :**
1. Écrivez vos fonctions Python avec docstrings
2. Créez les tests unittest correspondants
3. Générez le XML : `python python_to_moodle.py votre_fichier.py`
4. Importez le XML dans Moodle

---

### 2️⃣ moodle_docker/ - Environnement de test local

**Objectif :** Environnement Docker complet (Moodle + CodeRunner + Jobe) pour développer et tester vos questions localement avant de les déployer en production.

**Quick Start :**
```bash
cd moodle_docker
docker-compose up -d
```

Accédez à Moodle : http://localhost:8080
- **Utilisateur :** admin
- **Mot de passe :** Admin123!

➡️ [Voir la documentation complète](moodle_docker/README.md)

**Composants :**
- 🎓 **Moodle 4.3** - Plateforme d'apprentissage
- 💻 **CodeRunner** - Plugin pour questions de programmation
- ⚙️ **Jobe** - Serveur d'exécution de code (sandbox)
- 🗄️ **MariaDB** - Base de données

**Workflow typique :**
1. Lancez l'environnement Docker
2. Importez vos questions XML dans la banque de questions
3. Testez les questions avec différents codes étudiants
4. Ajustez si nécessaire
5. Exportez et déployez en production

---

## 🚀 Workflow complet recommandé

### Développement de questions

1. **Développer** vos fonctions Python avec docstrings
   ```python
   def ma_fonction(param):
       """
       Énoncé de l'exercice pour les étudiants...
       """
       return result
   ```

2. **Tester** avec unittest
   ```python
   class TestMaFonction(unittest.TestCase):
       def test_cas_simple(self):
           self.assertEqual(ma_fonction(42), 84)
   ```

3. **Générer le XML**
   ```bash
   cd python_to_moodle
   python python_to_moodle.py mon_fichier.py
   ```

4. **Tester localement**
   ```bash
   cd ../moodle_docker
   docker-compose up -d
   # Importer le XML dans Moodle local (http://localhost:8080)
   ```

5. **Valider** les questions dans l'environnement local

6. **Déployer** le XML validé sur votre Moodle de production

---

## 📚 Documentation détaillée

- [Guide d'utilisation Python to Moodle](python_to_moodle/UTILISATION.md)
- [Guide environnement Docker](moodle_docker/README.md)

## 🔧 Configuration requise

### Python to Moodle
- Python 3.8+
- PyYAML

### Moodle Docker
- Docker
- Docker Compose
- Ports disponibles : 8080, 8443, 4000

## 💡 Exemples

Des fichiers d'exemple complets sont fournis dans `python_to_moodle/input/` :

### test_minimal.py
Fichier d'exemple démontrant :
- **Deux fonctions** : `double()` et `somme_doubles()`
- **Dépendances** : `somme_doubles()` utilise `double()`
- **Docstrings complètes** avec Args, Returns, Raises et Exemples
- **Gestion d'exceptions** avec TypeError

### test_minimal_unittest.py
Fichier de tests démontrant tous les types d'assertions :
- ✅ **assertEqual** : tests d'égalité (nombres positifs, négatifs, zéro, décimaux)
- ✅ **assertIn** : tests d'appartenance (vérifier qu'un résultat est dans une liste)
- ✅ **assertRaises** : tests d'exceptions (TypeError avec arguments invalides)
- ✅ **Tests de messages d'erreur** : vérification du contenu des exceptions

**Génération :** Crée 2 questions Moodle avec 13 tests au total

## 🤝 Contribution

Pour signaler un bug ou proposer une amélioration, créez une issue dans le dépôt du projet.

## 📝 Licence

Ce projet est fourni tel quel pour un usage éducatif.

---

**Développé pour faciliter la création de questions CodeRunner pour Moodle** 🎓✨
