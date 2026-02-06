#!/usr/bin/env bash
set -o errexit
set -o nounset

sudo systemctl enable flickypedia-gunicorn
sudo systemctl start flickypedia-gunicorn

echo ""
echo "To see the access logs (e.g. people using the app):"
echo ""
echo "    tail -f access.log"
echo ""
echo "To follow the application logs (e.g. application errors):"
echo ""
echo "    tail -f app.log"
echo ""
echo "To pull changes from GitHub and restart the app:"
echo ""
echo "    bash scripts/restart_prod.sh"
echo ""
