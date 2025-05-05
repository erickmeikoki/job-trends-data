import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from scipy.stats import zscore

def calculate_job_market_health_index(df, window=3, weights=None):
    """
    Calculate a composite job market health index based on multiple factors.
    
    Args:
        df: DataFrame containing job posting data
        window: Number of months to include in the moving average
        weights: Dictionary of factor weights for the index
        
    Returns:
        DataFrame with index values by month
    """
    # Create a copy to avoid modifying the original
    health_df = df.copy()
    
    # Convert date to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(health_df['date']):
        health_df['date'] = pd.to_datetime(health_df['date'])
    
    # Sort by date
    health_df = health_df.sort_values('date')
    
    # Default weights if none provided
    if weights is None:
        weights = {
            'job_count': 0.4,        # Total number of job postings
            'company_diversity': 0.2, # Number of unique companies posting jobs
            'job_type_diversity': 0.2, # Diversity of job types
            'location_diversity': 0.1, # Diversity of locations
            'remote_ratio': 0.1       # Proportion of remote job opportunities
        }
    
    # Group by month_year to get monthly statistics
    monthly_stats = []
    
    for month, month_df in health_df.groupby('month_year'):
        # Calculate factors
        job_count = len(month_df)
        company_diversity = len(month_df['company'].unique())
        job_type_diversity = len(month_df['job_type'].unique())
        location_diversity = len(month_df['location'].unique())
        
        # Calculate remote ratio
        remote_count = month_df['location'].str.lower().str.contains('remote').sum()
        remote_ratio = remote_count / job_count if job_count > 0 else 0
        
        # Store statistics
        monthly_stats.append({
            'month_year': month,
            'date': pd.to_datetime(month),
            'job_count': job_count,
            'company_diversity': company_diversity,
            'job_type_diversity': job_type_diversity,
            'location_diversity': location_diversity,
            'remote_ratio': remote_ratio
        })
    
    # Convert to DataFrame
    monthly_stats_df = pd.DataFrame(monthly_stats)
    
    # If no data, return empty DataFrame
    if len(monthly_stats_df) == 0:
        return pd.DataFrame()
    
    # Sort by date
    monthly_stats_df = monthly_stats_df.sort_values('date')
    
    # Normalize each factor (convert to z-scores, but clamp outliers)
    for factor in weights.keys():
        if factor in monthly_stats_df.columns:
            # Only normalize if we have enough data points
            if len(monthly_stats_df) >= 3:
                monthly_stats_df[f'{factor}_norm'] = zscore(monthly_stats_df[factor], nan_policy='omit')
                # Clamp extreme values
                monthly_stats_df[f'{factor}_norm'] = monthly_stats_df[f'{factor}_norm'].clip(-3, 3)
            else:
                # With limited data, use basic min-max scaling
                min_val = monthly_stats_df[factor].min()
                max_val = monthly_stats_df[factor].max()
                if max_val > min_val:
                    monthly_stats_df[f'{factor}_norm'] = (monthly_stats_df[factor] - min_val) / (max_val - min_val) * 2 - 1
                else:
                    monthly_stats_df[f'{factor}_norm'] = 0
    
    # Calculate weighted index
    monthly_stats_df['health_index'] = 0
    for factor, weight in weights.items():
        if f'{factor}_norm' in monthly_stats_df.columns:
            monthly_stats_df['health_index'] += monthly_stats_df[f'{factor}_norm'] * weight
    
    # Convert to 0-100 scale for easier interpretation
    min_index = monthly_stats_df['health_index'].min()
    max_index = monthly_stats_df['health_index'].max()
    if max_index > min_index:
        monthly_stats_df['health_index_scaled'] = ((monthly_stats_df['health_index'] - min_index) / 
                                                  (max_index - min_index) * 100)
    else:
        monthly_stats_df['health_index_scaled'] = 50  # Default to middle value
    
    # Apply moving average to smooth the index
    if len(monthly_stats_df) >= window:
        monthly_stats_df['health_index_ma'] = monthly_stats_df['health_index_scaled'].rolling(window=window).mean()
    else:
        monthly_stats_df['health_index_ma'] = monthly_stats_df['health_index_scaled']
    
    # Calculate month-over-month change
    monthly_stats_df['mom_change'] = monthly_stats_df['health_index_scaled'].diff()
    
    return monthly_stats_df

