import boto3
import os
from io import BytesIO
from urllib.parse import unquote_plus
from PIL import Image

s3 = boto3.client("s3")

DEST_BUCKET = os.environ["DEST_BUCKET"]
RESIZE_WIDTH = int(os.environ.get("RESIZE_WIDTH", 300))
RESIZE_HEIGHT = int(os.environ.get("RESIZE_HEIGHT", 300))


def lambda_handler(event, context):
    for record in event["Records"]:
        src_bucket = record["s3"]["bucket"]["name"]

        # S3 event keys are URL-encoded (spaces become '+', etc.) — decode before use
        key = unquote_plus(record["s3"]["object"]["key"])

        if not key.lower().endswith((".png", ".jpg", ".jpeg")):
            print(f"Skipping non-image file: {key}")
            continue

        print(f"Processing '{key}' from bucket '{src_bucket}'")

        response = s3.get_object(Bucket=src_bucket, Key=key)
        image_content = response["Body"].read()

        image = Image.open(BytesIO(image_content))
        image_format = image.format  # preserve original format (JPEG/PNG)
        image.thumbnail((RESIZE_WIDTH, RESIZE_HEIGHT))

        buffer = BytesIO()
        image.save(buffer, format=image_format)
        buffer.seek(0)

        resized_key = f"resized-{key}"
        s3.put_object(
            Bucket=DEST_BUCKET,
            Key=resized_key,
            Body=buffer,
            ContentType=f"image/{image_format.lower()}",
        )

        print(f"Resized image saved to '{DEST_BUCKET}/{resized_key}'")

    return {
        "statusCode": 200,
        "body": "Image(s) resized successfully!",
    }
