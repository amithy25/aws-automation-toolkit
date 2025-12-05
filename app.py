import argparse
import boto3
from datetime import datetime, timezone, timedelta
from cloudwatch_monitor import print_instance_dashboard
import smtplib
from email.mime.text import MIMEText

cloudwatch = boto3.client("cloudwatch")

def get_instance_metrics(instance_id, period=300):
    """
    Fetch CPUUtilization and EBS metrics for an EC2 instance for the last 1 hour.
    period: granularity in seconds (default 5 min)
    """
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=1)  # last 1 hour

    metrics_data = {}

    # CPU Utilization
    cpu = cloudwatch.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
        StartTime=start_time,
        EndTime=end_time,
        Period=period,
        Statistics=["Average"]
    )
    if cpu["Datapoints"]:
        metrics_data["CPUUtilization"] = round(cpu["Datapoints"][-1]["Average"], 2)
    else:
        metrics_data["CPUUtilization"] = "N/A"

    # EBS Metrics (VolumeReadBytes + VolumeWriteBytes for simplicity)
    # Get all volumes attached to the instance
    ec2 = boto3.client("ec2")
    volumes = ec2.describe_volumes(
        Filters=[{"Name": "attachment.instance-id", "Values": [instance_id]}]
    )
    ebs_metrics = []
    for vol in volumes["Volumes"]:
        vol_id = vol["VolumeId"]
        read_bytes = cloudwatch.get_metric_statistics(
            Namespace="AWS/EBS",
            MetricName="VolumeReadBytes",
            Dimensions=[{"Name": "VolumeId", "Value": vol_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=period,
            Statistics=["Average"]
        )
        write_bytes = cloudwatch.get_metric_statistics(
            Namespace="AWS/EBS",
            MetricName="VolumeWriteBytes",
            Dimensions=[{"Name": "VolumeId", "Value": vol_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=period,
            Statistics=["Average"]
        )
        ebs_metrics.append({
            "VolumeId": vol_id,
            "ReadBytes": round(read_bytes["Datapoints"][-1]["Average"], 2) if read_bytes["Datapoints"] else "N/A",
            "WriteBytes": round(write_bytes["Datapoints"][-1]["Average"], 2) if write_bytes["Datapoints"] else "N/A"
        })

    metrics_data["EBS"] = ebs_metrics
    return metrics_data

def send_email_smtp(subject, body, recipient_email):
    """
    Send an email using SMTP (e.g., Gmail).
    """
    sender_email = "amithy25@gmail.com"
    #sender_password = <smtp password>            # Gmail App Password
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient_email

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)

    print("Email sent successfully to", recipient_email)

def generate_daily_report_smtp(recipient_email):
    report_lines = []

    # --- EC2 Summary ---
    ec2 = boto3.client("ec2")
    instances = ec2.describe_instances()["Reservations"]
    report_lines.append("=== EC2 Instances ===")
    for r in instances:
        for i in r["Instances"]:
            instance_id = i['InstanceId']
            name = ""
            if "Tags" in i:
                for t in i["Tags"]:
                    if t["Key"] == "Name":
                        name = t["Value"]
            state = i['State']['Name']
            instance_type = i['InstanceType']
            report_lines.append(f"{instance_id} | {name} | {state} | {instance_type}")

            # --- CloudWatch metrics ---
            metrics = get_instance_metrics(instance_id)
            report_lines.append(f"  CPUUtilization: {metrics['CPUUtilization']}%")
            for vol in metrics["EBS"]:
                report_lines.append(f"  EBS {vol['VolumeId']}: ReadBytes={vol['ReadBytes']} WriteBytes={vol['WriteBytes']}")

    # --- Cost Anomalies ---
    report_lines.append("\n=== Cost Anomalies ===")
    import io
    import sys
    buffer = io.StringIO()
    sys.stdout = buffer
    detect_cost_anomalies()
    sys.stdout = sys.__stdout__
    report_lines.append(buffer.getvalue())

    # Combine report
    body = "\n".join(report_lines)
    subject = "Daily AWS EC2 & Cost Summary"

    # Send email via SMTP
    send_email_smtp(subject, body, recipient_email)




pricing = boto3.client("pricing", region_name="us-east-1")

def get_ec2_cost(instance_type, region="US East (N. Virginia)"):
    """
    Returns the ON-DEMAND hourly price for the instance type.
    If pricing API fails (common), returns 'N/A'.
    """
    try:
        response = pricing.get_products(
            ServiceCode="AmazonEC2",
            Filters=[
                {"Type": "TERM_MATCH", "Field": "instanceType", "Value": instance_type},
                {"Type": "TERM_MATCH", "Field": "location", "Value": region},
                {"Type": "TERM_MATCH", "Field": "operatingSystem", "Value": "Linux"},
                {"Type": "TERM_MATCH", "Field": "preInstalledSw", "Value": "NA"},
                {"Type": "TERM_MATCH", "Field": "tenancy", "Value": "Shared"},
                {"Type": "TERM_MATCH", "Field": "capacitystatus", "Value": "Used"},
            ],
            MaxResults=1
        )

        # Pricing API returns nested JSON inside JSON as a string
        import json
        price_item = json.loads(response["PriceList"][0])

        # Navigate to OnDemand price
        on_demand = list(price_item["terms"]["OnDemand"].values())[0]
        price_dimensions = list(on_demand["priceDimensions"].values())[0]
        hourly_price = float(price_dimensions["pricePerUnit"]["USD"])

        monthly_price = round(hourly_price * 24 * 30, 2)
        return f"${monthly_price}/mo"

    except Exception:
        return "N/A"

def list_all_instances():
    ec2 = boto3.client("ec2")
    response = ec2.describe_instances()

    print("\n=== All EC2 Instances ===\n")

    instances = []

    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            launch_time = instance["LaunchTime"]  # boto3 returns datetime in UTC
            now = datetime.now(timezone.utc)
            uptime = now - launch_time

            # Format uptime nicely
            days = uptime.days
            hours = uptime.seconds // 3600
            minutes = (uptime.seconds % 3600) // 60
            uptime_str = f"{days}d {hours}h {minutes}m"

            instance_id = instance["InstanceId"]
            state = instance["State"]["Name"]
            instance_type = instance["InstanceType"]

            name = ""
            if "Tags" in instance:
                for tag in instance["Tags"]:
                    if tag["Key"] == "Name":
                        name = tag["Value"]

            cost = get_ec2_cost(instance_type)
            instances.append([instance_id, name, instance_type, state, uptime_str, cost])



    # Sort output by state, then name
    instances.sort(key=lambda x: (x[3], x[1]))

    # Pretty print
    print(f"{'Instance ID':<20} {'Name':<25} {'Type':<15} {'State':<15} {'Uptime':<15} {'Cost':<15}")
    print("-" * 115)



    for inst in instances:
        print(f"{inst[0]:<20} {inst[1]:<25} {inst[2]:<15} {inst[3]:<15} {inst[4]:<15} {inst[5]:<15}")




    if not instances:
        print("No instances found.")


def list_running_instances():
    ec2 = boto3.client("ec2")
    response = ec2.describe_instances(
        Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
    )

    print("\n=== Running EC2 Instances ===\n")
    found = False

    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            found = True
            instance_id = instance["InstanceId"]
            instance_type = instance["InstanceType"]
            state = instance["State"]["Name"]
            name = ""

            if "Tags" in instance:
                for tag in instance["Tags"]:
                    if tag["Key"] == "Name":
                        name = tag["Value"]

            print(f"ID: {instance_id} | Type: {instance_type} | Name: {name} | State: {state}")

    if not found:
        print("No running instances found.")


def start_instance(instance_id):
    ec2 = boto3.client("ec2")
    print(f"Starting instance: {instance_id} ...")
    ec2.start_instances(InstanceIds=[instance_id])
    print("Start command sent.")


def stop_instance(instance_id):
    ec2 = boto3.client("ec2")
    print(f"Stopping instance: {instance_id} ...")
    ec2.stop_instances(InstanceIds=[instance_id])
    print("Stop command sent.")

def start_instances_by_tag(tag_key, tag_value):
    ec2 = boto3.client("ec2")

    # Find instances with tag
    response = ec2.describe_instances(
        Filters=[
            {"Name": f"tag:{tag_key}", "Values": [tag_value]},
            {"Name": "instance-state-name", "Values": ["stopped"]}
        ]
    )

    instances_to_start = []
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            instances_to_start.append(instance["InstanceId"])

    if not instances_to_start:
        print("No stopped instances found with that tag.")
        return

    print("Starting instances:", instances_to_start)
    ec2.start_instances(InstanceIds=instances_to_start)
    print("Start command sent.")

def stop_instances_by_tag(tag_key, tag_value):
    ec2 = boto3.client("ec2")

    # Find instances with tag
    response = ec2.describe_instances(
        Filters=[
            {"Name": f"tag:{tag_key}", "Values": [tag_value]},
            {"Name": "instance-state-name", "Values": ["running"]}
        ]
    )

    instances_to_stop = []
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            instances_to_stop.append(instance["InstanceId"])

    if not instances_to_stop:
        print("No running instances found with that tag.")
        return

    print("Stopping instances:", instances_to_stop)
    ec2.stop_instances(InstanceIds=instances_to_stop)
    print("Stop command sent.")

ce = boto3.client("ce", region_name="us-east-1")

def detect_cost_anomalies(days=7, threshold_percent=50):
    """
    Checks EC2 cost over the past `days` days.
    Prints if today's cost exceeds threshold_percent increase over the average.
    """
    end = datetime.utcnow().date()
    start = end - timedelta(days=days)

    response = ce.get_cost_and_usage(
        TimePeriod={"Start": str(start), "End": str(end)},
        Granularity="DAILY",
        Metrics=["UnblendedCost"],
        Filter={
            "Dimensions": {
                "Key": "SERVICE",
                "Values": ["Amazon Elastic Compute Cloud - Compute"]
            }
        }
    )

    daily_costs = []
    for item in response["ResultsByTime"]:
        amount = float(item["Total"]["UnblendedCost"]["Amount"])
        daily_costs.append(amount)

    if len(daily_costs) < 2:
        print("Not enough data to detect anomalies.")
        return

    avg = sum(daily_costs[:-1]) / (len(daily_costs)-1)
    today = daily_costs[-1]

    increase_percent = ((today - avg) / avg) * 100 if avg else 0

    print("\n💰 EC2 Cost Anomaly Check")
    print("-" * 40)
    print(f"Average daily EC2 cost (past {days-1} days): ${avg:.2f}")
    print(f"Today's EC2 cost: ${today:.2f}")
    print(f"Change: {increase_percent:.1f}%")

    if increase_percent > threshold_percent:
        print("⚠️  ALERT: Today's EC2 cost spike exceeds threshold!")
    else:
        print("✅ No significant anomalies detected.")
    print("-" * 40)

def cleanup_unused_volumes(days_old=7):
    """
    Delete unattached EBS volumes older than `days_old`.
    """
    ec2 = boto3.client("ec2")
    volumes = ec2.describe_volumes(
        Filters=[{"Name": "status", "Values": ["available"]}]
    )["Volumes"]

    cutoff = datetime.now(timezone.utc) - timedelta(days=days_old)
    to_delete = [v for v in volumes if v["CreateTime"] < cutoff]

    if not to_delete:
        print(f"No unused EBS volumes older than {days_old} days found.")
        return

    print(f"Deleting {len(to_delete)} unused EBS volumes:")
    for v in to_delete:
        print(f"  Deleting volume {v['VolumeId']} created on {v['CreateTime']}")
        ec2.delete_volume(VolumeId=v["VolumeId"])
    print("Deletion complete.\n")


def cleanup_old_snapshots(days_old=30):
    """
    Delete EBS snapshots owned by the account older than `days_old`.
    """
    ec2 = boto3.client("ec2")
    snapshots = ec2.describe_snapshots(OwnerIds=["self"])["Snapshots"]

    cutoff = datetime.now(timezone.utc) - timedelta(days=days_old)
    to_delete = [s for s in snapshots if s["StartTime"] < cutoff]

    if not to_delete:
        print(f"No snapshots older than {days_old} days found.")
        return

    print(f"Deleting {len(to_delete)} snapshots:")
    for s in to_delete:
        print(f"  Deleting snapshot {s['SnapshotId']} created on {s['StartTime']}")
        ec2.delete_snapshot(SnapshotId=s["SnapshotId"])
    print("Deletion complete.\n")




def main():
    parser = argparse.ArgumentParser(description="AWS Infra Automation Toolkit")

    subparsers = parser.add_subparsers(dest="command")

    # list all ec2
    subparsers.add_parser("list-all", help="List all EC2 instances")

    # list-ec2
    subparsers.add_parser("list-ec2", help="List all running EC2 instances")

    # start instance
    start_parser = subparsers.add_parser("start", help="Start an EC2 instance")
    start_parser.add_argument("instance_id", help="EC2 Instance ID to start")
    start_tag_parser = subparsers.add_parser("start-tag", help="Start EC2 instances by tag")
    start_tag_parser.add_argument("tag_key")
    start_tag_parser.add_argument("tag_value")

    # stop instance
    stop_parser = subparsers.add_parser("stop", help="Stop an EC2 instance")
    stop_parser.add_argument("instance_id", help="EC2 Instance ID to stop")
    stop_tag_parser = subparsers.add_parser("stop-tag", help="Stop EC2 instances by tag")
    stop_tag_parser.add_argument("tag_key")
    stop_tag_parser.add_argument("tag_value")

    dashboard_parser = subparsers.add_parser("dashboard", help="Show CloudWatch metrics for an instance")
    dashboard_parser.add_argument("instance_id", help="EC2 Instance ID")

    cost_parser = subparsers.add_parser(
    "cost-check", help="Detect EC2 cost anomalies using Cost Explorer"
    )
    cost_parser.add_argument("--days", type=int, default=7, help="Number of days to average")
    cost_parser.add_argument("--threshold", type=int, default=50, help="Alert threshold in percent")


    cleanup_vol_parser = subparsers.add_parser(
    "cleanup-volumes", help="Delete unattached EBS volumes older than X days"
    )
    cleanup_vol_parser.add_argument("--days", type=int, default=7, help="Delete volumes older than this many days")

    cleanup_snap_parser = subparsers.add_parser(
        "cleanup-snapshots", help="Delete old EBS snapshots"
    )
    cleanup_snap_parser.add_argument("--days", type=int, default=30, help="Delete snapshots older than this many days")

    email_parser = subparsers.add_parser(
    "daily-report", help="Send daily AWS report email via SMTP"
    )
    email_parser.add_argument("--to", required=True, help="Recipient email")


    args = parser.parse_args()

    if args.command == "list-ec2":
        list_running_instances()

    elif args.command == "start":
        start_instance(args.instance_id)

    elif args.command == "stop":
        stop_instance(args.instance_id)
    
    elif args.command == "list-all":
        list_all_instances()
    
    elif args.command == "start-tag":
        start_instances_by_tag(args.tag_key, args.tag_value)

    elif args.command == "stop-tag":
        stop_instances_by_tag(args.tag_key, args.tag_value)
    
    elif args.command == "dashboard":
        print_instance_dashboard(args.instance_id)

    elif args.command == "cost-check":
        detect_cost_anomalies(days=args.days, threshold_percent=args.threshold)

    elif args.command == "cleanup-volumes":
        cleanup_unused_volumes(days_old=args.days)

    elif args.command == "cleanup-snapshots":
        cleanup_old_snapshots(days_old=args.days)
    
    elif args.command == "daily-report":
        generate_daily_report_smtp(args.to)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
