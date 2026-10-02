#!/usr/bin/env bash
# ONE-OFF setup, run once by a project owner in Cloud Shell AFTER reviewing
# the output of inspect-hosting.sh. Creates, in the Sunday School portal's
# project but deliberately separate from everything the portal uses:
#   1. Firebase on the project, if it is not already enabled
#   2. a NEW Hosting site for the church (does not touch any existing site)
#   3. a deploy service account with Hosting roles only: it cannot reach
#      Cloud Run, Cloud SQL, Artifact Registry or anything else the portal has
#   4. a Workload Identity pool of its own (not the portal's) + GitHub OIDC
#      provider that only accepts tokens from DanielEHanna/stmaryandstdemiana-web
#   5. permission for that repo (and only that repo) to impersonate the SA
# No service-account key is created at any point.
#
# Safe to re-run: each step skips when the resource already exists.
set -euo pipefail

PROJECT=${PROJECT:-project-b14e4945-5820-4d6e-808}
SITE=stmaryandstdemiana-church
REPO=DanielEHanna/stmaryandstdemiana-web
POOL=church-website-github
PROVIDER=stmaryandstdemiana-web
SA_NAME=church-website-deployer
SA=$SA_NAME@$PROJECT.iam.gserviceaccount.com

PROJECT_NUMBER=$(gcloud projects describe "$PROJECT" --format="value(projectNumber)")
echo "Project $PROJECT (number $PROJECT_NUMBER)"

echo "== 1. APIs"
gcloud services enable --project "$PROJECT" \
  firebase.googleapis.com firebasehosting.googleapis.com \
  iam.googleapis.com iamcredentials.googleapis.com sts.googleapis.com

TOKEN=$(gcloud auth print-access-token)
AUTH=(-H "Authorization: Bearer $TOKEN" -H "x-goog-user-project: $PROJECT")

echo "== 2. Firebase on the project"
STATUS=$(curl -sS -o /dev/null -w '%{http_code}' "${AUTH[@]}" \
  "https://firebase.googleapis.com/v1beta1/projects/$PROJECT")
if [ "$STATUS" = "200" ]; then
  echo "   already enabled, skipping"
else
  curl -fsS -X POST "${AUTH[@]}" -H "Content-Type: application/json" \
    "https://firebase.googleapis.com/v1beta1/projects/$PROJECT:addFirebase" -d '{}'
  echo
  echo "   addFirebase started; waiting 30s for it to finish"
  sleep 30
fi

echo "== 3. Hosting site $SITE"
STATUS=$(curl -sS -o /dev/null -w '%{http_code}' "${AUTH[@]}" \
  "https://firebasehosting.googleapis.com/v1beta1/projects/$PROJECT/sites/$SITE")
if [ "$STATUS" = "200" ]; then
  echo "   exists, skipping"
else
  # Fails loudly if the ID is taken globally by another project.
  curl -fsS -X POST "${AUTH[@]}" -H "Content-Type: application/json" \
    "https://firebasehosting.googleapis.com/v1beta1/projects/$PROJECT/sites?siteId=$SITE" -d '{}'
  echo
fi

echo "== 4. Service account $SA"
if ! gcloud iam service-accounts describe "$SA" --project "$PROJECT" >/dev/null 2>&1; then
  gcloud iam service-accounts create "$SA_NAME" --project "$PROJECT" \
    --display-name="GitHub Actions: deploy the church website to Firebase Hosting"
fi
gcloud projects add-iam-policy-binding "$PROJECT" --condition=None \
  --member="serviceAccount:$SA" --role=roles/firebasehosting.admin >/dev/null
# firebase-tools checks the Hosting API is enabled before deploying.
gcloud projects add-iam-policy-binding "$PROJECT" --condition=None \
  --member="serviceAccount:$SA" --role=roles/serviceusage.serviceUsageConsumer >/dev/null

echo "== 5. Workload Identity pool + provider (separate from the portal's)"
if ! gcloud iam workload-identity-pools describe "$POOL" --project "$PROJECT" \
     --location=global >/dev/null 2>&1; then
  gcloud iam workload-identity-pools create "$POOL" --project "$PROJECT" \
    --location=global --display-name="Church website (GitHub)"
fi
if ! gcloud iam workload-identity-pools providers describe "$PROVIDER" --project "$PROJECT" \
     --location=global --workload-identity-pool="$POOL" >/dev/null 2>&1; then
  gcloud iam workload-identity-pools providers create-oidc "$PROVIDER" --project "$PROJECT" \
    --location=global --workload-identity-pool="$POOL" \
    --display-name="stmaryandstdemiana-web repo" \
    --issuer-uri="https://token.actions.githubusercontent.com" \
    --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
    --attribute-condition="assertion.repository=='$REPO'"
fi

echo "== 6. Let only this repo impersonate the SA"
gcloud iam service-accounts add-iam-policy-binding "$SA" --project "$PROJECT" \
  --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL/attribute.repository/$REPO" >/dev/null

echo
echo "Done. Values for the workflow (not secrets):"
echo "  WIF_PROVIDER=projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/$POOL/providers/$PROVIDER"
echo "  SERVICE_ACCOUNT=$SA"
