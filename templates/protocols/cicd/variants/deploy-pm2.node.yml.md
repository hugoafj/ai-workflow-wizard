# deploy-pm2.node.yml.md
#
# Template: GitHub Actions deploy workflow for Node.js apps with PM2.
# Used by the Builder (Phase 6) when stack_detected == 'node_pure' and vps_runtime == 'pm2'.
#
# Placeholders:
#   {{trigger_event}}   — 'tags:\n        - \'v*\'' or 'branches:\n        - main'
#   {{node_version}}    — e.g. '20' (from .nvmrc or package.json engines)
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

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '{{node_version}}'

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build

      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.2.5
        with:
          host: ${{ '{{' }} secrets.SERVER_IP {{ '}}' }}
          username: ${{ '{{' }} secrets.SSH_USER {{ '}}' }}
          key: ${{ '{{' }} secrets.SSH_KEY {{ '}}' }}
          script: |
            set -euo pipefail
            cd {{deploy_path}}
            git pull origin main
            npm ci
            npm run build
            npm prune --omit=dev
            pm2 restart app
