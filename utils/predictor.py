import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.linear_model import LinearRegression
import plotly.express as px
import plotly.graph_objects as go

def prepare_time_series_data(df, time_column='month_year', value_column='count', freq='MS'):
    """
    Prepare time series data for predictive modeling.
    
    Args:
        df: DataFrame containing job posting data
        time_column: Column containing time information
        value_column: Column containing values to predict
        freq: Frequency string for resampling (MS = month start)
        
    Returns:
        Prepared DataFrame with datetime index
    """
    # Group data by time period and count
    if 'count' not in df.columns:
        ts_data = df.groupby(time_column).size().reset_index(name='count')
    else:
        ts_data = df.copy()
    
    # Convert time column to datetime if needed
    if not pd.api.types.is_datetime64_any_dtype(ts_data[time_column]):
        ts_data[time_column] = pd.to_datetime(ts_data[time_column])
    
    # Set time column as index and sort
    ts_data = ts_data.set_index(time_column).sort_index()
    
    # Select value column
    if value_column in ts_data.columns:
        ts_data = ts_data[value_column]
    
    # Ensure monthly frequency
    ts_data = ts_data.resample(freq).sum()
    
    # Fill missing values with 0
    ts_data = ts_data.fillna(0)
    
    return ts_data

def forecast_job_trends(df, periods=6, job_type=None):
    """
    Forecast future job posting trends using exponential smoothing.
    
    Args:
        df: DataFrame containing job posting data
        periods: Number of future periods to forecast
        job_type: Specific job type to forecast (None for all jobs)
        
    Returns:
        Tuple of (forecast_values, historical_values, dates)
    """
    # Filter by job type if specified
    if job_type is not None:
        filtered_df = df[df['job_type'] == job_type].copy()
    else:
        filtered_df = df.copy()
    
    # Calculate monthly job posting counts
    ts_data = filtered_df.groupby('month_year').size()
    
    # Convert index to datetime
    ts_data.index = pd.to_datetime(ts_data.index)
    
    # Sort by date
    ts_data = ts_data.sort_index()
    
    # Apply Holt-Winters Exponential Smoothing
    # Use additive for stable trends, multiplicative for exponential growth
    model = ExponentialSmoothing(
        ts_data,
        trend='add',  # 'add' for additive, 'mul' for multiplicative
        seasonal='add',  # 'add' for additive, 'mul' for multiplicative
        seasonal_periods=3  # Adjust based on data seasonality
    )
    
    # Fit the model
    fitted_model = model.fit(optimized=True, use_brute=True)
    
    # Generate forecast
    forecast = fitted_model.forecast(periods)
    
    # Generate dates for forecast periods
    last_date = ts_data.index[-1]
    forecast_dates = pd.date_range(
        start=last_date + pd.Timedelta(days=30), 
        periods=periods, 
        freq='MS'
    )
    
    # Set forecast dates as index
    forecast.index = forecast_dates
    
    # Return forecast, historical data, and dates
    return forecast, ts_data, forecast_dates

def predict_job_type_growth(df, periods=6):
    """
    Predict growth rates for different job types using linear regression.
    
    Args:
        df: DataFrame containing job posting data
        periods: Number of future periods to predict
        
    Returns:
        DataFrame with predicted growth rates for each job type
    """
    # Get all unique job types
    job_types = df['job_type'].unique()
    
    # Create empty dataframe for results
    growth_rates = pd.DataFrame(index=job_types, columns=['Current', 'Predicted', 'Growth %'])
    
    # Calculate growth rate for each job type
    for job_type in job_types:
        # Filter data for current job type
        job_data = df[df['job_type'] == job_type].copy()
        
        # Group by month_year and count
        monthly_counts = job_data.groupby('month_year').size()
        monthly_counts.index = pd.to_datetime(monthly_counts.index)
        monthly_counts = monthly_counts.sort_index()
        
        # Need at least 2 data points for prediction
        if len(monthly_counts) >= 2:
            # Get current count (average of last 3 months or all if less than 3)
            current_count = monthly_counts.iloc[-min(3, len(monthly_counts)):].mean()
            
            # Convert dates to numeric values for linear regression
            X = np.array(range(len(monthly_counts))).reshape(-1, 1)
            y = monthly_counts.values
            
            # Fit linear regression model
            model = LinearRegression()
            model.fit(X, y)
            
            # Predict future values
            future_X = np.array(range(len(monthly_counts), len(monthly_counts) + periods)).reshape(-1, 1)
            future_y = model.predict(future_X)
            
            # Calculate predicted count (average of predicted months)
            predicted_count = np.mean(future_y)
            
            # Calculate growth percentage
            if current_count > 0:
                growth_percent = ((predicted_count - current_count) / current_count) * 100
            else:
                growth_percent = 0
            
            # Store results
            growth_rates.loc[job_type] = [
                round(current_count, 1),
                round(predicted_count, 1),
                round(growth_percent, 1)
            ]
        else:
            # Not enough data for prediction
            growth_rates.loc[job_type] = [0, 0, 0]
    
    # Sort by growth percentage in descending order
    growth_rates = growth_rates.sort_values('Growth %', ascending=False)
    
    return growth_rates

