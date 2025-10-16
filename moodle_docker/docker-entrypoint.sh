#!/bin/bash
set -e

# Attendre que MySQL soit prêt
echo "Waiting for MySQL..."
until mysql -h"${MOODLE_DATABASE_HOST}" -u"${MOODLE_DATABASE_USER}" -p"${MOODLE_DATABASE_PASSWORD}" --skip-ssl -e "SELECT 1" >/dev/null 2>&1; do
  sleep 2
done
echo "MySQL is ready!"

# Créer et configurer moodledata si nécessaire
if [ ! -d "/var/www/moodledata" ]; then
    mkdir -p /var/www/moodledata
fi
chown -R www-data:www-data /var/www/moodledata
chmod 777 /var/www/moodledata

# Créer config.php si il n'existe pas
if [ ! -f "/var/www/html/config.php" ]; then
    echo "Creating Moodle config.php..."
    cat > /var/www/html/config.php <<EOF
<?php
unset(\$CFG);
global \$CFG;
\$CFG = new stdClass();

\$CFG->dbtype    = 'mysqli';
\$CFG->dblibrary = 'native';
\$CFG->dbhost    = '${MOODLE_DATABASE_HOST}';
\$CFG->dbname    = '${MOODLE_DATABASE_NAME}';
\$CFG->dbuser    = '${MOODLE_DATABASE_USER}';
\$CFG->dbpass    = '${MOODLE_DATABASE_PASSWORD}';
\$CFG->prefix    = 'mdl_';
\$CFG->dboptions = array(
    'dbpersist' => false,
    'dbsocket'  => false,
    'dbport'    => '',
);

\$CFG->wwwroot   = 'http://localhost:8080';
\$CFG->dataroot  = '/var/www/moodledata';
\$CFG->directorypermissions = 02777;
\$CFG->admin = 'admin';

require_once(__DIR__ . '/lib/setup.php');
EOF
    chown www-data:www-data /var/www/html/config.php

    echo "Installing Moodle..."
    cd /var/www/html
    php admin/cli/install_database.php \
        --agree-license \
        --adminuser=admin \
        --adminpass=Admin123! \
        --adminemail=admin@example.com \
        --fullname="Moodle CodeRunner Dev" \
        --shortname="MoodleDev"

    echo "Moodle installation complete!"
fi

# ============================================
# Configuration pour Jobe local
# ============================================
echo "Configuring Moodle for local Jobe server..."

# 1. Ajouter configuration cURL dans config.php si pas déjà présent
if ! grep -q "curlsecurityblockedhosts" /var/www/html/config.php; then
    echo "Adding cURL security configuration to config.php..."
    # Insérer avant la ligne require_once
    sed -i "/require_once(__DIR__ . '\/lib\/setup.php');/i \\
// Configuration pour autoriser la connexion au serveur Jobe local\\
\\\$CFG->curlsecurityblockedhosts = '';\\
\\\$CFG->curlsecurityallowedport = '80:443,4000:4999';\\
" /var/www/html/config.php
fi

# 2. Patcher curl_security_helper.php pour désactiver le blocage d'URLs
if [ -f "/var/www/html/lib/classes/files/curl_security_helper.php" ]; then
    if ! grep -q "PATCH: Désactiver la sécurité cURL" /var/www/html/lib/classes/files/curl_security_helper.php; then
        echo "Patching curl_security_helper.php to allow local Jobe server..."
        # Backup du fichier original
        cp /var/www/html/lib/classes/files/curl_security_helper.php \
           /var/www/html/lib/classes/files/curl_security_helper.php.backup

        # Remplacer la fonction is_enabled() pour retourner false
        sed -i '/public function is_enabled() {/!b;n;c\        return false; \/\/ PATCH: Désactiver la sécurité cURL pour Jobe local' \
            /var/www/html/lib/classes/files/curl_security_helper.php
    fi
fi

# 3. Configurer le serveur Jobe dans la base de données (si Moodle est déjà installé)
if mysql -h"${MOODLE_DATABASE_HOST}" -u"${MOODLE_DATABASE_USER}" -p"${MOODLE_DATABASE_PASSWORD}" \
   "${MOODLE_DATABASE_NAME}" --skip-ssl -e "SELECT 1 FROM mdl_config LIMIT 1" >/dev/null 2>&1; then
    echo "Configuring Jobe server in database..."
    mysql -h"${MOODLE_DATABASE_HOST}" -u"${MOODLE_DATABASE_USER}" -p"${MOODLE_DATABASE_PASSWORD}" \
        "${MOODLE_DATABASE_NAME}" --skip-ssl <<EOSQL
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
fi

echo "Jobe configuration complete!"

# Démarrer Apache
echo "Starting Apache..."
exec apache2-foreground
