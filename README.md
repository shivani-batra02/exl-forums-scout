# AEM Forms Forum Scraper

This utility scrapes unanswered questions from the Adobe Experience Manager Forms forum on Adobe Experience League Communities.

## Features

- Scrapes unanswered questions from the AEM Forms forum
- Filters questions by date
- Collects title, author, date, content preview, and other metadata
- Supports pagination
- Saves results to a JSON file
- Automatically cleans up temporary files
- Sends email reports with formatted question listings

## Requirements

- Python 3.7+
- Required packages: `requests`, `beautifulsoup4`, `python-dotenv`

## Installation

1. Clone this repository or download the source code.
2. Create a virtual environment (recommended):

```bash
python -m venv aem_env
source aem_env/bin/activate  # On Windows: aem_env\Scripts\activate
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

Run the scraper with the minimal required options:

```bash
python scraper.py --start-date 2024-12-01
```

This will scrape 10 pages of questions from December 1, 2024, and save them to `questions.json`.

### Common Options

Customize output file and number of pages:

```bash
python scraper.py --start-date 2024-12-01 --output aem_questions.json --max-pages 20
```

### Debugging

Enable debug mode to save HTML files for inspection:

```bash
# Save and keep HTML files for debugging
python scraper.py --start-date 2024-12-01 --debug --keep-html

# Only clean up HTML files from previous runs
python scraper.py --cleanup
```

### Email Notifications

Send email reports after scraping:

```bash
# Basic email with command line parameters
python scraper.py --start-date 2024-12-01 --email user@example.com --smtp-server smtp.gmail.com --sender-email sender@gmail.com --email-password mypassword

# Using SSL instead of TLS
python scraper.py --start-date 2024-12-01 --email user@example.com --use-ssl

# Using environment variables for SMTP settings
python scraper.py --start-date 2024-12-01 --email user@example.com
```

### Full Command Reference

```bash
python scraper.py --start-date YYYY-MM-DD [--output FILENAME] [--max-pages N] [--debug] [--keep-html] [--cleanup]
                  [--email EMAIL] [--smtp-server SERVER] [--smtp-port PORT] 
                  [--sender-email EMAIL] [--sender-name NAME] [--email-password PASSWORD]
                  [--use-ssl] [--skip-email]
