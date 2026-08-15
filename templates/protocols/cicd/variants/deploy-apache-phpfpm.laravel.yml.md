# deploy-apache-phpfpm.laravel.yml.md
#
# Template: GitHub Actions deploy workflow for Laravel apps with Apache + PHP-FPM.
# Used by the Builder (Phase 6) when stack_detected in ('laravel', 'laravel_node') and vps_runtime == 'apache_php_fpm'.
#
# Placeholders:
#   {{trigger_event}}   — 'tags:\n        - \'v*\'' or 'branches:\n        - main'
#   {{php_version}}     — e.g. '8.3' (from composer.json require.php)
#   {{node_version}}    — e.g. '20' (from .nvmrc or package.json engines)
#   {{has_node_assets}} — 'true' or 'false' (true when stack_detected == 'laravel_node')
#   {{deploy_path}}     — e.g. '/var/www/my-app/current'

name: Deploy to Production

on:
  push:
    {{trigger_event}}

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup PHP
        uses: shivammathur/setup-php@v2
        with:
          php-version: '{{php_version}}'
          extensions: mbstring, xml, curl, mysql, zip, gd, bcmath, dom, fileinfo
          coverage: none

      {{if has_node_assets}}
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '{{node_version}}'
      {{/if}}

      - name: Install Composer dependencies
        run: composer install --no-dev --optimize-autoloader --no-interaction

      {{if has_node_assets}}
      - name: Install NPM dependencies
        run: npm ci

      - name: Build frontend assets
        run: npm run build
      {{/if}}

      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ '{{' }} secrets.SERVER_IP {{ '}}' }}
          username: ${{ '{{' }} secrets.SSH_USER {{ '}}' }}
          key: ${{ '{{' }} secrets.SSH_KEY {{ '}}' }}
          script: |
            set -e
            cd {{deploy_path}}

            # Backup current .env (never overwrite)
            cp .env .env.backup 2>/dev/null || true

            # Pull latest code
            git pull origin main

            # Install PHP dependencies
            composer install --no-dev --optimize-autoloader --no-interaction

            {{if has_node_assets}}
            # Install and build frontend assets
            npm ci
            npm run build
            {{/if}}

            # Restore .env if git overwrote it
            cp .env.backup .env 2>/dev/null || true

            # Run migrations
            php artisan migrate --force

            # Cache configs
            php artisan config:cache
            php artisan route:cache
            php artisan view:cache
            php artisan event:cache

            # Restart queue workers
            php artisan queue:restart

            # Restart Apache + PHP-FPM
            sudo systemctl restart php{{php_version}}-fpm
            sudo systemctl restart apache2

            echo "✅ Deploy complete"
