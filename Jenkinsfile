pipeline {
    agent any
    
    options {
        timeout(time: 30, unit: 'MINUTES')
        disableConcurrentBuilds()
    }
    
    parameters {
        string(name: 'START_DATE', defaultValue: '2024-12-01', description: 'Start date for scraping questions (YYYY-MM-DD)')
        string(name: 'MAX_PAGES', defaultValue: '20', description: 'Maximum number of pages to scrape')
    }
    
    stages {
        stage('Setup') {
            steps {
                sh '''
                    # Try to upgrade pip first
                    python3 -m pip install --upgrade pip --user || true
                    
                    # Install dependencies with trusted hosts
                    python3 -m pip install -r requirements.txt --user --trusted-host pypi.org --trusted-host files.pythonhosted.org
                '''
            }
        }
        
        stage('Setup Environment') {
            steps {
                script {
                    // Create .env file from Jenkins environment variables
                    sh '''
                        # Create .env file from job parameters
                        env | grep "AEM_" > .env
                        cat .env
                    '''
                }
            }
        }
        
        stage('Run Scraper') {
            steps {
                script {
                    def timestamp = new Date().format('yyyyMMdd_HHmmss')
                    def startDate = params.START_DATE
                    def maxPages = params.MAX_PAGES
                    
                    // Build command based on parameters
                    def scraperCmd = """
                        python3 scraper.py \\
                            --output questions_${timestamp}.json \\
                            --max-pages ${maxPages}
                    """
                    
                    // Add start date parameter only if provided
                    if (startDate && !startDate.trim().isEmpty()) {
                        scraperCmd = """
                            python3 scraper.py \\
                                --start-date ${startDate} \\
                                --output questions_${timestamp}.json \\
                                --max-pages ${maxPages}
                        """
                    }
                    
                    sh scraperCmd
                }
            }
        }
        
        stage('Archive Results') {
            steps {
                archiveArtifacts artifacts: 'questions_*.json', fingerprint: true
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        
        success {
            echo 'Successfully scraped AEM Forms questions!'
        }
        
        failure {
            echo 'Failed to scrape AEM Forms questions!'
        }
    }
} 