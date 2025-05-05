# Software Engineering Job Market Analytics Platform

A comprehensive Streamlit-based analytics platform for tracking, analyzing, and visualizing software engineering job market trends. This platform provides deep insights into hiring patterns, salary trends, skill demands, and career progression paths across the tech industry.

## Key Features

- **Comprehensive Market Analysis**: Track job market health indicators, growth rates, and regional differences
- **Diverse Job Data**: Coverage across various company types (big tech, startups, mid-sized, consulting, non-tech, educational) and geographical regions
- **Interactive Visualizations**: 20+ advanced visualizations with filtering capabilities and drill-down analysis
- **Career Development Tools**: Interview difficulty tracking, compensation benchmarking, and career path visualization
- **Personalized Job Alerts**: Create customized job alerts based on skills, companies, and locations
- **Resume Analysis**: AI-powered resume analysis and skill gap identification
- **Data Integration Options**: PostgreSQL database for persistent storage, CSV import/export, and manual data entry
- **Error Handling**: Robust error handling and fallback mechanisms for data processing

## Advanced Analytics Features

The platform includes multiple specialized analytics modules:

### Market Intelligence
- **Market Health Analysis**: Composite index of job market health with trend analysis
- **Predictive Analytics**: ML-powered job market forecasting with growth trends
- **Geographical Distribution**: Regional job market analysis and visualization

### Career Insights
- **Interview Difficulty Tracker**: Company-specific interview complexity analysis
- **Compensation Benchmarking**: Detailed salary analysis with cost-of-living adjustments
- **Career Path Visualization**: Progression paths and skill requirements for different roles
- **Job Application Tracking**: Monitor application status and outcomes

### Company Analysis
- **Company Hiring Patterns**: Detect hiring surges and slowdowns
- **Company Growth Rates**: Analyze company expansion by job postings
- **Company Comparison**: Side-by-side analysis of hiring practices

### Skill Analytics
- **Skill Demand Trends**: Track emerging and declining skill requirements
- **Skill Clusters**: Identify related skills frequently requested together
- **Technology Adoption**: Monitor adoption rates of new technologies

## Job Categories

The application categorizes software engineering positions into these job types:

- Frontend Development
- Backend Development
- Full-Stack Development
- DevOps & SRE
- Data Engineering
- Machine Learning & AI
- Mobile Development
- QA/Testing
- Cybersecurity
- Game Development
- Embedded Systems
- AR/VR Development
- Technical Writing
- Product Management
- Security Engineering
- Other specialized roles

## Getting Started

1. Launch the application: `streamlit run app.py`
2. Access the application in your browser at http://localhost:5000
3. Upload existing job data or use the sample data generation tools

## Data Management

- **Multiple Data Sources**: Upload CSV files, connect to APIs, or use web scraping (with appropriate credentials)
- **Sample Data Generation**: Generate diverse sample datasets with `python generate_diverse_data.py`
- **PostgreSQL Integration**: Persistent data storage with robust database connection

## Data Format

Job posting data should include these fields:
- `date`: Posting date (YYYY-MM-DD)
- `job_title`: Title of the position
- `job_type`: Category/type of the job
- `company`: Company name
- `location`: Job location
- `salary`: Compensation information (when available)

Additional fields for advanced analytics:
- `skills_required`: Technical skills required
- `experience_level`: Years of experience required
- `education`: Education requirements
- `benefits`: Benefits offered
- `remote_options`: Remote work policies

## Requirements

- Python 3.8+
- Streamlit
- Pandas
- Plotly
- NumPy
- scikit-learn
- SQLAlchemy
- PostgreSQL
- BeautifulSoup4
- Trafilatura (for web scraping)
- Twilio (for notifications)

## Project Structure

- `app.py`: Main Streamlit application
- `utils/`: Module directory
  - `data_processor.py`: Data cleaning and processing
  - `database.py`: Database integration
  - `visualizer.py`: Visualization functions
  - `predictor.py`: ML prediction models
  - `salary_analyzer.py`: Compensation analysis
  - `job_comparator.py`: Job comparison tools
  - `skill_tracker.py`: Skill demand analysis
  - `company_analyzer.py`: Company hiring patterns
  - `market_health.py`: Market health indicators
  - `live_data.py`: Live data fetching
  - `resume_analyzer.py`: Resume analysis
  - `interview_tracker.py`: Interview difficulty analysis
  - `job_alerts.py`: Personalized job alerts
- `generate_diverse_data.py`: Sample data generation script
- `init_database.py`: Database initialization

## Recent Updates

- Added unique chart element keys to prevent duplicate ID errors
- Improved error handling in data processing pipelines
- Fixed column name issues in experience-based progression visualization
- Enhanced data type conversion reliability throughout the application
- Added fallback mechanisms for robust operation with diverse datasets

## License

This project is open source and available under the MIT License.