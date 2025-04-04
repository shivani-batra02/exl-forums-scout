#!/usr/bin/env python3
"""
Slack notification module for AEM Forms Question Scraper
Sends notifications with scraped questions to Slack channels
"""

import os
import logging
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file if it exists
env_path = Path('.') / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

class SlackSender:
    """Slack notification sender for the AEM Forms Question Scraper"""
    
    def __init__(self, token=None, channel=None):
        """Initialize the Slack sender with API token and channel."""
        self.token = token or os.environ.get("AEM_SLACK_TOKEN")
        self.channel = channel or os.environ.get("AEM_SLACK_CHANNEL", "general")
        
        # Get report title from environment variable with fallback
        self.report_title = os.environ.get("AEM_REPORT_TITLE", 
            "Adobe Experience League Forums: Unresolved Questions")
        
        # Validate required settings
        self._validate_settings()
    
    def _validate_settings(self):
        """Validate Slack settings and log warnings for missing settings."""
        missing = []
        if not self.token:
            missing.append("Slack token")
        if not self.channel:
            missing.append("Slack channel")
                
        if missing:
            logging.warning(f"Missing Slack settings: {', '.join(missing)}")
    
    def create_slack_blocks(self, questions, start_date):
        """Create Slack message blocks with the list of questions."""
        # Get current date and time for the report
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create header blocks
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": self.report_title,
                    "emoji": True
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Report generated:* {now}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Questions since:* {start_date}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Found *{len(questions)}* unanswered questions."
                }
            },
            {
                "type": "divider"
            }
        ]
        
        if not questions:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "No unanswered questions found in the specified time period."
                }
            })
        else:
            # Add question blocks (up to 10 to avoid message size limits)
            display_count = min(10, len(questions))
            
            for i, question in enumerate(questions[:display_count]):
                title = question.get("title", "Untitled Question")
                url = question.get("url", "#")
                date = question.get("date", "Unknown Date")
                replies = question.get("replies", 0)
                
                # Calculate age in days
                try:
                    logging.info(f"Attempting to parse date: {date}")
                    question_date = datetime.strptime(date, "%Y-%m-%d")
                    age_days = (datetime.now() - question_date).days
                    age_text = f"{age_days} days"
                    color = "danger" if age_days > 3 else "good"
                except Exception as e:
                    logging.error(f"Failed to parse date '{date}': {str(e)}")
                    age_text = "Unknown"
                    color = "good"
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*<{url}|{title}>*\nAge: {age_text} | Replies: {replies}"
                    }
                })
                
                # Add divider between questions
                if i < display_count - 1:
                    blocks.append({"type": "divider"})
            
            # If there are more questions than we're showing, add a note
            if len(questions) > display_count:
                blocks.append({
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"_Showing {display_count} of {len(questions)} questions. Check email report for complete list._"
                        }
                    ]
                })
        
        return blocks
    
    def send_notification(self, questions=None, start_date=None):
        """Send a Slack notification with the list of questions."""
        if not questions:
            logging.warning("No questions to send in the Slack notification")
            return False
            
        if not start_date:
            start_date = "unknown date"
            
        # Validate required Slack settings
        if not self.token or not self.channel:
            logging.error("Missing required Slack settings")
            return False
            
        # Prepare Slack API request
        url = "https://slack.com/api/chat.postMessage"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # Create Slack message blocks
        blocks = self.create_slack_blocks(questions, start_date)
        
        # Create the message payload
        data = {
            "channel": self.channel,
            "text": f"{self.report_title} - Found {len(questions)} questions since {start_date}",
            "blocks": blocks
        }
        
        try:
            # Send the message to Slack
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response_data = response.json()
            
            if response.status_code == 200 and response_data.get("ok"):
                logging.info(f"Slack notification sent successfully to #{self.channel}")
                return True
            else:
                error = response_data.get("error", "Unknown error")
                logging.error(f"Failed to send Slack notification: {error}")
                return False
            
        except Exception as e:
            logging.error(f"Failed to send Slack notification: {str(e)}")
            return False 