import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Define schema for interview data
INTERVIEW_SCHEMA = {
    'company': str,
    'job_title': str,
    'date': 'datetime64[ns]',
    'difficulty': float,  # Scale from 1-5
    'length': float,  # In hours
    'rounds': int,
    'technical_focus': float,  # Scale from 1-5
    'behavioral_focus': float,  # Scale from 1-5
    'took_home_assignment': bool,
    'whiteboard_coding': bool,
    'system_design': bool,
    'algorithm_questions': bool,
    'outcome': str,  # 'offer', 'rejected', 'pending', etc.
    'notes': str
}

def validate_interview_data(df):
    """
    Validate that the interview data has the required format.
    
    Args:
        df: DataFrame containing interview data
        
    Returns:
        Validated DataFrame or None if validation fails
    """
    # Check required columns
    required_columns = ['company', 'job_title', 'date', 'difficulty']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        return None
    
    # Create a copy to avoid modifying the original
    validated_df = df.copy()
    
    # Convert date to datetime if it's not already
    if not pd.api.types.is_datetime64_any_dtype(validated_df['date']):
        try:
            validated_df['date'] = pd.to_datetime(validated_df['date'])
        except:
            return None
    
    # Ensure difficulty is in the right range
    if 'difficulty' in validated_df.columns:
        validated_df['difficulty'] = pd.to_numeric(validated_df['difficulty'], errors='coerce')
        validated_df = validated_df[validated_df['difficulty'].between(1, 5)]
    
    # Add month_year column for consistency with job posting data
    validated_df['month_year'] = validated_df['date'].dt.strftime('%Y-%m')
    
    return validated_df

def calculate_company_difficulty_ratings(df):
    """
    Calculate average interview difficulty ratings by company.
    
    Args:
        df: DataFrame containing interview data
        
    Returns:
        DataFrame with company difficulty ratings
    """
    # Validate interview data
    validated_df = validate_interview_data(df)
    
    if validated_df is None or validated_df.empty:
        return pd.DataFrame()
    
    # Group by company and calculate average difficulty
    company_ratings = validated_df.groupby('company').agg({
        'difficulty': 'mean',
        'length': 'mean',
        'rounds': 'mean',
        'technical_focus': 'mean',
        'behavioral_focus': 'mean',
        'company': 'count'
    }).rename(columns={'company': 'count'})
    
    # Reset index
    company_ratings = company_ratings.reset_index()
    
    # Sort by difficulty
    company_ratings = company_ratings.sort_values('difficulty', ascending=False)
    
    return company_ratings

def plot_company_difficulty_comparison(df, top_n=15):
    """
    Create a bar chart comparing interview difficulty across companies.
    
    Args:
        df: DataFrame containing interview data
        top_n: Number of top companies to include
        
    Returns:
        Plotly figure object
    """
    # Calculate company difficulty ratings
    company_ratings = calculate_company_difficulty_ratings(df)
    
    # If no data, return empty figure with message
    if company_ratings.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No interview data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Get top N companies by interview count
    top_companies = company_ratings.nlargest(top_n, 'count')
    
    # Create bar chart
    fig = px.bar(
        top_companies,
        y='company',
        x='difficulty',
        orientation='h',
        color='difficulty',
        color_continuous_scale='RdYlGn_r',  # Reversed so red is more difficult
        range_color=[1, 5],
        labels={'company': 'Company', 'difficulty': 'Average Difficulty (1-5)', 'count': 'Number of Interviews'},
        title=f'Interview Difficulty by Company',
        hover_data=['count', 'rounds', 'length']
    )
    
    # Improve layout
    fig.update_layout(
        xaxis_title='Difficulty Rating (1-5)',
        yaxis_title='Company',
        yaxis={'categoryorder': 'total ascending'},
        height=max(400, len(top_companies) * 25)  # Adjust height based on number of companies
    )
    
    # Add reference lines for difficulty levels
    for level, label in [(2, 'Easy'), (3, 'Medium'), (4, 'Hard')]:
        fig.add_shape(
            type="line",
            x0=level,
            y0=-0.5,
            x1=level,
            y1=len(top_companies) - 0.5,
            line=dict(color="gray", width=1, dash="dash")
        )
        
        fig.add_annotation(
            x=level,
            y=len(top_companies) - 1,
            text=label,
            showarrow=False,
            yshift=10
        )
    
    return fig

