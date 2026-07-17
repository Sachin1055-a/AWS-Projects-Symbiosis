# Automated EC2 Cost Optimizer

A scheduled Lambda function that automatically stops EC2 instances that are either idle (low CPU usage) or running outside defined business hours — reducing unnecessary compute cost with no manual intervention.

## Architecture

```
EventBridge (every 30 min)
        │
        ▼
ec2-cost-optimizer (Lambda)
        │
        ├── describe_instances(tag:AutoStop=true, state=running)
        ├── check business hours (UTC)
        ├── check average CPU via CloudWatch (last N minutes)
        └── stop_instances() for any that match either condition
```

No frontend, no database — just Lambda + CloudWatch metrics + an EventBridge schedule.

## How it works

1. An EventBridge scheduled rule invokes the Lambda function every 30 minutes
2. The function lists all **running** EC2 instances tagged `AutoStop: true` — untagged instances are never touched
3. For each matching instance:
   - If the current UTC hour is outside the configured business-hour window → stop it
   - Otherwise, check its average CPU utilization (via CloudWatch) over the last `IDLE_MINUTES_CHECK` minutes — if below `IDLE_CPU_THRESHOLD`, stop it
4. Logs a summary of what was stopped and what was kept running

## Safety design

- **Opt-in only via tagging.** The function's `describe_instances` filter requires `tag:AutoStop = true`. Any instance without this exact tag/value is invisible to the function and will never be stopped, no matter how idle it is.
- **No datapoints = no action.** If CloudWatch has no CPU data yet for an instance (e.g. just launched), it's skipped rather than assumed idle.

## Prerequisites

- AWS account with permissions to create IAM roles, Lambda functions, and EventBridge rules
- At least one EC2 instance you're willing to have auto-managed

## Deployment steps

### 1. Create the IAM role

Create a role named `CostOptimizerLambdaRole` with:
- Trusted entity: Lambda
- Policies: `AmazonEC2FullAccess`, `CloudWatchReadOnlyAccess`, `CloudWatchLogsFullAccess`

### 2. Tag the instances you want managed

For each EC2 instance you want this function to control:
1. EC2 → select instance → **Tags** tab → **Manage tags**
2. Add tag: Key = `AutoStop`, Value = `true`
3. Save

Case-sensitive — `Autostop` or `True` will **not** match the filter.

### 3. Create the Lambda function

1. Lambda → Create function → name `ec2-cost-optimizer`, runtime Python 3.12
2. Execution role: `CostOptimizerLambdaRole`
3. Timeout: 1 min, Memory: 256 MB
4. Add environment variables (see Configuration table below)
5. Paste in `lambda_function.py` → Deploy

### 4. Schedule it with EventBridge

1. EventBridge → Rules → **Create rule**
2. Name: `cost-optimizer-schedule`
3. Rule type: **Schedule**
4. Schedule pattern: rate expression → `rate(30 minutes)`
5. Target: Lambda function → `ec2-cost-optimizer`
6. Create rule

### 5. Test manually before relying on the schedule

Lambda console → **Test** tab → create a test event (empty `{}` works, since this function ignores the event payload) → **Test**. Check the response and CloudWatch Logs to confirm it's evaluating instances as expected.

⚠️ **Caution:** `stop_instances()` really stops the instance. Test with a throwaway instance first, or make sure nothing important is tagged `AutoStop: true` before your first test run.

## Configuration

| Environment variable | Default | Description |
|---|---|---|
| `BUSINESS_HOUR_START` | 9 | Hour (0–23, **UTC**) business day starts |
| `BUSINESS_HOUR_END` | 19 | Hour (0–23, **UTC**) business day ends |
| `IDLE_CPU_THRESHOLD` | 5 | CPU % below which an instance is considered idle |
| `IDLE_MINUTES_CHECK` | 30 | Lookback window (minutes) used for the idle CPU check |

Adjust `BUSINESS_HOUR_START`/`BUSINESS_HOUR_END` to account for your local timezone offset, since the check runs against UTC.

## Project structure

```
project6-automated-cost-optimizer/
├── lambda_function.py    # Lambda handler — checks and stops idle/off-hours instances
├── requirements.txt
├── .gitignore
└── README.md
```

## Pausing the automation

To temporarily stop the auto-stopping behavior without deleting anything:
EventBridge → Rules → `cost-optimizer-schedule` → **Disable**

## What this project demonstrates

| Concept | How it's shown |
|---|---|
| Scheduled (time-based) serverless triggers | EventBridge rate expression → Lambda |
| CloudWatch metrics queried programmatically | `get_metric_statistics()` for CPUUtilization |
| Tag-based resource filtering for safety | `Filters=[{"Name": "tag:AutoStop", ...}]` |
| Cost governance automation | Auto-stopping idle/off-hours EC2 instances |
