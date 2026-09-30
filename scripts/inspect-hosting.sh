#!/usr/bin/env bash
# READ-ONLY. Lists every Hosting site in the project, each site's custom
# domains, and its most recent releases. Changes nothing.
# Run in Cloud Shell as a project owner:  bash scripts/inspect-hosting.sh
set -euo pipefail

PROJECT=stmary-stdemiana
API=https://firebasehosting.googleapis.com/v1beta1
TOKEN=$(gcloud auth print-access-token)
call() { curl -fsS -H "Authorization: Bearer $TOKEN" -H "x-goog-user-project: $PROJECT" "$1"; }

echo "### Sites"
SITES_JSON=$(call "$API/projects/$PROJECT/sites")
echo "$SITES_JSON"

for SITE in $(echo "$SITES_JSON" | python3 -c 'import sys,json; [print(s["name"].split("/")[-1]) for s in json.load(sys.stdin).get("sites",[])]'); do
  echo
  echo "### Site: $SITE — custom domains"
  call "$API/projects/$PROJECT/sites/$SITE/customDomains"
  echo
  echo "### Site: $SITE — legacy domain records"
  call "$API/sites/$SITE/domains"
  echo
  echo "### Site: $SITE — releases on live (newest first, up to 5)"
  call "$API/sites/$SITE/channels/live/releases?pageSize=5"
  echo
  echo "### Site: $SITE — channels"
  call "$API/sites/$SITE/channels"
done
