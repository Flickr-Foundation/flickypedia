#!/usr/bin/env bash
set -o errexit
set -o nounset

# Enable and start production units. Run as root (this script calls sudo
# systemctl; flickrfoundation cannot use sudo).
#
# Live unit names on flickr-foundation-apps (must match systemd/ and
# /etc/systemd/system/). Both gunicorn and the upload worker are required;
# the site can look healthy while uploads sit forever if the worker is down.

sudo systemctl enable flickypedia-gunicorn
sudo systemctl start flickypedia-gunicorn
sudo systemctl enable flickypedia-upload-worker
sudo systemctl start flickypedia-upload-worker

echo ""
echo "To see the access logs (e.g. people using the app):"
echo ""
echo "    tail -f access.log"
echo ""
echo "To follow the application logs (e.g. application errors):"
echo ""
echo "    tail -f app.log"
echo ""
echo "To follow the upload worker:"
echo ""
echo "    journalctl -u flickypedia-upload-worker.service -f"
echo ""
echo "To pull changes from GitHub and restart the web app:"
echo ""
echo "    bash scripts/restart_prod.sh"
echo ""
echo "After worker-related code changes, also restart the worker as root:"
echo ""
echo "    systemctl restart flickypedia-upload-worker.service"
echo ""
