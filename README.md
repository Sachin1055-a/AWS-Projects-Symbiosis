# AWS Projects — Symbiosis

A collection of hands-on AWS projects covering serverless automation, infrastructure provisioning, cost optimization, and full-stack cloud deployment — built to explore core AWS services through practical, working implementations rather than isolated tutorials.

---

## 📁 Projects

### 1. Static Website Hosting Automation
**Folder:** `static-website-automation/`

A Python (boto3) script that fully automates deploying a static website on Amazon S3 — creating the bucket, configuring public read access, enabling static website hosting, and uploading site files, all with zero manual console clicks.

- **Tech:** Python, boto3
- **AWS services:** S3

---

### 2. Serverless Image Resizer
**Folder:** `serverless-image-resizer/`

An event-driven pipeline where uploading an image to one S3 bucket automatically triggers a Lambda function that resizes it (via Pillow) and saves the result to a second bucket — fully serverless, no EC2 or database involved.

- **Tech:** Python, Pillow, boto3
- **AWS services:** S3, Lambda, Lambda Layers, CloudWatch Logs

---

### 3. Automated EC2 Cost Optimizer
**Folder:** `automated-cost-optimizer/`

A scheduled Lambda function that inspects tagged EC2 instances every 30 minutes and automatically stops any that are idle (low CPU) or running outside defined business hours — a lightweight cost-governance tool with no frontend or database.

- **Tech:** Python, boto3
- **AWS services:** Lambda, EventBridge (Scheduler), CloudWatch Metrics & Logs, EC2, IAM

---

### 4. Automated AWS Resource Provisioning
**Folder:** `aws-resource-provisioning/`

A single boto3 script that provisions a complete environment — S3 bucket, IAM role + instance profile, EC2 key pair, security group, and a running EC2 instance — replacing manual console setup with one repeatable, idempotent-by-timestamp run.

- **Tech:** Python, boto3
- **AWS services:** EC2, S3, IAM

---

### 5. Vetal OTT Platform ("Pyzilla")
**Folder:** `vetal-ott-platform/`

A curated dark-cinema streaming platform with a Netflix-style frontend, hosted on EC2 and backed by a Node.js/Express server. Media is served securely from S3 using time-limited pre-signed URLs, with an IAM role granting the EC2 instance scoped access — no hardcoded credentials, no public bucket.

- **Tech:** Node.js, Express, PM2, HTML/CSS/JS
- **AWS services:** EC2, S3, IAM

---

## 🛠️ Overall Tech Stack

| Category | Tools / Languages |
|---|---|
| Languages | Python, JavaScript (Node.js) |
| Backend framework | Express.js |
| AWS SDK | boto3 (Python), AWS SDK for JavaScript v3 |
| Process management | PM2 |
| Image processing | Pillow |
| Infrastructure approach | Scripted / code-first (no Terraform/CloudFormation — pure SDK calls) |

## ☁️ AWS Services Used Across All Projects

- **S3** — static hosting, image storage, media storage, pre-signed URL delivery
- **Lambda** — event-driven image resizing, scheduled cost-optimization checks
- **Lambda Layers** — packaging third-party Python dependencies (Pillow)
- **EC2** — hosting the OTT platform and resource-provisioning target
- **IAM** — roles, instance profiles, and scoped policies for least-privilege access (no hardcoded credentials in any project)
- **EventBridge (Scheduler)** — time-based Lambda triggering
- **CloudWatch** — Logs (all Lambda functions) and Metrics (CPU utilization checks)

## 📂 Repository Structure

```
AWS-Projects-Symbiosis/
├── static-website-automation/
│   ├── deploy.py
│   ├── update.py
│   ├── website/
│   │   ├── index.html
│   │   └── error.html
│   ├── requirements.txt
│   └── README.md
│
├── serverless-image-resizer/
│   ├── lambda_function.py
│   ├── build_layer.sh
│   ├── requirements.txt
│   └── README.md
│
├── automated-cost-optimizer/
│   ├── lambda_function.py
│   ├── requirements.txt
│   └── README.md
│
├── aws-resource-provisioning/
│   ├── provision.py
│   ├── requirements.txt
│   └── README.md
│
├── vetal-ott-platform/
│   ├── server.js
│   ├── ecosystem.config.js
│   ├── data/
│   │   └── movies.json
│   ├── public/
│   │   └── index.html
│   ├── package.json
│   └── README.md
│
└── README.md  
```

Each project folder is self-contained with its own dependencies and README covering detailed setup and deployment steps.

## 🎯 Learning Outcomes

- Automating AWS infrastructure end-to-end using SDKs (boto3, AWS SDK for JS) instead of manual console operations
- Designing event-driven serverless pipelines (S3 → Lambda → S3) and understanding trigger configuration, event payload structure, and URL encoding edge cases
- Building and deploying Lambda Layers for third-party dependencies, including platform-specific binary compatibility (`manylinux2014_x86_64` targeting for Pillow)
- Implementing least-privilege access patterns using IAM roles and instance profiles instead of static credentials
- Generating and using S3 pre-signed URLs for secure, time-limited access to private media
- Writing scheduled automation with EventBridge and querying CloudWatch metrics programmatically for cost governance
- Managing long-running Node.js processes on EC2 with PM2 for uptime and auto-restart
- Structuring multi-project repositories with per-project documentation, dependency isolation, and consistent conventions

## 👤 Author

**Sachin Chaudhari**
Final-year B.Tech student, Artificial Intelligence and Machine Learning
R.C. Patel Institute of Technology, Shirpur, Dhule, Maharashtra

GitHub: [@Sachin1055-a](https://github.com/Sachin1055-a)
