import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re

def extract_salary_value(salary_str):
    """
    Extract numeric salary value from string.
    Handles formats like "$120,000", "120k", etc.
    
    Args:
        salary_str: String containing salary information
        
    Returns:
        Numeric salary value or np.nan if not extractable
    """
    if not salary_str or pd.isna(salary_str) or salary_str == '':
        return np.nan
    
    # Convert to string if not already
    salary_str = str(salary_str)
    
    # Remove currency symbols and commas
    salary_str = salary_str.replace('$', '').replace(',', '').replace(' ', '')
    
    # Handle 'k' for thousands
    if 'k' in salary_str.lower():
        salary_str = salary_str.lower().replace('k', '')
        try:
            return float(salary_str) * 1000
        except ValueError:
            return np.nan
    
    # Extract numeric value using regex
    match = re.search(r'(\d+\.?\d*)', salary_str)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            return np.nan
    
    return np.nan

def extract_salary_range(df):
    """
    Extract min/max salary ranges and convert to numeric values.
    
    Args:
        df: DataFrame containing job posting data with salary column
        
    Returns:
        DataFrame with added min_salary and max_salary columns
    """
    # Create a copy to avoid modifying the original
    processed_df = df.copy()
    
    # If no salary column, return the original dataframe
    if 'salary' not in processed_df.columns:
        return processed_df
    
    # Identify range patterns (e.g., "$80,000 - $120,000", "80k-120k")
    def extract_range(salary_str):
        if not salary_str or pd.isna(salary_str) or salary_str == '':
            return np.nan, np.nan
        
        salary_str = str(salary_str)
        
        # Look for range indicators
        if '-' in salary_str or '–' in salary_str or 'to' in salary_str:
            # Normalize separators
            salary_str = salary_str.replace('–', '-').replace(' to ', '-')
            
            # Split by the separator
            parts = salary_str.split('-')
            if len(parts) >= 2:
                min_val = extract_salary_value(parts[0].strip())
                max_val = extract_salary_value(parts[1].strip())
                return min_val, max_val
        
        # Single value, use as both min and max
        value = extract_salary_value(salary_str)
        return value, value
    
    # Apply the extraction
    results = processed_df['salary'].apply(extract_range)
    processed_df['min_salary'] = results.apply(lambda x: x[0])
    processed_df['max_salary'] = results.apply(lambda x: x[1])
    
    # Calculate average salary for easier analysis
    processed_df['avg_salary'] = processed_df[['min_salary', 'max_salary']].mean(axis=1)
    
    return processed_df

def plot_salary_by_job_type(df):
    """
    Create a box plot showing salary distribution by job type.
    
    Args:
        df: DataFrame containing job posting data with salary information
        
    Returns:
        Plotly figure object
    """
    # Ensure salary data is processed
    if 'avg_salary' not in df.columns:
        df = extract_salary_range(df)
    
    # Filter out rows without salary information
    salary_df = df.dropna(subset=['avg_salary'])
    
    # If no salary data available, return empty figure with message
    if len(salary_df) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No salary data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Create the box plot
    fig = px.box(
        salary_df,
        x='job_type',
        y='avg_salary',
        color='job_type',
        title='Salary Distribution by Job Type',
        labels={'avg_salary': 'Average Salary ($)', 'job_type': 'Job Type'},
        height=500
    )
    
    # Improve layout
    fig.update_layout(
        xaxis_title='Job Type',
        yaxis_title='Salary ($)',
        showlegend=False,
        yaxis_tickprefix='$',
        yaxis_tickformat=',',
    )
    
    return fig

