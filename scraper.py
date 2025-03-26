#!/usr/bin/env python3
"""
AEM Forms Question Scraper - Scrapes unanswered questions from Adobe Experience League forums
"""

import argparse
import json
import logging
import os
import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import glob
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
env_path = Path('.') / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)-8s %(message)s",
    datefmt="%H:%M:%S",
)

class ForumScraper:
    def __init__(self, start_date, max_pages=10, debug=False, keep_html=False):
        """Initialize the scraper with the given parameters."""
        self.start_date = start_date
        self.max_pages = max_pages
        self.debug = debug
        self.keep_html = keep_html
        self.base_url = "https://experienceleaguecommunities.adobe.com/t5/adobe-experience-manager-forms/bd-p/experience-manager-forms-qanda"
        self.questions = []
        self.html_files = []
        
    def save_html(self, html_content, page_num):
        """Save HTML content to a file for debugging."""
        if self.debug:
            filename = f"page_{page_num}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(html_content)
            self.html_files.append(filename)
            logging.debug(f"Saved HTML to {filename}")

    def cleanup(self):
        """Clean up temporary files after scraping."""
        if self.debug and not self.keep_html:
            logging.info("Cleaning up temporary HTML files...")
            for file in self.html_files:
                try:
                    os.remove(file)
                    logging.debug(f"Removed {file}")
                except OSError as e:
                    logging.warning(f"Failed to remove {file}: {e}")

    def format_date(self, date_str):
        """Convert date string to a standard format."""
        # Handle dates like "3/18/25" (MM/DD/YY)
        try:
            date_obj = datetime.strptime(date_str.strip(), "%m/%d/%y")
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            return date_str  # Return as is if parsing fails

    def get_page_url(self, page_number=1):
        """Generate the URL for a specific page number."""
        if page_number == 1:
            return f"{self.base_url}?filter=unresolved&order=DESC&sort=date"
        return f"{self.base_url}/page/{page_number}?filter=unresolved&order=DESC&sort=date"

    def get_questions(self, page_number):
        """Scrape questions from a specific page."""
        url = self.get_page_url(page_number)
        logging.info(f"Scraping page {page_number}")
        logging.info(f"Fetching URL: {url}")
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logging.error(f"Failed to fetch page {page_number}: {response.status_code}")
            return []
            
        html_content = response.text
        self.save_html(html_content, page_number)
        
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Find all question elements (list items within the messages unordered list)
        question_elements = soup.select('div#messages > ul > li')
        logging.info(f"Found {len(question_elements)} potential question rows on page {page_number}")
        
        if self.debug:
            logging.debug("HTML structure exploration:")
            main_content = soup.select('div#messages')
            logging.debug(f"Main content elements: {len(main_content)}")
            logging.debug(f"Found {len(question_elements)} question elements")
            
        questions = []
        for question_elem in question_elements:
            try:
                # Extract the question ID from the data-id attribute
                question_id = question_elem.get('data-id', '').replace('message-', '')
                
                # Extract the title
                title_elem = question_elem.select_one('div.message-box div.spectrum-Heading--sizeM a.subject')
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)
                url = 'https://experienceleaguecommunities.adobe.com' + title_elem['href'] if title_elem.has_attr('href') else ''
                
                # Extract the author
                author_elem = question_elem.select_one('div.author a')
                author = author_elem.get_text(strip=True) if author_elem else "Unknown"
                
                # Extract the date
                date_elem = question_elem.select_one('span.post-time')
                date_text = date_elem.get_text(strip=True).split('•')[-1] if date_elem else ""
                date = self.format_date(date_text)
                
                # Extract stats (views, likes, replies)
                stats = {}
                stats_elements = question_elem.select('div[data-stat]')
                for stat_elem in stats_elements:
                    stat_type = stat_elem.get('data-stat', '').lower()
                    stat_value = stat_elem.get('data-value', '0')
                    stats[stat_type] = int(stat_value)
                
                # Extract content snippet
                content_elem = question_elem.select_one('div.truncated-body')
                content = content_elem.get_text(strip=True) if content_elem else ""
                
                # Get topics/tags
                topics = []
                topic_elements = question_elem.select('div.conversation-topics a.tag')
                for topic_elem in topic_elements:
                    topics.append(topic_elem.get_text(strip=True))
                
                # Check if the question date is after our start date
                question_date = datetime.strptime(date, "%Y-%m-%d") if re.match(r"\d{4}-\d{2}-\d{2}", date) else None
                start_date_obj = datetime.strptime(self.start_date, "%Y-%m-%d")
                
                if question_date and question_date >= start_date_obj:
                    question_data = {
                        "id": question_id,
                        "title": title,
                        "url": url,
                        "author": author,
                        "date": date,
                        "content": content,
                        "views": stats.get("views", 0),
                        "likes": stats.get("likes", 0),
                        "replies": stats.get("replies", 0),
                        "topics": topics
                    }
                    questions.append(question_data)
                
            except Exception as e:
                logging.error(f"Error parsing question: {e}")
                continue
                
        if not questions:
            logging.warning(f"No questions extracted from page {page_number}")
            
        return questions

    def scrape(self):
        """Main method to scrape questions from all pages."""
        page_number = 1
        has_more_pages = True
        
        while has_more_pages and page_number <= self.max_pages:
            page_questions = self.get_questions(page_number)
            if not page_questions:
                # No more questions or error occurred
                has_more_pages = False
            else:
                self.questions.extend(page_questions)
                
            # Move to the next page
            page_number += 1
            # Add a delay to avoid hitting rate limits
            if has_more_pages and page_number <= self.max_pages:
                time.sleep(2)
                
        return self.questions

