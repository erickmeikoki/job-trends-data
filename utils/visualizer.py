import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import re

def plot_jobs_by_month(df):
    """
    Create a bar chart showing job postings by month.
    
    Args:
        df: Processed DataFrame containing job posting data
        
    Returns:
        Plotly figure object
    """
    # Group by month_year and count
    monthly_counts = df.groupby('month_year').size().reset_index(name='count')
    
    # Sort chronologically
    monthly_counts['month_year_dt'] = pd.to_datetime(monthly_counts['month_year'])
    monthly_counts = monthly_counts.sort_values('month_year_dt')
    
    # Create the plot
    fig = px.bar(
        monthly_counts, 
        x='month_year', 
        y='count',
        labels={'month_year': 'Month', 'count': 'Number of Job Postings'},
        title='Job Postings by Month',
        text='count'
    )
    
    # Improve layout
    fig.update_layout(
        xaxis_title='Month',
        yaxis_title='Number of Job Postings',
        xaxis={'categoryorder': 'array', 'categoryarray': monthly_counts['month_year'].tolist()}
    )
    
    # Add data labels on top of bars
    fig.update_traces(textposition='outside')
    
    return fig

def plot_jobs_by_type(df):
    """
    Create a pie chart showing distribution of job postings by job type.
    
    Args:
        df: Processed DataFrame containing job posting data
        
    Returns:
        Plotly figure object
    """
    # Count by job type
    type_counts = df['job_type'].value_counts().reset_index()
    type_counts.columns = ['job_type', 'count']
    
    # Create the plot
    fig = px.pie(
        type_counts, 
        values='count', 
        names='job_type',
        title='Job Postings by Type',
        hole=0.4,  # Donut chart
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    
    # Improve layout
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hoverinfo='label+percent+value'
    )
    
    return fig

def plot_jobs_trend(df):
    """
    Create a line chart showing job posting trends over time by job type.
    
    Args:
        df: Processed DataFrame containing job posting data
        
    Returns:
        Plotly figure object
    """
    # Group by month and job type
    trend_data = df.groupby(['month_year', 'job_type']).size().reset_index(name='count')
    
    # Create datetime for proper ordering
    trend_data['month_year_dt'] = pd.to_datetime(trend_data['month_year'])
    trend_data = trend_data.sort_values('month_year_dt')
    
    # Create the plot
    fig = px.line(
        trend_data, 
        x='month_year', 
        y='count', 
        color='job_type',
        markers=True,
        labels={'month_year': 'Month', 'count': 'Number of Job Postings', 'job_type': 'Job Type'},
        title='Job Posting Trends by Type'
    )
    
    # Improve layout
    fig.update_layout(
        xaxis_title='Month',
        yaxis_title='Number of Job Postings',
        legend_title='Job Type',
        xaxis={'categoryorder': 'array', 'categoryarray': trend_data['month_year'].unique().tolist()}
    )
    
    return fig

def plot_company_distribution(df):
    """
    Create a horizontal bar chart showing top companies by job postings.
    
    Args:
        df: Processed DataFrame containing job posting data
        
    Returns:
        Plotly figure object
    """
    # Count by company and get top 15
    company_counts = df['company'].value_counts().reset_index()
    company_counts.columns = ['company', 'count']
    
    # Take top 15 companies or all if less than 15
    top_n = min(15, len(company_counts))
    top_companies = company_counts.head(top_n)
    
    # Sort for visualization
    top_companies = top_companies.sort_values('count')
    
    # Create the plot
    fig = px.bar(
        top_companies, 
        y='company', 
        x='count',
        orientation='h',
        labels={'company': 'Company', 'count': 'Number of Job Postings'},
        title=f'Top {top_n} Companies by Job Postings',
        text='count'
    )
    
    # Improve layout
    fig.update_layout(
        yaxis_title='Company',
        xaxis_title='Number of Job Postings',
        height=max(400, top_n * 25)  # Adjust height based on number of companies
    )
    
    # Add data labels
    fig.update_traces(textposition='outside')
    
    return fig

