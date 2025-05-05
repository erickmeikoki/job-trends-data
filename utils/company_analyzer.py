import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def analyze_company_hiring_patterns(df, company=None, top_n=5):
    """
    Analyze hiring patterns for a specific company or top companies.
    
    Args:
        df: DataFrame containing job posting data
        company: Specific company to analyze (None for top companies)
        top_n: Number of top companies to analyze if no specific company is provided
        
    Returns:
        Plotly figure object
    """
    # Create a copy to avoid modifying the original
    hiring_df = df.copy()
    
    # Convert date to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(hiring_df['date']):
        hiring_df['date'] = pd.to_datetime(hiring_df['date'])
    
    # Filter for specific company or get top companies
    if company is not None:
        hiring_df = hiring_df[hiring_df['company'] == company]
        title = f"Hiring Pattern: {company}"
    else:
        # Get top companies by job posting count
        top_companies = hiring_df['company'].value_counts().nlargest(top_n).index.tolist()
        hiring_df = hiring_df[hiring_df['company'].isin(top_companies)]
        title = f"Hiring Patterns: Top {top_n} Companies"
    
    # Group by month_year and company
    hiring_patterns = hiring_df.groupby(['month_year', 'company']).size().reset_index(name='count')
    
    # Convert month_year to datetime for proper sorting
    hiring_patterns['date'] = pd.to_datetime(hiring_patterns['month_year'])
    hiring_patterns = hiring_patterns.sort_values('date')
    
    # Create the line chart
    fig = px.line(
        hiring_patterns,
        x='month_year',
        y='count',
        color='company',
        markers=True,
        labels={'month_year': 'Month', 'count': 'Number of Job Postings', 'company': 'Company'},
        title=title
    )
    
    # Improve layout
    fig.update_layout(
        xaxis_title='Month',
        yaxis_title='Number of Job Postings',
        legend_title='Company',
        height=500
    )
    
    return fig

def detect_hiring_surges(df, threshold_pct=50, min_jobs=3):
    """
    Detect companies with unusual hiring activity (surges or slowdowns).
    
    Args:
        df: DataFrame containing job posting data
        threshold_pct: Percentage increase/decrease to consider as unusual
        min_jobs: Minimum number of job postings required to be considered
        
    Returns:
        DataFrame with companies showing unusual activity
    """
    # Create a copy to avoid modifying the original
    surge_df = df.copy()
    
    # Convert date to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(surge_df['date']):
        surge_df['date'] = pd.to_datetime(surge_df['date'])
    
    # Sort by date
    surge_df = surge_df.sort_values('date')
    
    # Get unique months
    months = surge_df['month_year'].unique()
    
    # Need at least 2 months of data
    if len(months) < 2:
        return pd.DataFrame()
    
    # Get recent and previous months
    recent_month = months[-1]
    previous_month = months[-2]
    
    # Count job postings by company in recent and previous months
    recent_counts = surge_df[surge_df['month_year'] == recent_month]['company'].value_counts()
    previous_counts = surge_df[surge_df['month_year'] == previous_month]['company'].value_counts()
    
    # Calculate changes
    surge_data = []
    
    for company in set(recent_counts.index) | set(previous_counts.index):
        recent_count = recent_counts.get(company, 0)
        previous_count = previous_counts.get(company, 0)
        
        # Skip if both counts are below minimum
        if recent_count < min_jobs and previous_count < min_jobs:
            continue
        
        # Calculate percentage change
        if previous_count > 0:
            pct_change = ((recent_count - previous_count) / previous_count) * 100
        elif recent_count > 0:
            pct_change = 100  # New company (wasn't in previous month)
        else:
            pct_change = 0
        
        # Only include if change exceeds threshold
        if abs(pct_change) >= threshold_pct:
            surge_data.append({
                'company': company,
                'recent_month': recent_month,
                'previous_month': previous_month,
                'recent_count': recent_count,
                'previous_count': previous_count,
                'pct_change': pct_change,
                'activity_type': 'Surge' if pct_change > 0 else 'Slowdown'
            })
    
    # Convert to DataFrame
    surge_df = pd.DataFrame(surge_data)
    
    # Sort by absolute percentage change
    if not surge_df.empty:
        surge_df = surge_df.sort_values('pct_change', ascending=False, key=abs)
    
    return surge_df

def plot_hiring_alerts(df, top_n=10):
    """
    Create a visualization of hiring surges and slowdowns.
    
    Args:
        df: DataFrame containing job posting data
        top_n: Number of top companies to include
        
    Returns:
        Plotly figure object
    """
    # Detect hiring surges
    surge_data = detect_hiring_surges(df)
    
    # If no surges detected, return empty figure with message
    if len(surge_data) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No unusual hiring activity detected",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Get top surges
    top_surges = surge_data.head(top_n)
    
    # Create horizontal bar chart
    fig = px.bar(
        top_surges,
        y='company',
        x='pct_change',
        orientation='h',
        color='activity_type',
        color_discrete_map={'Surge': 'green', 'Slowdown': 'red'},
        labels={'company': 'Company', 'pct_change': 'Percentage Change (%)', 'activity_type': 'Activity Type'},
        title=f'Notable Hiring Activity ({top_surges["recent_month"].iloc[0]} vs {top_surges["previous_month"].iloc[0]})',
        text='recent_count',
        hover_data=['previous_count']
    )
    
    # Improve layout
    fig.update_layout(
        xaxis_title='Percentage Change (%)',
        yaxis_title='Company',
        yaxis={'categoryorder': 'total ascending'},
        height=max(400, len(top_surges) * 25)  # Adjust height based on number of companies
    )
    
    # Add data labels
    fig.update_traces(
        texttemplate='%{text} jobs',
        textposition='outside'
    )
    
    return fig

