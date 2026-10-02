#!/usr/bin/env bash
# READ-ONLY. Shows whether Firebase is enabled on the project, every Hosting
# site in it, each site's custom domains, recent releases and channels, and
# any existing Workload Identity pools. Changes nothing.
# Run in Cloud Shell as a project owner:  bash scripts/inspect-hosting.sh
set -euo pipefail

PROJECT=${PROJECT:-project-b14e4945-5820-4d6e-808}
API=https://firebasehosting.googleapis.com/v1beta1
TOKEN=$(gcloud auth print-access-token)
call() { curl -fsS -H "Authorization: Bearer $TOKEN" -H "x-goog-user-project: $PROJECT" "$1"; }

echo "### Project"
gcloud projects describe "$PROJECT" --format="value(projectId,projectNumber,parent.type,parent.id)"

echo
echo "### Is Firebase enabled on this project? (404 = no)"
curl -sS -o /dev/null -w '%{http_code}\n' -H "Authorization: Bearer $TOKEN" \
  -H "x-goog-user-project: $PROJECT" "https://firebase.googleapis.com/v1beta1/projects/$PROJECT"

echo
echo "### Enabled APIs relevant to this site"
gcloud services list --enabled --project "$PROJECT" \
  --filter="config.name:(firebase.googleapis.com firebasehosting.googleapis.com iamcredentials.googleapis.com sts.googleapis.com)" \
  --format="value(config.name)"

echo
echo "### Existing Workload Identity pools (the site gets its own; listed so nothing collides)"
gcloud iam workload-identity-pools list --location=global --project "$PROJECT" \
  --format="table(name.basename(), displayName, state)"

echo
echo "### Hosting sites (fails if Hosting has never been used here; that is fine)"
if SITES_JSON=$(call "$API/projects/$PROJECT/sites"); then
  echo "$SITES_JSON"
  for SITE in $(echo "$SITES_JSON" | python3 -c 'import sys,json; [print(s["name"].split("/")[-1]) for s in json.load(sys.stdin).get("sites",[])]'); do
    echo
    echo "### Site: $SITE — custom domains"
    call "$API/projects/$PROJECT/sites/$SITE/customDomains"
    echo
    echo "### Site: $SITE — releases on live (newest first, up to 5)"
    call "$API/sites/$SITE/channels/live/releases?pageSize=5"
  done
else
  echo "(no Hosting sites readable)"
fi
