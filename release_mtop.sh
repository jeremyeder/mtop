#!/bin/bash
set -e

REPO_NAME="llm-d-debug"
GITHUB_USER="jeremyeder"  # <-- CHANGE THIS
VERSION="v0.1.0"
RELEASE_NAME="kubectl-ld"
BINARY_NAME="kubectl-ld"
TMP_DIR="release-build"
PLATFORMS=("linux_amd64" "darwin_amd64")

echo "🔧 Creating temp build directory..."
rm -rf $TMP_DIR
mkdir -p $TMP_DIR

echo "📦 Creating tar.gz archives..."
for PLATFORM in "${PLATFORMS[@]}"; do
  PLATFORM_DIR="${TMP_DIR}/${RELEASE_NAME}_${PLATFORM}"
  mkdir -p "$PLATFORM_DIR"
  cp ./kubectl-ld "$PLATFORM_DIR/$BINARY_NAME"
  cp ./README.md ./LICENSE "$PLATFORM_DIR/" 2>/dev/null || true
  tar -czf "${TMP_DIR}/${RELEASE_NAME}_${PLATFORM}.tar.gz" -C "$PLATFORM_DIR" .
done

echo "🔐 Generating SHA256 checksums..."
cd $TMP_DIR
for FILE in *.tar.gz; do
  shasum -a 256 "$FILE" > "$FILE.sha256"
done
cd ..

echo "🌐 Creating GitHub repo (if needed)..."
gh repo create "$GITHUB_USER/$REPO_NAME" --public --source=. --remote=origin --push || true

echo "🏷️ Creating release $VERSION..."
gh release create "$VERSION"   "$TMP_DIR"/*.tar.gz   "$TMP_DIR"/*.sha256   --title "$VERSION"   --notes "Initial release of kubectl-ld"

echo "✅ Done. You can now submit the Krew manifest with the uploaded URIs and SHAs."