def plot_interview_difficulty_trend(df):
    """
    Create a line chart showing interview difficulty trend over time.
    
    Args:
        df: DataFrame containing interview data
        
    Returns:
        Plotly figure object
    """
    # Validate interview data
    validated_df = validate_interview_data(df)
    
    if validated_df is None or validated_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No interview data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Group by month_year and calculate average difficulty
    difficulty_trend = validated_df.groupby('month_year').agg({
        'difficulty': 'mean',
        'date': 'min',
        'company': 'count'
    }).rename(columns={'company': 'count'}).reset_index()
    
    # Sort by date
    difficulty_trend = difficulty_trend.sort_values('date')
    
    # Create line chart
    fig = px.line(
        difficulty_trend,
        x='month_year',
        y='difficulty',
        markers=True,
        labels={'month_year': 'Month', 'difficulty': 'Average Difficulty (1-5)', 'count': 'Number of Interviews'},
        title='Interview Difficulty Trend Over Time',
        hover_data=['count']
    )
    
    # Add range for "normal" difficulty
    fig.add_shape(
        type="rect",
        x0=difficulty_trend['month_year'].iloc[0],
        y0=2.5,
        x1=difficulty_trend['month_year'].iloc[-1],
        y1=3.5,
        fillcolor="lightgreen",
        opacity=0.2,
        line_width=0
    )
    
    # Improve layout
    fig.update_layout(
        xaxis_title='Month',
        yaxis_title='Average Difficulty (1-5)',
        yaxis=dict(range=[1, 5])
    )
    
    return fig

def plot_interview_components_comparison(df):
    """
    Create a radar chart comparing different components of interviews.
    
    Args:
        df: DataFrame containing interview data
        
    Returns:
        Plotly figure object
    """
    # Validate interview data
    validated_df = validate_interview_data(df)
    
    if validated_df is None or validated_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No interview data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Components for radar chart
    components = [
        'difficulty',
        'technical_focus',
        'behavioral_focus',
        'length',
        'rounds'
    ]
    
    # Boolean components
    bool_components = [
        'took_home_assignment', 
        'whiteboard_coding',
        'system_design',
        'algorithm_questions'
    ]
    
    # Top companies by interview count
    top_companies = validated_df['company'].value_counts().nlargest(5).index.tolist()
    
    # Create radar chart
    fig = go.Figure()
    
    # Add traces for each company
    for company in top_companies:
        company_data = validated_df[validated_df['company'] == company]
        
        # Calculate average values
        values = []
        for component in components:
            if component in company_data.columns:
                # Normalize rounds and length to 1-5 scale
                if component == 'rounds':
                    max_rounds = validated_df['rounds'].max() if 'rounds' in validated_df.columns else 5
                    value = min(5, company_data[component].mean() * 5 / max_rounds)
                elif component == 'length':
                    max_length = validated_df['length'].max() if 'length' in validated_df.columns else 8
                    value = min(5, company_data[component].mean() * 5 / max_length)
                else:
                    value = company_data[component].mean()
                
                values.append(value)
            else:
                values.append(0)
        
        # Add percentage of boolean components
        for component in bool_components:
            if component in company_data.columns:
                percentage = company_data[component].mean() * 5  # Scale to 0-5
                values.append(percentage)
                components.append(component.replace('_', ' ').title())
        
        # Add trace
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=[c.replace('_', ' ').title() for c in components],
            fill='toself',
            name=company
        ))
    
    # Improve layout
    fig.update_layout(
        title="Interview Components by Company",
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5]
            )
        ),
        showlegend=True
    )
    
    return fig

