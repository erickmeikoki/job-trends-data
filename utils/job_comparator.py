import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

def compare_job_postings_over_time(df, job_types=None, companies=None):
    """
    Compare job posting trends over time for multiple job types or companies.
    
    Args:
        df: DataFrame containing job posting data
        job_types: List of job types to compare (None for all)
        companies: List of companies to compare (None for all)
        
    Returns:
        Plotly figure object
    """
    # Create a copy to avoid modifying the original
    compare_df = df.copy()
    
    # Determine whether to compare by job type or company
    if job_types is not None and len(job_types) > 0:
        # Filter to the selected job types
        compare_df = compare_df[compare_df['job_type'].isin(job_types)]
        group_by_col = 'job_type'
        color_col = 'job_type'
        title = 'Job Posting Comparison by Type'
    elif companies is not None and len(companies) > 0:
        # Filter to the selected companies
        compare_df = compare_df[compare_df['company'].isin(companies)]
        group_by_col = 'company'
        color_col = 'company'
        title = 'Job Posting Comparison by Company'
    else:
        # Default to top 5 job types if nothing specified
        top_types = df['job_type'].value_counts().nlargest(5).index.tolist()
        compare_df = compare_df[compare_df['job_type'].isin(top_types)]
        group_by_col = 'job_type'
        color_col = 'job_type'
        title = 'Job Posting Comparison (Top 5 Types)'
    
    # Group by month_year and the selected column
    trend_data = compare_df.groupby(['month_year', group_by_col]).size().reset_index(name='count')
    
    # Convert month_year to datetime for proper sorting
    trend_data['date'] = pd.to_datetime(trend_data['month_year'])
    trend_data = trend_data.sort_values('date')
    
    # Create the line chart
    fig = px.line(
        trend_data, 
        x='month_year', 
        y='count', 
        color=color_col,
        markers=True,
        labels={'month_year': 'Month', 'count': 'Number of Job Postings', color_col: color_col.capitalize()},
        title=title
    )
    
    # Improve layout
    fig.update_layout(
        xaxis_title='Month',
        yaxis_title='Number of Job Postings',
        legend_title=color_col.capitalize(),
        height=500
    )
    
    return fig

def create_side_by_side_comparison(df, items, column='job_type'):
    """
    Create side-by-side comparison of different job types or companies.
    
    Args:
        df: DataFrame containing job posting data
        items: List of job types or companies to compare
        column: Column to compare ('job_type' or 'company')
        
    Returns:
        Plotly figure object with subplots
    """
    # Validate inputs
    if column not in ['job_type', 'company']:
        raise ValueError("Column must be 'job_type' or 'company'")
    
    if not items or len(items) == 0:
        # Default to top 3 items if none specified
        items = df[column].value_counts().nlargest(3).index.tolist()
    
    # Create subplots (1 row, n columns)
    fig = make_subplots(
        rows=1, 
        cols=len(items),
        subplot_titles=items,
        shared_yaxes=True
    )
    
    # Add data for each item
    for i, item in enumerate(items):
        # Filter data for this item
        item_df = df[df[column] == item]
        
        # Skip if no data
        if len(item_df) == 0:
            continue
            
        # Monthly trend
        monthly_counts = item_df.groupby('month_year').size()
        monthly_counts.index = pd.to_datetime(monthly_counts.index)
        monthly_counts = monthly_counts.sort_index()
        
        # Add bar chart to subplot
        fig.add_trace(
            go.Bar(
                x=monthly_counts.index.strftime('%Y-%m'),
                y=monthly_counts.values,
                name=item,
                showlegend=False
            ),
            row=1, col=i+1
        )
    
    # Update layout
    fig.update_layout(
        title=f"Side-by-Side Comparison by {column.capitalize()}",
        height=400,
        margin=dict(t=50, b=50)
    )
    
    # Update y-axis title only for the first subplot
    fig.update_yaxes(title_text="Number of Job Postings", row=1, col=1)
    
    # Update x-axis title for all subplots
    for i in range(len(items)):
        fig.update_xaxes(title_text="Month", row=1, col=i+1)
    
    return fig

