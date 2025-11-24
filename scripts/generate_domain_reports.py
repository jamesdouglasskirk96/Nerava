#!/usr/bin/env python3
"""
Generate Domain Merchant Weekly Reports

CLI script to generate and print merchant reports for the Domain hub.
"""
import sys
import os
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent / "nerava-backend-v9"))

from sqlalchemy.orm import Session
from app.db import SessionLocal
from app.services.merchant_reports import (
    get_domain_merchant_reports_for_period,
    DEFAULT_AVG_TICKET_CENTS
)
from app.utils.log import get_logger

logger = get_logger(__name__)


def format_currency(cents: int) -> str:
    """Format cents as currency string."""
    return f"${cents / 100:.2f}"


def format_date(dt: datetime) -> str:
    """Format datetime as readable string."""
    return dt.strftime("%Y-%m-%d")


def print_report(report, avg_ticket_cents: int):
    """Print a single merchant report in human-readable format."""
    print(f"\nMerchant: {report.merchant_name} (id={report.merchant_id})")
    print(f"Period: {format_date(report.period_start)} → {format_date(report.period_end)}")
    print(f"EV Visits: {report.ev_visits}")
    print(f"Unique Drivers: {report.unique_drivers}")
    print(f"Total Nova Awarded: {report.total_nova_awarded:,}")
    print(f"Total Rewards ($): {format_currency(report.total_rewards_cents)}")
    if report.implied_revenue_cents:
        print(f"Implied Revenue ($): {format_currency(report.implied_revenue_cents)}")
    print("---")


def print_csv_header():
    """Print CSV header row."""
    print("merchant_id,merchant_name,period_start,period_end,ev_visits,unique_drivers,total_nova_awarded,total_rewards_cents,implied_revenue_cents")


def print_csv_row(report):
    """Print a single merchant report as CSV row."""
    revenue = report.implied_revenue_cents if report.implied_revenue_cents else ""
    print(f"{report.merchant_id},{report.merchant_name},{format_date(report.period_start)},{format_date(report.period_end)},{report.ev_visits},{report.unique_drivers},{report.total_nova_awarded},{report.total_rewards_cents},{revenue}")


def parse_period(period_str: str) -> tuple:
    """
    Parse period string into (period_start, period_end).
    
    Supports:
    - "7d" or "week": Last 7 days
    - "30d": Last 30 days
    - "full-week": Last complete week (Monday-Sunday)
    """
    now = datetime.utcnow()
    
    if period_str in ("7d", "week"):
        period_start = now - timedelta(days=7)
        period_end = now
    elif period_str == "30d":
        period_start = now - timedelta(days=30)
        period_end = now
    elif period_str == "full-week":
        # Last complete week (Monday to Sunday)
        days_since_monday = now.weekday()  # Monday = 0
        if days_since_monday == 0:  # Today is Monday
            # Last week
            period_end = now - timedelta(days=1)
            period_start = period_end - timedelta(days=6)
        else:
            # This week's Monday
            this_monday = now - timedelta(days=days_since_monday)
            period_end = this_monday - timedelta(seconds=1)
            period_start = period_end - timedelta(days=6)
    else:
        raise ValueError(f"Unsupported period: {period_str}. Use '7d', '30d', or 'full-week'")
    
    return period_start, period_end


def main():
    parser = argparse.ArgumentParser(
        description="Generate Domain merchant weekly reports",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Last 7 days (default)
  python scripts/generate_domain_reports.py
  
  # Last 30 days
  python scripts/generate_domain_reports.py --period=30d
  
  # Last complete week (Mon-Sun)
  python scripts/generate_domain_reports.py --period=full-week
  
  # Output as CSV
  python scripts/generate_domain_reports.py --csv
  
  # Custom average ticket size
  python scripts/generate_domain_reports.py --avg-ticket=1200
        """
    )
    
    parser.add_argument(
        "--period",
        default="7d",
        choices=["7d", "week", "30d", "full-week"],
        help="Reporting period (default: 7d)"
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Output as CSV instead of human-readable format"
    )
    parser.add_argument(
        "--avg-ticket",
        type=int,
        default=None,
        help=f"Average ticket size in cents (default: {DEFAULT_AVG_TICKET_CENTS})"
    )
    
    args = parser.parse_args()
    
    # Parse period
    try:
        period_start, period_end = parse_period(args.period)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Get database session
    db: Session = SessionLocal()
    
    try:
        # Get reports
        reports = get_domain_merchant_reports_for_period(
            db=db,
            period_start=period_start,
            period_end=period_end,
            avg_ticket_cents=args.avg_ticket
        )
        
        if not reports:
            print("No merchant reports found for the specified period.", file=sys.stderr)
            sys.exit(0)
        
        # Output reports
        if args.csv:
            print_csv_header()
            for report in reports:
                print_csv_row(report)
        else:
            print(f"Domain Merchant Reports")
            print(f"Period: {format_date(period_start)} → {format_date(period_end)}")
            if args.avg_ticket:
                print(f"Average Ticket Size: {format_currency(args.avg_ticket)}")
            print(f"\nFound {len(reports)} merchant(s) with visits in this period:\n")
            
            for report in reports:
                print_report(report, args.avg_ticket or DEFAULT_AVG_TICKET_CENTS)
            
            # Summary
            total_visits = sum(r.ev_visits for r in reports)
            total_drivers = len(set(
                # This is approximate - actual unique drivers across all merchants would need a separate query
                driver for r in reports
            ))
            total_rewards = sum(r.total_rewards_cents for r in reports)
            total_revenue = sum(r.implied_revenue_cents or 0 for r in reports)
            
            print(f"\n=== Summary ===")
            print(f"Total EV Visits: {total_visits}")
            print(f"Total Rewards ($): {format_currency(total_rewards)}")
            if total_revenue > 0:
                print(f"Total Implied Revenue ($): {format_currency(total_revenue)}")
    
    except Exception as e:
        logger.error(f"Failed to generate reports: {str(e)}", exc_info=True)
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()

