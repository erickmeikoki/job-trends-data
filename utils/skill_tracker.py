import pandas as pd
import numpy as np
import re
import plotly.express as px
import plotly.graph_objects as go

# Dictionary of skills to search for in job titles and other fields
COMMON_SKILLS = {
    # Programming Languages
    'python': ['python', 'django', 'flask', 'fastapi', 'pytorch', 'tensorflow', 'pandas'],
    'javascript': ['javascript', 'js', 'node', 'nodejs', 'node.js', 'react', 'reactjs', 'vue', 'angular', 'next', 'nextjs', 'next.js'],
    'typescript': ['typescript', 'ts'],
    'java': ['java', 'spring', 'spring boot', 'hibernate'],
    'c#': ['c#', '.net', 'asp.net', 'dotnet', 'csharp'],
    'c++': ['c++', 'cpp'],
    'go': ['golang', 'go language'],
    'rust': ['rust'],
    'php': ['php', 'laravel', 'symfony'],
    'ruby': ['ruby', 'rails', 'ruby on rails'],
    'swift': ['swift', 'ios'],
    'kotlin': ['kotlin', 'android'],
    'r': ['r language', 'rstudio'],
    'scala': ['scala', 'akka'],
    
    # Frontend
    'html': ['html', 'html5'],
    'css': ['css', 'scss', 'sass', 'less', 'css3'],
    'react': ['react', 'reactjs', 'react.js'],
    'angular': ['angular', 'angularjs', 'angular.js'],
    'vue': ['vue', 'vuejs', 'vue.js', 'nuxt'],
    'svelte': ['svelte'],
    'redux': ['redux'],
    'tailwind': ['tailwind', 'tailwindcss'],
    'bootstrap': ['bootstrap'],
    'jquery': ['jquery'],
    'responsive design': ['responsive design', 'responsive web', 'mobile-first'],
    
    # Backend
    'node.js': ['node.js', 'nodejs', 'node', 'express', 'expressjs'],
    'django': ['django'],
    'flask': ['flask'],
    'fastapi': ['fastapi'],
    'spring': ['spring', 'spring boot', 'spring cloud'],
    'rails': ['rails', 'ruby on rails'],
    'asp.net': ['asp.net', 'asp net'],
    'laravel': ['laravel'],
    
    # Databases
    'sql': ['sql', 'mysql', 'postgresql', 'postgres', 'oracle', 'mssql', 'sql server'],
    'nosql': ['nosql', 'mongodb', 'dynamodb', 'cassandra', 'couchdb'],
    'postgres': ['postgres', 'postgresql'],
    'mongodb': ['mongodb', 'mongo'],
    'mysql': ['mysql'],
    'oracle': ['oracle database', 'oracle db'],
    'redis': ['redis'],
    
    # DevOps & Cloud
    'aws': ['aws', 'amazon web services', 'ec2', 's3', 'lambda', 'cloudformation'],
    'azure': ['azure', 'microsoft azure'],
    'gcp': ['gcp', 'google cloud', 'google cloud platform'],
    'docker': ['docker', 'containerization'],
    'kubernetes': ['kubernetes', 'k8s'],
    'terraform': ['terraform', 'iac'],
    'jenkins': ['jenkins', 'ci/cd', 'cicd'],
    'gitlab ci': ['gitlab ci', 'gitlab-ci'],
    'github actions': ['github actions', 'github workflow'],
    'ansible': ['ansible'],
    'chef': ['chef'],
    'puppet': ['puppet'],
    
    # Data Science & ML
    'machine learning': ['machine learning', 'ml', 'ai', 'artificial intelligence'],
    'deep learning': ['deep learning', 'neural networks', 'cnn', 'rnn', 'lstm'],
    'nlp': ['nlp', 'natural language processing'],
    'computer vision': ['computer vision', 'cv', 'image processing'],
    'data science': ['data science', 'data scientist'],
    'tensorflow': ['tensorflow', 'tf'],
    'pytorch': ['pytorch', 'torch'],
    'keras': ['keras'],
    'scikit-learn': ['scikit-learn', 'sklearn'],
    'pandas': ['pandas'],
    'numpy': ['numpy'],
    'jupyter': ['jupyter', 'jupyter notebook'],
    
    # Mobile
    'ios': ['ios', 'swift', 'objective-c', 'objective c'],
    'android': ['android', 'kotlin', 'java android'],
    'react native': ['react native', 'react-native'],
    'flutter': ['flutter', 'dart'],
    'xamarin': ['xamarin'],
    
    # Testing
    'testing': ['testing', 'qa', 'quality assurance', 'tdd', 'bdd'],
    'selenium': ['selenium'],
    'cypress': ['cypress'],
    'jest': ['jest'],
    'mocha': ['mocha'],
    'junit': ['junit'],
    
    # Web Technologies
    'rest': ['rest', 'rest api', 'restful', 'restful api'],
    'graphql': ['graphql'],
    'websocket': ['websocket', 'ws'],
    'microservices': ['microservices', 'microservice architecture'],
    'serverless': ['serverless', 'lambda'],
    'pwa': ['pwa', 'progressive web app'],
    
    # Other
    'agile': ['agile', 'scrum', 'kanban'],
    'git': ['git', 'github', 'gitlab', 'version control'],
    'blockchain': ['blockchain', 'ethereum', 'solidity', 'smart contracts'],
    'security': ['security', 'infosec', 'cybersecurity', 'cyber security'],
    'linux': ['linux', 'unix', 'bash', 'shell scripting'],
    'ui/ux': ['ui/ux', 'ui design', 'ux design', 'user interface', 'user experience'],
}

