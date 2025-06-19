#!/usr/bin/env bash
# Check if Tailscale is running, and prompt you to start it if not.

set -o errexit
set -o nounset

source "$(dirname "$0")/functions.sh"

print_info "Checking if Tailscale is running…"

# Call the Tailscale CLI to check if Tailscale is running
#
# This usually returns one of two statuses: "Stopped" or "Running"
backend_state=$(
  /Applications/Tailscale.app/Contents/MacOS/Tailscale status --json \
    | jq -r .BackendState
)

if [[ "$backend_state" = "Running" ]]
then
  print_info "Tailscale is running!"
  exit 0
elif [[ "$backend_state" = "Stopped" ]]
then
  print_error "You need to start Tailscale!"
  exit 1
else
  print_warning "Unexpected BackendState from Tailscale CLI: $backend_state"
  exit 2
fi
