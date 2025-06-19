#!/usr/bin/env bash
# Run this script to update the version of the site running
# at www.flickr.org/tools/flickypedia.

set -o errexit
set -o nounset

source "$(dirname "$0")/functions.sh"



# 0. If we're not running on Sontag, SSH into Sontag and run the sript there.
if [[ "$(hostname)" != "sontag.local" ]]
then
  print_info "Not on Sontag, so running script over SSH/Tailscale"
  
  bash "$(dirname "$0")/ensure_tailscale_running.sh"
  
  SONTAG_IP_ADDRESS="$(/Applications/Tailscale.app/Contents/MacOS/Tailscale ip --4 sontag)"
  print_info "Detected Sontag IP address as $SONTAG_IP_ADDRESS"
  
  print_info "Running SSH command on Sontag"
  print_info "---"
  
  ssh "sontag@$SONTAG_IP_ADDRESS" "cd ~/repos/flickypedia && bash scripts/restart_prod.sh"
  exit 0
fi



# 1. Pull the latest version of the code from GitHub
#
# We only pull changes if we're on main; if we're on a different branch,
# somebody is doing something experimental and we don't want to mess it
# up with a merge conflict or something.

BRANCH="$(git rev-parse --abbrev-ref HEAD)"
COMMIT="$(git rev-parse --short HEAD)"

if [[ "$BRANCH" == "main" ]]
then
  print_info "Pulling latest changes from 'main' on GitHub"
  git pull origin main
else
  print_warning "You are not on branch $BRANCH, commit $COMMIT, which is not main."
  print_warning "This script is not pulling changes to avoid merge conflicts; you must"
  print_warning "pull your changes manually from GitHub."
fi



# 2. Activate the virtualenv, and install the latest version of
#    all our packages
print_info "Installing latest versions of any Python packages"
source .venv/bin/activate
pip install --quiet -r requirements.txt



# 3. Restart the app with the new code.
#
#    Specifically, we send a SIGHUP to gunicorn, the web server, which
#    tells it to reload its configuration and start new worker processes.
#    See https://docs.gunicorn.org/en/stable/signals.html#reload-the-configuration
#
print_info "Restarting the app with the latest changes"
kill -HUP $(cat flickypedia.pid)




echo ""
echo "To see the access logs (e.g. people using the app):"
echo ""
echo "    tail -f access.log"
echo ""
echo "To follow the application logs (e.g. application errors):"
echo ""
echo "    tail -f app.log"
echo ""