def plot_job_forecast(df, periods=6, job_type=None, confidence_interval=0.9):
    """
    Create a plot of historical job posting data with forecasted future trends.
    
    Args:
        df: DataFrame containing job posting data
        periods: Number of future periods to forecast
        job_type: Specific job type to forecast (None for all jobs)
        confidence_interval: Confidence interval for prediction bands (0-1)
        
    Returns:
        Plotly figure object
    """
    # Get forecast data
    forecast, historical, forecast_dates = forecast_job_trends(df, periods, job_type)
    
    # Convert index to strings for better display
    historical_dates = historical.index.strftime('%Y-%m')
    forecast_dates_str = forecast.index.strftime('%Y-%m')
    
    # Calculate confidence intervals (simple approach)
    std_dev = historical.std()
    z_value = 1.96  # 95% confidence interval
    ci_width = z_value * std_dev
    
    upper_bound = forecast + ci_width
    lower_bound = forecast - ci_width
    
    # Ensure lower bound is not negative
    lower_bound = lower_bound.clip(lower=0)
    
    # Create plot with historical data
    fig = go.Figure()
    
    # Add historical data
    fig.add_trace(go.Scatter(
        x=historical_dates,
        y=historical.values,
        mode='lines+markers',
        name='Historical Data',
        line=dict(color='blue')
    ))
    
    # Add forecast
    fig.add_trace(go.Scatter(
        x=forecast_dates_str,
        y=forecast.values,
        mode='lines+markers',
        name='Forecast',
        line=dict(color='red', dash='dot')
    ))
    
    # Add prediction intervals
    fig.add_trace(go.Scatter(
        x=forecast_dates_str,
        y=upper_bound.values,
        mode='lines',
        line=dict(width=0),
        showlegend=False
    ))
    
    fig.add_trace(go.Scatter(
        x=forecast_dates_str,
        y=lower_bound.values,
        mode='lines',
        line=dict(width=0),
        fill='tonexty',
        fillcolor='rgba(255, 0, 0, 0.2)',
        name='95% Confidence Interval'
    ))
    
    # Set title and labels
    title = f'Job Postings Forecast: {job_type}' if job_type else 'Job Postings Forecast: All Types'
    fig.update_layout(
        title=title,
        xaxis_title='Month',
        yaxis_title='Number of Job Postings',
        hovermode='x unified',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    return fig

def plot_job_type_growth_forecast(growth_df):
    """
    Create a horizontal bar chart showing predicted growth by job type.
    
    Args:
        growth_df: DataFrame containing growth rates from predict_job_type_growth
        
    Returns:
        Plotly figure object
    """
    # Create color scale based on growth rate
    colors = growth_df['Growth %'].values
    
    # Create horizontal bar chart
    fig = px.bar(
        growth_df,
        y=growth_df.index,
        x='Growth %',
        orientation='h',
        title='Predicted Job Growth by Type (%)',
        color='Growth %',
        color_continuous_scale='RdBu',
        color_continuous_midpoint=0,
        text='Growth %'
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title='Predicted Growth (%)',
        yaxis_title='Job Type',
        yaxis={'categoryorder': 'total ascending'},
        height=max(400, len(growth_df) * 25)  # Adjust height based on number of job types
    )
    
    # Add data labels
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
    
    return fig