def compare_growth_rates(df, items, column='job_type', periods=3):
    """
    Compare growth rates between different job types or companies.
    
    Args:
        df: DataFrame containing job posting data
        items: List of job types or companies to compare
        column: Column to compare ('job_type' or 'company')
        periods: Number of recent periods to use for growth calculation
        
    Returns:
        Plotly figure object
    """
    # Validate inputs
    if column not in ['job_type', 'company']:
        raise ValueError("Column must be 'job_type' or 'company'")
    
    if not items or len(items) == 0:
        # Default to top 5 items if none specified
        items = df[column].value_counts().nlargest(5).index.tolist()
    
    # Create dataframe to store growth rates
    growth_data = []
    
    # Calculate growth for each item
    for item in items:
        # Filter data for this item
        item_df = df[df[column] == item]
        
        # Skip if no data
        if len(item_df) == 0:
            continue
            
        # Monthly trend
        monthly_counts = item_df.groupby('month_year').size()
        monthly_counts.index = pd.to_datetime(monthly_counts.index)
        monthly_counts = monthly_counts.sort_index()
        
        # Need at least 2 periods to calculate growth
        if len(monthly_counts) < 2:
            growth_data.append({
                'item': item,
                'current': monthly_counts.iloc[-1] if len(monthly_counts) > 0 else 0,
                'previous': 0,
                'growth_pct': 0
            })
            continue
        
        # Calculate recent and previous periods
        recent_periods = min(periods, len(monthly_counts))
        current = monthly_counts.iloc[-recent_periods:].mean()
        
        # If we have enough data for previous periods
        if len(monthly_counts) > recent_periods:
            previous = monthly_counts.iloc[-(2*recent_periods):-recent_periods].mean()
        else:
            previous = monthly_counts.iloc[0]
        
        # Calculate growth percentage
        if previous > 0:
            growth_pct = ((current - previous) / previous) * 100
        else:
            growth_pct = 0 if current == 0 else 100  # Avoid division by zero
        
        # Store results
        growth_data.append({
            'item': item,
            'current': current,
            'previous': previous,
            'growth_pct': growth_pct
        })
    
    # Convert to DataFrame
    growth_df = pd.DataFrame(growth_data)
    
    # If no data, return empty figure
    if len(growth_df) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available for comparison",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Sort by growth percentage
    growth_df = growth_df.sort_values('growth_pct', ascending=False)
    
    # Create bar chart
    fig = px.bar(
        growth_df,
        y='item',
        x='growth_pct',
        orientation='h',
        color='growth_pct',
        color_continuous_scale='RdBu',
        color_continuous_midpoint=0,
        labels={'item': column.capitalize(), 'growth_pct': 'Growth %'},
        title=f"{column.capitalize()} Growth Rate Comparison",
        text='growth_pct'
    )
    
    # Improve layout
    fig.update_layout(
        yaxis_title=column.capitalize(),
        xaxis_title='Growth Percentage (%)',
        height=max(400, len(growth_df) * 30)  # Adjust height based on number of items
    )
    
    # Add data labels
    fig.update_traces(
        texttemplate='%{text:.1f}%', 
        textposition='outside'
    )
    
    return fig

def create_heatmap_comparison(df, rows='job_type', cols='region'):
    """
    Create a heatmap comparing job postings across two dimensions.
    
    Args:
        df: DataFrame containing job posting data
        rows: Column to use for heatmap rows
        cols: Column to use for heatmap columns
        
    Returns:
        Plotly figure object
    """
    # Add region if needed
    if cols == 'region' and 'region' not in df.columns:
        from utils.visualizer import extract_region
        compare_df = df.copy()
        compare_df['region'] = compare_df['location'].apply(extract_region)
    else:
        compare_df = df
    
    # Verify columns exist
    if rows not in compare_df.columns or cols not in compare_df.columns:
        raise ValueError(f"Columns {rows} and {cols} must exist in DataFrame")
    
    # Create cross-tabulation
    cross_tab = pd.crosstab(
        index=compare_df[rows], 
        columns=compare_df[cols],
        normalize='all'  # Normalize to show percentages
    ) * 100  # Convert to percentage
    
    # Create heatmap
    fig = px.imshow(
        cross_tab,
        labels=dict(x=cols.capitalize(), y=rows.capitalize(), color="Percentage (%)"),
        x=cross_tab.columns,
        y=cross_tab.index,
        color_continuous_scale='Viridis',
        title=f"Heatmap: {rows.capitalize()} vs {cols.capitalize()}",
        text_auto='.1f'  # Show one decimal place
    )
    
    # Improve layout
    fig.update_layout(
        height=max(400, len(cross_tab) * 30),  # Adjust height based on number of rows
        xaxis={'categoryorder': 'total descending'},
        yaxis={'categoryorder': 'total ascending'}
    )
    
    return fig