```

### Arguments:

#### Scraping Options:

- `--start-date`: Only include questions posted after this date (required, format: YYYY-MM-DD)
- `--output`: Output JSON file name (default: questions.json)
- `--max-pages`: Maximum number of pages to scrape (default: 10)
- `--debug`: Enable debug mode (saves downloaded HTML to files)
- `--keep-html`: Keep HTML files after scraping (only applies in debug mode)
- `--cleanup`: Only clean up HTML files from previous runs without scraping

#### Email Options:

- `--email`: Send email report to this address (optional if default recipients configured)
- `--smtp-server`: SMTP server address (or set AEM_SMTP_SERVER env var)
- `--smtp-port`: SMTP server port (or set AEM_SMTP_PORT env var)
- `--sender-email`: Sender email address (or set AEM_SENDER_EMAIL env var)
- `--sender-name`: Sender name (or set AEM_SENDER_NAME env var)
- `--email-password`: Email password (or set AEM_EMAIL_PASSWORD env var)
- `--use-ssl`: Use SSL instead of TLS (or set AEM_USE_SSL=true)
- `--skip-email`: Skip sending email even if --email is provided

## Email Configuration

Email notifications can be configured in three ways:

1. **Command line arguments:** Provide SMTP settings directly via command line
2. **Environment variables:** Set the environment variables with your SMTP settings
3. **.env file:** Create a `.env` file with your SMTP settings (a template is provided)

The following settings can be configured:
   - `AEM_SMTP_SERVER`: SMTP server address
   - `AEM_SMTP_PORT`: SMTP server port (default: 587 for TLS, 465 for SSL)
   - `AEM_SENDER_EMAIL`: Sender email address
   - `AEM_SENDER_NAME`: Sender name (displayed in email clients)
   - `AEM_EMAIL_PASSWORD`: Email password or app password
   - `AEM_USE_SSL`: Set to "true" to use SSL instead of TLS
   - `AEM_DEFAULT_RECIPIENTS`: Comma-separated list of default email recipients (To: field)
   - `AEM_CC_RECIPIENTS`: Comma-separated list of CC recipients
   - `AEM_BCC_RECIPIENTS`: Comma-separated list of BCC recipients

### Using .env File

1. Copy the `.env.template` file to `.env` in the same directory
2. Edit the `.env` file with your SMTP settings
3. The script will automatically load these settings when run

### Using Gmail

If using Gmail as your SMTP provider:
1. Use `smtp.gmail.com` as the SMTP server
2. Use port 587 for TLS (default) or 465 for SSL
3. Enable 2-factor authentication and create an app password
4. Use your Gmail address as the sender and the app password instead of your regular password

### Email Format

The email report includes:
- Summary of scraped questions
- Each question with title, author, date, content preview, and stats
- Clickable links to the original questions
- Clean formatting in both HTML and plain text formats

## Output Format

The script produces a JSON file with an array of question objects. Each question contains the following fields:

- `id`: Question ID
- `title`: Question title
- `url`: URL to the question
- `author`: Username of the author
- `date`: Publication date (YYYY-MM-DD format)
- `content`: Preview of the question content
- `views`: Number of views
- `likes`: Number of likes
- `replies`: Number of replies
- `topics`: Array of topic tags

## File Management

The script handles temporary files as follows:

- HTML files from previous runs are automatically cleaned up before each new run
- When debug mode is enabled, HTML files of each page are saved for inspection
- By default, these files are deleted after successful scraping
- Use `--keep-html` to preserve the HTML files after scraping
- Use `--cleanup` to remove HTML files without running the scraper

## Troubleshooting

If you encounter issues:

1. Enable debug mode with the `--debug` flag to save the HTML content to files for inspection
2. Use `--keep-html` to preserve the HTML files for further analysis
3. Check your internet connection and proxy settings
4. Make sure the forum structure hasn't changed
5. For email issues, verify your SMTP settings and try sending to a different email address

## Running as a Scheduled Task

To run the scraper regularly and receive email notifications:

### Using cron (Linux/Mac):

```bash
# Run daily at 8 AM and save logs
0 8 * * * cd /path/to/aem_scraper && source aem_env/bin/activate && python scraper.py --start-date $(date -d "7 days ago" +\%Y-\%m-\%d) --email your@email.com > /path/to/logs/scraper_$(date +\%Y\%m\%d).log 2>&1
```

### Using Task Scheduler (Windows):

Create a batch file (run_scraper.bat) with:

```batch
@echo off
cd /d D:\path\to\aem_scraper
call aem_env\Scripts\activate
python scraper.py --start-date 2024-12-01 --email your@email.com
```

Then schedule this batch file to run at your desired interval using Windows Task Scheduler.

## License

MIT 

## Security and Sensitive Information

This project uses environment variables to handle sensitive information like email credentials and Slack tokens.

### Setup for Development

1. Copy `.env.template` to `.env` in your local directory:
   ```bash
   cp .env.template .env
   ```

2. Edit the `.env` file with your actual credentials:
   ```
   AEM_SENDER_EMAIL=your-actual-email@company.com
   AEM_SMTP_SERVER=your-actual-smtp-server
   AEM_EMAIL_PASSWORD=your-actual-password
   AEM_SLACK_TOKEN=your-actual-slack-token
   ```

3. The `.env` file is included in `.gitignore` to prevent committing sensitive information.

### Important Security Notes

- **NEVER** commit your `.env` file with actual credentials
- **NEVER** hardcode credentials in the Python files
- Use the `.env.template` as a reference for required environment variables
- For CI/CD pipelines, use secret management features of your platform 

## Jenkins Deployment

The project includes a Jenkinsfile for easy deployment to Jenkins. To deploy to Jenkins:

1. Ensure your code is in a Git repository accessible by Jenkins.

2. In Jenkins:
   - Create a new Pipeline job
   - Configure "Pipeline script from SCM" and select your Git repository
   - Keep "Script Path" as "Jenkinsfile"

3. The pipeline accepts these parameters:
   - `START_DATE`: Date to start scraping from (format: YYYY-MM-DD, default: 2024-12-01)
   - `MAX_PAGES`: Maximum number of pages to scrape (default: 20)

4. Environment variables:
   - Add all required environment variables from `.env.template` as parameters in Jenkins
   - All variables starting with `AEM_` will be included in the .env file during execution

5. Run the job:
   - Click "Build with Parameters" to customize the run
   - The pipeline will install dependencies, run the scraper, and archive the results 