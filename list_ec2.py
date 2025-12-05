import boto3

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

            # Extract Name tag if exists
            if "Tags" in instance:
                for tag in instance["Tags"]:
                    if tag["Key"] == "Name":
                        name = tag["Value"]

            print(f"ID: {instance_id}  |  Type: {instance_type}  |  Name: {name}  |  State: {state}")

    if not found:
        print("No running instances found.")

if __name__ == "__main__":
    list_running_instances()
