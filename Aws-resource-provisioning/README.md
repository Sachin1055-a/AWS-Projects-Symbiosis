# AWS Resource Auto-Provisioning

A single Python (boto3) script that provisions a complete, ready-to-use AWS environment — S3 bucket, IAM role + instance profile, EC2 key pair, security group, and a running EC2 instance — with one command instead of manual console clicks.

## What it provisions

Running the script creates, in order:

1. **S3 bucket** — uniquely named with a timestamp
2. **IAM role** (`AutoProvisionedEC2Role-<timestamp>`) — trusted by the EC2 service, with `AmazonS3FullAccess` attached
3. **Instance profile** — wraps the IAM role so it can actually be attached to an EC2 instance
4. **EC2 key pair** — private key saved locally as a `.pem` file for SSH access
5. **Security group** — allows inbound SSH (port 22) and HTTP (port 80)
6. **EC2 instance** (`t2.micro`, latest Amazon Linux 2023 AMI) — launched with the IAM instance profile and security group attached, waited on until it reaches `running` state

At the end, it prints every resource name/ID created and the exact SSH command to connect.

## How this was implemented

This script consolidates a repeatable AWS setup pattern used across other projects in this repo (IAM role creation, EC2 launch, security groups) into a single automated, idempotent-by-timestamp workflow:

- **Timestamped naming** (`TIMESTAMP = datetime.now().strftime("%Y%m%d%H%M%S")`) is used for every resource name — the bucket, IAM role, instance profile, key pair, and security group all get the same timestamp suffix. This means the script can be re-run repeatedly without name collisions, and every run's resources can be traced back to a single provisioning event.
- **IAM propagation delay handled explicitly.** A freshly created IAM role/instance profile isn't always immediately usable by `run_instances()` — AWS's IAM changes can take a few seconds to propagate globally. The script adds a `time.sleep(10)` after creating the instance profile specifically to avoid a race condition where EC2 launch fails because the instance profile "doesn't exist yet" from EC2's point of view.
- **Latest AMI resolved dynamically**, not hardcoded. Instead of pinning a specific AMI ID (which goes stale as AWS releases new Amazon Linux versions), the script queries `describe_images()` for all `al2023-ami-*-x86_64` images owned by Amazon, sorts by `CreationDate`, and picks the newest. This keeps the script working correctly even months later without edits.
- **Waiter used instead of polling manually.** Rather than writing a custom loop to check instance state, boto3's built-in `get_waiter("instance_running")` is used — it blocks until the instance reaches `running`, so the script can reliably print a working public IP at the end instead of `None` or a stale pending state.
- **Order of operations matters.** S3 bucket and IAM role/profile are created *before* the EC2 instance, since the instance launch references the instance profile by name — provisioning must happen in dependency order, not just any order.

## Prerequisites

- Python 3.8+
- AWS account with an IAM user/role that has permissions to create S3 buckets, IAM roles/instance profiles, EC2 key pairs, security groups, and EC2 instances (`AmazonEC2FullAccess`, `AmazonS3FullAccess`, `IAMFullAccess`, or a scoped custom policy covering these actions)
- AWS credentials configured locally:
  ```bash
  aws configure
  ```

## Setup

```bash
git clone <this-repo-url>
cd project4-aws-resource-provisioning
pip install -r requirements.txt
```

## Usage

```bash
python3 provision.py
```

Example output:

```
=======================================================
  AWS Resource Auto-Provisioning Script
=======================================================
Creating S3 bucket: auto-provisioned-bucket-20260717101530
S3 bucket created.
Creating IAM role: AutoProvisionedEC2Role-20260717101530
IAM role created and policy attached.
Creating instance profile: AutoProvisionedProfile-20260717101530
Instance profile ready. Waiting for IAM propagation...
Creating key pair: auto-key-20260717101530
Key pair saved: auto-key-20260717101530.pem
Creating security group...
Security group created: sg-0abc123def456789
Launching EC2 instance...
Instance launched: i-0123456789abcdef0. Waiting for it to enter 'running' state...
Instance running. Public IP: 13.234.56.78

=======================================================
PROVISIONING COMPLETE!
S3 Bucket        : auto-provisioned-bucket-20260717101530
IAM Role         : AutoProvisionedEC2Role-20260717101530
Key Pair File    : auto-key-20260717101530.pem
Security Group   : sg-0abc123def456789
EC2 Instance ID  : i-0123456789abcdef0
EC2 Public IP    : 13.234.56.78
=======================================================
SSH: ssh -i auto-key-20260717101530.pem ec2-user@13.234.56.78
```

Copy the printed SSH command to connect to the new instance.

## Project structure

```
project4-aws-resource-provisioning/
├── provision.py         # Creates S3 bucket, IAM role/profile, key pair, security group, EC2 instance
├── requirements.txt
├── .gitignore            # Excludes generated .pem key files from being committed
└── README.md
```

## Configuration

Edit the top of `provision.py` to change:
- `REGION` — defaults to `ap-south-1`
- Instance type — defaults to `t2.micro` inside `launch_ec2_instance()`
- Security group ports — defaults to 22 (SSH) and 80 (HTTP) inside `create_security_group()`

## Important notes

- **The `.pem` key file is never committed** — it's excluded via `.gitignore`. Each run generates a new one locally; keep it safe, since it's the only way to SSH into that specific instance.
- **This script does not tear down resources.** Every run creates new resources rather than reusing or replacing old ones. Remember to terminate unused EC2 instances, delete unused S3 buckets, and clean up IAM roles/instance profiles/security groups via the console or CLI to avoid ongoing cost and IAM clutter.
- Security group currently opens SSH (22) to `0.0.0.0/0` for convenience — for anything beyond testing, restrict the source IP range to your own IP.

## What this project demonstrates

| Concept | How it's shown |
|---|---|
| Infrastructure-as-code without a framework | Pure boto3, no Terraform/CloudFormation |
| IAM role + instance profile creation via code | `create_iam_role()` |
| Handling IAM propagation delay | `time.sleep(10)` after instance profile creation |
| Dynamic AMI resolution | `describe_images()` sorted by `CreationDate` |
| Waiting for async AWS operations | `ec2.get_waiter("instance_running")` |
| End-to-end resource orchestration | S3 → IAM → key pair → security group → EC2, in dependency order |
