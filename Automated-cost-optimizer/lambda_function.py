import boto3
from datetime import datetime, timedelta, timezone
import os

ec2 = boto3.client("ec2")
cloudwatch = boto3.client("cloudwatch")

BUSINESS_HOUR_START = int(os.environ.get("BUSINESS_HOUR_START", 9))
BUSINESS_HOUR_END = int(os.environ.get("BUSINESS_HOUR_END", 19))
IDLE_CPU_THRESHOLD = float(os.environ.get("IDLE_CPU_THRESHOLD", 5))
IDLE_MINUTES_CHECK = int(os.environ.get("IDLE_MINUTES_CHECK", 30))


def is_outside_business_hours():
    """Business hours are evaluated in UTC. Adjust BUSINESS_HOUR_START/END
    env vars to match your timezone offset if needed."""
    now_utc = datetime.now(timezone.utc)
    return not (BUSINESS_HOUR_START <= now_utc.hour < BUSINESS_HOUR_END)


def get_average_cpu(instance_id):
    """Returns average CPU utilization over the last IDLE_MINUTES_CHECK
    minutes, or None if no CloudWatch datapoints are available yet."""
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(minutes=IDLE_MINUTES_CHECK)

    response = cloudwatch.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
        StartTime=start_time,
        EndTime=end_time,
        Period=300,
        Statistics=["Average"],
    )

    datapoints = response.get("Datapoints", [])
    if not datapoints:
        return None

    avg_cpu = sum(dp["Average"] for dp in datapoints) / len(datapoints)
    return avg_cpu


def lambda_handler(event, context):
    stopped_instances = []
    skipped_instances = []

    # Only instances explicitly tagged AutoStop=true are considered —
    # this prevents the function from ever touching unrelated instances.
    reservations = ec2.describe_instances(
        Filters=[
            {"Name": "tag:AutoStop", "Values": ["true"]},
            {"Name": "instance-state-name", "Values": ["running"]},
        ]
    )["Reservations"]

    outside_hours = is_outside_business_hours()

    for reservation in reservations:
        for instance in reservation["Instances"]:
            instance_id = instance["InstanceId"]
            reason = None

            if outside_hours:
                reason = "outside business hours"
            else:
                avg_cpu = get_average_cpu(instance_id)
                if avg_cpu is not None and avg_cpu < IDLE_CPU_THRESHOLD:
                    reason = f"idle (avg CPU {avg_cpu:.2f}% over last {IDLE_MINUTES_CHECK} min)"

            if reason:
                print(f"Stopping {instance_id} — {reason}")
                ec2.stop_instances(InstanceIds=[instance_id])
                stopped_instances.append({"instance_id": instance_id, "reason": reason})
            else:
                print(f"Keeping {instance_id} running — active during business hours")
                skipped_instances.append(instance_id)

    print(f"Summary: stopped {len(stopped_instances)}, kept running {len(skipped_instances)}")

    return {
        "statusCode": 200,
        "stopped": stopped_instances,
        "kept_running": skipped_instances,
    }
