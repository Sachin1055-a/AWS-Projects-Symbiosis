#!/bin/bash
# Builds a Pillow Lambda layer compatible with the Lambda Python 3.12 runtime.
# Run this in AWS CloudShell (or an Amazon Linux EC2 instance) — NOT on your
# local Windows/Mac machine, since Pillow ships compiled C extensions that
# must match Lambda's execution environment.
#
# Usage:
#   chmod +x build_layer.sh
#   ./build_layer.sh <your-s3-bucket-name>

set -e

BUCKET_NAME="$1"

if [ -z "$BUCKET_NAME" ]; then
  echo "Usage: ./build_layer.sh <s3-bucket-name>"
  echo "  (the bucket must already exist — used to stage the layer zip for upload)"
  exit 1
fi

echo "Building Pillow layer..."
rm -rf /tmp/layer
mkdir -p /tmp/layer/python

pip3 install pillow \
  --platform manylinux2014_x86_64 \
  --target /tmp/layer/python \
  --only-binary=:all: \
  --python-version 3.12 \
  --implementation cp

cd /tmp/layer
zip -r pillow-layer.zip python/

echo "Uploading layer zip to s3://${BUCKET_NAME}/layers/pillow-layer.zip"
aws s3 cp pillow-layer.zip "s3://${BUCKET_NAME}/layers/pillow-layer.zip"

echo ""
echo "Done. Next steps:"
echo "  1. Lambda console -> Layers -> Create layer"
echo "  2. Upload from S3 -> s3://${BUCKET_NAME}/layers/pillow-layer.zip"
echo "  3. Compatible runtime: Python 3.12"
echo "  4. Copy the Layer ARN and attach it to your Lambda function"