def plot_job_market_health_index(df, window=3):
    """
    Create a line chart of the job market health index over time.
    
    Args:
        df: DataFrame containing job posting data
        window: Number of months to include in the moving average
        
    Returns:
        Plotly figure object
    """
    # Calculate health index
    health_df = calculate_job_market_health_index(df, window=window)
    
    # If no data, return empty figure with message
    if len(health_df) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="Not enough data to calculate job market health index",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Create the line chart
    fig = go.Figure()
    
    # Add raw index line
    fig.add_trace(go.Scatter(
        x=health_df['month_year'],
        y=health_df['health_index_scaled'],
        mode='lines+markers',
        name='Raw Index',
        line=dict(color='rgba(0, 0, 255, 0.3)'),
        marker=dict(size=6)
    ))
    
    # Add moving average line
    fig.add_trace(go.Scatter(
        x=health_df['month_year'],
        y=health_df['health_index_ma'],
        mode='lines+markers',
        name=f'{window}-Month Moving Average',
        line=dict(color='blue', width=3),
        marker=dict(size=8)
    ))
    
    # Add benchmark line at 50
    fig.add_shape(
        type="line",
        x0=health_df['month_year'].iloc[0],
        y0=50,
        x1=health_df['month_year'].iloc[-1],
        y1=50,
        line=dict(color="gray", width=1, dash="dash")
    )
    
    # Add annotations for the latest value
    latest_index = health_df['health_index_ma'].iloc[-1]
    latest_month = health_df['month_year'].iloc[-1]
    latest_change = health_df['mom_change'].iloc[-1]
    
    # Determine market sentiment
    if latest_index >= 70:
        sentiment = "Very Strong"
        color = "darkgreen"
    elif latest_index >= 55:
        sentiment = "Strong"
        color = "green"
    elif latest_index >= 45:
        sentiment = "Stable"
        color = "blue"
    elif latest_index >= 30:
        sentiment = "Weak"
        color = "orange"
    else:
        sentiment = "Very Weak"
        color = "red"
    
    # Add annotation for the latest value
    fig.add_annotation(
        x=latest_month,
        y=latest_index,
        text=f"{sentiment}: {latest_index:.1f}",
        showarrow=True,
        arrowhead=1,
        arrowcolor=color,
        font=dict(color=color, size=14),
        align="center"
    )
    
    # Improve layout
    fig.update_layout(
        title="Job Market Health Index",
        xaxis_title="Month",
        yaxis_title="Health Index (0-100)",
        legend_title="Index Type",
        yaxis=dict(range=[0, 100]),
        height=500
    )
    
    return fig

def get_market_health_insights(df, window=3):
    """
    Get key insights about the current job market health.
    
    Args:
        df: DataFrame containing job posting data
        window: Number of months to include in the moving average
        
    Returns:
        Dictionary with market health insights
    """
    # Calculate health index
    health_df = calculate_job_market_health_index(df, window=window)
    
    # If no data, return empty insights
    if len(health_df) == 0:
        return {'has_data': False}
    
    # Get latest values
    latest = health_df.iloc[-1]
    
    # Determine market sentiment
    if latest['health_index_ma'] >= 70:
        sentiment = "Very Strong"
        color = "darkgreen"
        description = "The job market is booming with abundant opportunities."
    elif latest['health_index_ma'] >= 55:
        sentiment = "Strong"
        color = "green"
        description = "The job market is healthy with good opportunities available."
    elif latest['health_index_ma'] >= 45:
        sentiment = "Stable"
        color = "blue"
        description = "The job market is stable with steady demand for workers."
    elif latest['health_index_ma'] >= 30:
        sentiment = "Weak"
        color = "orange"
        description = "The job market is showing signs of weakness with limited opportunities."
    else:
        sentiment = "Very Weak"
        color = "red"
        description = "The job market is experiencing significant challenges with few opportunities."
    
    # Determine trend
    if len(health_df) >= 3:
        trend_values = health_df['health_index_ma'].iloc[-3:].values
        if trend_values[2] > trend_values[0]:
            trend = "Improving"
            trend_icon = "↗"
            trend_description = "The job market is showing signs of improvement."
        elif trend_values[2] < trend_values[0]:
            trend = "Declining"
            trend_icon = "↘"
            trend_description = "The job market is showing signs of decline."
        else:
            trend = "Stable"
            trend_icon = "→"
            trend_description = "The job market is maintaining stability."
    else:
        trend = "Insufficient Data"
        trend_icon = "–"
        trend_description = "Not enough historical data to determine trend."
    
    # Compile insights
    insights = {
        'has_data': True,
        'current_index': latest['health_index_ma'],
        'sentiment': sentiment,
        'color': color,
        'description': description,
        'trend': trend,
        'trend_icon': trend_icon,
        'trend_description': trend_description,
        'last_updated': latest['month_year'],
        'job_count': latest['job_count'],
        'company_diversity': latest['company_diversity'],
        'job_type_diversity': latest['job_type_diversity'],
        'location_diversity': latest['location_diversity'],
        'remote_ratio': latest['remote_ratio']
    }
    
    return insights

