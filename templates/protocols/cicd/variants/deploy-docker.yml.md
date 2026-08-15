# deploy-docker.yml.md
#
# Template: GitHub Actions deploy workflow using Docker Compose for any stack.
# Used by the Builder (Phase 6) when vps_runtime == 'docker'.
#
# Placeholders:
#   {{trigger_event}}   — 'tags:\n        - \'v*\'' or 'branches:\n        - main'
#   {{deploy_path}}     — e.g. '/var/www/my-app/current'
#   {{compose_file}}    — e.g. 'docker-compose.prod.yml' (user-specified or default)

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

      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1.2.5
        with:
          host: ${{ '{{' }} secrets.SERVER_IP {{ '}}' }}
          username: ${{ '{{' }} secrets.SSH_USER {{ '}}' }}
          key: ${{ '{{' }} secrets.SSH_KEY {{ '}}' }}
          script: |
            set -e
            cd {{deploy_path}}

            # Pull latest code
            git pull origin main

            # Pull latest images and rebuild
            docker compose -f {{compose_file}} pull
            docker compose -f {{compose_file}} up -d --build

            # Verify containers are running
            docker compose -f {{compose_file}} ps

            echo "✅ Deploy complete"
