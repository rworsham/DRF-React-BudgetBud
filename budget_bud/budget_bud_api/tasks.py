from django_apscheduler.jobstores import DjangoJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import date


def check_budget_goals():
    from .models import BudgetGoal
    today = date.today()
    budgets = BudgetGoal.objects.filter(end_date=today)
    for budget in budgets:
        budget.check_goal_met()

def check_savings_goal():
    from .models import SavingsGoal
    today = date.today()
    savings_goals = SavingsGoal.objects.filter(end_date=today)
    for goals in savings_goals:
        goals.check_goal_met()

def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")

    scheduler.add_job(
        check_budget_goals,
        trigger=CronTrigger(hour=21, minute=0),
        id="check_budget_goals",
        replace_existing=True,
    )

    scheduler.add_job(
        check_savings_goal,
        trigger=CronTrigger(hour=21, minute=0),
        id="check_savings_goal",
        replace_existing=True,
    )

    scheduler.start()