#!/bin/bash
# Script pour configurer Moodle afin qu'il utilise le serveur Jobe local
# Ce script peut être exécuté manuellement si nécessaire

set -e

echo "=========================================="
echo "Configuration de Moodle pour Jobe local"
echo "=========================================="

# Vérifier que le conteneur Moodle est actif
if ! docker ps | grep -q moodle_app; then
    echo "Erreur: Le conteneur moodle_app n'est pas démarré."
    echo "Lancez 'docker-compose up -d' d'abord."
    exit 1
fi

echo "1. Ajout de la configuration cURL dans config.php..."
docker exec moodle_app bash -c "
if ! grep -q 'curlsecurityblockedhosts' /var/www/html/config.php; then
    sed -i \"/require_once(__DIR__ . '\/lib\/setup.php');/i \\\\
// Configuration pour autoriser la connexion au serveur Jobe local\\\\
\\\$CFG->curlsecurityblockedhosts = '';\\\\
\\\$CFG->curlsecurityallowedport = '80:443,4000:4999';\\\\
\" /var/www/html/config.php
    echo '   ✓ Configuration cURL ajoutée'
else
    echo '   ℹ Configuration cURL déjà présente'
fi
"

echo "2. Patch du fichier curl_security_helper.php..."
docker exec moodle_app bash -c "
if [ -f '/var/www/html/lib/classes/files/curl_security_helper.php' ]; then
    if ! grep -q 'PATCH: Désactiver la sécurité cURL' /var/www/html/lib/classes/files/curl_security_helper.php; then
        # Backup
        cp /var/www/html/lib/classes/files/curl_security_helper.php \
           /var/www/html/lib/classes/files/curl_security_helper.php.backup

        # Patch
        sed -i '/public function is_enabled() {/!b;n;c\        return false; \/\/ PATCH: Désactiver la sécurité cURL pour Jobe local' \
            /var/www/html/lib/classes/files/curl_security_helper.php
        echo '   ✓ Fichier patché'
    else
        echo '   ℹ Fichier déjà patché'
    fi
fi
"

echo "3. Configuration du serveur Jobe dans la base de données..."
docker exec moodle_db mysql -u moodleuser -pmoodlepass moodle --skip-ssl <<EOSQL 2>/dev/null
INSERT INTO mdl_config_plugins (plugin, name, value)
VALUES ('qtype_coderunner', 'jobe_host', 'jobe:80')
ON DUPLICATE KEY UPDATE value='jobe:80';

INSERT INTO mdl_config_plugins (plugin, name, value)
VALUES ('qtype_coderunner', 'jobesandbox_enabled', '1')
ON DUPLICATE KEY UPDATE value='1';

INSERT INTO mdl_config_plugins (plugin, name, value)
VALUES ('qtype_coderunner', 'jobe_apikey', '')
ON DUPLICATE KEY UPDATE value='';
EOSQL

if [ $? -eq 0 ]; then
    echo "   ✓ Configuration de la base de données terminée"
else
    echo "   ⚠ Erreur lors de la configuration de la base de données"
fi

echo "4. Vidage du cache Moodle..."
docker exec moodle_app bash -c "cd /var/www/html && php admin/cli/purge_caches.php" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✓ Cache vidé"
else
    echo "   ⚠ Impossible de vider le cache"
fi

echo ""
echo "=========================================="
echo "✅ Configuration terminée avec succès !"
echo "=========================================="
echo ""
echo "Votre Moodle utilise maintenant le serveur Jobe local (jobe:80)"
echo "Accédez à Moodle: http://localhost:8080"
echo "  - Utilisateur: admin"
echo "  - Mot de passe: Admin123!"
echo ""
