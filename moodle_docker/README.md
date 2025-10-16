# Environnement Moodle + CodeRunner + Jobe (Docker)

Environnement Docker pour développer et tester des questions CodeRunner pour Moodle en local.

## Architecture

- **Moodle 4.3** : Plateforme d'apprentissage
- **CodeRunner** : Plugin de questions de programmation pour Moodle
- **Jobe** : Serveur d'exécution de code (sandbox)
- **MariaDB** : Base de données

## Démarrage rapide

### 1. Lancer l'environnement

```bash
docker-compose up -d
```

Le premier démarrage prend quelques minutes (téléchargement des images et initialisation).

### 2. Accéder à Moodle

- **URL** : http://localhost:8080
- **Utilisateur** : admin
- **Mot de passe** : Admin123!

### 3. Installation de CodeRunner

Après le premier démarrage :

1. Connectez-vous à Moodle avec les identifiants ci-dessus
2. Moodle détectera automatiquement les nouveaux plugins
3. Allez dans **Administration du site > Notifications**
4. Cliquez sur **Mettre à jour la base de données Moodle** pour installer CodeRunner
5. Suivez les instructions d'installation

### 4. Configuration de Jobe

Une fois CodeRunner installé :

1. Allez dans **Administration du site > Plugins > Types de questions > CodeRunner**
2. Dans la section "Jobe sandbox settings" :
   - **Jobe server** : `http://jobe:80`
   - Cliquez sur **Test connexion** pour vérifier
3. Sauvegardez les paramètres

### 5. Créer un cours

1. Cliquez sur **Administration du site > Cours > Gérer les cours et catégories**
2. Créez une nouvelle catégorie (ex: "Python")
3. Créez un nouveau cours (ex: "Exercices Python")

## Utilisation

### Importer une banque de questions

1. Dans votre cours, allez dans **Banque de questions**
2. Cliquez sur **Importer**
3. Choisissez le format **Moodle XML**
4. Importez votre fichier XML contenant les questions CodeRunner
   (généré avec l'outil python_to_moodle)

### Tester Jobe directement

Vérifier que Jobe fonctionne :

```bash
curl -X POST http://localhost:4000/jobe/index.php/restapi/runs \
  -H "Content-Type: application/json" \
  -d '{
    "run_spec": {
      "language_id": "python3",
      "sourcefilename": "test.py",
      "sourcecode": "print(\"Hello from Jobe!\")"
    }
  }'
```

### Arrêter l'environnement

```bash
docker-compose down
```

### Supprimer toutes les données (reset complet)

```bash
docker-compose down -v
```

## Ports utilisés

- **8080** : Moodle HTTP
- **8443** : Moodle HTTPS
- **4000** : Jobe (accès direct pour tests)

## Volumes persistants

Les données sont conservées dans des volumes Docker :
- `mariadb_data` : Base de données
- `moodle_data` : Fichiers Moodle
- `moodledata` : Données utilisateur
- `jobe_data` : Cache Jobe

## Workflow recommandé avec python_to_moodle

1. **Développer** vos questions Python dans `../python_to_moodle/`
2. **Générer le XML** avec l'outil python_to_moodle
3. **Lancer cet environnement** : `docker-compose up -d`
4. **Importer le XML** dans la banque de questions Moodle
5. **Tester** les questions avec différents codes étudiants
6. **Ajuster** si nécessaire et régénérer le XML
7. **Valider** que tout fonctionne correctement
8. **Déployer** sur votre Moodle de production

## Dépannage

### Moodle ne démarre pas

Vérifiez les logs :
```bash
docker-compose logs moodle
```

### Jobe ne répond pas

Vérifiez que le conteneur est lancé :
```bash
docker-compose ps
docker-compose logs jobe
```

### Problèmes de permissions

Sur Linux/Mac, vous devrez peut-être ajuster les permissions :
```bash
sudo chown -R 1001:1001 ./volumes
```

### Erreur lors de l'import XML

- Vérifiez que le format XML est correct
- Assurez-vous que CodeRunner est bien installé
- Consultez les logs Moodle pour plus de détails

## Ressources

- [Documentation CodeRunner](https://coderunner.org.nz/)
- [Documentation Jobe](https://github.com/trampgeek/jobe)
- [Moodle Docs](https://docs.moodle.org/)

---

⬅️ [Retour au projet principal](../README.md)
