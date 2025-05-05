import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import random
import csv
import os

def generate_job_data(num_entries=50):
    """
    Generate sample job posting data that matches the expected schema for the application.
    
    Args:
        num_entries: Number of job postings to generate
        
    Returns:
        DataFrame containing generated job data
    """
    # Lists for random sampling
    companies = [
        "Google", "Microsoft", "Amazon", "Facebook", "Apple", 
        "Netflix", "Uber", "Airbnb", "Spotify", "Twitter",
        "LinkedIn", "Adobe", "Salesforce", "Oracle", "IBM",
        "Intel", "AMD", "Nvidia", "Square", "Stripe",
        "PayPal", "Shopify", "Twilio", "Slack", "Zoom"
    ]
    
    locations = [
        "San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX",
        "Boston, MA", "Chicago, IL", "Los Angeles, CA", "Denver, CO",
        "Atlanta, GA", "Portland, OR", "Remote", "Hybrid - NYC",
        "Hybrid - SF", "Hybrid - Seattle", "Toronto, Canada",
        "London, UK", "Berlin, Germany", "Singapore"
    ]
    
    job_types = [
        "Frontend", "Backend", "Full-Stack", "DevOps", "Data Engineering",
        "Machine Learning", "Mobile", "QA/Testing", "Other"
    ]
    
    job_titles = {
        "Frontend": ["Frontend Developer", "UI Engineer", "React Developer", "Angular Developer", "Web Developer"],
        "Backend": ["Backend Engineer", "Python Developer", "Java Developer", "Node.js Developer", "API Engineer"],
        "Full-Stack": ["Full Stack Developer", "Full Stack Engineer", "Web Application Developer", "Software Engineer"],
        "DevOps": ["DevOps Engineer", "Site Reliability Engineer", "Cloud Engineer", "Infrastructure Engineer"],
        "Data Engineering": ["Data Engineer", "ETL Developer", "Database Administrator", "Data Architect"],
        "Machine Learning": ["ML Engineer", "AI Researcher", "Data Scientist", "ML Ops Engineer"],
        "Mobile": ["iOS Developer", "Android Developer", "Mobile Engineer", "React Native Developer"],
        "QA/Testing": ["QA Engineer", "Test Automation Engineer", "Quality Assurance Analyst", "Software Tester"],
        "Other": ["Blockchain Developer", "Security Engineer", "Product Manager", "Technical Writer"]
    }
    
    # Generate random dates in the last 6 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    # Create empty lists for each column
    dates = []
    titles = []
    types = []
    companies_list = []
    locations_list = []
    salaries = []
    
    # Generate data
    for _ in range(num_entries):
        # Random date between start_date and end_date
        days_between = (end_date - start_date).days
        random_days = random.randint(0, days_between)
        random_date = start_date + timedelta(days=random_days)
        dates.append(random_date.strftime('%Y-%m-%d'))
        
        # Random job type
        job_type = random.choice(job_types)
        types.append(job_type)
        
        # Random job title that matches the job type
        titles.append(random.choice(job_titles[job_type]))
        
        # Random company
        companies_list.append(random.choice(companies))
        
        # Random location
        locations_list.append(random.choice(locations))
        
        # Random salary (some entries may have no salary)
        if random.random() > 0.3:  # 70% chance to have salary
            base_salary = random.randint(80, 200) * 1000
            salaries.append(f"${base_salary:,}")
        else:
            salaries.append("")
    
    # Create DataFrame
    df = pd.DataFrame({
        'date': dates,
        'job_title': titles,
        'job_type': types,
        'company': companies_list,
        'location': locations_list,
        'salary': salaries
    })
    
    return df

def save_job_data_to_csv(df, filename="job_postings.csv"):
    """
    Save the job data DataFrame to a CSV file
    
    Args:
        df: DataFrame containing job data
        filename: Name of the output CSV file
    """
    df.to_csv(filename, index=False)
    print(f"Job data saved to {filename}")
    return filename

# Main function to generate data and save to CSV
def create_sample_job_data(num_entries=50, filename="job_postings.csv"):
    """
    Generate sample job posting data and save to CSV
    
    Args:
        num_entries: Number of job postings to generate
        filename: Name of the output CSV file
        
    Returns:
        Path to the created CSV file
    """
    df = generate_job_data(num_entries)
    return save_job_data_to_csv(df, filename)

if __name__ == "__main__":
    create_sample_job_data()