def extract_skills_from_text(text, skill_dict=COMMON_SKILLS):
    """
    Extract skills from job title or description text.
    
    Args:
        text: Text to extract skills from
        skill_dict: Dictionary of skills and their patterns
        
    Returns:
        List of skills found in the text
    """
    if not text or pd.isna(text):
        return []
    
    text = str(text).lower()
    found_skills = []
    
    for skill, patterns in skill_dict.items():
        for pattern in patterns:
            # Use word boundary for more accurate matching
            if re.search(r'\b' + re.escape(pattern) + r'\b', text):
                found_skills.append(skill)
                break  # Found this skill, no need to check other patterns
    
    return found_skills

def extract_skills_from_jobs(df):
    """
    Extract skills from job titles in a dataframe.
    
    Args:
        df: DataFrame containing job posting data
        
    Returns:
        DataFrame with added 'skills' column
    """
    # Create a copy to avoid modifying the original
    skills_df = df.copy()
    
    # Extract skills from job titles
    skills_df['skills'] = skills_df['job_title'].apply(extract_skills_from_text)
    
    return skills_df

def get_top_skills(df, n=10):
    """
    Get top n skills from the job postings.
    
    Args:
        df: DataFrame containing job posting data with 'skills' column
        n: Number of top skills to return
        
    Returns:
        DataFrame with skill counts
    """
    # Ensure skills are extracted
    if 'skills' not in df.columns:
        skills_df = extract_skills_from_jobs(df)
    else:
        skills_df = df
    
    # Explode the skills lists into separate rows
    skills_exploded = skills_df.explode('skills')
    
    # Count occurrences of each skill
    skill_counts = skills_exploded['skills'].value_counts().reset_index()
    skill_counts.columns = ['skill', 'count']
    
    # Calculate percentage
    total_jobs = len(skills_df)
    skill_counts['percentage'] = (skill_counts['count'] / total_jobs) * 100
    
    # Return top n skills
    return skill_counts.head(n)

def plot_top_skills(df, n=15):
    """
    Create a bar chart of top skills.
    
    Args:
        df: DataFrame containing job posting data
        n: Number of top skills to display
        
    Returns:
        Plotly figure object
    """
    # Get top skills
    top_skills = get_top_skills(df, n)
    
    # If no skills found, return empty figure with message
    if len(top_skills) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No skills data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Create horizontal bar chart
    fig = px.bar(
        top_skills,
        y='skill',
        x='percentage',
        orientation='h',
        labels={'skill': 'Skill', 'percentage': 'Percentage of Job Postings'},
        title=f'Top {n} Skills in Demand',
        color='percentage',
        color_continuous_scale='Viridis',
        text='count'
    )
    
    # Improve layout
    fig.update_layout(
        xaxis_title='Percentage of Job Postings (%)',
        yaxis_title='Skill',
        yaxis={'categoryorder': 'total ascending'},
        height=max(400, len(top_skills) * 25)  # Adjust height based on number of skills
    )
    
    # Add data labels
    fig.update_traces(
        texttemplate='%{text} jobs',
        textposition='outside'
    )
    
    return fig

