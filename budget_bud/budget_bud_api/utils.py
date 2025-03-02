from rest_framework.response import Response
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
import logging

logger = logging.getLogger(__name__)

class SendEmail:
    def send_mail(self, recipient, message_type, data):
        if message_type == 'Invitation':
            subject = 'Family Invitation'
            html_message = render_to_string('invitation.html', data)
            text_message = render_to_string('invitation.txt', data)
        elif message_type == 'Invitation_Existing_User':
            subject = 'Invitation'
            html_message = render_to_string('invitation_existing_user.html', data)
            text_message = render_to_string('invitation_existing_user.txt', data)
        elif message_type == 'SavingsGoal':
            subject = 'Savings Goal Met!'
            html_message = render_to_string('savings_goal.html', data)
            text_message = render_to_string('savings_goals.txt', data)
        elif message_type == 'SavingsGoalFailed':
            subject = 'Savings Goal'
            html_message = render_to_string('savings_goal_failed.html', data)
            text_message = render_to_string('savings_goals_failed.txt', data)
        elif message_type == 'BudgetGoal':
            subject = 'Budget Goal Met!'
            html_message = render_to_string('budget_goal.html', data)
            text_message = render_to_string('budget_goal.txt', data)
        elif message_type == 'BudgetGoalFailed':
            subject = 'Budget Goal'
            html_message = render_to_string('budget_goal_failed.html', data)
            text_message = render_to_string('budget_goal_failed.txt', data)

        from_email = settings.EMAIL_HOST_USER
        recipient_list = [recipient]

        try:
            message = EmailMultiAlternatives(subject, text_message, from_email, recipient_list)
            message.attach_alternative(html_message, "text/html")
            message.send()
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")