def cleanup_html_files():
    """Remove any HTML files from previous runs."""
    html_files = glob.glob("page_*.html")
    if html_files:
        logging.info(f"Cleaning up {len(html_files)} HTML files from previous runs...")
        for file in html_files:
            try:
                os.remove(file)
                logging.debug(f"Removed {file}")
            except OSError as e:
                logging.warning(f"Failed to remove {file}: {e}")

def send_email_report(questions, start_date, recipient_email=None, smtp_server=None, smtp_port=None, 
                     sender_email=None, sender_name=None, display_from=None, password=None, use_ssl=False,
                     debug_email=False):
    """Send an email report with the scraped questions."""
    try:
        # Import here to make email optional
        from email_sender import EmailSender
        
        if recipient_email:
            logging.info(f"Sending email report to {recipient_email}")
        else:
            logging.info("Sending email report to default recipients")
        
        # Set more verbose logging for email debugging
        if debug_email:
            logger = logging.getLogger()
            original_level = logger.level
            logger.setLevel(logging.DEBUG)
            logging.debug("Email debugging enabled - verbose logging active")
        
        # Initialize email sender
        sender = EmailSender(
            smtp_server=smtp_server,
            smtp_port=smtp_port,
            sender_email=sender_email,
            sender_name=sender_name,
            display_from=display_from,
            password=password,
            use_ssl=use_ssl
        )
        
        # Send the email
        success = sender.send_email(recipient_email, questions, start_date)
        
        # Reset logging level if it was changed
        if debug_email:
            logger.setLevel(original_level)
        
        if success:
            logging.info("Email report sent successfully")
        else:
            logging.error("Failed to send email report")
            
        return success
    
    except ImportError:
        logging.error("Email module not found. Make sure email_sender.py is in the same directory.")
        return False
    
    except Exception as e:
        logging.error(f"Error sending email: {e}")
        return False

def send_slack_notification(questions, start_date, slack_token=None, slack_channel=None):
    """Send a Slack notification with the scraped questions."""
    try:
        # Import here to make slack optional
        from slack_sender import SlackSender
        
        logging.info(f"Sending Slack notification to #{slack_channel or 'default channel'}")
        
        # Initialize Slack sender
        sender = SlackSender(
            token=slack_token,
            channel=slack_channel
        )
        
        # Send the notification
        success = sender.send_notification(questions, start_date)
        
        if success:
            logging.info("Slack notification sent successfully")
        else:
            logging.error("Failed to send Slack notification")
            
        return success
    
    except ImportError:
        logging.error("Slack module not found. Make sure slack_sender.py is in the same directory.")
        return False
    
    except Exception as e:
        logging.error(f"Error sending Slack notification: {e}")
        return False