def analyze_company_seasonality(df, company):
    """
    Analyze seasonal hiring patterns for a specific company.
    
    Args:
        df: DataFrame containing job posting data
        company: Company to analyze
        
    Returns:
        Plotly figure object
    """
    # Create a copy to avoid modifying the original
    company_df = df[df['company'] == company].copy()
    
    # If no data for this company, return empty figure with message
    if len(company_df) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text=f"No data available for {company}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Convert date to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(company_df['date']):
        company_df['date'] = pd.to_datetime(company_df['date'])
    
    # Extract month from date
    company_df['month'] = company_df['date'].dt.month
    
    # Group by month and count
    monthly_hiring = company_df.groupby('month').size().reset_index(name='count')
    
    # Ensure all months are represented
    all_months = pd.DataFrame({'month': range(1, 13)})
    monthly_hiring = all_months.merge(monthly_hiring, on='month', how='left').fillna(0)
    
    # Add month names
    month_names = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
        7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }
    monthly_hiring['month_name'] = monthly_hiring['month'].map(month_names)
    
    # Create the bar chart
    fig = px.bar(
        monthly_hiring,
        x='month_name',
        y='count',
        labels={'month_name': 'Month', 'count': 'Average Job Postings'},
        title=f'Seasonal Hiring Pattern: {company}',
        color='count',
        color_continuous_scale='Viridis'
    )
    
    # Improve layout
    fig.update_layout(
        xaxis={'categoryorder': 'array', 'categoryarray': list(month_names.values())},
        xaxis_title='Month',
        yaxis_title='Average Job Postings'
    )
    
    return fig

def compare_company_job_types(df, companies=None, top_n=5):
    """
    Compare job type distribution across different companies.
    
    Args:
        df: DataFrame containing job posting data
        companies: List of companies to compare (None for top companies)
        top_n: Number of top companies to include if no specific companies provided
        
    Returns:
        Plotly figure object
    """
    # Create a copy to avoid modifying the original
    company_df = df.copy()
    
    # Filter for specific companies or get top companies
    if companies is not None and len(companies) > 0:
        company_df = company_df[company_df['company'].isin(companies)]
        title = f"Job Type Distribution by Company"
    else:
        # Get top companies by job posting count
        top_companies = company_df['company'].value_counts().nlargest(top_n).index.tolist()
        company_df = company_df[company_df['company'].isin(top_companies)]
        title = f"Job Type Distribution: Top {top_n} Companies"
    
    # If no data, return empty figure with message
    if len(company_df) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for selected companies",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Create cross-tabulation of companies and job types
    cross_tab = pd.crosstab(
        index=company_df['company'],
        columns=company_df['job_type'],
        normalize='index'  # Normalize by row (company)
    ) * 100  # Convert to percentage
    
    # Create heatmap
    fig = px.imshow(
        cross_tab,
        labels=dict(x='Job Type', y='Company', color='Percentage (%)'),
        x=cross_tab.columns,
        y=cross_tab.index,
        color_continuous_scale='Viridis',
        title=title,
        text_auto='.1f'  # Show one decimal place
    )
    
    # Improve layout
    fig.update_layout(
        height=max(400, len(cross_tab) * 30),  # Adjust height based on number of companies
        xaxis={'tickangle': 45}  # Angle job type names for better readability
    )
    
    return fig

def calculate_company_growth_rates(df, lookback_periods=3):
    """
    Calculate company growth rates based on job posting activity.
    
    Args:
        df: DataFrame containing job posting data
        lookback_periods: Number of periods to analyze
        
    Returns:
        DataFrame with company growth rates
    """
    # Create a copy to avoid modifying the original
    growth_df = df.copy()
    
    # Convert date to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(growth_df['date']):
        growth_df['date'] = pd.to_datetime(growth_df['date'])
    
    # Sort by date
    growth_df = growth_df.sort_values('date')
    
    # Get unique months
    months = growth_df['month_year'].unique()
    
    # Need at least 2 months of data
    if len(months) < 2:
        return pd.DataFrame()
    
    # Determine periods for analysis
    recent_periods = min(lookback_periods, len(months))
    if recent_periods < 2:
        return pd.DataFrame()
    
    # Split months into recent and previous
    half_point = recent_periods // 2
    recent_months = months[-half_point:]
    previous_months = months[-(recent_periods):-half_point]
    
    # Count job postings by company in recent and previous periods
    recent_counts = growth_df[growth_df['month_year'].isin(recent_months)]['company'].value_counts()
    previous_counts = growth_df[growth_df['month_year'].isin(previous_months)]['company'].value_counts()
    
    # Calculate growth rates
    growth_data = []
    
    for company in set(recent_counts.index) | set(previous_counts.index):
        recent_count = recent_counts.get(company, 0)
        previous_count = previous_counts.get(company, 0)
        
        # Calculate growth rate
        if previous_count > 0:
            growth_pct = ((recent_count - previous_count) / previous_count) * 100
        elif recent_count > 0:
            growth_pct = 100  # New company (wasn't in previous period)
        else:
            growth_pct = 0
        
        # Only include companies with at least 3 job postings
        if recent_count + previous_count >= 3:
            growth_data.append({
                'company': company,
                'recent_count': recent_count,
                'previous_count': previous_count,
                'total_count': recent_count + previous_count,
                'growth_pct': growth_pct
            })
    
    # Convert to DataFrame
    growth_df = pd.DataFrame(growth_data)
    
    # Sort by growth percentage
    if not growth_df.empty:
        growth_df = growth_df.sort_values('growth_pct', ascending=False)
    
    return growth_df