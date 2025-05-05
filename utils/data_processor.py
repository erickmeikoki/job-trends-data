import pandas as pd
import numpy as np
from datetime import datetime

def process_data(df):
    """
    Process and clean the job posting data.
    
    Args:
        df: Pandas DataFrame containing job posting data
        
    Returns:
        Processed DataFrame
    """
    # Make a copy to avoid modifying the original
    processed_df = df.copy()
    
    # Ensure required columns exist
    required_cols = ['date', 'job_title', 'job_type', 'company', 'location']
    for col in required_cols:
        if col not in processed_df.columns:
            raise ValueError(f"Required column '{col}' missing from data")
    
    # Convert date to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(processed_df['date']):
        processed_df['date'] = pd.to_datetime(processed_df['date'], errors='coerce')
    
    # Drop rows with missing dates
    processed_df = processed_df.dropna(subset=['date'])
    
    # Standardize job type categories
    if 'job_type' in processed_df.columns:
        # Mapping to standardize job type categories
        job_type_mapping = {
            'front end': 'Frontend',
            'frontend': 'Frontend',
            'front-end': 'Frontend',
            'back end': 'Backend',
            'backend': 'Backend',
            'back-end': 'Backend',
            'full stack': 'Full-Stack',
            'fullstack': 'Full-Stack',
            'full-stack': 'Full-Stack',
            'devops': 'DevOps',
            'dev ops': 'DevOps',
            'dev-ops': 'DevOps',
            'data engineer': 'Data Engineering',
            'data engineering': 'Data Engineering',
            'machine learning': 'Machine Learning',
            'ml': 'Machine Learning',
            'ai': 'Machine Learning',
            'artificial intelligence': 'Machine Learning',
            'qa': 'QA/Testing',
            'quality assurance': 'QA/Testing',
            'testing': 'QA/Testing',
            'mobile': 'Mobile',
            'ios': 'Mobile',
            'android': 'Mobile',
            'qa/testing': 'QA/Testing'
        }
        
        # Apply mapping (case-insensitive)
        processed_df['job_type'] = processed_df['job_type'].str.lower().map(
            lambda x: next((v for k, v in job_type_mapping.items() if k in str(x).lower()), 
                          'Other' if pd.notna(x) else x)
        )
    
    # Ensure all text columns are strings
    text_cols = ['job_title', 'company', 'location', 'job_type']
    for col in text_cols:
        if col in processed_df.columns:
            processed_df[col] = processed_df[col].astype(str)
    
    # Add month and year columns for easier analysis
    processed_df['month'] = processed_df['date'].dt.month
    processed_df['year'] = processed_df['date'].dt.year
    processed_df['month_year'] = processed_df['date'].dt.strftime('%Y-%m')
    
    # Sort by date
    processed_df = processed_df.sort_values('date')
    
    return processed_df

def generate_sample_schema():
    """
    Generate a sample schema to guide users on the expected data format.
    
    Returns:
        String containing sample CSV format
    """
    sample = """date,job_title,job_type,company,location,salary
2023-01-15,Frontend Developer,Frontend,Tech Company Inc.,New York,120000
2023-01-20,Backend Engineer,Backend,Software Solutions LLC,San Francisco,130000
2023-02-05,Full Stack Developer,Full-Stack,StartupXYZ,Remote,110000
2023-02-10,DevOps Engineer,DevOps,Enterprise Tech Corp.,Seattle,140000
2023-03-01,ML Engineer,Machine Learning,AI Innovations,Boston,150000"""
    
    return sample
