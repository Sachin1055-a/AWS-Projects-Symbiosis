import boto3
import os
import mimetypes

REGION      = "ap-south-1"
WEBSITE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "website")
LAST_DEPLOY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".last_deploy")


def get_bucket_name():
    # Try to read the bucket name saved by deploy.py, else ask for it
    if os.path.exists(LAST_DEPLOY_FILE):
        with open(LAST_DEPLOY_FILE) as f:
            return f.read().strip()
    return input("Enter your bucket name (from deploy.py output): ").strip()


def main():
    bucket_name = get_bucket_name()
    s3 = boto3.client("s3", region_name=REGION)

    print(f"Updating website files in bucket: {bucket_name}")
    for filename in os.listdir(WEBSITE_DIR):
        filepath = os.path.join(WEBSITE_DIR, filename)
        if not os.path.isfile(filepath):
            continue
        content_type, _ = mimetypes.guess_type(filepath)
        content_type = content_type or "application/octet-stream"
        s3.upload_file(
            filepath, bucket_name, filename,
            ExtraArgs={"ContentType": content_type}
        )
        print(f"  Updated: {filename}")

    print(f"Done! Visit: http://{bucket_name}.s3-website.{REGION}.amazonaws.com")


if __name__ == "__main__":
    main()
