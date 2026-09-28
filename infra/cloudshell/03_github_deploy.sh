#!/usr/bin/env bash
# Lets GitHub Actions deploy Hosting and the Cloud Run API from TusharTechs/aurora-lifeline's
# main branch, with Workload Identity Federation (short-lived tokens; no service-account keys).
# Run once in Cloud Shell, after 02_deploy_web.sh has created ~/aurora-lifeline/.env:
#   cd ~/aurora-lifeline && git pull && bash infra/cloudshell/03_github_deploy.sh
# Revoke everything it grants with:
#   gcloud iam workload-identity-pools delete github --location=global
set -euo pipefail
PROJECT="${PROJECT:-aurora-lifeline}"
REGION="asia-south1"
REPO="TusharTechs/aurora-lifeline"
POOL="github"
PROVIDER="aurora-lifeline"
DEPLOY_SA="aurora-deploy@$PROJECT.iam.gserviceaccount.com"
API_SA="aurora-api@$PROJECT.iam.gserviceaccount.com"
cd "$(git rev-parse --show-toplevel)"
gcloud config set project "$PROJECT" >/dev/null
NUM="$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')"

echo "== Workload Identity pool and GitHub provider (main branch of $REPO only)"
gcloud iam workload-identity-pools describe "$POOL" --location=global >/dev/null 2>&1 \
  || gcloud iam workload-identity-pools create "$POOL" --location=global --display-name="GitHub Actions"
gcloud iam workload-identity-pools providers describe "$PROVIDER" --location=global \
  --workload-identity-pool="$POOL" >/dev/null 2>&1 \
  || gcloud iam workload-identity-pools providers create-oidc "$PROVIDER" --location=global \
       --workload-identity-pool="$POOL" --display-name="aurora-lifeline main" \
       --issuer-uri="https://token.actions.githubusercontent.com" \
       --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
       --attribute-condition="assertion.repository=='$REPO' && assertion.ref=='refs/heads/main'"

echo "== Deploy service account"
gcloud iam service-accounts describe "$DEPLOY_SA" >/dev/null 2>&1 \
  || gcloud iam service-accounts create aurora-deploy --display-name="AURORA deploy (GitHub Actions)"
for role in roles/run.admin roles/firebasehosting.admin roles/firebase.viewer \
            roles/serviceusage.serviceUsageConsumer; do
  gcloud projects add-iam-policy-binding "$PROJECT" --member="serviceAccount:$DEPLOY_SA" \
    --role="$role" --condition=None --quiet >/dev/null
done
gcloud iam service-accounts add-iam-policy-binding "$API_SA" --member="serviceAccount:$DEPLOY_SA" \
  --role=roles/iam.serviceAccountUser --quiet >/dev/null
gcloud iam service-accounts add-iam-policy-binding "$DEPLOY_SA" --role=roles/iam.workloadIdentityUser \
  --member="principalSet://iam.googleapis.com/projects/$NUM/locations/global/workloadIdentityPools/$POOL/attribute.repository/$REPO" \
  --quiet >/dev/null

echo "== Artifact Registry repository for the API image"
gcloud artifacts repositories describe aurora --location="$REGION" >/dev/null 2>&1 \
  || gcloud artifacts repositories create aurora --location="$REGION" --repository-format=docker \
       --description="AURORA Lifeline images"
gcloud artifacts repositories add-iam-policy-binding aurora --location="$REGION" \
  --member="serviceAccount:$DEPLOY_SA" --role=roles/artifactregistry.writer --quiet >/dev/null
# Keep only recent images (storage is billed).
cat > /tmp/aurora-ar-cleanup.json <<'JSON'
[{"name": "keep-recent", "action": {"type": "Keep"}, "mostRecentVersions": {"keepCount": 5}},
 {"name": "delete-old", "action": {"type": "Delete"}, "condition": {"tagState": "any", "olderThan": "1d"}}]
