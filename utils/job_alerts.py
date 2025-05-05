import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import streamlit as st
from utils.skill_tracker import extract_skills_from_text

def create_job_alert(df, preferences):
    """
    Create a personalized job alert based on user preferences.
    
    Args:
        df: DataFrame containing job posting data
        preferences: Dictionary with user preferences
        
    Returns:
        DataFrame with matching job postings
    """
    # Create a copy to avoid modifying the original
    alert_df = df.copy()
    
    # Apply filters based on preferences
    if not alert_df.empty:
        # Filter by job type if specified
        if 'job_types' in preferences and preferences['job_types']:
            alert_df = alert_df[alert_df['job_type'].isin(preferences['job_types'])]
        
        # Filter by companies if specified
        if 'companies' in preferences and preferences['companies']:
            alert_df = alert_df[alert_df['company'].isin(preferences['companies'])]
        
        # Filter by locations/regions if specified
        if 'locations' in preferences and preferences['locations']:
            # Check if any location contains the specified locations
            location_filter = alert_df['location'].str.contains('|'.join(preferences['locations']), case=False)
            alert_df = alert_df[location_filter]
        
        # Filter by remote preference
        if 'remote_only' in preferences and preferences['remote_only']:
            remote_filter = alert_df['location'].str.contains('remote', case=False)
            alert_df = alert_df[remote_filter]
        
        # Filter by recency if specified
        if 'recent_days' in preferences and preferences['recent_days'] > 0:
            latest_date = alert_df['date'].max()
            cutoff_date = latest_date - timedelta(days=preferences['recent_days'])
            alert_df = alert_df[alert_df['date'] >= cutoff_date]
        
        # Filter by skills if specified and skills are extracted
        if 'skills' in preferences and preferences['skills'] and 'skills' in alert_df.columns:
            # Only include jobs that require at least one of the preferred skills
            skill_filter = alert_df['skills'].apply(
                lambda job_skills: any(skill in job_skills for skill in preferences['skills'])
            )
            alert_df = alert_df[skill_filter]
    
    # Sort by date (most recent first)
    if not alert_df.empty:
        alert_df = alert_df.sort_values('date', ascending=False)
    
    return alert_df

def rank_job_matches(df, preferences):
    """
    Rank job postings based on how well they match user preferences.
    
    Args:
        df: DataFrame containing job posting data
        preferences: Dictionary with user preferences
        
    Returns:
        DataFrame with ranked job postings
    """
    # Get jobs matching basic filters
    matches = create_job_alert(df, preferences)
    
    # If no matches or empty DataFrame, return as is
    if matches.empty:
        return matches
    
    # Prepare for scoring
    matches = matches.copy()
    matches['match_score'] = 0.0
    
    # Score based on job type match
    if 'job_types' in preferences and preferences['job_types']:
        # Exact job type match
        matches.loc[matches['job_type'].isin(preferences['job_types']), 'match_score'] += 30
    
    # Score based on company match
    if 'companies' in preferences and preferences['companies']:
        # Exact company match
        matches.loc[matches['company'].isin(preferences['companies']), 'match_score'] += 20
    
    # Score based on location match
    if 'locations' in preferences and preferences['locations']:
        # Location contains any preferred location
        for location in preferences['locations']:
            matches.loc[matches['location'].str.contains(location, case=False), 'match_score'] += 15
    
    # Score based on remote preference
    if 'remote_only' in preferences and preferences['remote_only']:
        # Remote job
        matches.loc[matches['location'].str.contains('remote', case=False), 'match_score'] += 15
    
    # Score based on skill match
    if 'skills' in preferences and preferences['skills'] and 'skills' in matches.columns:
        # Calculate percentage of preferred skills that match job skills
        matches['skill_match_pct'] = matches['skills'].apply(
            lambda job_skills: len([s for s in job_skills if s in preferences['skills']]) / len(preferences['skills']) 
            if preferences['skills'] else 0
        )
        
        # Add skill match score (up to 35 points)
        matches['match_score'] += matches['skill_match_pct'] * 35
    
    # Score based on recency
    latest_date = matches['date'].max()
    matches['days_old'] = (latest_date - matches['date']).dt.days
    
    # More recent jobs get higher scores (up to 15 points for jobs posted today)
    matches['recency_score'] = 15 * np.exp(-0.1 * matches['days_old'])
    matches['match_score'] += matches['recency_score']
    
    # Normalize scores to 0-100 range
    max_score = matches['match_score'].max()
    if max_score > 0:
        matches['match_score'] = (matches['match_score'] / max_score) * 100
    
    # Sort by match score
    matches = matches.sort_values('match_score', ascending=False)
    
    # Round match score for display
    matches['match_score'] = matches['match_score'].round(1)
    
    return matches

