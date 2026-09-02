"""APScheduler job that runs the daily digest (application follow-ups +
today's tasks). Run with: python -m backend.scheduler
"""

import logging

from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

from backend.agents import planner, tracker
from backend.db import init_db

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("careerpilot.digest")


def run_daily_digest() -> str:
    tasks = planner.todays_tasks()
    digest = [f"{len(tasks)} tasks due today.", tracker.daily_digest()]
    text = "\n".join(digest)
    logger.info("Daily digest:\n%s", text)
    return text


def main() -> None:
    init_db()
    scheduler = BlockingScheduler()
    scheduler.add_job(run_daily_digest, "cron", hour=8, minute=0)
    logger.info("Scheduler started, daily digest at 08:00")
    scheduler.start()


if __name__ == "__main__":
    main()