def extract_region(location):
    """
    Extract region from location string for geographical grouping.
    
    Args:
        location: Location string from job posting
        
    Returns:
        Region category for geographical analysis
    """
    # Define region patterns
    us_regions = {
        'US West': ['San Francisco', 'Los Angeles', 'Seattle', 'Portland', 'Denver', 'Phoenix', 'Salt Lake City', 'CA', 'WA', 'OR', 'CO', 'AZ', 'UT', 'NV'],
        'US East': ['New York', 'Boston', 'Atlanta', 'Miami', 'Raleigh', 'Washington', 'Philadelphia', 'NY', 'MA', 'GA', 'FL', 'NC', 'DC', 'PA', 'VA'],
        'US Central': ['Chicago', 'Austin', 'Dallas', 'Minneapolis', 'Detroit', 'Nashville', 'TX', 'IL', 'MN', 'MI', 'TN'],
    }
    
    regions = {
        'Remote': ['Remote'],
        'Hybrid': ['Hybrid'],
        'North America': ['Canada', 'Toronto', 'Vancouver', 'Montreal'],
        'Europe': ['UK', 'London', 'Manchester', 'Berlin', 'Munich', 'Amsterdam', 'Paris', 'Dublin', 'Ireland', 'Germany', 'France', 'Netherlands'],
        'Asia': ['Singapore', 'Tokyo', 'Bangalore', 'Hyderabad', 'Seoul', 'Hong Kong', 'India', 'Japan', 'South Korea'],
        'Australia': ['Sydney', 'Melbourne', 'Australia']
    }
    
    # Add US regions to the regions dictionary
    regions.update(us_regions)
    
    # Check if location matches any region pattern
    location = str(location).lower()
    for region, patterns in regions.items():
        for pattern in patterns:
            if pattern.lower() in location:
                return region
    
    # Default region if no match found
    return 'Other'

def plot_geographical_distribution(df):
    """
    Create a bar chart showing job posting distribution by region.
    
    Args:
        df: Processed DataFrame containing job posting data
        
    Returns:
        Plotly figure object
    """
    # Create a copy to avoid modifying the original dataframe
    geo_df = df.copy()
    
    # Extract region from location
    geo_df['region'] = geo_df['location'].apply(extract_region)
    
    # Group by region and count
    region_counts = geo_df['region'].value_counts().reset_index()
    region_counts.columns = ['region', 'count']
    
    # Sort by count for better visualization
    region_counts = region_counts.sort_values('count', ascending=False)
    
    # Create the bar chart
    fig = px.bar(
        region_counts,
        x='region',
        y='count',
        color='count',
        labels={'region': 'Region', 'count': 'Number of Job Postings'},
        title='Geographical Distribution of Job Postings',
        text='count',
        color_continuous_scale='Viridis'
    )
    
    fig.update_layout(
        xaxis_title='Region',
        yaxis_title='Number of Job Postings',
        xaxis={'categoryorder': 'total descending'}
    )
    
    # Add data labels
    fig.update_traces(textposition='outside')
    
    return fig

def plot_location_type_distribution(df):
    """
    Create a stacked bar chart showing job types by location type
    (Remote, Hybrid, On-site).
    
    Args:
        df: Processed DataFrame containing job posting data
        
    Returns:
        Plotly figure object
    """
    # Create a copy to avoid modifying the original dataframe
    loc_df = df.copy()
    
    # Categorize location types
    def categorize_location(location):
        location = str(location).lower()
        if 'remote' in location:
            return 'Remote'
        elif 'hybrid' in location:
            return 'Hybrid'
        else:
            return 'On-site'
    
    loc_df['location_type'] = loc_df['location'].apply(categorize_location)
    
    # Group by location type and job type
    location_job_counts = loc_df.groupby(['location_type', 'job_type']).size().reset_index(name='count')
    
    # Create the stacked bar chart
    fig = px.bar(
        location_job_counts,
        x='location_type',
        y='count',
        color='job_type',
        labels={'location_type': 'Location Type', 'count': 'Number of Job Postings', 'job_type': 'Job Type'},
        title='Job Types by Location Type',
        color_discrete_sequence=px.colors.qualitative.Safe
    )
    
    fig.update_layout(
        xaxis_title='Location Type',
        yaxis_title='Number of Job Postings',
        legend_title='Job Type',
        barmode='stack'
    )
    
    return fig