def get_matching_job_count(df, preferences):
    """
    Get the count of jobs matching user preferences.
    
    Args:
        df: DataFrame containing job posting data
        preferences: Dictionary with user preferences
        
    Returns:
        Number of matching jobs
    """
    matches = create_job_alert(df, preferences)
    return len(matches)

def plot_preference_match_distribution(df, preferences):
    """
    Create a visualization showing the distribution of job matches.
    
    Args:
        df: DataFrame containing job posting data
        preferences: Dictionary with user preferences
        
    Returns:
        Plotly figure object
    """
    # Rank jobs based on preferences
    ranked_jobs = rank_job_matches(df, preferences)
    
    # If no matches, return empty figure with message
    if ranked_jobs.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No jobs match your preferences",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Create histogram of match scores
    fig = px.histogram(
        ranked_jobs,
        x='match_score',
        nbins=10,
        title='Distribution of Job Matches',
        labels={'match_score': 'Match Score (%)', 'count': 'Number of Jobs'},
        color_discrete_sequence=['#3366CC']
    )
    
    # Improve layout
    fig.update_layout(
        xaxis_title='Match Score (%)',
        yaxis_title='Number of Jobs',
        xaxis=dict(range=[0, 100])
    )
    
    # Add vertical lines for match quality thresholds
    thresholds = [
        (80, 'Excellent Match', 'green'),
        (60, 'Good Match', 'orange'),
        (40, 'Fair Match', 'red')
    ]
    
    for value, label, color in thresholds:
        fig.add_shape(
            type="line",
            x0=value,
            y0=0,
            x1=value,
            y1=ranked_jobs['match_score'].value_counts().max() * 1.1,
            line=dict(color=color, width=2, dash="dash")
        )
        
        fig.add_annotation(
            x=value,
            y=ranked_jobs['match_score'].value_counts().max() * 1.05,
            text=label,
            showarrow=False,
            font=dict(color=color)
        )
    
    return fig

def extract_user_preferences_from_text(text):
    """
    Extract user preferences from natural language description.
    
    Args:
        text: User description of job preferences
        
    Returns:
        Dictionary with extracted preferences
    """
    preferences = {
        'job_types': [],
        'companies': [],
        'locations': [],
        'skills': [],
        'remote_only': False,
        'recent_days': 30
    }
    
    # Extract job types
    job_type_patterns = [
        r'(software engineer|developer|data scientist|product manager|designer|frontend|backend|full stack|devops|security|qa|test|architect)',
        r'looking for (a|an) ([a-z\s]+) (position|job|role)'
    ]
    
    for pattern in job_type_patterns:
        job_types = re.findall(pattern, text.lower())
        if job_types:
            # Extract the job type from the matches
            if isinstance(job_types[0], tuple):
                for job_type in job_types:
                    if len(job_type) >= 2:
                        preferences['job_types'].append(job_type[1].strip())
            else:
                for job_type in job_types:
                    preferences['job_types'].append(job_type.strip())
    
    # Extract companies
    company_patterns = [
        r'(interested in|looking at|want to work for|prefer) ([a-z\s,]+) companies',
        r'companies like ([a-z\s,]+)',
        r'(google|facebook|amazon|apple|microsoft|netflix|twitter|uber|airbnb|linkedin)'
    ]
    
    for pattern in company_patterns:
        companies = re.findall(pattern, text.lower())
        if companies:
            # Extract the companies from the matches
            if isinstance(companies[0], tuple):
                for company in companies:
                    if len(company) >= 2:
                        # Split by commas and 'and'
                        company_list = re.split(r',|\sand\s', company[1])
                        preferences['companies'].extend([c.strip() for c in company_list])
            else:
                for company in companies:
                    preferences['companies'].append(company.strip())
    
    # Extract locations
    location_patterns = [
        r'(in|around|near) ([a-z\s,]+)',
        r'(new york|san francisco|seattle|boston|austin|chicago|los angeles|london|berlin|tokyo|remote)'
    ]
    
    for pattern in location_patterns:
        locations = re.findall(pattern, text.lower())
        if locations:
            # Extract the locations from the matches
            if isinstance(locations[0], tuple):
                for location in locations:
                    if len(location) >= 2:
                        # Split by commas and 'and'
                        location_list = re.split(r',|\sand\s', location[1])
                        preferences['locations'].extend([l.strip() for l in location_list])
            else:
                for location in locations:
                    preferences['locations'].append(location.strip())
    
    # Check for remote preference
    remote_patterns = [
        r'(remote|work from home|wfh|remote-only|remote only)',
        r'(don\'t|do not) want to (go|work|commute) (in|to) (an|the) office'
    ]
    
    for pattern in remote_patterns:
        if re.search(pattern, text.lower()):
            preferences['remote_only'] = True
            preferences['locations'].append('remote')
            break
    
    # Extract time frame
    time_patterns = [
        r'(in the last|within|past) (\d+) (days?|weeks?|months?)',
        r'(\d+) (days?|weeks?|months?) ago'
    ]
    
    for pattern in time_patterns:
        time_matches = re.findall(pattern, text.lower())
        if time_matches:
            for match in time_matches:
                if len(match) >= 3:
                    value = int(match[1])
                    unit = match[2]
                    if 'week' in unit:
                        preferences['recent_days'] = value * 7
                    elif 'month' in unit:
                        preferences['recent_days'] = value * 30
                    else:  # days
                        preferences['recent_days'] = value
                    break
    
    # Extract skills using the skill tracker
    preferences['skills'] = extract_skills_from_text(text)
    
    # Remove duplicates
    preferences['job_types'] = list(set(preferences['job_types']))
    preferences['companies'] = list(set(preferences['companies']))
    preferences['locations'] = list(set(preferences['locations']))
    preferences['skills'] = list(set(preferences['skills']))
    
    return preferences

