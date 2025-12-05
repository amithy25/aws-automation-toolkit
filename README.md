# AWS Infra Automation & CloudOps Toolkit

A Python-based DevOps automation toolkit for managing AWS EC2,
monitoring CloudWatch metrics, detecting cost anomalies, and sending
daily operational reports.\
Built using **Python**, **boto3**, and **SMTP/email automation**.

------------------------------------------------------------------------

## 🚀 Features

### ✅ **EC2 Management**

-   List all EC2 instances (running + stopped)
-   List only running instances
-   Start/stop EC2 instances by:
    -   Instance ID
    -   Tag key/value (ex: `Environment=Dev`)

### ✅ **CloudWatch Dashboard**

Fetches and displays: - CPU utilization (last 24h) - Network In / Out -
Disk Read/Write Ops - Formatted CLI dashboard:

    python app.py dashboard i-0123456789abcdef

### ✅ **Cost Anomaly Detection**

Detects unusual spikes in AWS spending: - Define time range (`--days`) -
Define deviation threshold (`--threshold`) - Provides a clean summary in
terminal:

    python app.py cost-check --days 7 --threshold 40

### ✅ **Daily Email Report**

Sends a daily summary containing: - Instance health - CPU/network
metrics - Cost checks - Potential anomalies

Delivered using standard **SMTP (no SES required)**.

Run manually:

    python app.py daily-report youremail@example.com

### ✅ **Daily Automation (macOS LaunchAgent)**

A background scheduler runs every day at a configured time.\
Implemented using: - Python `schedule` library - macOS LaunchAgents

------------------------------------------------------------------------

## 🛠 Project Structure

    aws-automation-toolkit/
    │
    ├── app.py                     # Main CLI tool
    ├── cloudwatch_monitor.py      # CloudWatch metric functions
    ├── daily_runner.py            # Scheduled daily automation
    ├── requirements.txt
    ├── README.md
    └── .venv/

------------------------------------------------------------------------

## 📦 Installation

### 1. Clone the repository

``` bash
git clone https://github.com/yourname/aws-automation-toolkit.git
cd aws-automation-toolkit
```

### 2. Create a virtual environment

``` bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

``` bash
pip install -r requirements.txt
```

------------------------------------------------------------------------

## 🔐 AWS Authentication

``` bash
aws configure
```

Required IAM permissions: - ec2:DescribeInstances - ec2:StartInstances -
ec2:StopInstances - cloudwatch:GetMetricStatistics - ce:GetCostAndUsage

------------------------------------------------------------------------

## 💻 Usage

### 1. List all EC2 instances

    python app.py list-all

### 2. List only running instances

    python app.py list-ec2

### 3. Start an instance

    python app.py start i-0123456

### 4. Stop an instance

    python app.py stop i-0123456

### 5. Start/Stop by tag

    python app.py start-tag Environment Dev
    python app.py stop-tag Environment Dev

### 6. CloudWatch dashboard

    python app.py dashboard i-0123456789abcdef

### 7. Cost anomaly detection

    python app.py cost-check --days 7 --threshold 50

### 8. Send daily report

    python app.py daily-report youremail@example.com

------------------------------------------------------------------------

## ⏱ Automating Daily Reports

### Using daily_runner.py

    python daily_runner.py

### macOS LaunchAgent

    launchctl load ~/Library/LaunchAgents/aws.daily.report.plist

------------------------------------------------------------------------

## ✨ Author

**Amith Y**\
<<<<<<< HEAD
Site Reliability Engineer 
=======
Site Reliability Engineer 
>>>>>>> 9b10d29 (added Dockerfile, to containerize the application)
