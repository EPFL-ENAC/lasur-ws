#!/bin/bash

set -euo pipefail

# Configuration
# vars from env file
LFS_SERVER_URL="https://$LFS_USERNAME:$LFS_PASSWORD@$LFS_SERVER_PATH"

# The directory to process
TARGET_DIR="$1"

# Ensure the target directory exists
if [ ! -d "$TARGET_DIR" ]; then
  echo "Error: Directory $TARGET_DIR does not exist."
  exit 1
fi

# Find all files in the directory and subdirectories
find "$TARGET_DIR" -type f | while read -r file; do
  # Check if the file is a Git LFS pointer
  if grep -q "version https://git-lfs.github.com/spec/v1" "$file"; then
    echo "Processing LFS pointer: $file"

    # Extract the OID from the file, stripping "oid sha256:" and any potential whitespace
    OID=$(grep "oid sha256:" "$file" | sed 's/oid sha256://' | tr -d '[:space:]')

    if [ -n "$OID" ]; then      
      # Construct the authenticated download URL
      DOWNLOAD_URL="$LFS_SERVER_URL/object/${OID}"

      echo "Downloading OID: ${OID}..."

      if wget -q -O "$file" "$DOWNLOAD_URL"; then
        echo "Successfully replaced: $file"
      else
        echo "Error: Failed to download OID $OID for file $file"
        # Optional: You might want to restore the pointer or mark the failure
      fi
    else
      echo "Warning: Could not extract OID from $file"
    fi
  fi
done

echo "Processing complete."