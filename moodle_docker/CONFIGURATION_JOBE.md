# Configuration de Moodle pour utiliser le serveur Jobe local

Ce document explique comment configurer Moodle pour utiliser le serveur Jobe local au lieu du serveur public de l'Université de Canterbury.

## 🚀 Configuration automatique (Recommandé)

Les modifications sont **automatiquement appliquées** au démarrage du conteneur Moodle grâce au script `docker-entrypoint.sh`.

### Démarrage initial

```bash
cd moodle_docker
docker-compose up -d
```

Attendez environ 30 secondes que l'installation et la configuration se terminent.

### Redémarrage après arrêt

```bash
docker-compose down
docker-compose up -d
```

Les modifications seront **automatiquement réappliquées** à chaque démarrage.

## 🔧 Configuration manuelle (si nécessaire)

Si vous avez besoin de réappliquer la configuration manuellement :

```bash
cd moodle_docker
bash configure-jobe.sh
```

Ce script :
1. ✅ Ajoute la configuration cURL dans `config.php`
2. ✅ Patche le fichier `curl_security_helper.php` pour désactiver le blocage d'URLs
3. ✅ Configure le serveur Jobe dans la base de données
4. ✅ Vide le cache Moodle

## 📋 Modifications appliquées

### 1. Configuration cURL (config.php)

Ajout de ces lignes dans `/var/www/html/config.php` :

```php
// Configuration pour autoriser la connexion au serveur Jobe local
$CFG->curlsecurityblockedhosts = '';
$CFG->curlsecurityallowedport = '80:443,4000:4999';
```

### 2. Patch de sécurité cURL

Modification de `/var/www/html/lib/classes/files/curl_security_helper.php` :

```php
public function is_enabled() {
    return false; // PATCH: Désactiver la sécurité cURL pour Jobe local
}
```

⚠️ **Attention** : Ce patch désactive complètement la sécurité cURL de Moodle.
**À utiliser uniquement en environnement de développement local !**

### 3. Configuration base de données

Configuration dans la table `mdl_config_plugins` :

| Plugin | Name | Value |
|--------|------|-------|
| qtype_coderunner | jobe_host | jobe:80 |
| qtype_coderunner | jobesandbox_enabled | 1 |
| qtype_coderunner | jobe_apikey | (vide) |

## 🧪 Vérification

Pour vérifier que tout fonctionne :

1. **Accédez à Moodle** : http://localhost:8080
   - Utilisateur : `admin`
   - Mot de passe : `Admin123!`

2. **Créez ou prévisualisez une question CodeRunner**

3. **Vérifiez que le message "University of Canterbury" n'apparaît plus**

4. **Surveillez les logs Jobe** :
   ```bash
   docker logs moodle_jobe -f
   ```
   Vous devriez voir des requêtes POST arriver depuis `192.168.0.X` (le conteneur Moodle)

## 🔍 Dépannage

### Le message "URL is blocked" apparaît

Si vous voyez ce message après un redémarrage :

```bash
cd moodle_docker
bash configure-jobe.sh
```

### Vérifier la configuration Jobe dans la BDD

```bash
docker exec moodle_db mysql -u moodleuser -pmoodlepass moodle -e \
  "SELECT name, value FROM mdl_config_plugins WHERE plugin='qtype_coderunner' AND name LIKE '%jobe%';"
```

Vous devriez voir :
```
name                    value
jobe_host               jobe:80
jobesandbox_enabled     1
jobe_apikey
```

### Vérifier que Jobe fonctionne

```bash
# Depuis votre machine hôte
curl http://localhost:4000/jobe/index.php/restapi/languages

# Depuis le conteneur Moodle
docker exec moodle_app curl http://jobe/jobe/index.php/restapi/languages
```

Les deux commandes devraient retourner une liste de langages en JSON.

## 📁 Structure des fichiers

```
moodle_docker/
├── docker-compose.yml          # Configuration Docker
├── Dockerfile                  # Image Moodle personnalisée
├── docker-entrypoint.sh        # Script de démarrage (avec config Jobe automatique)
├── configure-jobe.sh           # Script de configuration manuelle
└── CONFIGURATION_JOBE.md       # Cette documentation
```

## ⚠️ Avertissement de sécurité

Les modifications apportées **désactivent les protections de sécurité cURL de Moodle**.

- ✅ **OK pour développement local**
- ❌ **NE JAMAIS utiliser en production**

En production, utilisez :
- Le serveur Jobe public de Canterbury, ou
- Un serveur Jobe avec une URL publique et un certificat SSL valide

## 🔄 Réinitialisation complète

Pour repartir de zéro (efface toutes les données !) :

```bash
cd moodle_docker
docker-compose down -v
docker-compose up -d
```

Les configurations seront automatiquement réappliquées.
