#!/usr/bin/env python3
"""
Reminder SMS system for strategic actions.
Sends weekly, monthly, and quarterly reminders as SMS using Twilio.
"""

import os
import sys
import argparse
import datetime as dt
import calendar
from twilio.rest import Client


# --------------------------
# Config
# --------------------------
# Dashboard link comes from workflow env (DASHBOARD_LINK).
# We also allow a fallback to keep the script robust.
DEFAULT_DASHBOARD = os.environ.get("DASHBOARD_LINK", "https://tinyurl.com/wcpaz")


# --------------------------
# Message Builders
# --------------------------
def build_message(mode: str, today: dt.date, excel_url: str) -> str:
    """Construct reminder text body."""
    lines = [f"📅 Strategic Reminder ({mode.title()}) — {today.isoformat()}"]

    if mode == "weekly":
        lines += [
            "✅ Review progress and update key actions.",
            "🔍 Check overdue & upcoming tasks.",
        ]
    elif mode == "monthly":
        lines += [
            "📊 Prepare monthly wrap-up and finalize metrics.",
            "📌 Ensure sustainability & margin reviews are complete.",
        ]
    elif mode == "quarterly":
        lines += [
            "📈 Quarterly review — assess goals vs outcomes.",
            "🚀 Plan adjustments for next quarter.",
        ]

    lines.append(f"🔗 Dashboard: {excel_url}")
    return "\n".join(lines)


# --------------------------
# Date Guardrails
# --------------------------
def is_two_days_before_month_end(today: dt.date) -> bool:
    """True if today is 2 days before end of month."""
    last_day = calendar.monthrange(today.year, today.month)[1]
    return today.day == last_day - 1


def is_one_week_before_quarter_end(today: dt.date) -> bool:
    """True if today is 7 days before end of quarter."""
    q_month = ((today.month - 1) // 3 + 1) * 3
    last_day = calendar.monthrange(today.year, q_month)[1]
    q_end = dt.date(today.year, q_month, last_day)
    return (q_end - today).days == 7


# --------------------------
# Twilio Sender
# --------------------------
def need_env(name: str) -> str:
    val = os.getenv(name)
    if not val:
        raise RuntimeError(f"Missing environment variable: {name}")
    return val


def send_sms(body: str) -> None:
    """Send SMS using Twilio credentials from env vars."""
    sid = need_env("TWILIO_ACCOUNT_SID")
    token = need_env("TWILIO_AUTH_TOKEN")
    from_phone = need_env("TWILIO_FROM")
    to_phone = need_env("TO_PHONE")

    client = Client(sid, token)
    msg = client.messages.create(to=to_phone, from_=from_phone, body=body)
    print(f"Sent SMS SID: {msg.sid}")


# --------------------------
# Main
# --------------------------
def main():
    parser = argparse.ArgumentParser(description="Send strategic reminders by SMS.")
    parser.add_argument("mode", choices=["weekly", "monthly", "quarterly"], help="Type of reminder")
    # Hidden/testing flag for simulations (not used by Actions normally)
    parser.add_argument("--today", help="Simulate date YYYY-MM-DD (for tests)")
    args = parser.parse_args()

    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()

    # Guardrails to prevent accidental sends
    if args.mode == "monthly" and not is_two_days_before_month_end(today):
        print("Not 2 days before month-end; skipping.")
        return
    if args.mode == "quarterly" and not is_one_week_before_quarter_end(today):
        print("Not 1 week before quarter-end; skipping.")
        return

    body = build_message(args.mode, today, DEFAULT_DASHBOARD)
    send_sms(body)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Make failures visible in CI logs
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
