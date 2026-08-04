# deploy-docker.yml.md
#
# Template: GitHub Actions deploy workflow using Docker Compose for any stack.
# Used when cd.vps_runtime == 'docker'.
#
# Template variables (from .wizard-state.json):
#   cd.trigger — 'tags:\n        - \'v*\'' or 'branches:\n        - main'
#   cd.deploy_path — e.g. '/var/www/my-app/current'
#   cd.deploy_docker_compose — e.g. 'docker-compose.prod.yml'

name: Deploy to Production

on:
  push:
    {{cd.trigger}}

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Deploy via SSH
        uses: appleboy/ssh-action@v1
        with:
          host: ${{ secrets.SERVER_IP }}
          username: ${{ secrets.SSH_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            set -e
            cd {{cd.deploy_path}}

            # Pull latest code
            git pull origin main

            # Pull latest images and rebuild
            docker compose -f {{cd.deploy_docker_compose}} pull
            docker compose -f {{cd.deploy_docker_compose}} up -d --build

            # Verify containers are running
            docker compose -f {{cd.deploy_docker_compose}} ps

            echo "✅ Deploy complete"
