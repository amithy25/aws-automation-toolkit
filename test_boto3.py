import boto3

ec2 = boto3.client("ec2")

try:
    response = ec2.describe_instances()
    print("🚀 Boto3 is working! Number of reservations:", len(response["Reservations"]))
except Exception as e:
    print("❌ Error:", e)
