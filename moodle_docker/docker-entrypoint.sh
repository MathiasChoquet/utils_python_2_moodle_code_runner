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

# Démarrer Apache
echo "Starting Apache..."
exec apache2-foreground
