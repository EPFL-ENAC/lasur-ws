echo "$1"
./scripts/download_from_lfs_oid.sh "$1"

# Run migrations
uvicorn --host=0.0.0.0 --timeout-keep-alive=0 api.main:app --reload