JSON
gcloud artifacts repositories set-cleanup-policies aurora --location="$REGION" \
  --policy=/tmp/aurora-ar-cleanup.json --no-dry-run --quiet >/dev/null

echo "== Web build settings in Secret Manager (secret: web-env)"
# Firebase web config comes from the Firebase Management API; the Maps key and Map ID from .env.
TOKEN="$(gcloud auth print-access-token)"
APP="$(curl -fsS -H "Authorization: Bearer $TOKEN" -H "x-goog-user-project: $PROJECT" \
  "https://firebase.googleapis.com/v1beta1/projects/$PROJECT/webApps" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['apps'][0]['appId'])")"
curl -fsS -H "Authorization: Bearer $TOKEN" -H "x-goog-user-project: $PROJECT" \
  "https://firebase.googleapis.com/v1beta1/projects/$PROJECT/webApps/$APP/config" > /tmp/aurora-fb.json
test -f .env || { echo "no .env here: run 02_deploy_web.sh first" >&2; exit 1; }
getenv() { grep -E "^$1=" .env | tail -1 | cut -d= -f2- || true; }
VAPID="$(getenv NEXT_PUBLIC_FCM_VAPID_KEY)"
[ -n "$VAPID" ] || read -rp "NEXT_PUBLIC_FCM_VAPID_KEY (Firebase > Project settings > Cloud Messaging > Web Push key pair): " VAPID
python3 - "$(getenv NEXT_PUBLIC_MAPS_API_KEY)" "$(getenv NEXT_PUBLIC_MAPS_MAP_ID)" "$VAPID" > /tmp/aurora-web.env <<'PY'
import json, sys
maps_key, map_id, vapid = sys.argv[1:4]
c = json.load(open("/tmp/aurora-fb.json"))
assert maps_key and map_id, "NEXT_PUBLIC_MAPS_API_KEY and NEXT_PUBLIC_MAPS_MAP_ID must be in .env"
rows = {
    "NEXT_PUBLIC_MAPS_API_KEY": maps_key,
    "NEXT_PUBLIC_MAPS_MAP_ID": map_id,
    "NEXT_PUBLIC_FIREBASE_API_KEY": c["apiKey"],
    "NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN": c["authDomain"],
    "NEXT_PUBLIC_FIREBASE_PROJECT_ID": c["projectId"],
    "NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET": c["storageBucket"],
    "NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID": c["messagingSenderId"],
    "NEXT_PUBLIC_FIREBASE_APP_ID": c["appId"],
    "NEXT_PUBLIC_FCM_VAPID_KEY": vapid,
}
print("\n".join(f"{k}={v}" for k, v in rows.items()))
PY
rm -f /tmp/aurora-fb.json
gcloud secrets describe web-env >/dev/null 2>&1 \
  || gcloud secrets create web-env --replication-policy=user-managed --locations="$REGION" >/dev/null
gcloud secrets versions add web-env --data-file=/tmp/aurora-web.env >/dev/null
rm -f /tmp/aurora-web.env
gcloud secrets add-iam-policy-binding web-env --member="serviceAccount:$DEPLOY_SA" \
  --role=roles/secretmanager.secretAccessor --quiet >/dev/null

echo
echo "===== SUMMARY (paste this back) ====="
echo "provider: projects/$NUM/locations/global/workloadIdentityPools/$POOL/providers/$PROVIDER"
gcloud iam workload-identity-pools providers describe "$PROVIDER" --location=global \
  --workload-identity-pool="$POOL" --format="value(state,attributeCondition)" | sed 's/^/condition: /'
echo "deploy sa: $DEPLOY_SA"
gcloud artifacts repositories describe aurora --location="$REGION" --format="value(name)" | sed 's/^/registry: /'
gcloud secrets versions list web-env --format="value(name,state)" --limit=1 | sed 's/^/web-env version: /'
echo "web-env keys: $(gcloud secrets versions access latest --secret=web-env | cut -d= -f1 | paste -sd, -)"
echo "======================================"
