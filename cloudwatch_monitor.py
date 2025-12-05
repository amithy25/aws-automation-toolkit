import boto3
from datetime import datetime, timedelta

cloudwatch = boto3.client("cloudwatch")

def get_metric(instance_id, metric_name, namespace, statistic="Average"):
    """Fetch CloudWatch metric data for an EC2 instance."""
    end = datetime.utcnow()
    start = end - timedelta(hours=24)

    response = cloudwatch.get_metric_statistics(
        Namespace=namespace,
        MetricName=metric_name,
        Dimensions=[
            {"Name": "InstanceId", "Value": instance_id}
        ],
        StartTime=start,
        EndTime=end,
        Period=3600,
        Statistics=[statistic]
    )

    datapoints = response.get("Datapoints", [])
    if not datapoints:
        return None

    # Return the latest datapoint
    latest = sorted(datapoints, key=lambda x: x["Timestamp"])[-1]
    return latest.get(statistic, None)


def print_instance_dashboard(instance_id):
    """Display a small dashboard of key EC2 health metrics."""

    cpu = get_metric(instance_id, "CPUUtilization", "AWS/EC2")
    network_in = get_metric(instance_id, "NetworkIn", "AWS/EC2")
    network_out = get_metric(instance_id, "NetworkOut", "AWS/EC2")
    disk_read = get_metric(instance_id, "DiskReadBytes", "AWS/EC2")
    disk_write = get_metric(instance_id, "DiskWriteBytes", "AWS/EC2")

    print(f"\n📊 Health Dashboard for {instance_id}")
    print("-" * 50)
    print(f"CPU Utilization (avg last 24h):     {cpu}")
    print(f"Network In (bytes):                 {network_in}")
    print(f"Network Out (bytes):                {network_out}")
    print(f"Disk Read (bytes):                  {disk_read}")
    print(f"Disk Write (bytes):                 {disk_write}")
    print("-" * 50)
