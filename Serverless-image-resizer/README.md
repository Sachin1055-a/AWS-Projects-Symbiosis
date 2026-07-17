# Serverless Image Resizer (S3 → Lambda → S3)

A fully serverless pipeline that automatically resizes any image uploaded to an S3 bucket and saves the resized version to a second bucket. No EC2 instances, no database, no servers to manage.

## Architecture

```
Upload image                Lambda function                Resized image
     │                      (Pillow layer)                       │
     ▼                            ▼                               ▼
┌─────────────────┐   trigger   ┌──────────────────┐   writes   ┌──────────────────┐
│ image-resizer-   │ ──────────▶│ image-resizer      │ ─────────▶│ image-resizer-    │
│ original (S3)    │             │ (Lambda function)  │           │ resized (S3)       │
└─────────────────┘             └──────────────────┘           └──────────────────┘
```

Two separate S3 buckets are used (source and destination) to avoid the Lambda function re-triggering itself in an infinite loop when it writes the resized image back.

## How it works

1. An image (`.jpg`, `.jpeg`, `.png`) is uploaded to the **source** bucket (`image-resizer-original`)
2. This triggers the `image-resizer` Lambda function via an S3 event notification
3. The function downloads the image, resizes it (max 300×300, aspect ratio preserved via `Image.thumbnail()`), and uploads it to the **destination** bucket (`image-resizer-resized`) as `resized-<original-filename>`
4. Non-image files are skipped and logged

## Prerequisites

- An AWS account with permissions to create S3 buckets, IAM roles, and Lambda functions
- AWS CLI configured (or access to AWS CloudShell, which comes pre-authenticated)

## Deployment steps

### 1. Create two S3 buckets

```bash
aws s3 mb s3://image-resizer-original --region ap-south-1
aws s3 mb s3://image-resizer-resized --region ap-south-1
```

(Bucket names must be globally unique — adjust names if taken.)

### 2. Create the IAM role for Lambda

Create a role named `ImageResizerLambdaRole` with:
- Trusted entity: Lambda
- Policies: `AmazonS3FullAccess`, `CloudWatchLogsFullAccess`

### 3. Build the Pillow Lambda layer

Pillow isn't included in the default Lambda runtime and has compiled C extensions, so it must be built for Lambda's Amazon Linux environment — **not** on Windows/Mac. Use **AWS CloudShell** (browser-based, no server to manage):

```bash
chmod +x build_layer.sh
./build_layer.sh image-resizer-original
```

This builds `pillow-layer.zip` targeting `manylinux2014_x86_64` / Python 3.12 (matches the Lambda runtime exactly) and uploads it to `s3://image-resizer-original/layers/pillow-layer.zip`.

Then in the Lambda console:
1. **Layers** → **Create layer**
2. Upload from S3 → `s3://image-resizer-original/layers/pillow-layer.zip`
3. Compatible runtime: Python 3.12
4. Create, and copy the **Layer ARN**

### 4. Create the Lambda function

1. Lambda → **Create function**
2. Name: `image-resizer`, Runtime: Python 3.12
3. Execution role: `ImageResizerLambdaRole`
4. Timeout: 30 sec, Memory: 512 MB
5. Attach the Pillow layer (paste the Layer ARN from step 3)
6. Environment variables:

   | Key | Value |
   |---|---|
   | DEST_BUCKET | image-resizer-resized |

7. Paste the contents of `lambda_function.py` into the code editor → **Deploy**

### 5. Add the S3 trigger

1. Lambda function → **Add trigger** → S3
2. Bucket: `image-resizer-original`
3. Event type: All object create events
4. Add (repeat with a different suffix filter, e.g. `.png`, if you want multiple extensions covered — S3 allows one trigger per suffix pattern)

### 6. Test

Upload any `.jpg`/`.png` file to `image-resizer-original`, then check `image-resizer-resized` for a `resized-<filename>` object scaled to fit within 300×300.

## Configuration

| Environment variable | Default | Description |
|---|---|---|
| `DEST_BUCKET` | *(required)* | Destination bucket for resized images |
| `RESIZE_WIDTH` | 300 | Max width in pixels |
| `RESIZE_HEIGHT` | 300 | Max height in pixels |

## Project structure

```
project9-serverless-image-resizer/
├── lambda_function.py   # Lambda handler — downloads, resizes, re-uploads
├── build_layer.sh        # Builds the Pillow layer on Amazon Linux (CloudShell/EC2)
├── requirements.txt
├── .gitignore
└── README.md
```

## Known issues & fixes

- **`cannot import name '_imaging' from 'PIL'`** — Pillow was built for the wrong platform/architecture. Fixed by using `--platform manylinux2014_x86_64 --only-binary=:all:` when installing (already handled in `build_layer.sh`).
- **`NoSuchKey` error on upload** — S3 event notifications URL-encode the object key (spaces become `+`). Fixed by decoding with `urllib.parse.unquote_plus()` before calling `get_object` (already handled in `lambda_function.py`).

## What this project demonstrates

| Concept | How it's shown |
|---|---|
| Event-driven serverless architecture | S3 event → Lambda trigger |
| Lambda layers for third-party dependencies | Pillow packaged separately from function code |
| Cross-platform build considerations | `manylinux2014_x86_64` targeting for compiled libraries |
| Handling S3 event key encoding | `unquote_plus()` on the object key |
| Image processing in a stateless function | Pillow `thumbnail()` resize, format preserved |
