#!/usr/bin/env bash
# Start a new instance of the site.
#
# This is meant to be run on our web server, i.e. Sontag.

set -o errexit
set -o nounset

source "$(dirname "$0")/functions.sh"



# Which address should the app run on?
#
# 8003 is the port we use for the Flickypedia; see
# https://github.com/flickr-foundation/infrastructure#port-mappings
BIND_ADDRESS="127.0.0.1:8003"



print_info "Activating Python virtual environment"
source .venv/bin/activate



print_info "Checking we can get secrets from the keychain…"

if ! keyring get flinumeratr flickr_api_key >/dev/null 2>&1
then
  print_error "Before you start Flickypedia, you need to unlock the"
  print_error "login keychain, by running the following command:"
  print_error ""
  print_error "    security unlock-keychain ~/Library/Keychains/login.keychain"
  print_error ""
  print_error "This will prompt you for the 'sontag' user password, which you"
  print_error "can find in our shared 1Password vault."
  exit 1
else
  print_info "Keychain is unlocked!"
fi



print_info "Starting the web app…"

export FLICKR_CLIENT_ID=$(keyring get flickypedia api_key)
export FLICKR_CLIENT_SECRET=$(keyring get flickypedia api_secret)
export FLICKR_API_KEY=$(keyring get flickypedia flickr_api_key)
export WIKIMEDIA_CLIENT_ID=$(keyring get flickypedia wikimedia_client_id)
export WIKIMEDIA_CLIENT_SECRET=$(keyring get flickypedia wikimedia_client_secret)
export SECRET_KEY=$(keyring get flickypedia secret_key)
export SCRIPT_NAME=/tools/flickypedia

gunicorn "flickypedia.uploadr:create_app()" \
  --workers 4 \
  --bind "$BIND_ADDRESS" \
  --access-logfile access.log \
  --log-file app.log \
  --pid flickypedia.pid \
  --daemon


echo "http://$BIND_ADDRESS" > bind_address.txt

print_success "App started successfully! Running at http://$BIND_ADDRESS"
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
