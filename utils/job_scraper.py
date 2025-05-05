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
        # Big Tech
        "Google", "Microsoft", "Amazon", "Meta", "Apple", 
        "Netflix", "Uber", "Airbnb", "Spotify", "Twitter",
        
        # Startups & Growing Companies
        "Notion", "Figma", "Canva", "Airtable", "Vercel",
        "Retool", "Loom", "Calendly", "Zapier", "Pitch",
        
        # Mid-sized Tech
        "Atlassian", "Datadog", "MongoDB", "GitLab", "Elastic",
        "Cloudflare", "Confluent", "Databricks", "HashiCorp", "Twilio",
        
        # Consulting/Agency
        "Thoughtworks", "Slalom", "Accenture", "Deloitte Digital", "EPAM",
        "Cognizant", "Capgemini", "Wipro", "Infosys", "Tata Consultancy",
        
        # Non-Tech Companies with Tech Roles
        "Capital One", "JPMorgan Chase", "Bank of America", "Walmart Labs", "Target Tech",
        "Home Depot Tech", "CVS Health Tech", "Disney Streaming", "Comcast", "NBC Universal",

        # Educational/Public
        "EdX", "Coursera", "Khan Academy", "NASA", "USDS",
        "18F", "Code for America", "Wikimedia", "Mozilla", "Digital Ocean"
    ]
    
    locations = [
        # US Tech Hubs
        "San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX",
        "Boston, MA", "Chicago, IL", "Los Angeles, CA", "Denver, CO",
        "Atlanta, GA", "Portland, OR", 
        
        # Remote/Hybrid
        "Remote", "Hybrid - NYC", "Hybrid - SF", "Hybrid - Seattle", 
        "Hybrid - Chicago", "Hybrid - Austin", "Remote - US Only", "Remote - Worldwide",
        
        # International
        "Toronto, Canada", "Vancouver, Canada", "Montreal, Canada",
        "London, UK", "Manchester, UK", "Berlin, Germany", "Munich, Germany",
        "Amsterdam, Netherlands", "Paris, France", "Dublin, Ireland", 
        
        # Asia/Pacific
        "Singapore", "Tokyo, Japan", "Sydney, Australia", "Melbourne, Australia",
        "Bangalore, India", "Hyderabad, India", "Seoul, South Korea", "Hong Kong",
        
        # Emerging Tech Hubs
        "Raleigh, NC", "Nashville, TN", "Salt Lake City, UT", "Miami, FL",
        "Detroit, MI", "Phoenix, AZ", "Minneapolis, MN", "Dallas, TX"
    ]
    
    job_types = [
        "Frontend", "Backend", "Full-Stack", "DevOps", "Data Engineering",
        "Machine Learning", "Mobile", "QA/Testing", "Cybersecurity", 
        "Game Development", "Embedded", "AR/VR", "Other"
    ]
    
    job_titles = {
        "Frontend": [
            "Frontend Developer", "UI Engineer", "React Developer", 
            "Angular Developer", "Vue Developer", "Web Developer",
            "UI/UX Developer", "JavaScript Developer", "Frontend Architect"
        ],
        "Backend": [
            "Backend Engineer", "Python Developer", "Java Developer", 
            "Node.js Developer", "API Engineer", "Go Developer",
            "Ruby Developer", "PHP Developer", "C# Developer", ".NET Developer"
        ],
        "Full-Stack": [
            "Full Stack Developer", "Full Stack Engineer", "Web Application Developer", 
            "Software Engineer", "MERN Stack Developer", "MEAN Stack Developer",
            "Ruby on Rails Developer", "Django Developer", "Laravel Developer"
        ],
        "DevOps": [
            "DevOps Engineer", "Site Reliability Engineer", "Cloud Engineer", 
            "Infrastructure Engineer", "Platform Engineer", "Release Engineer",
            "Kubernetes Engineer", "AWS Specialist", "Azure Engineer", "GCP Engineer"
        ],
        "Data Engineering": [
            "Data Engineer", "ETL Developer", "Database Administrator", 
            "Data Architect", "Big Data Engineer", "SQL Developer",
            "Data Pipeline Engineer", "Hadoop Developer", "Spark Engineer"
        ],
        "Machine Learning": [
            "ML Engineer", "AI Researcher", "Data Scientist", "ML Ops Engineer",
            "NLP Engineer", "Computer Vision Engineer", "AI Engineer",
            "Research Scientist", "Deep Learning Engineer", "ML Infrastructure Engineer"
        ],
        "Mobile": [
            "iOS Developer", "Android Developer", "Mobile Engineer", 
            "React Native Developer", "Flutter Developer", "Swift Developer",
            "Kotlin Developer", "Mobile App Developer", "Cross-Platform Developer"
        ],
        "QA/Testing": [
            "QA Engineer", "Test Automation Engineer", "Quality Assurance Analyst", 
            "Software Tester", "SDET", "Test Engineer", "QA Lead",
            "Performance Tester", "Security Tester", "Accessibility Tester"
        ],
        "Cybersecurity": [
            "Security Engineer", "Information Security Analyst", "Penetration Tester",
            "Security Architect", "Application Security Engineer", "Cryptographer",
            "Security Consultant", "SOC Analyst", "Ethical Hacker"
        ],
        "Game Development": [
            "Game Developer", "Game Programmer", "Unity Developer", 
            "Unreal Engine Developer", "Game Engine Developer", "Graphics Programmer",
            "Game AI Programmer", "Physics Programmer", "Game Client Developer"
        ],
        "Embedded": [
            "Embedded Systems Engineer", "Firmware Developer", "IoT Developer",
            "Embedded C/C++ Developer", "RTOS Developer", "Microcontroller Programmer",
            "Hardware Engineer", "FPGA Developer", "Embedded Linux Engineer"
        ],
        "AR/VR": [
            "AR Developer", "VR Developer", "Mixed Reality Engineer", 
            "3D Developer", "Spatial Computing Engineer", "XR Designer",
            "Unity XR Developer", "WebXR Developer", "Metaverse Engineer"
        ],
        "Other": [
            "Blockchain Developer", "Technical Writer", "Product Manager", 
            "Developer Relations", "Developer Advocate", "Technical Support Engineer",
            "Systems Analyst", "Quantum Computing Engineer", "Robotics Engineer",
            "Edge Computing Specialist", "Bioinformatics Developer"
        ]
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