def save_user_alert(preferences, name):
    """
    Save a named job alert to user session state.
    
    Args:
        preferences: Dictionary with user preferences
        name: Name of the alert
        
    Returns:
        True if alert was saved successfully, False otherwise
    """
    # Initialize alerts dictionary in session state if it doesn't exist
    if 'saved_job_alerts' not in st.session_state:
        st.session_state.saved_job_alerts = {}
    
    # Add timestamp
    preferences['created_at'] = datetime.now()
    
    # Save alert
    st.session_state.saved_job_alerts[name] = preferences
    
    return True

def get_saved_alerts():
    """
    Get all saved job alerts.
    
    Returns:
        Dictionary with saved alerts
    """
    return st.session_state.get('saved_job_alerts', {})

def delete_user_alert(name):
    """
    Delete a saved job alert.
    
    Args:
        name: Name of the alert to delete
        
    Returns:
        True if alert was deleted successfully, False otherwise
    """
    if 'saved_job_alerts' in st.session_state and name in st.session_state.saved_job_alerts:
        del st.session_state.saved_job_alerts[name]
        return True
    return False

def check_alert_for_new_matches(alert_name, preferences, df, lookback_days=1):
    """
    Check if there are new job postings matching a saved alert.
    
    Args:
        alert_name: Name of the alert
        preferences: Dictionary with user preferences
        df: DataFrame containing job posting data
        lookback_days: Number of days to look back for new matches
        
    Returns:
        DataFrame with new matching job postings
    """
    # Create a copy of preferences with modified recency filter
    recent_preferences = preferences.copy()
    recent_preferences['recent_days'] = lookback_days
    
    # Get recent matching jobs
    recent_matches = create_job_alert(df, recent_preferences)
    
    # Track alert checks in session state
    if 'alert_check_history' not in st.session_state:
        st.session_state.alert_check_history = {}
    
    # Get history for this alert
    alert_history = st.session_state.alert_check_history.get(alert_name, {'last_check': None, 'last_matches': set()})
    
    # If never checked before, all matches are new
    if alert_history['last_check'] is None:
        new_matches = recent_matches
        is_first_check = True
    else:
        # Compare with previous matches
        current_match_ids = set(recent_matches.index.tolist())
        new_match_ids = current_match_ids - alert_history['last_matches']
        new_matches = recent_matches.loc[list(new_match_ids)] if new_match_ids else pd.DataFrame()
        is_first_check = False
    
    # Update check history
    alert_history['last_check'] = datetime.now()
    alert_history['last_matches'] = set(recent_matches.index.tolist())
    st.session_state.alert_check_history[alert_name] = alert_history
    
    return new_matches, is_first_check