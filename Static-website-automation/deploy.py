import boto3
import json
import os
import mimetypes
from datetime import datetime

BUCKET_NAME = "my-static-website-" + datetime.now().strftime("%Y%m%d%H%M%S")
REGION      = "ap-south-1"
WEBSITE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "website")

s3 = boto3.client("s3", region_name=REGION)


def create_bucket():
    print(f"Creating bucket: {BUCKET_NAME}")
    s3.create_bucket(
        Bucket=BUCKET_NAME,
        CreateBucketConfiguration={"LocationConstraint": REGION}
    )
    print("Bucket created.")


def disable_block_public_access():
    print("Disabling block public access...")
    s3.put_public_access_block(
        Bucket=BUCKET_NAME,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls"      : False,
            "IgnorePublicAcls"     : False,
            "BlockPublicPolicy"    : False,
            "RestrictPublicBuckets": False,
        }
    )
    print("Done.")


def set_bucket_policy():
    print("Setting public read policy...")
    policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid"      : "PublicReadGetObject",
            "Effect"   : "Allow",
            "Principal": "*",
            "Action"   : "s3:GetObject",
            "Resource" : f"arn:aws:s3:::{BUCKET_NAME}/*"
        }]
    }
    s3.put_bucket_policy(Bucket=BUCKET_NAME, Policy=json.dumps(policy))
    print("Policy set.")


def enable_static_hosting():
    print("Enabling static website hosting...")
    s3.put_bucket_website(
        Bucket=BUCKET_NAME,
        WebsiteConfiguration={
            "IndexDocument": {"Suffix": "index.html"},
            "ErrorDocument": {"Key": "error.html"},
        }
    )
    print("Hosting enabled.")


def upload_files():
    print(f"Uploading files from {WEBSITE_DIR}...")
    for filename in os.listdir(WEBSITE_DIR):
        filepath = os.path.join(WEBSITE_DIR, filename)
        if not os.path.isfile(filepath):
            continue
        content_type, _ = mimetypes.guess_type(filepath)
        content_type = content_type or "application/octet-stream"
        s3.upload_file(
            Filename  = filepath,
            Bucket    = BUCKET_NAME,
            Key       = filename,
            ExtraArgs = {"ContentType": content_type}
        )
        print(f"  Uploaded: {filename} ({content_type})")
    print("All files uploaded.")


def main():
    print("=" * 55)
    print("  AWS S3 Static Website Automation Script")
    print("=" * 55)
    create_bucket()
    disable_block_public_access()
    set_bucket_policy()
    enable_static_hosting()
    upload_files()
    url = f"http://{BUCKET_NAME}.s3-website.{REGION}.amazonaws.com"
    print()
    print("=" * 55)
    print("DEPLOYMENT COMPLETE!")
    print(f"Bucket Name : {BUCKET_NAME}")
    print(f"Region      : {REGION}")
    print(f"Website URL : {url}")
    print("=" * 55)

    # Save the bucket name so update.py can reuse it
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".last_deploy"), "w") as f:
        f.write(BUCKET_NAME)


if __name__ == "__main__":
    main()
