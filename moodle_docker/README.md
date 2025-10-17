# Environnement Moodle + CodeRunner + Jobe (Docker)

Environnement Docker pour développer et tester des questions CodeRunner pour Moodle en local.

## Architecture

- **Moodle 4.1** : Plateforme d'apprentissage
- **CodeRunner** : Plugin de questions de programmation pour Moodle (installé automatiquement)
- **Jobe** : Serveur d'exécution de code (sandbox)
- **MySQL 8.0** : Base de données

## Démarrage rapide

### 1. Lancer l'environnement

```bash
docker-compose up -d
```

Le premier démarrage prend quelques minutes (téléchargement des images et initialisation).

> **Important** : Si vous avez déjà utilisé cet environnement auparavant, il est recommandé de supprimer les volumes existants pour repartir sur une installation propre :
> ```bash
> docker-compose down -v
> docker-compose up -d
> ```

### 2. Accéder à Moodle

- **URL** : http://localhost:8080
- **Utilisateur** : admin
- **Mot de passe** : Admin123!

> **Note** : Le premier démarrage prend quelques minutes car le système installe automatiquement Moodle, CodeRunner, et configure Jobe. Attendez que les logs indiquent "Starting Apache..." avant de vous connecter.

### 3. Vérifier l'installation de CodeRunner (automatique)

**CodeRunner et Jobe sont installés et configurés automatiquement !** Vous pouvez vérifier :

1. Connectez-vous à Moodle
2. Allez dans **Administration du site > Plugins > Types de questions > CodeRunner**
3. Vérifiez que le serveur Jobe est configuré sur `http://jobe:80`
4. Cliquez sur **Test connexion** pour vérifier que tout fonctionne

### 4. Créer un cours

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

## Installation automatique de CodeRunner

L'environnement est configuré pour installer et configurer automatiquement CodeRunner :

### Lors du build Docker
1. Le plugin CodeRunner v5.2.1 (compatible Moodle 4.1) est téléchargé depuis GitHub
2. Il est installé dans `/var/www/html/question/type/coderunner`
3. Le behaviour `adaptive_adapted_for_coderunner` est également installé automatiquement

### Au premier démarrage
1. Moodle est installé avec la base de données
2. Le script d'installation détecte le plugin CodeRunner et l'installe automatiquement
3. La configuration de Jobe est automatiquement mise à jour dans la base de données :
   - `jobe_host` = `http://jobe:80`
   - `jobesandbox_enabled` = `1`
4. Les restrictions de sécurité cURL sont désactivées pour autoriser la connexion à Jobe

Le bouton "Check" devrait fonctionner immédiatement après l'installation !

### Vérification manuelle

Pour vérifier que tout est bien configuré :

```bash
# Voir les logs d'installation
docker logs moodle_app

# Vous devriez voir :
# - "Installing Moodle plugins (CodeRunner)..."
# - "Plugins installation complete!"
# - "Jobe server configured for CodeRunner!"
```

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

### CodeRunner n'est pas installé

Si CodeRunner n'apparaît pas dans les plugins :

1. Vérifiez les logs : `docker logs moodle_app`
2. Réinstallez manuellement depuis le conteneur :
```bash
docker exec -it moodle_app bash
cd /var/www/html
php admin/cli/upgrade.php --non-interactive
```

### Jobe ne se connecte pas à CodeRunner

1. Vérifiez que Jobe fonctionne :
```bash
curl http://localhost:4000/jobe/index.php/restapi/languages
```

2. Testez la connexion depuis le conteneur Moodle :
```bash
docker exec -it moodle_app curl http://jobe:80/jobe/index.php/restapi/languages
```

3. Si la connexion échoue, vérifiez les paramètres dans la base de données :
```bash
docker exec -it moodle_app bash
mysql -hmysql -umoodleuser -pmoodlepass moodle -e "SELECT * FROM mdl_config_plugins WHERE plugin='qtype_coderunner';"
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
