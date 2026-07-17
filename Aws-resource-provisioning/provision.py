import boto3
import json
import time
import os
from datetime import datetime

REGION = "ap-south-1"
TIMESTAMP = datetime.now().strftime("%Y%m%d%H%M%S")

BUCKET_NAME = f"auto-provisioned-bucket-{TIMESTAMP}"
ROLE_NAME = f"AutoProvisionedEC2Role-{TIMESTAMP}"
INSTANCE_PROFILE_NAME = f"AutoProvisionedProfile-{TIMESTAMP}"
KEY_NAME = f"auto-key-{TIMESTAMP}"

ec2 = boto3.client("ec2", region_name=REGION)
s3 = boto3.client("s3", region_name=REGION)
iam = boto3.client("iam", region_name=REGION)


def create_s3_bucket():
    print(f"Creating S3 bucket: {BUCKET_NAME}")
    s3.create_bucket(
        Bucket=BUCKET_NAME,
        CreateBucketConfiguration={"LocationConstraint": REGION}
    )
    print("S3 bucket created.")
    return BUCKET_NAME


def create_iam_role():
    print(f"Creating IAM role: {ROLE_NAME}")
    trust_policy = {
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole"
        }]
    }
    iam.create_role(
        RoleName=ROLE_NAME,
        AssumeRolePolicyDocument=json.dumps(trust_policy)
    )
    iam.attach_role_policy(
        RoleName=ROLE_NAME,
        PolicyArn="arn:aws:iam::aws:policy/AmazonS3FullAccess"
    )
    print("IAM role created and policy attached.")

    print(f"Creating instance profile: {INSTANCE_PROFILE_NAME}")
    iam.create_instance_profile(InstanceProfileName=INSTANCE_PROFILE_NAME)
    iam.add_role_to_instance_profile(
        InstanceProfileName=INSTANCE_PROFILE_NAME,
        RoleName=ROLE_NAME
    )
    print("Instance profile ready. Waiting for IAM propagation...")
    time.sleep(10)


def create_key_pair():
    print(f"Creating key pair: {KEY_NAME}")
    key = ec2.create_key_pair(KeyName=KEY_NAME)
    with open(f"{KEY_NAME}.pem", "w") as f:
        f.write(key["KeyMaterial"])
    os.chmod(f"{KEY_NAME}.pem", 0o400)
    print(f"Key pair saved: {KEY_NAME}.pem")


def create_security_group():
    print("Creating security group...")
    vpc_id = ec2.describe_vpcs()["Vpcs"][0]["VpcId"]
    sg = ec2.create_security_group(
        GroupName=f"auto-sg-{TIMESTAMP}",
        Description="Auto-provisioned SG",
        VpcId=vpc_id
    )
    sg_id = sg["GroupId"]
    ec2.authorize_security_group_ingress(
        GroupId=sg_id,
        IpPermissions=[
            {"IpProtocol": "tcp", "FromPort": 22, "ToPort": 22,
             "IpRanges": [{"CidrIp": "0.0.0.0/0"}]},
            {"IpProtocol": "tcp", "FromPort": 80, "ToPort": 80,
             "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}
        ]
    )
    print(f"Security group created: {sg_id}")
    return sg_id


def launch_ec2_instance(sg_id):
    print("Launching EC2 instance...")
    images = ec2.describe_images(
        Owners=["amazon"],
        Filters=[
            {"Name": "name", "Values": ["al2023-ami-*-x86_64"]},
            {"Name": "state", "Values": ["available"]}
        ]
    )["Images"]
    ami_sorted = sorted(images, key=lambda x: x["CreationDate"], reverse=True)
    ami_id = ami_sorted[0]["ImageId"]

    instance = ec2.run_instances(
        ImageId=ami_id,
        InstanceType="t2.micro",
        KeyName=KEY_NAME,
        MinCount=1,
        MaxCount=1,
        SecurityGroupIds=[sg_id],
        IamInstanceProfile={"Name": INSTANCE_PROFILE_NAME},
        TagSpecifications=[{
            "ResourceType": "instance",
            "Tags": [{"Key": "Name", "Value": f"auto-provisioned-{TIMESTAMP}"}]
        }]
    )
    instance_id = instance["Instances"][0]["InstanceId"]
    print(f"Instance launched: {instance_id}. Waiting for it to enter 'running' state...")

    waiter = ec2.get_waiter("instance_running")
    waiter.wait(InstanceIds=[instance_id])

    desc = ec2.describe_instances(InstanceIds=[instance_id])
    public_ip = desc["Reservations"][0]["Instances"][0].get("PublicIpAddress", "N/A")
    print(f"Instance running. Public IP: {public_ip}")
    return instance_id, public_ip


def main():
    print("=" * 55)
    print("  AWS Resource Auto-Provisioning Script")
    print("=" * 55)

    create_s3_bucket()
    create_iam_role()
    create_key_pair()
    sg_id = create_security_group()
    instance_id, public_ip = launch_ec2_instance(sg_id)

    print()
    print("=" * 55)
    print("PROVISIONING COMPLETE!")
    print(f"S3 Bucket        : {BUCKET_NAME}")
    print(f"IAM Role         : {ROLE_NAME}")
    print(f"Key Pair File    : {KEY_NAME}.pem")
    print(f"Security Group   : {sg_id}")
    print(f"EC2 Instance ID  : {instance_id}")
    print(f"EC2 Public IP    : {public_ip}")
    print("=" * 55)
    print(f"SSH: ssh -i {KEY_NAME}.pem ec2-user@{public_ip}")


if __name__ == "__main__":
    main()