def skills_by_job_type(df):
    """
    Create a heatmap of skills by job type.
    
    Args:
        df: DataFrame containing job posting data
        
    Returns:
        Plotly figure object
    """
    # Ensure skills are extracted
    if 'skills' not in df.columns:
        skills_df = extract_skills_from_jobs(df)
    else:
        skills_df = df
    
    # Explode the skills lists into separate rows
    skills_exploded = skills_df.explode('skills')
    
    # Remove rows with no skills
    skills_exploded = skills_exploded.dropna(subset=['skills'])
    
    # If no skills found, return empty figure with message
    if len(skills_exploded) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No skills data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Get top 20 skills overall
    top_skills = get_top_skills(skills_df, 20)['skill'].tolist()
    
    # Filter to only include top skills
    skills_exploded = skills_exploded[skills_exploded['skills'].isin(top_skills)]
    
    # Create cross-tabulation of job types and skills
    cross_tab = pd.crosstab(
        index=skills_exploded['job_type'],
        columns=skills_exploded['skills'],
        normalize='index'  # Normalize by row (job type)
    ) * 100  # Convert to percentage
    
    # Sort skills by overall popularity
    cross_tab = cross_tab[top_skills]
    
    # Create heatmap
    fig = px.imshow(
        cross_tab,
        labels=dict(x='Skill', y='Job Type', color='Percentage (%)'),
        x=cross_tab.columns,
        y=cross_tab.index,
        color_continuous_scale='Viridis',
        title='Skills by Job Type',
        aspect='auto',  # Adjust aspect ratio automatically
        text_auto='.1f'  # Show one decimal place
    )
    
    # Improve layout
    fig.update_layout(
        height=max(400, len(cross_tab) * 30),  # Adjust height based on number of job types
        xaxis={'tickangle': 45}  # Angle skill names for better readability
    )
    
    return fig

def plot_skill_trends(df):
    """
    Create a line chart showing skill popularity trends over time.
    
    Args:
        df: DataFrame containing job posting data
        
    Returns:
        Plotly figure object
    """
    # Ensure skills are extracted
    if 'skills' not in df.columns:
        skills_df = extract_skills_from_jobs(df)
    else:
        skills_df = df
    
    # Explode the skills lists into separate rows
    skills_exploded = skills_df.explode('skills')
    
    # Remove rows with no skills
    skills_exploded = skills_exploded.dropna(subset=['skills'])
    
    # If no skills found, return empty figure with message
    if len(skills_exploded) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="No skills data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Get top 10 skills overall
    top_skills = get_top_skills(skills_df, 10)['skill'].tolist()
    
    # Filter to only include top skills
    skills_exploded = skills_exploded[skills_exploded['skills'].isin(top_skills)]
    
    # Group by month_year and skill, count occurrences
    skill_trends = skills_exploded.groupby(['month_year', 'skills']).size().reset_index(name='count')
    
    # Calculate total jobs per month for percentage calculation
    monthly_totals = skills_df.groupby('month_year').size().reset_index(name='total')
    
    # Merge the counts with totals
    skill_trends = skill_trends.merge(monthly_totals, on='month_year')
    
    # Calculate percentage
    skill_trends['percentage'] = (skill_trends['count'] / skill_trends['total']) * 100
    
    # Convert month_year to datetime for proper sorting
    skill_trends['date'] = pd.to_datetime(skill_trends['month_year'])
    skill_trends = skill_trends.sort_values('date')
    
    # Create the line chart
    fig = px.line(
        skill_trends,
        x='month_year',
        y='percentage',
        color='skills',
        markers=True,
        labels={'month_year': 'Month', 'percentage': 'Percentage of Job Postings', 'skills': 'Skill'},
        title='Skill Popularity Trends Over Time'
    )
    
    # Improve layout
    fig.update_layout(
        xaxis_title='Month',
        yaxis_title='Percentage of Job Postings (%)',
        legend_title='Skills'
    )
    
    return fig

