# Deployment

Deploy CDI in `/opt/apps/cofinets-data-intelligence` as an independent Compose project. Bind host ports only to loopback during validation. Do not reuse the existing Cofinets database, network, volumes, or Compose project. Nginx/DNS changes happen only after application health checks pass.