def plot_interview_success_factors(df):
    """
    Create visualizations showing factors correlated with interview success.
    
    Args:
        df: DataFrame containing interview data
        
    Returns:
        Plotly figure object
    """
    # Validate interview data
    validated_df = validate_interview_data(df)
    
    if validated_df is None or validated_df.empty or 'outcome' not in validated_df.columns:
        fig = go.Figure()
        fig.add_annotation(
            text="No interview outcome data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Filter to only include interviews with offer or rejected outcomes
    outcomes_df = validated_df[validated_df['outcome'].isin(['offer', 'rejected'])]
    
    if outcomes_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No interview outcome data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Create success rate by factor subplot
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Success Rate by Difficulty", "Success Rate by Technical Focus",
                       "Success Rate by Interview Length", "Success Rate by Number of Rounds")
    )
    
    # Function to calculate success rate by factor
    def calc_success_rate(column):
        success_rate = outcomes_df.groupby(column)['outcome'].apply(
            lambda x: (x == 'offer').mean() * 100
        ).reset_index()
        success_rate.columns = [column, 'success_rate']
        return success_rate
    
    # Difficulty
    if 'difficulty' in outcomes_df.columns:
        difficulty_success = calc_success_rate('difficulty')
        fig.add_trace(
            go.Bar(
                x=difficulty_success['difficulty'],
                y=difficulty_success['success_rate'],
                name='Difficulty',
                marker_color='blue'
            ),
            row=1, col=1
        )
    
    # Technical focus
    if 'technical_focus' in outcomes_df.columns:
        technical_success = calc_success_rate('technical_focus')
        fig.add_trace(
            go.Bar(
                x=technical_success['technical_focus'],
                y=technical_success['success_rate'],
                name='Technical Focus',
                marker_color='green'
            ),
            row=1, col=2
        )
    
    # Interview length
    if 'length' in outcomes_df.columns:
        # Bin interview lengths
        outcomes_df['length_bin'] = pd.cut(
            outcomes_df['length'],
            bins=[0, 1, 2, 3, 4, float('inf')],
            labels=['<1', '1-2', '2-3', '3-4', '4+']
        )
        length_success = calc_success_rate('length_bin')
        fig.add_trace(
            go.Bar(
                x=length_success['length_bin'],
                y=length_success['success_rate'],
                name='Length',
                marker_color='orange'
            ),
            row=2, col=1
        )
    
    # Number of rounds
    if 'rounds' in outcomes_df.columns:
        rounds_success = calc_success_rate('rounds')
        fig.add_trace(
            go.Bar(
                x=rounds_success['rounds'],
                y=rounds_success['success_rate'],
                name='Rounds',
                marker_color='purple'
            ),
            row=2, col=2
        )
    
    # Update layout
    fig.update_layout(
        title="Interview Success Factors",
        showlegend=False,
        height=600
    )
    
    # Update y-axis titles
    fig.update_yaxes(title_text="Success Rate (%)", range=[0, 100])
    
    return fig

