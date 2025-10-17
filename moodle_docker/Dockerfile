FROM php:8.0-apache

# Installation des extensions PHP requises par Moodle
RUN apt-get update && apt-get install -y \
    git \
    curl \
    libpng-dev \
    libzip-dev \
    libicu-dev \
    libxml2-dev \
    libfreetype6-dev \
    libjpeg62-turbo-dev \
    libpq-dev \
    libonig-dev \
    ghostscript \
    clamav \
    unzip \
    && docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install -j$(nproc) \
        gd \
        zip \
        intl \
        mysqli \
        pdo \
        pdo_mysql \
        soap \
        opcache \
        mbstring \
    && a2enmod rewrite \
    && rm -rf /var/lib/apt/lists/*

# Configuration PHP pour Moodle
RUN { \
        echo 'memory_limit = 512M'; \
        echo 'upload_max_filesize = 100M'; \
        echo 'post_max_size = 100M'; \
        echo 'max_execution_time = 300'; \
        echo 'max_input_vars = 5000'; \
    } > /usr/local/etc/php/conf.d/moodle.ini

# Télécharger Moodle
WORKDIR /var/www/html
RUN git clone --depth=1 --branch=MOODLE_401_STABLE https://github.com/moodle/moodle.git /var/www/html \
    && chown -R www-data:www-data /var/www/html

# Créer le répertoire pour les données Moodle
RUN mkdir -p /var/www/moodledata && chown -R www-data:www-data /var/www/moodledata

# Installer mysql client pour le script d'installation
RUN apt-get update && apt-get install -y default-mysql-client && rm -rf /var/lib/apt/lists/*

# Télécharger et installer le plugin CodeRunner depuis GitHub (version compatible avec Moodle 4.1)
RUN cd /var/www/html/question/type && \
    git clone --depth=1 --branch=v5.2.1 https://github.com/trampgeek/moodle-qtype_coderunner.git coderunner && \
    chown -R www-data:www-data /var/www/html/question/type/coderunner

# Télécharger et installer le behaviour adaptive_adapted_for_coderunner (version compatible)
RUN cd /var/www/html/question/behaviour && \
    git clone --depth=1 --branch=master https://github.com/trampgeek/moodle-qbehaviour_adaptive_adapted_for_coderunner.git adaptive_adapted_for_coderunner && \
    chown -R www-data:www-data /var/www/html/question/behaviour/adaptive_adapted_for_coderunner

# Copier le script d'entrypoint
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

EXPOSE 80

ENTRYPOINT ["docker-entrypoint.sh"]