def identify_emerging_skills(df, recent_periods=2):
    """
    Identify emerging skills with the highest growth rates.
    
    Args:
        df: DataFrame containing job posting data
        recent_periods: Number of recent periods to consider as "recent"
        
    Returns:
        DataFrame with skill growth rates
    """
    # Ensure skills are extracted
    if 'skills' not in df.columns:
        skills_df = extract_skills_from_jobs(df)
    else:
        skills_df = df
    
    # Explode the skills lists into separate rows
    skills_exploded = skills_df.explode('skills')
    
    # Remove rows with no skills
    skills_exploded = skills_exploded.dropna(subset=['skills'])
    
    # If no skills found, return empty DataFrame
    if len(skills_exploded) == 0:
        return pd.DataFrame()
    
    # Convert month_year to datetime for sorting
    skills_exploded['date'] = pd.to_datetime(skills_exploded['month_year'])
    
    # Sort by date
    skills_exploded = skills_exploded.sort_values('date')
    
    # Get unique months
    months = skills_exploded['month_year'].unique()
    
    # Need at least 2 months of data
    if len(months) < 2:
        return pd.DataFrame()
    
    # Get recent and previous months
    recent_months = months[-recent_periods:] if len(months) >= recent_periods else months[-1:]
    previous_months = months[:-recent_periods] if len(months) > recent_periods else months[0:1]
    
    # Count skills in recent and previous periods
    recent_skills = skills_exploded[skills_exploded['month_year'].isin(recent_months)]['skills'].value_counts()
    previous_skills = skills_exploded[skills_exploded['month_year'].isin(previous_months)]['skills'].value_counts()
    
    # Calculate growth rates
    growth_data = []
    
    for skill in set(recent_skills.index) | set(previous_skills.index):
        recent_count = recent_skills.get(skill, 0)
        previous_count = previous_skills.get(skill, 0)
        
        # Calculate growth
        if previous_count > 0:
            growth_pct = ((recent_count - previous_count) / previous_count) * 100
        elif recent_count > 0:
            growth_pct = 100  # New skill (wasn't in previous period)
        else:
            growth_pct = 0
        
        growth_data.append({
            'skill': skill,
            'recent_count': recent_count,
            'previous_count': previous_count,
            'growth_pct': growth_pct
        })
    
    # Convert to DataFrame
    growth_df = pd.DataFrame(growth_data)
    
    # Only include skills that appear at least 3 times in recent period
    growth_df = growth_df[growth_df['recent_count'] >= 3]
    
    # Sort by growth percentage
    growth_df = growth_df.sort_values('growth_pct', ascending=False)
    
    return growth_df

def plot_emerging_skills(df, n=10):
    """
    Create a bar chart of emerging skills with highest growth rates.
    
    Args:
        df: DataFrame containing job posting data
        n: Number of emerging skills to display
        
    Returns:
        Plotly figure object
    """
    # Get emerging skills
    emerging_skills = identify_emerging_skills(df)
    
    # If no skills found, return empty figure with message
    if len(emerging_skills) == 0:
        fig = go.Figure()
        fig.add_annotation(
            text="Not enough data to identify emerging skills",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Get top n emerging skills
    top_emerging = emerging_skills.head(n)
    
    # Create horizontal bar chart
    fig = px.bar(
        top_emerging,
        y='skill',
        x='growth_pct',
        orientation='h',
        labels={'skill': 'Skill', 'growth_pct': 'Growth Rate (%)', 'recent_count': 'Recent Job Count'},
        title=f'Top {n} Emerging Skills',
        color='growth_pct',
        color_continuous_scale='Viridis',
        text='recent_count',
        hover_data=['previous_count']
    )
    
    # Improve layout
    fig.update_layout(
        xaxis_title='Growth Rate (%)',
        yaxis_title='Skill',
        yaxis={'categoryorder': 'total ascending'},
        height=max(400, len(top_emerging) * 25)  # Adjust height based on number of skills
    )
    
    # Add data labels
    fig.update_traces(
        texttemplate='%{text} jobs',
        textposition='outside'
    )
    
    return fig