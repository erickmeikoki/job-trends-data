import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import re
from utils.skill_tracker import COMMON_SKILLS, extract_skills_from_text

def extract_resume_skills(resume_text):
    """
    Extract skills from resume text.
    
    Args:
        resume_text: Text content of resume
        
    Returns:
        List of skills found in the resume
    """
    return extract_skills_from_text(resume_text, COMMON_SKILLS)

def compare_resume_to_market(resume_skills, df):
    """
    Compare resume skills to job market demand.
    
    Args:
        resume_skills: List of skills extracted from resume
        df: DataFrame containing job posting data
        
    Returns:
        Dictionary with comparison results
    """
    # Ensure skills are extracted from job postings
    if 'skills' not in df.columns:
        from utils.skill_tracker import extract_skills_from_jobs
        job_df = extract_skills_from_jobs(df)
    else:
        job_df = df
    
    # Explode the skills lists into separate rows
    skills_exploded = job_df.explode('skills')
    
    # Get market demand for each skill
    market_demand = skills_exploded['skills'].value_counts().reset_index()
    market_demand.columns = ['skill', 'job_count']
    
    # Calculate percentage of jobs requiring each skill
    total_jobs = len(job_df)
    market_demand['demand_pct'] = (market_demand['job_count'] / total_jobs) * 100
    
    # Filter to only include skills in our resume
    resume_skill_demand = market_demand[market_demand['skill'].isin(resume_skills)]
    
    # Find missing in-demand skills (top 20 that aren't in the resume)
    top_skills = market_demand.head(20)['skill'].tolist()
    missing_skills = [skill for skill in top_skills if skill not in resume_skills]
    
    # Get skills that are on the resume but not in high demand
    low_demand_skills = resume_skill_demand[resume_skill_demand['demand_pct'] < 1]['skill'].tolist()
    
    # Calculate match percentage
    total_market_skills = len(market_demand)
    if total_market_skills > 0:
        resume_skills_in_market = len(resume_skill_demand)
        match_percentage = (resume_skills_in_market / min(len(resume_skills), 20)) * 100
    else:
        match_percentage = 0
    
    # Calculate market coverage
    if top_skills:
        top_skills_in_resume = [skill for skill in top_skills if skill in resume_skills]
        market_coverage = (len(top_skills_in_resume) / len(top_skills)) * 100
    else:
        market_coverage = 0
    
    # Calculate skill gap score (0-100)
    gap_score = (match_percentage + market_coverage) / 2
    
    return {
        'resume_skills': resume_skills,
        'skills_in_demand': resume_skill_demand.to_dict('records'),
        'missing_key_skills': missing_skills,
        'low_demand_skills': low_demand_skills,
        'match_percentage': match_percentage,
        'market_coverage': market_coverage,
        'gap_score': gap_score
    }

def find_matching_job_types(resume_skills, df, threshold=0.3):
    """
    Find job types that match the resume skills.
    
    Args:
        resume_skills: List of skills extracted from resume
        df: DataFrame containing job posting data
        threshold: Minimum skill match threshold
        
    Returns:
        DataFrame with matching job types and scores
    """
    # Ensure skills are extracted from job postings
    if 'skills' not in df.columns:
        from utils.skill_tracker import extract_skills_from_jobs
        job_df = extract_skills_from_jobs(df)
    else:
        job_df = df
    
    # Get job types with their required skills
    job_type_skills = {}
    for job_type, jobs in job_df.groupby('job_type'):
        # Combine all skills for this job type
        all_skills = set()
        for skills_list in jobs['skills']:
            all_skills.update(skills_list)
        job_type_skills[job_type] = list(all_skills)
    
    # Calculate match score for each job type
    job_type_matches = []
    
    for job_type, skills in job_type_skills.items():
        # Skip if no skills for this job type
        if not skills:
            continue
        
        # Calculate overlap
        matching_skills = [skill for skill in resume_skills if skill in skills]
        
        # Calculate match score
        match_score = len(matching_skills) / len(skills) if skills else 0
        
        # Only include if match score meets threshold
        if match_score >= threshold:
            job_type_matches.append({
                'job_type': job_type,
                'required_skills': len(skills),
                'matching_skills': len(matching_skills),
                'match_score': match_score,
                'match_percentage': match_score * 100
            })
    
    # Convert to DataFrame
    matches_df = pd.DataFrame(job_type_matches)
    
    # Sort by match score
    if not matches_df.empty:
        matches_df = matches_df.sort_values('match_score', ascending=False)
    
    return matches_df

