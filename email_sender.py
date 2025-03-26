#!/usr/bin/env python3
"""
Email sender module for AEM Forms Question Scraper
Sends email reports with scraped questions
"""

import os
import logging
import smtplib
import random
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

class EmailSender:
    """Email sender class for the AEM Forms Question Scraper"""
    
    def __init__(self, smtp_server=None, smtp_port=None, sender_email=None, sender_name=None, 
                 display_from=None, password=None, use_ssl=False):
        """Initialize the email sender with SMTP settings."""
        self.smtp_server = smtp_server or os.environ.get("AEM_SMTP_SERVER")
        
        # Get SMTP port from args, env, or default to standard ports (465 for SSL, 587 for TLS)
        if smtp_port:
            self.smtp_port = smtp_port
        elif os.environ.get("AEM_SMTP_PORT"):
            self.smtp_port = int(os.environ.get("AEM_SMTP_PORT"))
        else:
            self.smtp_port = 465 if use_ssl else 587
            
        self.sender_email = sender_email or os.environ.get("AEM_SENDER_EMAIL")
        self.sender_name = sender_name or os.environ.get("AEM_SENDER_NAME", "AEM Forms Scraper")
        
        # Display From can be different from sender email (useful for corporate relays)
        self.display_from = display_from or os.environ.get("AEM_DISPLAY_FROM", self.sender_email)
        
        self.password = password or os.environ.get("AEM_EMAIL_PASSWORD")
        self.use_ssl = use_ssl or os.environ.get("AEM_USE_SSL", "").lower() == "true"
        
        # Get recipients (comma-separated lists in env vars)
        self._parse_recipients()
        
        # Validate required settings
        self._validate_settings()
            
    def _parse_recipients(self):
        """Parse recipients from environment variables."""
        # Default recipients
        self.default_recipients = os.environ.get("AEM_DEFAULT_RECIPIENTS", "").split(",")
        self.default_recipients = [email.strip() for email in self.default_recipients if email.strip()]
        
        # CC recipients
        self.cc_recipients = os.environ.get("AEM_CC_RECIPIENTS", "").split(",")
        self.cc_recipients = [email.strip() for email in self.cc_recipients if email.strip()]
        
        # BCC recipients
        self.bcc_recipients = os.environ.get("AEM_BCC_RECIPIENTS", "").split(",")
        self.bcc_recipients = [email.strip() for email in self.bcc_recipients if email.strip()]
        
    def _validate_settings(self):
        """Validate email settings and log warnings for missing settings."""
        missing = []
        if not self.smtp_server:
            missing.append("SMTP server")
        if not self.smtp_port:
            missing.append("SMTP port")
        if not self.sender_email:
            missing.append("Sender email")
        if not self.password:
            missing.append("Email password")
                
        if missing:
            logging.warning(f"Missing email settings: {', '.join(missing)}")
            
    def create_email_html(self, questions, start_date):
        """Create HTML email content with the list of questions."""
        # Get current date and time for the report
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Get sender name for visibility in content
        sender_name = self.sender_name or "AEM Forms Scraper"
        
        # Create email HTML content - matching the structure of the working email
        html = f"""
        <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                    h1 {{ color: #1473E6; }} /* Adobe blue */
                    h2 {{ color: #505050; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
                    .question-link {{ color: #1473E6; text-decoration: none; }}
                    .question-link:hover {{ text-decoration: underline; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th {{ background-color: #f2f2f2; text-align: left; padding: 8px; border: 1px solid #ddd; }}
                    td {{ padding: 8px; border: 1px solid #ddd; }}
                    tr:nth-child(even) {{ background-color: #f9f9f9; }}
                    .footer {{ margin-top: 30px; padding-top: 10px; border-top: 1px solid #ddd; font-size: 0.8em; color: #777; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>AEM Forms Unanswered Questions Report</h1>
                    <p>Report generated on: {now}</p>
                    <p>Found {len(questions)} unanswered questions since {start_date}</p>
        """
        
        if not questions:
            html += """
                    <p>No unanswered questions found in the specified time period.</p>
            """
        else:
            html += """
                    <h2>Questions</h2>
                    <table>
                        <tr>
                            <th>ID</th>
                            <th>Title</th>
                            <th>Author</th>
                            <th>Date</th>
                        </tr>
            """
            
            # Add each question to the email
            for question in questions:
                question_id = question.get("id", "N/A")
                title = question.get("title", "Untitled Question")
                url = question.get("url", "#")
                author = question.get("author", "Unknown Author")
                date = question.get("date", "Unknown Date")
                
                html += f"""
                        <tr>
                            <td>{question_id}</td>
                            <td><a class="question-link" href="{url}">{title}</a></td>
                            <td>{author}</td>
                            <td>{date}</td>
                        </tr>
                """
            
            html += """
                    </table>
            """
        
        # Add footer matching the structure of the working email
        html += """
                    <div class="footer">
                        <p>This is an automated report from the AEM Forms Question Scraper.</p>
                        <p>For questions or issues, please contact the administrator.</p>
                    </div>
                </div>
            </body>
        </html>
        """
        
        return html
        
    def send_email(self, recipient_email=None, questions=None, start_date=None):
        """Send an email with the list of questions."""
        if not questions:
            logging.warning("No questions to send in the email report")
            return False
            
        if not start_date:
            start_date = "unknown date"
            
        # Determine TO recipients - use specified, fall back to default
        to_recipients = []
        if recipient_email:
            to_recipients.append(recipient_email)
        if not to_recipients and self.default_recipients:
            to_recipients.extend(self.default_recipients)
            
        if not to_recipients and not self.cc_recipients and not self.bcc_recipients:
            logging.error("No recipients specified for email report")
            return False
            
        # Validate required email settings
        if not self.smtp_server or not self.smtp_port or not self.sender_email or not self.password:
            logging.error("Missing required email settings")
            return False
            
        # Create a simpler email with both plain text and HTML parts
        msg = MIMEMultipart("alternative")
        
        # Get sender information
        from_name = self.sender_name or "AEM Forms Scraper"
        from_address = self.display_from or self.sender_email
        
        # Create dynamic subject line to help prevent spam filtering
        current_date = datetime.now().strftime("%m%d")
        
        # Add a random element - first create a hash of the timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_hash = hashlib.md5(timestamp.encode()).hexdigest()[:5]
        
        # Format: "AEM Forms Forums: Unanswered Questions (count) [date-hash]"
        subject = f"AEM Forms Forums: Unanswered Questions ({len(questions)}) [{current_date}-{random_hash}]"
        msg["Subject"] = subject
        logging.info(f"Using dynamic subject: {subject}")
        
        # Use display_from parameter for visible From address
        msg["From"] = f"{from_name} <{from_address}>"
        
        # Add sender identification to ensure visibility
        msg["Sender"] = f"{from_name} <{from_address}>"
        
        # Adobe-specific header that might help
        if "adobe.com" in self.smtp_server:
            msg["X-Adobe-Sender"] = self.sender_email
            
        # Create return-path for reply chain
        msg["Return-Path"] = self.sender_email
        
        # Add recipients
        if to_recipients:
            msg["To"] = ", ".join(to_recipients)
        if self.cc_recipients:
            msg["Cc"] = ", ".join(self.cc_recipients)
        
        # Set reply-to
        msg["Reply-To"] = self.sender_email
        
        # Create minimal headers for corporate email
        msg["Date"] = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
        msg["Message-ID"] = f"<aemforms{datetime.now().strftime('%Y%m%d%H%M%S')}@{self.smtp_server.split('.')[0]}>"
        
        # Create plain text version first (will be shown if HTML fails)
        plain_text = f"""
FROM: {from_name}
SUBJECT: AEM Forms Forums: Unanswered Questions

Report Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Questions Since: {start_date}
Questions Found: {len(questions)}
Report ID: {random_hash}

"""
        # Add questions to plain text if there are any
        if questions:
            plain_text += "QUESTIONS:\n\n"
            for idx, question in enumerate(questions, 1):
                title = question.get("title", "Untitled Question")
                url = question.get("url", "#")
                author = question.get("author", "Unknown Author")
                date = question.get("date", "Unknown Date")
                plain_text += f"{idx}. {title}\n   By: {author} on {date}\n   URL: {url}\n\n"
                
        plain_text += "This is an automated report from the AEM Forms Question Scraper."
        
        # Attach plain text part first (fallback)
        text_part = MIMEText(plain_text, "plain")
        msg.attach(text_part)
        
        # Create HTML email content
        html_content = self.create_email_html(questions, start_date)
        html_part = MIMEText(html_content, "html")
        msg.attach(html_part)
        
        try:
            # Combine all recipients for sending
            all_recipients = to_recipients + self.cc_recipients + self.bcc_recipients
            
            # Create SMTP connection using SSL or TLS based on configuration
            if self.use_ssl:
                logging.info(f"Connecting to SMTP server {self.smtp_server}:{self.smtp_port} using SSL")
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port)
            else:
                logging.info(f"Connecting to SMTP server {self.smtp_server}:{self.smtp_port} using TLS")
                server = smtplib.SMTP(self.smtp_server, self.smtp_port)
                server.ehlo()
                server.starttls()
                server.ehlo()
                
            # Login and send email
            server.login(self.sender_email, self.password)
            
            # Simple send - avoiding complex customizations that might trigger spam
            server.send_message(msg, from_addr=self.sender_email, to_addrs=all_recipients)
            server.quit()
            
            logging.info(f"Email sent successfully to {len(all_recipients)} recipients")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send email: {str(e)}")
            return False 