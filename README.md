# Software Engineering Job Tracker

A Streamlit-based dashboard application that tracks and visualizes software engineering job postings by type and month, offering insights into job market trends.

## Features

- **Diverse Job Data**: Track job postings across various company types (big tech, startups, mid-sized, consulting, non-tech, educational) and locations
- **Interactive Visualizations**: Multiple charts showing job posting trends over time, distribution by job type, and company hiring patterns
- **Data Filtering**: Filter job postings by date range, job type, and company
- **Database Integration**: PostgreSQL database for persistent data storage
- **CSV Upload/Download**: Import and export job posting data
- **Manual Data Entry**: Add individual job postings directly through the UI

## Job Types Tracked

The application categorizes software engineering positions into these job types:

- Frontend
- Backend
- Full-Stack
- DevOps
- Data Engineering
- Machine Learning
- Mobile
- QA/Testing
- Cybersecurity
- Game Development
- Embedded Systems
- AR/VR
- Other specialized roles

## Getting Started

1. Launch the application: `streamlit run app.py`
2. Access the application in your browser at http://localhost:5000

## Data Management

- **Upload Data**: Use the CSV upload feature to import job posting data
- **Generate Sample Data**: Run `python generate_diverse_data.py` to create sample job postings
- **Database Management**: The application connects to a PostgreSQL database

## Adding Job Postings

Job postings can be added in three ways:
1. Upload a CSV file
2. Add individual jobs through the UI form
3. Generate sample data using the included scripts

## Data Format

The CSV file should have the following columns:
- `date`: Posting date (YYYY-MM-DD)
- `job_title`: Title of the job posting
- `job_type`: Category/type of the job
- `company`: Company name
- `location`: Job location
- `salary`: Optional salary information

## Visualizations

1. **Monthly Trends**: Bar chart showing job postings by month
2. **Job Types**: Pie chart showing distribution of job types
3. **Time Series Analysis**: Line chart showing trends over time by job type
4. **Company Distribution**: Bar chart showing top companies by number of job postings

## Requirements

- Python 3.6+
- Streamlit
- Pandas
- Plotly
- SQLAlchemy
- PostgreSQL (for database integration)

## Project Structure

- `app.py`: Main Streamlit application
- `utils/`: Helper modules
  - `data_processor.py`: Data cleaning and processing functions
  - `visualizer.py`: Visualization functions
  - `database.py`: Database integration
  - `job_scraper.py`: Sample data generation
- `generate_diverse_data.py`: Script to generate diverse sample data
- `init_database.py`: Script to initialize the database

## License

This project is open source and available under the MIT License.