def plot_market_health_components(df):
    """
    Create a radar chart showing the components of the market health index.
    
    Args:
        df: DataFrame containing job posting data
        
    Returns:
        Plotly figure object
    """
    # Calculate health index
    health_df = calculate_job_market_health_index(df)
    
    # If no data, return empty figure with message
    if len(health_df) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="Not enough data to calculate job market health components",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Get latest values
    latest = health_df.iloc[-1]
    
    # Components for radar chart
    components = [
        'job_count',
        'company_diversity',
        'job_type_diversity',
        'location_diversity',
        'remote_ratio'
    ]
    
    # Normalize each component to 0-100 scale for the radar chart
    component_values = []
    for component in components:
        # Get min and max values from the entire dataset
        min_val = health_df[component].min()
        max_val = health_df[component].max()
        
        # Normalize to 0-100 scale
        if max_val > min_val:
            value = ((latest[component] - min_val) / (max_val - min_val) * 100)
        else:
            value = 50  # Default to middle value
        
        component_values.append(value)
    
    # Create radar chart
    fig = go.Figure()
    
    # Add radar chart trace
    fig.add_trace(go.Scatterpolar(
        r=component_values,
        theta=[c.replace('_', ' ').title() for c in components],
        fill='toself',
        name='Market Components'
    ))
    
    # Add benchmark trace (50% circle)
    fig.add_trace(go.Scatterpolar(
        r=[50, 50, 50, 50, 50],
        theta=[c.replace('_', ' ').title() for c in components],
        fill='none',
        name='Benchmark',
        line=dict(color='gray', dash='dash')
    ))
    
    # Improve layout
    fig.update_layout(
        title="Job Market Health Components",
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )
        ),
        showlegend=True
    )
    
    return fig

def calculate_regional_health_indices(df):
    """
    Calculate job market health indices for different regions.
    
    Args:
        df: DataFrame containing job posting data
        
    Returns:
        DataFrame with health indices by region
    """
    # Get region for each job
    from utils.visualizer import extract_region
    
    # Create a copy with region information
    regional_df = df.copy()
    regional_df['region'] = regional_df['location'].apply(extract_region)
    
    # Calculate health index for each region
    region_indices = []
    
    for region, region_df in regional_df.groupby('region'):
        # Calculate health index for this region
        region_health = calculate_job_market_health_index(region_df)
        
        # If enough data, get the latest index
        if len(region_health) > 0:
            latest = region_health.iloc[-1]
            
            region_indices.append({
                'region': region,
                'health_index': latest['health_index_scaled'],
                'job_count': latest['job_count'],
                'company_diversity': latest['company_diversity'],
                'job_type_diversity': latest['job_type_diversity'],
                'location_diversity': latest['location_diversity'],
                'remote_ratio': latest['remote_ratio']
            })
    
    # Convert to DataFrame
    region_indices_df = pd.DataFrame(region_indices)
    
    # Sort by health index
    if not region_indices_df.empty:
        region_indices_df = region_indices_df.sort_values('health_index', ascending=False)
    
    return region_indices_df

def plot_regional_health_comparison(df):
    """
    Create a bar chart comparing job market health across regions.
    
    Args:
        df: DataFrame containing job posting data
        
    Returns:
        Plotly figure object
    """
    # Calculate regional health indices
    region_indices = calculate_regional_health_indices(df)
    
    # If no data, return empty figure with message
    if len(region_indices) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="Not enough data to calculate regional health indices",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Create bar chart
    fig = px.bar(
        region_indices,
        x='region',
        y='health_index',
        text='health_index',
        color='health_index',
        color_continuous_scale='RdYlGn',
        range_color=[0, 100],
        labels={'region': 'Region', 'health_index': 'Health Index'},
        title='Job Market Health by Region'
    )
    
    # Improve layout
    fig.update_layout(
        xaxis_title='Region',
        yaxis_title='Health Index (0-100)',
        yaxis=dict(range=[0, 100]),
        coloraxis_showscale=True,
        coloraxis_colorbar=dict(title='Health Index')
    )
    
    # Add data labels
    fig.update_traces(
        texttemplate='%{text:.1f}',
        textposition='outside'
    )
    
    # Add a reference line at 50
    fig.add_shape(
        type="line",
        x0=-0.5,
        y0=50,
        x1=len(region_indices) - 0.5,
        y1=50,
        line=dict(color="gray", width=1, dash="dash")
    )
    
    return fig