#!/usr/bin/env bash
# ONE-OFF setup, run once by a project owner in Cloud Shell AFTER reviewing
# the output of inspect-hosting.sh. Creates:
#   1. a NEW Hosting site (does not touch the default site or link.* domain)
#   2. a deploy service account with Hosting Admin only
#   3. a Workload Identity pool + GitHub OIDC provider whose condition only
#      accepts tokens from DanielEHanna/stmaryandstdemiana-web
#   4. permission for that repo (and only that repo) to impersonate the SA
# No service-account key is created at any point.
#
# Safe to re-run: each step skips when the resource already exists.
set -euo pipefail

PROJECT=stmary-stdemiana
PROJECT_NUMBER=907000223329
SITE=stmaryandstdemiana-web
REPO=DanielEHanna/stmaryandstdemiana-web
POOL=github
PROVIDER=stmaryandstdemiana-web
SA_NAME=hosting-deployer
SA=$SA_NAME@$PROJECT.iam.gserviceaccount.com

gcloud config set project "$PROJECT"

echo "== 1. Hosting site $SITE"
TOKEN=$(gcloud auth print-access-token)
STATUS=$(curl -sS -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $TOKEN" \
  "https://firebasehosting.googleapis.com/v1beta1/projects/$PROJECT/sites/$SITE")
if [ "$STATUS" = "200" ]; then
  echo "   exists, skipping"
else
  # Fails loudly if the ID is taken globally by another project.
  curl -fsS -X POST -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
    -H "x-goog-user-project: $PROJECT" \
    "https://firebasehosting.googleapis.com/v1beta1/projects/$PROJECT/sites?siteId=$SITE" -d '{}'
  echo
fi

echo "== 2. APIs needed for keyless auth"
gcloud services enable iam.googleapis.com iamcredentials.googleapis.com sts.googleapis.com

echo "== 3. Service account $SA"
if ! gcloud iam service-accounts describe "$SA" >/dev/null 2>&1; then
  gcloud iam service-accounts create "$SA_NAME" \
    --display-name="GitHub Actions: deploy stmaryandstdemiana-web to Firebase Hosting"
fi
gcloud projects add-iam-policy-binding "$PROJECT" --condition=None \
  --member="serviceAccount:$SA" --role=roles/firebasehosting.admin >/dev/null
# firebase-tools checks the Hosting API is enabled before deploying.
gcloud projects add-iam-policy-binding "$PROJECT" --condition=None \
  --member="serviceAccount:$SA" --role=roles/serviceusage.serviceUsageConsumer >/dev/null

echo "== 4. Workload Identity pool + provider"
if ! gcloud iam workload-identity-pools describe "$POOL" --location=global >/dev/null 2>&1; then
  gcloud iam workload-identity-pools create "$POOL" --location=global \
    --display-name="GitHub Actions"
fi
if ! gcloud iam workload-identity-pools providers describe "$PROVIDER" \
     --location=global --workload-identity-pool="$POOL" >/dev/null 2>&1; then
  gcloud iam workload-identity-pools providers create-oidc "$PROVIDER" \
    --location=global --workload-identity-pool="$POOL" \
    --display-name="stmaryandstdemiana-web repo" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
    --attribute-condition="assertion.repository=='$REPO'"
fi

echo "== 5. Let only this repo impersonate the SA"
gcloud iam service-accounts add-iam-policy-binding "$SA" \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL/attribute.repository/$REPO" >/dev/null

echo
echo "Done. Values for the workflow (not secrets):"
echo "  WIF_PROVIDER=projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL/providers/$PROVIDER"
echo "  SERVICE_ACCOUNT=$SA"