def get_interview_preparation_tips(company, job_title, df):
    """
    Generate interview preparation tips based on historical data.
    
    Args:
        company: Target company
        job_title: Target job title
        df: DataFrame containing interview data
        
    Returns:
        Dictionary with interview preparation tips
    """
    # Validate interview data
    validated_df = validate_interview_data(df)
    
    if validated_df is None or validated_df.empty:
        return {
            'has_data': False,
            'message': 'No interview data available'
        }
    
    # Filter by company if specified
    if company:
        company_df = validated_df[validated_df['company'].str.lower() == company.lower()]
    else:
        company_df = validated_df
    
    # If no data for this company, use all data
    if company_df.empty:
        company_df = validated_df
        company_specific = False
    else:
        company_specific = True
    
    # Filter by job title if specified and data exists
    if job_title and not company_df.empty:
        # Look for partial matches in job titles
        job_df = company_df[company_df['job_title'].str.lower().str.contains(job_title.lower())]
        
        # If no matches, use company data
        if job_df.empty:
            job_df = company_df
            job_specific = False
        else:
            job_specific = True
    else:
        job_df = company_df
        job_specific = False
    
    # Calculate average metrics
    metrics = {}
    
    for column in ['difficulty', 'length', 'rounds', 'technical_focus', 'behavioral_focus']:
        if column in job_df.columns:
            metrics[column] = job_df[column].mean()
    
    # Calculate frequency of components
    components = {}
    
    for column in ['took_home_assignment', 'whiteboard_coding', 'system_design', 'algorithm_questions']:
        if column in job_df.columns:
            components[column] = job_df[column].mean() * 100  # Convert to percentage
    
    # Extract common interview questions from notes if available
    common_questions = []
    
    if 'notes' in job_df.columns:
        # Combine all notes
        all_notes = ' '.join(job_df['notes'].dropna().astype(str))
        
        # Look for question patterns
        question_patterns = [
            r'"([^"]+)\?"',  # Text in quotes ending with question mark
            r'asked[:\s]+([^.]+\?)',  # "asked" followed by a question
            r'question[s]?[:\s]+([^.]+\?)'  # "question" followed by a question
        ]
        
        for pattern in question_patterns:
            questions = re.findall(pattern, all_notes)
            common_questions.extend(questions)
        
        # Remove duplicates and limit to top 5
        common_questions = list(set(common_questions))[:5]
    
    # Generate preparation tips
    tips = []
    
    # Difficulty-based tips
    if 'difficulty' in metrics:
        difficulty = metrics['difficulty']
        if difficulty >= 4:
            tips.append("Prepare for a challenging interview process with rigorous technical assessments.")
        elif difficulty >= 3:
            tips.append("Expect a moderately challenging interview with a mix of technical and behavioral questions.")
        else:
            tips.append("The interview process is relatively approachable, but still prepare thoroughly.")
    
    # Component-based tips
    if 'whiteboard_coding' in components and components['whiteboard_coding'] >= 50:
        tips.append("Practice coding on a whiteboard or without an IDE as this is likely part of the process.")
    
    if 'system_design' in components and components['system_design'] >= 50:
        tips.append("Review system design principles and be prepared to architect complex systems.")
    
    if 'algorithm_questions' in components and components['algorithm_questions'] >= 50:
        tips.append("Focus on data structures and algorithms, especially time and space complexity analysis.")
    
    if 'took_home_assignment' in components and components['took_home_assignment'] >= 50:
        tips.append("Expect a take-home coding assignment as part of the interview process.")
    
    # Focus-based tips
    if 'technical_focus' in metrics and 'behavioral_focus' in metrics:
        technical = metrics['technical_focus']
        behavioral = metrics['behavioral_focus']
        
        if technical > behavioral:
            tips.append(f"The interview has a strong technical focus ({technical:.1f}/5), so prioritize technical preparation.")
        elif behavioral > technical:
            tips.append(f"Behavioral questions are emphasized ({behavioral:.1f}/5), so prepare your experience stories.")
        else:
            tips.append("The interview balances technical and behavioral assessments equally.")
    
    # Process tips
    if 'rounds' in metrics:
        rounds = metrics['rounds']
        tips.append(f"Prepare for approximately {rounds:.1f} interview rounds.")
    
    if 'length' in metrics:
        length = metrics['length']
        tips.append(f"Each interview session typically lasts around {length:.1f} hours.")
    
    return {
        'has_data': True,
        'company_specific': company_specific,
        'job_specific': job_specific,
        'metrics': metrics,
        'components': components,
        'common_questions': common_questions,
        'tips': tips,
        'interview_count': len(job_df)
    }