def plot_skill_gap_analysis(resume_analysis):
    """
    Create a visual representation of the skill gap analysis.
    
    Args:
        resume_analysis: Dictionary with resume analysis results
        
    Returns:
        Plotly figure object
    """
    # Extract data from analysis
    skills_in_demand = resume_analysis['skills_in_demand']
    
    # If no skills in demand, return empty figure with message
    if not skills_in_demand:
        fig = go.Figure()
        fig.add_annotation(
            text="No skills from your resume match current market demand",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Create DataFrame for visualization
    skills_df = pd.DataFrame(skills_in_demand)
    
    # Sort by demand percentage
    skills_df = skills_df.sort_values('demand_pct', ascending=False)
    
    # Create bar chart
    fig = px.bar(
        skills_df,
        y='skill',
        x='demand_pct',
        orientation='h',
        labels={'skill': 'Skill', 'demand_pct': 'Market Demand (%)', 'job_count': 'Job Count'},
        title='Your Skills: Market Demand Analysis',
        color='demand_pct',
        color_continuous_scale='Viridis',
        text='job_count'
    )
    
    # Improve layout
    fig.update_layout(
        xaxis_title='Percentage of Job Postings (%)',
        yaxis_title='Skill',
        yaxis={'categoryorder': 'total ascending'},
        height=max(400, len(skills_df) * 25)  # Adjust height based on number of skills
    )
    
    # Add data labels
    fig.update_traces(
        texttemplate='%{text} jobs',
        textposition='outside'
    )
    
    return fig

def plot_missing_skills(resume_analysis):
    """
    Create a visual representation of missing in-demand skills.
    
    Args:
        resume_analysis: Dictionary with resume analysis results
        
    Returns:
        Plotly figure object
    """
    # Extract data from analysis
    missing_skills = resume_analysis['missing_key_skills']
    
    # If no missing skills, return empty figure with message
    if not missing_skills:
        fig = go.Figure()
        fig.add_annotation(
            text="Your resume covers all the top in-demand skills!",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Create DataFrame with placeholder demand values
    # In a real application, you would have actual demand data
    skills_df = pd.DataFrame({
        'skill': missing_skills,
        'importance': range(len(missing_skills), 0, -1)  # Proxy for importance
    })
    
    # Create bar chart
    fig = px.bar(
        skills_df,
        y='skill',
        x='importance',
        orientation='h',
        labels={'skill': 'Skill', 'importance': 'Market Importance'},
        title='Missing High-Demand Skills',
        color='importance',
        color_continuous_scale='Oranges'
    )
    
    # Improve layout
    fig.update_layout(
        xaxis_title='Relative Importance',
        yaxis_title='Skill',
        yaxis={'categoryorder': 'total ascending'},
        height=max(400, len(skills_df) * 25),  # Adjust height based on number of skills
        showlegend=False
    )
    
    # Hide x-axis as the importance is just a proxy
    fig.update_xaxes(showticklabels=False)
    
    return fig

def plot_job_type_matches(job_matches):
    """
    Create a visual representation of job type matches.
    
    Args:
        job_matches: DataFrame with job type matches
        
    Returns:
        Plotly figure object
    """
    # If no job matches, return empty figure with message
    if job_matches.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No job types match your skills at the specified threshold",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=20)
        )
        return fig
    
    # Create bar chart
    fig = px.bar(
        job_matches,
        y='job_type',
        x='match_percentage',
        orientation='h',
        labels={'job_type': 'Job Type', 'match_percentage': 'Match Percentage (%)'},
        title='Job Types Matching Your Skills',
        color='match_percentage',
        color_continuous_scale='Greens',
        hover_data=['matching_skills', 'required_skills']
    )
    
    # Improve layout
    fig.update_layout(
        xaxis_title='Match Percentage (%)',
        yaxis_title='Job Type',
        yaxis={'categoryorder': 'total ascending'},
        height=max(400, len(job_matches) * 25)  # Adjust height based on number of job types
    )
    
    # Add reference line for good match threshold
    fig.add_shape(
        type="line",
        x0=70,
        y0=-0.5,
        x1=70,
        y1=len(job_matches) - 0.5,
        line=dict(color="green", width=2, dash="dash")
    )
    
    # Add annotation for threshold
    fig.add_annotation(
        x=70,
        y=len(job_matches) - 1,
        text="Good Match",
        showarrow=True,
        arrowhead=1,
        ax=30,
        ay=0
    )
    
    return fig

def generate_skill_improvement_recommendations(resume_analysis, df):
    """
    Generate recommendations for skill improvement based on market demand.
    
    Args:
        resume_analysis: Dictionary with resume analysis results
        df: DataFrame containing job posting data
        
    Returns:
        Dictionary with skill improvement recommendations
    """
    # Missing key skills from the analysis
    missing_skills = resume_analysis['missing_key_skills']
    
    # Ensure skills are extracted from job postings
    if 'skills' not in df.columns:
        from utils.skill_tracker import extract_skills_from_jobs
        job_df = extract_skills_from_jobs(df)
    else:
        job_df = df
    
    # Find emerging skills
    from utils.skill_tracker import identify_emerging_skills
    emerging_skills_df = identify_emerging_skills(job_df)
    
    # Filter emerging skills to those not in resume
    resume_skills = resume_analysis['resume_skills']
    emerging_recommendations = emerging_skills_df[
        (emerging_skills_df['skill'].isin(missing_skills)) & 
        (emerging_skills_df['growth_pct'] > 0)
    ].head(5)
    
    # Get top paying skills that are missing from resume
    # This would require salary data with skill information
    # For simplification, we'll use the top missing skills
    salary_boosting_skills = missing_skills[:3]
    
    # Find complementary skills based on job type matches
    complementary_skills = []
    job_type_matches = resume_analysis.get('job_type_matches', [])
    
    if job_type_matches and not isinstance(job_type_matches, list) and not job_type_matches.empty:
        # Get top matching job type
        top_job_type = job_type_matches.iloc[0]['job_type']
        
        # Find skills commonly associated with this job type
        job_type_skills = job_df[job_df['job_type'] == top_job_type].explode('skills')['skills'].value_counts()
        
        # Filter to skills not in resume
        job_type_missing_skills = [skill for skill in job_type_skills.index[:5] if skill not in resume_skills]
        
        complementary_skills = job_type_missing_skills[:3]
    
    return {
        'high_impact_skills': missing_skills[:5],
        'emerging_skills': emerging_recommendations['skill'].tolist() if not emerging_recommendations.empty else [],
        'salary_boosting_skills': salary_boosting_skills,
        'complementary_skills': complementary_skills
    }

def extract_resume_experience(resume_text):
    """
    Extract years of experience from resume text.
    
    Args:
        resume_text: Text content of resume
        
    Returns:
        Estimated years of experience
    """
    # Common patterns for years of experience
    patterns = [
        r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
        r'experience\s*(?:of\s*)?(\d+)\+?\s*years?',
        r'(?:work|professional)\s+experience\s*(?:of\s*)?(\d+)\+?\s*years?',
        r'(?:worked|been working)\s+for\s+(\d+)\+?\s*years?'
    ]
    
    # Search for patterns
    for pattern in patterns:
        matches = re.findall(pattern, resume_text.lower())
        if matches:
            # Take the highest number
            years = max([int(year) for year in matches])
            return years
    
    # If no explicit years mentioned, try to estimate from work history
    work_history_pattern = r'((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})\s*(?:-|–|to)\s*((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4}|Present|Current|Now)'
    
    work_periods = re.findall(work_history_pattern, resume_text)
    
    if work_periods:
        total_months = 0
        current_year = datetime.datetime.now().year
        current_month = datetime.datetime.now().month
        
        for start, end in work_periods:
            # Parse start date
            try:
                start_date = pd.to_datetime(start)
                
                # Parse end date
                if any(current_term in end for current_term in ['Present', 'Current', 'Now']):
                    end_date = pd.to_datetime(f"{current_month}/{current_year}")
                else:
                    end_date = pd.to_datetime(end)
                
                # Calculate duration in months
                duration = (end_date.year - start_date.year) * 12 + (end_date.month - start_date.month)
                total_months += max(0, duration)
            
            except:
                # Skip if date parsing fails
                continue
        
        # Convert months to years
        return total_months / 12
    
    # Default if no experience information found
    return 0

def recommend_job_titles(resume_skills, experience_years, df):
    """
    Recommend job titles based on resume skills and experience.
    
    Args:
        resume_skills: List of skills extracted from resume
        experience_years: Years of experience
        df: DataFrame containing job posting data
        
    Returns:
        List of recommended job titles
    """
    # Ensure skills are extracted from job postings
    if 'skills' not in df.columns:
        from utils.skill_tracker import extract_skills_from_jobs
        job_df = extract_skills_from_jobs(df)
    else:
        job_df = df
    
    # Experience level mapping
    experience_levels = {
        'entry': (0, 2),
        'mid': (2, 5),
        'senior': (5, float('inf'))
    }
    
    # Determine experience level
    experience_level = None
    for level, (min_years, max_years) in experience_levels.items():
        if min_years <= experience_years < max_years:
            experience_level = level
            break
    
    if experience_level is None:
        experience_level = 'senior'  # Default to senior if not matched
    
    # Calculate skill match for each job title
    job_title_scores = {}
    
    for _, row in job_df.iterrows():
        job_title = row['job_title']
        job_skills = row['skills']
        
        # Skip if no skills for this job
        if not job_skills:
            continue
        
        # Calculate match score
        matching_skills = [skill for skill in resume_skills if skill in job_skills]
        match_score = len(matching_skills) / len(job_skills) if job_skills else 0
        
        # Adjust score based on experience level match
        if experience_level == 'entry' and ('senior' in job_title.lower() or 'lead' in job_title.lower()):
            match_score *= 0.5
        elif experience_level == 'mid' and 'senior' in job_title.lower():
            match_score *= 0.8
        elif experience_level == 'senior' and 'junior' in job_title.lower():
            match_score *= 0.5
        
        # Add or update score
        if job_title in job_title_scores:
            job_title_scores[job_title] = max(job_title_scores[job_title], match_score)
        else:
            job_title_scores[job_title] = match_score
    
    # Convert to DataFrame
    recommendations = pd.DataFrame({
        'job_title': list(job_title_scores.keys()),
        'match_score': list(job_title_scores.values())
    })
    
    # Sort by match score
    recommendations = recommendations.sort_values('match_score', ascending=False)
    
    # Get top 10 recommendations
    top_recommendations = recommendations.head(10)['job_title'].tolist()
    
    return top_recommendations