def main():
    """Main function to parse arguments and run the scraper."""
    parser = argparse.ArgumentParser(description="Scrape questions from Adobe Experience League forums")
    
    # Create a mutually exclusive group for cleanup vs. scraping
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--cleanup", action="store_true", help="Clean up HTML files from previous runs without scraping")
    
    # Scraping arguments
    parser.add_argument("--start-date", help="Start date in YYYY-MM-DD format")
    parser.add_argument("--output", default="questions.json", help="Output file name")
    parser.add_argument("--max-pages", type=int, default=10, help="Maximum number of pages to scrape")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--keep-html", action="store_true", help="Keep HTML files after scraping (only applies in debug mode)")
    
    # Email arguments
    email_group = parser.add_argument_group("Email Options")
    email_group.add_argument("--email", help="Send email report to this address (optional if default recipients configured)")
    email_group.add_argument("--smtp-server", help="SMTP server address (or set AEM_SMTP_SERVER env var)")
    email_group.add_argument("--smtp-port", type=int, help="SMTP server port (or set AEM_SMTP_PORT env var)")
    email_group.add_argument("--sender-email", help="Sender email address (or set AEM_SENDER_EMAIL env var)")
    email_group.add_argument("--sender-name", help="Sender name (or set AEM_SENDER_NAME env var)")
    email_group.add_argument("--display-from", help="Display From address for email clients like Outlook (or set AEM_DISPLAY_FROM env var)")
    email_group.add_argument("--email-password", help="Email password (or set AEM_EMAIL_PASSWORD env var)")
    email_group.add_argument("--use-ssl", action="store_true", help="Use SSL instead of TLS (or set AEM_USE_SSL=true)")
    email_group.add_argument("--skip-email", action="store_true", help="Skip sending email even if --email is provided")
    email_group.add_argument("--debug-email", action="store_true", help="Enable detailed email debugging")
    
    # Slack arguments
    slack_group = parser.add_argument_group("Slack Options")
    slack_group.add_argument("--slack", action="store_true", help="Send Slack notification (or set AEM_SLACK_ENABLED=true)")
    slack_group.add_argument("--slack-token", help="Slack Bot User OAuth Token (or set AEM_SLACK_TOKEN env var)")
    slack_group.add_argument("--slack-channel", help="Slack channel to send notification to (or set AEM_SLACK_CHANNEL env var)")
    slack_group.add_argument("--skip-slack", action="store_true", help="Skip sending Slack notification even if Slack is enabled")
    
    args = parser.parse_args()
    
    # Clean up HTML files from previous runs if requested
    if args.cleanup:
        cleanup_html_files()
        return
    
    # Validate start date for scraping
    if not args.start_date:
        parser.error("--start-date is required when scraping")
    
    logging.info(f"Scraping questions after {args.start_date}")
    logging.info(f"Maximum pages to scrape: {args.max_pages}")
    
    # Always clean up HTML files from previous runs first
    cleanup_html_files()
    
    # Run the scraper
    scraper = ForumScraper(args.start_date, args.max_pages, args.debug, args.keep_html)
    questions = scraper.scrape()
    
    logging.info(f"Found {len(questions)} unanswered questions")
    
    # Write questions to the output file
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(questions, f, indent=4, ensure_ascii=False)
        
    logging.info(f"Results saved to {args.output}")
    
    # Send email report if requested and not skipped
    if (args.email or os.environ.get('AEM_DEFAULT_RECIPIENTS')) and not args.skip_email:
        send_email_report(
            questions=questions,
            start_date=args.start_date,
            recipient_email=args.email,
            smtp_server=args.smtp_server,
            smtp_port=args.smtp_port,
            sender_email=args.sender_email,
            sender_name=args.sender_name,
            display_from=args.display_from,
            password=args.email_password,
            use_ssl=args.use_ssl,
            debug_email=args.debug_email
        )
    
    # Send Slack notification if requested and not skipped
    slack_enabled = args.slack or os.environ.get('AEM_SLACK_ENABLED', '').lower() == 'true'
    if slack_enabled and not args.skip_slack:
        send_slack_notification(
            questions=questions,
            start_date=args.start_date,
            slack_token=args.slack_token,
            slack_channel=args.slack_channel
        )
    
    # Clean up temporary files
    scraper.cleanup()

if __name__ == "__main__":
    main() 