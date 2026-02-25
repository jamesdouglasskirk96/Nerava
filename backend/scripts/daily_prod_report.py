#!/usr/bin/env python3
"""Daily Production Report — queries CloudWatch Logs Insights and metrics,
generates a digest, and publishes to SNS.

Usage:
    python scripts/daily_prod_report.py            # send via SNS
    python scripts/daily_prod_report.py --dry-run   # print to stdout only
"""

import os
import sys
import time
import json
from datetime import datetime, timedelta, timezone

try:
    import boto3
except ImportError:
    print("ERROR: boto3 required. Install with: pip install boto3")
    sys.exit(1)

REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
LOG_GROUP = "/aws/apprunner/nerava-backend/88e85a3063c14ea9a1e39f8fdf3c35e3/application"
RDS_INSTANCE_ID = "nerava-db"
SNS_TOPIC_ARN = os.getenv("SNS_TOPIC_ARN", "")
DRY_RUN = "--dry-run" in sys.argv

logs_client = boto3.client("logs", region_name=REGION)
cw_client = boto3.client("cloudwatch", region_name=REGION)
sns_client = boto3.client("sns", region_name=REGION)

# Time window: past 24 hours
END_TIME = datetime.now(timezone.utc)
START_TIME = END_TIME - timedelta(hours=24)
START_EPOCH = int(START_TIME.timestamp())
END_EPOCH = int(END_TIME.timestamp())


def run_insights_query(query: str, limit: int = 25) -> list[dict]:
    """Run a CloudWatch Logs Insights query and wait for results."""
    try:
        resp = logs_client.start_query(
            logGroupName=LOG_GROUP,
            startTime=START_EPOCH,
            endTime=END_EPOCH,
            queryString=query,
            limit=limit,
        )
    except Exception as e:
        return [{"error": str(e)}]

    query_id = resp["queryId"]

    for _ in range(30):  # wait up to 30s
        time.sleep(1)
        result = logs_client.get_query_results(queryId=query_id)
        if result["status"] == "Complete":
            rows = []
            for row in result.get("results", []):
                rows.append({f["field"]: f["value"] for f in row})
            return rows
    return [{"error": "query timed out"}]


def get_rds_metric(metric_name: str, stat: str = "Average") -> str:
    """Get a single RDS metric value for the past 24h."""
    try:
        resp = cw_client.get_metric_statistics(
            Namespace="AWS/RDS",
            MetricName=metric_name,
            Dimensions=[{"Name": "DBInstanceIdentifier", "Value": RDS_INSTANCE_ID}],
            StartTime=START_TIME,
            EndTime=END_TIME,
            Period=86400,  # 24h single datapoint
            Statistics=[stat],
        )
        points = resp.get("Datapoints", [])
        if points:
            return f"{points[0][stat]:.1f}"
        return "N/A"
    except Exception as e:
        return f"Error: {e}"


def get_alarm_history() -> list[str]:
    """Get CloudWatch alarms that fired in the past 24h."""
    try:
        resp = cw_client.describe_alarm_history(
            AlarmNamePrefix="nerava-",
            HistoryItemType="StateUpdate",
            StartDate=START_TIME,
            EndDate=END_TIME,
            MaxRecords=50,
        )
        alerts = []
        for item in resp.get("AlarmHistoryItems", []):
            try:
                data = json.loads(item.get("HistoryData", "{}"))
                new_state = data.get("newState", {}).get("stateValue", "")
                if new_state == "ALARM":
                    alerts.append(
                        f"  {item['AlarmName']} -> ALARM at {item['Timestamp']}"
                    )
            except (json.JSONDecodeError, KeyError):
                pass
        return alerts
    except Exception as e:
        return [f"  Error fetching alarm history: {e}"]


def section(title: str) -> str:
    return f"\n{'=' * 50}\n  {title}\n{'=' * 50}"


