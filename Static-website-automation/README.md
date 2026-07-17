# AWS S3 Static Website Automation

A Python (boto3) script that fully automates hosting a static website on Amazon S3 — no manual AWS Console clicks required. Running one script creates the bucket, configures public read access, enables static website hosting, and uploads the site files.

## What it does

1. Creates a uniquely-named S3 bucket (timestamped)
2. Disables the account-level "block public access" setting on that bucket
3. Attaches a bucket policy allowing public `s3:GetObject` (read-only) access
4. Enables static website hosting (`index.html` as the index document, `error.html` as the error document)
5. Uploads every file in the `website/` folder with the correct `Content-Type`
6. Prints the live website URL

## Prerequisites

- Python 3.8+
- AWS account with an IAM user/role that has S3 permissions (`AmazonS3FullAccess` or an equivalent scoped policy)
- AWS credentials configured locally, e.g. via:
  ```bash
  aws configure
  ```

## Setup

```bash
git clone <this-repo-url>
cd project5-static-website-automation
pip install -r requirements.txt
```

## Usage

### 1. Deploy the website

```bash
python3 deploy.py
```

This creates a new bucket every time it's run (bucket names are timestamped to stay globally unique) and prints output like:

```
=======================================================
   AWS S3 Static Website Automation Script
=======================================================
Creating bucket: my-static-website-20260716133555
Bucket created.
Disabling block public access...
Public access unblocked.
Setting bucket policy for public read...
Bucket policy set.
Enabling static website hosting...
Static hosting enabled.
Uploading files from .../website...
  Uploaded: index.html (text/html)
  Uploaded: error.html (text/html)
All files uploaded.

=======================================================
DEPLOYMENT COMPLETE!
Bucket Name : my-static-website-20260716133555
Region      : ap-south-1
Website URL : http://my-static-website-20260716133555.s3-website.ap-south-1.amazonaws.com
=======================================================
```

Copy the **Website URL** into your browser to see it live.

### 2. Update the website (redeploy after edits)

Edit any file inside `website/`, then run:

```bash
python3 update.py
```

This re-uploads the changed files to the same bucket used in the last `deploy.py` run (read from a local `.last_deploy` file). No new bucket is created.

## Project structure

```
project5-static-website-automation/
├── deploy.py           # Creates bucket, sets policy, enables hosting, uploads files
├── update.py            # Re-uploads files to the existing bucket
├── website/
│   ├── index.html        # Homepage
│   └── error.html        # Custom 404 page
├── requirements.txt
├── .gitignore
└── README.md
```

## Configuration

Both scripts default to region `ap-south-1`. To use a different region, edit the `REGION` variable at the top of `deploy.py` and `update.py`.

## Notes / limitations

- Each `deploy.py` run creates a **new** bucket rather than reusing an old one — old buckets are not deleted automatically. Clean up unused buckets manually via the S3 console or CLI to avoid clutter.
- The bucket is configured for **public read access**, which is required for static website hosting to work over HTTP. Don't upload sensitive files into `website/`.
- S3 static website hosting endpoints are HTTP-only (not HTTPS). For HTTPS, front the bucket with CloudFront and an ACM certificate.

## What this project demonstrates

| Concept | How it's shown |
|---|---|
| S3 bucket creation via code | `create_bucket()` |
| Public access configuration | `disable_block_public_access()` |
| Bucket policy via code | `set_bucket_policy()` |
| Static website hosting via code | `enable_static_hosting()` |
| File upload automation | `upload_files()` |
| No manual AWS Console clicks | Everything handled in one script |