def plot_salary_by_region(df):
    """
    Create a bar chart showing average salary by region.
    
    Args:
        df: DataFrame containing job posting data with salary and location
        
    Returns:
        Plotly figure object
    """
    from utils.visualizer import extract_region
    
    # Ensure salary data is processed
    if 'avg_salary' not in df.columns:
        df = extract_salary_range(df)
    
    # Add region information
    salary_df = df.copy()
    salary_df['region'] = salary_df['location'].apply(extract_region)
    
    # Filter out rows without salary information
    salary_df = salary_df.dropna(subset=['avg_salary'])
    
    # If no salary data available, return empty figure with message
    if len(salary_df) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No salary data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Calculate average salary by region
    region_salary = salary_df.groupby('region')['avg_salary'].agg(['mean', 'count']).reset_index()
    region_salary = region_salary.sort_values('mean', ascending=False)
    
    # Create the bar chart
    fig = px.bar(
        region_salary,
        x='region',
        y='mean',
        text='count',
        color='mean',
        title='Average Salary by Region',
        labels={'mean': 'Average Salary ($)', 'region': 'Region', 'count': 'Number of Job Postings'},
        color_continuous_scale='Viridis'
    )
    
    # Improve layout
    fig.update_layout(
        xaxis_title='Region',
        yaxis_title='Average Salary ($)',
        yaxis_tickprefix='$',
        yaxis_tickformat=',',
        xaxis={'categoryorder': 'total descending'}
    )
    
    # Add data labels
    fig.update_traces(
        texttemplate='%{text} jobs',
        textposition='outside'
    )
    
    return fig

def plot_salary_trends(df):
    """
    Create a line chart showing salary trends over time.
    
    Args:
        df: DataFrame containing job posting data with salary information
        
    Returns:
        Plotly figure object
    """
    # Ensure salary data is processed
    if 'avg_salary' not in df.columns:
        df = extract_salary_range(df)
    
    # Filter out rows without salary information
    salary_df = df.dropna(subset=['avg_salary'])
    
    # If no salary data available, return empty figure with message
    if len(salary_df) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No salary data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Aggregate average salary by month_year and job_type
    salary_trends = salary_df.groupby(['month_year', 'job_type'])['avg_salary'].mean().reset_index()
    
    # Convert month_year to datetime for proper sorting
    salary_trends['date'] = pd.to_datetime(salary_trends['month_year'])
    salary_trends = salary_trends.sort_values('date')
    
    # Create the line chart
    fig = px.line(
        salary_trends,
        x='month_year',
        y='avg_salary',
        color='job_type',
        markers=True,
        title='Salary Trends Over Time by Job Type',
        labels={'avg_salary': 'Average Salary ($)', 'month_year': 'Month', 'job_type': 'Job Type'}
    )
    
    # Improve layout
    fig.update_layout(
        xaxis_title='Month',
        yaxis_title='Average Salary ($)',
        yaxis_tickprefix='$',
        yaxis_tickformat=',',
        legend_title='Job Type'
    )
    
    return fig

def get_salary_statistics(df):
    """
    Calculate various salary statistics for the dataset.
    
    Args:
        df: DataFrame containing job posting data
        
    Returns:
        Dictionary with salary statistics
    """
    # Ensure salary data is processed
    if 'avg_salary' not in df.columns:
        df = extract_salary_range(df)
    
    # Filter out rows without salary information
    salary_df = df.dropna(subset=['avg_salary'])
    
    # If no salary data available, return empty statistics
    if len(salary_df) == 0:
        return {
            'has_data': False,
            'count': 0
        }
    
    # Calculate overall statistics
    overall_stats = {
        'has_data': True,
        'count': len(salary_df),
        'mean': salary_df['avg_salary'].mean(),
        'median': salary_df['avg_salary'].median(),
        'min': salary_df['avg_salary'].min(),
        'max': salary_df['avg_salary'].max(),
        'std': salary_df['avg_salary'].std()
    }
    
    # Calculate job type statistics
    job_type_stats = {}
    for job_type in salary_df['job_type'].unique():
        job_data = salary_df[salary_df['job_type'] == job_type]
        if len(job_data) > 0:
            job_type_stats[job_type] = {
                'count': len(job_data),
                'mean': job_data['avg_salary'].mean(),
                'median': job_data['avg_salary'].median()
            }
    
    # Find highest and lowest paying job types
    if job_type_stats:
        highest_paying = max(job_type_stats.items(), key=lambda x: x[1]['mean'])
        lowest_paying = min(job_type_stats.items(), key=lambda x: x[1]['mean'])
        
        overall_stats['highest_paying_job_type'] = {
            'job_type': highest_paying[0],
            'mean_salary': highest_paying[1]['mean']
        }
        
        overall_stats['lowest_paying_job_type'] = {
            'job_type': lowest_paying[0],
            'mean_salary': lowest_paying[1]['mean']
        }
    
    return overall_stats