def build_report() -> str:
    lines = []
    lines.append("=" * 50)
    lines.append("  NERAVA DAILY PRODUCTION REPORT")
    lines.append("=" * 50)
    lines.append(f"  Period: {START_TIME.strftime('%Y-%m-%d %H:%M')} to {END_TIME.strftime('%Y-%m-%d %H:%M')} UTC")
    lines.append("")

    # 1. Error Summary
    lines.append(section("1. ERROR SUMMARY"))
    errors = run_insights_query(
        'filter @message like /ERROR/'
        ' | stats count(*) as cnt by @message'
        ' | sort cnt desc'
        ' | limit 10'
    )
    if errors and "error" not in errors[0]:
        for row in errors:
            msg = row.get("@message", "unknown")[:80]
            cnt = row.get("cnt", "?")
            lines.append(f"  [{cnt}x] {msg}")
    else:
        lines.append("  No errors found (or query failed)")

    # 2. Endpoint Performance
    lines.append(section("2. ENDPOINT PERFORMANCE (top 10 slowest)"))
    perf = run_insights_query(
        'filter @message like /duration_ms/'
        ' | parse @message "path=* " as path'
        ' | parse @message "duration_ms=*" as duration'
        ' | stats avg(duration) as avg_ms, count(*) as requests by path'
        ' | sort avg_ms desc'
        ' | limit 10'
    )
    if perf and "error" not in perf[0]:
        lines.append(f"  {'Endpoint':<40} {'Avg ms':>8} {'Requests':>10}")
        lines.append(f"  {'-'*40} {'-'*8} {'-'*10}")
        for row in perf:
            path = row.get("path", "?")[:40]
            avg = row.get("avg_ms", "?")
            reqs = row.get("requests", "?")
            try:
                avg = f"{float(avg):.0f}"
            except (ValueError, TypeError):
                pass
            lines.append(f"  {path:<40} {avg:>8} {reqs:>10}")
    else:
        lines.append("  No performance data found (or query failed)")

    # 3. Traffic Overview
    lines.append(section("3. TRAFFIC OVERVIEW"))
    traffic = run_insights_query(
        'filter @message like /status_code/'
        ' | stats count(*) as total_requests'
    )
    if traffic and "error" not in traffic[0]:
        total = traffic[0].get("total_requests", "N/A")
        lines.append(f"  Total requests: {total}")
    else:
        lines.append("  Traffic data unavailable")

    top_endpoints = run_insights_query(
        'filter @message like /status_code/'
        ' | parse @message "path=* " as path'
        ' | stats count(*) as cnt by path'
        ' | sort cnt desc'
        ' | limit 10'
    )
    if top_endpoints and "error" not in top_endpoints[0]:
        lines.append(f"\n  {'Top Endpoints':<40} {'Requests':>10}")
        lines.append(f"  {'-'*40} {'-'*10}")
        for row in top_endpoints:
            path = row.get("path", "?")[:40]
            cnt = row.get("cnt", "?")
            lines.append(f"  {path:<40} {cnt:>10}")

    # 4. 5xx Breakdown
    lines.append(section("4. 5xx BREAKDOWN"))
    fives = run_insights_query(
        'filter @message like /status_code=5/'
        ' | parse @message "path=* " as path'
        ' | parse @message "status_code=*" as status'
        ' | stats count(*) as cnt by path, status'
        ' | sort cnt desc'
        ' | limit 10'
    )
    if fives and "error" not in fives[0]:
        for row in fives:
            path = row.get("path", "?")
            status = row.get("status", "?")
            cnt = row.get("cnt", "?")
            lines.append(f"  [{cnt}x] {status} {path}")
    else:
        lines.append("  No 5xx errors (good!)")

    # 5. Auth Activity
    lines.append(section("5. AUTH ACTIVITY"))
    auth = run_insights_query(
        'filter @message like /otp/ or @message like /login/ or @message like /auth/'
        ' | parse @message "status_code=*" as status'
        ' | stats count(*) as cnt by status'
        ' | sort cnt desc'
    )
    if auth and "error" not in auth[0]:
        for row in auth:
            status = row.get("status", "?")
            cnt = row.get("cnt", "?")
            lines.append(f"  Status {status}: {cnt} requests")
    else:
        lines.append("  No auth activity data")

    # 6. Integration Health
    lines.append(section("6. INTEGRATION HEALTH"))
    integrations = run_insights_query(
        'filter @message like /tesla/ or @message like /stripe/ or @message like /twilio/'
        ' | filter @message like /ERROR/ or @message like /error/ or @message like /failed/'
        ' | stats count(*) as cnt by @message'
        ' | sort cnt desc'
        ' | limit 5'
    )
    if integrations and "error" not in integrations[0]:
        for row in integrations:
            msg = row.get("@message", "unknown")[:80]
            cnt = row.get("cnt", "?")
            lines.append(f"  [{cnt}x] {msg}")
    else:
        lines.append("  No integration errors detected")

    # 7. Database Metrics
    lines.append(section("7. DATABASE (RDS)"))
    cpu = get_rds_metric("CPUUtilization", "Average")
    conns = get_rds_metric("DatabaseConnections", "Average")
    storage = get_rds_metric("FreeStorageSpace", "Average")
    read_iops = get_rds_metric("ReadIOPS", "Average")
    write_iops = get_rds_metric("WriteIOPS", "Average")

    lines.append(f"  Avg CPU:         {cpu}%")
    lines.append(f"  Avg Connections: {conns}")
    try:
        storage_gb = f"{float(storage) / (1024**3):.1f} GB"
    except (ValueError, TypeError):
        storage_gb = storage
    lines.append(f"  Free Storage:    {storage_gb}")
    lines.append(f"  Avg Read IOPS:   {read_iops}")
    lines.append(f"  Avg Write IOPS:  {write_iops}")

    # 8. Alerts Fired
    lines.append(section("8. ALERTS FIRED (past 24h)"))
    alerts = get_alarm_history()
    if alerts:
        lines.extend(alerts)
    else:
        lines.append("  No alarms triggered (good!)")

    lines.append("")
    lines.append("=" * 50)
    lines.append(f"  Report generated at {END_TIME.strftime('%Y-%m-%d %H:%M:%S')} UTC")
    lines.append("=" * 50)

    return "\n".join(lines)


def main():
    report = build_report()

    if DRY_RUN:
        print(report)
        print("\n  (dry-run mode — not sent to SNS)")
        return

    print(report)

    if not SNS_TOPIC_ARN:
        print("\n  WARNING: SNS_TOPIC_ARN not set, skipping SNS publish")
        print("  Set SNS_TOPIC_ARN secret in GitHub Actions or pass as env var")
        return

    try:
        sns_client.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject=f"Nerava Daily Report — {END_TIME.strftime('%Y-%m-%d')}",
            Message=report,
        )
        print(f"\n  Report sent to SNS topic: {SNS_TOPIC_ARN}")
    except Exception as e:
        print(f"\n  ERROR: Failed to publish to SNS: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
