#!/usr/bin/env bash
# One-time, idempotent Google Cloud setup for AURORA Lifeline. Run in Cloud Shell:
#   git clone https://github.com/TusharTechs/aurora-lifeline.git && cd aurora-lifeline
#   bash infra/cloudshell/01_bootstrap.sh
# Enables only the APIs pre-approved in docs/COSTS.md §1a; creates Firestore (default), storage
# buckets and BigQuery datasets in asia-south1 and two least-privilege service accounts; then
# checks Gemini models on Agent Platform's global endpoint and Earth Engine access.
# Paste the "SUMMARY" block at the end back into the chat.
set -uo pipefail
PROJECT="${PROJECT:-aurora-lifeline}"
REGION="asia-south1"
gcloud config set project "$PROJECT" >/dev/null
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')"

echo "== Enabling pre-approved APIs (docs/COSTS.md §1a)"
APIS=(
  aiplatform run cloudbuild artifactregistry storage bigquery bigquerystorage firestore
  firebase firebasehosting identitytoolkit fcm fcmregistrations firebaseappcheck
  earthengine texttospeech maps-backend apikeys secretmanager iam iamcredentials sts
  cloudresourcemanager serviceusage logging monitoring pubsub eventarc cloudscheduler
  billingbudgets
)
# The Service Usage API accepts at most 20 services per request.
for ((i = 0; i < ${#APIS[@]}; i += 15)); do
  batch=("${APIS[@]:i:15}")
  gcloud services enable "${batch[@]/%/.googleapis.com}" \
    || { echo "API enable failed; fix the error above and re-run" >&2; exit 1; }
done

echo "== Firestore (default) in $REGION"
gcloud firestore databases describe --database="(default)" >/dev/null 2>&1 \
  || gcloud firestore databases create --database="(default)" --location="$REGION" --type=firestore-native

echo "== Storage buckets (private)"
for b in "$PROJECT-data" "$PROJECT-quarantine"; do
  gcloud storage buckets describe "gs://$b" >/dev/null 2>&1 \
    || gcloud storage buckets create "gs://$b" --location="$REGION" \
         --uniform-bucket-level-access --public-access-prevention
done
echo '{"rule":[{"action":{"type":"Delete"},"condition":{"age":90}}]}' > /tmp/aurora-lifecycle.json
gcloud storage buckets update "gs://$PROJECT-quarantine" --lifecycle-file=/tmp/aurora-lifecycle.json >/dev/null

echo "== BigQuery datasets"
for d in aurora_ref aurora_runs aurora_eval; do
  bq --location="$REGION" show --dataset "$PROJECT:$d" >/dev/null 2>&1 \
    || bq --location="$REGION" mk --dataset "$PROJECT:$d"
done

echo "== Service accounts"
sa() {  # sa <name> <display name> <role>...
  local name="$1" display="$2"; shift 2
  local email="$name@$PROJECT.iam.gserviceaccount.com"
  gcloud iam service-accounts describe "$email" >/dev/null 2>&1 \
    || gcloud iam service-accounts create "$name" --display-name="$display"
  for role in "$@"; do
    gcloud projects add-iam-policy-binding "$PROJECT" --member="serviceAccount:$email" \
      --role="$role" --condition=None --quiet >/dev/null
  done
  gcloud storage buckets add-iam-policy-binding "gs://$PROJECT-data" \
    --member="serviceAccount:$email" --role=roles/storage.objectAdmin >/dev/null
}
sa aurora-api "AURORA API (Cloud Run)" roles/aiplatform.user roles/datastore.user \
  roles/bigquery.dataViewer roles/bigquery.jobUser roles/serviceusage.serviceUsageConsumer \
  roles/logging.logWriter
sa aurora-jobs "AURORA pipeline jobs" roles/aiplatform.user roles/datastore.user \
  roles/bigquery.dataEditor roles/bigquery.jobUser roles/serviceusage.serviceUsageConsumer \
  roles/earthengine.writer roles/logging.logWriter
gcloud storage buckets add-iam-policy-binding "gs://$PROJECT-quarantine" \
  --member="serviceAccount:aurora-api@$PROJECT.iam.gserviceaccount.com" \
  --role=roles/storage.objectCreator >/dev/null

echo "== Python tools (virtualenv at ~/.aurora-venv)"
python3 -m venv "$HOME/.aurora-venv"
"$HOME/.aurora-venv/bin/pip" install --quiet --upgrade pip
"$HOME/.aurora-venv/bin/pip" install --quiet "google-genai>=2.25,<3.0.0" earthengine-api

echo "== Checks"
"$HOME/.aurora-venv/bin/python" - "$PROJECT" > /tmp/aurora-checks.txt 2>&1 <<'PY'
import sys
from importlib.metadata import version

from google import genai

project = sys.argv[1]
print(f"google-genai {version('google-genai')}")
client = genai.Client(enterprise=True, project=project, location="global")
for model in ["gemini-3.7-flash", "gemini-3.8-flash", "gemini-3.5-flash-lite"]:
    try:
        r = client.models.generate_content(model=model, contents="Reply with the single word: ready")
        print(f"gemini {model:22} OK   {(r.text or '').strip()[:20]!r}")
    except Exception as e:  # noqa: BLE001 - record every failure mode
        print(f"gemini {model:22} FAIL {type(e).__name__}: {str(e)[:200]}")
for model in ["gemini-embedding-2", "gemini-embedding-2-preview"]:
    try:
        emb = client.models.embed_content(model=model, contents="flooded bridge near Kakinada")
        print(f"gemini {model:22} OK   dim {len(emb.embeddings[0].values)}")
        break
    except Exception as e:  # noqa: BLE001
        print(f"gemini {model:22} FAIL {type(e).__name__}: {str(e)[:200]}")
try:
    import ee

    ee.Initialize(project=project)
    dem = ee.ImageCollection("COPERNICUS/DEM/GLO30_2024_1").size().getInfo()
    print(f"earthengine OK   GLO30 tiles visible: {dem}")
except Exception as e:  # noqa: BLE001
    print(f"earthengine FAIL {type(e).__name__}: {str(e)[:200]}")
PY
cat /tmp/aurora-checks.txt

echo
echo "===== SUMMARY (paste this back) ====="
echo "project: $PROJECT ($PROJECT_NUMBER)"
gcloud firestore databases describe --database="(default)" --format="value(locationId,type)" | sed 's/^/firestore: /'
gcloud storage buckets list --format="value(name,location)" | sed 's/^/bucket: /'
bq ls --format=csv 2>/dev/null | tail -n +2 | sed 's/^/bigquery: /'
gcloud iam service-accounts list --format="value(email)" | grep aurora- | sed 's/^/sa: /'
grep -E '^(google-genai|gemini|earthengine)' /tmp/aurora-checks.txt
echo "======================================"
