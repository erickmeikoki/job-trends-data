import streamlit as st
import pandas as pd
import numpy as np
import io
import re
import datetime
import plotly.express as px
import plotly.graph_objects as go
from utils.data_processor import process_data, generate_sample_schema
from utils.database import (
    get_all_job_postings, 
    add_job_posting, 
    delete_job_posting, 
    get_connection_status,
    add_multiple_job_postings
)
from utils.visualizer import (
    plot_jobs_by_month,
    plot_jobs_by_type,
    plot_jobs_trend,
    plot_company_distribution,
    plot_geographical_distribution,
    plot_location_type_distribution,
    extract_region
)
from utils.predictor import (
    forecast_job_trends,
    predict_job_type_growth,
    plot_job_forecast,
    plot_job_type_growth_forecast
)
# Import new feature modules
from utils.salary_analyzer import (
    extract_salary_range,
    plot_salary_by_job_type,
    plot_salary_by_region,
    plot_salary_trends,
    get_salary_statistics
)
from utils.job_comparator import (
    compare_job_postings_over_time,
    create_side_by_side_comparison,
    compare_growth_rates,
    create_heatmap_comparison
)
from utils.skill_tracker import (
    extract_skills_from_jobs,
    plot_top_skills,
    skills_by_job_type,
    plot_skill_trends,
    plot_emerging_skills
)
from utils.company_analyzer import (
    analyze_company_hiring_patterns,
    detect_hiring_surges,
    plot_hiring_alerts,
    analyze_company_seasonality,
    compare_company_job_types,
    calculate_company_growth_rates
)
from utils.market_health import (
    calculate_job_market_health_index,
    plot_job_market_health_index,
    get_market_health_insights,
    plot_market_health_components,
    plot_regional_health_comparison
)
from utils.live_data import (
    fetch_job_data_from_api,
    process_api_response,
    scrape_jobs_from_website,
    schedule_data_refresh,
    import_jobs_from_linkedin_export,
    import_jobs_from_indeed_export
)
from utils.resume_analyzer import (
    extract_resume_skills,
    compare_resume_to_market,
    find_matching_job_types,
    plot_skill_gap_analysis,
    plot_job_type_matches,
    generate_skill_improvement_recommendations
)
from utils.job_alerts import (
    create_job_alert,
    rank_job_matches,
    extract_user_preferences_from_text,
    save_user_alert,
    get_saved_alerts,
    delete_user_alert,
    get_matching_job_count,
    plot_preference_match_distribution
)
from utils.interview_tracker import (
    validate_interview_data,
    calculate_company_difficulty_ratings,
    plot_company_difficulty_comparison,
    plot_interview_difficulty_trend,
    plot_interview_components_comparison,
    plot_interview_success_factors,
    get_interview_preparation_tips
)

# Set page configuration
st.set_page_config(
    page_title="SWE Job Tracker",
    page_icon="💻",
    layout="wide"
)

# Initialize session state variables
if "data" not in st.session_state:
    # Try to load data from database
    db_data = get_all_job_postings()
    if not db_data.empty:
        st.session_state.data = process_data(db_data)
    else:
        st.session_state.data = None

# Check database connection
db_connected = get_connection_status()

# Application title
st.title("Software Engineering Job Posting Tracker")
st.write("Track and visualize software engineering job trends over time")

# Show database connection status
if db_connected:
    st.sidebar.success("✅ Connected to database")
else:
    st.sidebar.error("❌ Database connection failed")

# Sidebar for data input and filtering
st.sidebar.header("Data Management")

# Option to upload data or manually input
data_input_method = st.sidebar.radio(
    "Choose data input method:",
    ["Upload CSV file", "Manual data entry"]
)

if data_input_method == "Upload CSV file":
    upload_file = st.sidebar.file_uploader(
        "Upload your job posting data (CSV)",
        type=["csv"],
        help="File should contain: date, job_title, job_type, company, location, salary"
    )
    
    # Option to save to database
    save_to_db = st.sidebar.checkbox("Save to database", value=True, disabled=not db_connected)
    
    if upload_file is not None:
        try:
            data = pd.read_csv(upload_file)
            processed_data = process_data(data)
            
            # Save to database if requested
            if save_to_db and db_connected:
                success_count, error_count = add_multiple_job_postings(processed_data)
                if error_count > 0:
                    st.sidebar.warning(f"Added {success_count} job postings, but {error_count} failed.")
                else:
                    st.sidebar.success(f"Added {success_count} job postings to database!")
                
                # Refresh data from database
                st.session_state.data = get_all_job_postings()
                st.sidebar.info("Data loaded from database!")
            else:
                st.session_state.data = processed_data
                st.sidebar.success("Data loaded successfully!")
                
        except Exception as e:
            st.sidebar.error(f"Error loading data: {e}")
            
            # Display expected schema
            st.sidebar.info("Expected CSV format:")
            st.sidebar.code(generate_sample_schema())
            
else:  # Manual data entry
    st.sidebar.subheader("Add New Job Posting")
    
    with st.sidebar.form("job_entry_form"):
        posting_date = st.date_input("Posting Date")
        job_title = st.text_input("Job Title")
        
        job_type = st.selectbox(
            "Job Type",
            ["Frontend", "Backend", "Full-Stack", "DevOps", "Data Engineering", 
             "Machine Learning", "Mobile", "QA/Testing", "Cybersecurity", 
             "Game Development", "Embedded", "AR/VR", "Other"]
        )
        
        company = st.text_input("Company")
        location = st.text_input("Location")
        salary = st.text_input("Salary (optional)")
        
        save_to_db = st.checkbox("Save to database", value=True, disabled=not db_connected)
        
        submit_button = st.form_submit_button("Add Job Posting")
        
        if submit_button:
            if not job_title or not company:
                st.sidebar.error("Please fill in all required fields")
            else:
                # Create new data entry
                new_entry = pd.DataFrame({
                    'date': [posting_date],
                    'job_title': [job_title],
                    'job_type': [job_type],
                    'company': [company],
                    'location': [location],
                    'salary': [salary]
                })
                
                # Save to database if requested
                if save_to_db and db_connected:
                    success = add_job_posting(
                        date=posting_date,
                        job_title=job_title,
                        job_type=job_type,
                        company=company,
                        location=location,
                        salary=salary
                    )
                    
                    if success:
                        st.sidebar.success("Job posting added to database!")
                        # Refresh data from database
                        st.session_state.data = get_all_job_postings()
                    else:
                        st.sidebar.error("Failed to add job posting to database")
                else:
                    # Add to existing data or create new dataframe
                    if st.session_state.data is not None:
                        st.session_state.data = pd.concat([st.session_state.data, new_entry], ignore_index=True)
                    else:
                        st.session_state.data = process_data(new_entry)
                        
                    st.sidebar.success("Job posting added!")
                
                st.rerun()

# Filtering options (only shown if data exists)
if st.session_state.data is not None and not st.session_state.data.empty:
    st.sidebar.header("Data Filters")
    
    # Date range filter
    min_date = st.session_state.data['date'].min().date()
    max_date = st.session_state.data['date'].max().date()
    
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Job type filter
    all_job_types = st.session_state.data['job_type'].unique().tolist()
    selected_job_types = st.sidebar.multiselect(
        "Job Types",
        options=all_job_types,
        default=all_job_types
    )
    
    # Company filter
    all_companies = st.session_state.data['company'].unique().tolist()
    selected_companies = st.sidebar.multiselect(
        "Companies",
        options=all_companies,
        default=[]  # Default to no filtering by company
    )
    
    # Apply filters
    filtered_data = st.session_state.data.copy()
    
    # Date filter
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_data = filtered_data[
            (filtered_data['date'].dt.date >= start_date) & 
            (filtered_data['date'].dt.date <= end_date)
        ]
    
    # Job type filter
    if selected_job_types:
        filtered_data = filtered_data[filtered_data['job_type'].isin(selected_job_types)]
    
    # Company filter
    if selected_companies:
        filtered_data = filtered_data[filtered_data['company'].isin(selected_companies)]

# Main content - Data Visualization and Analysis
if st.session_state.data is None or st.session_state.data.empty:
    st.info("No data available. Please upload a CSV file or add job postings manually.")
    
    # Check if database has data
    if db_connected:
        db_data = get_all_job_postings()
        if not db_data.empty:
            if st.button("Load data from database"):
                st.session_state.data = db_data
                st.rerun()
    
    # Show example schema
    st.subheader("Expected Data Format")
    st.code(generate_sample_schema())
    
else:
    # Display data statistics
    st.header("Job Posting Data")
    
    # Display filtered data or all data
    if 'filtered_data' in locals() and not filtered_data.empty:
        display_data = filtered_data
        st.write(f"Showing {len(filtered_data)} job postings (filtered)")
    else:
        display_data = st.session_state.data
        st.write(f"Showing all {len(st.session_state.data)} job postings")
    
    # Data table with pagination
    st.dataframe(display_data)
    
    # Data download button
    csv_buffer = io.StringIO()
    display_data.to_csv(csv_buffer, index=False)
    csv_str = csv_buffer.getvalue()
    
    st.download_button(
        label="Download data as CSV",
        data=csv_str,
        file_name="swe_job_postings.csv",
        mime="text/csv"
    )
    
    # Visualizations section
    st.header("Job Posting Visualizations")
    
    tabs = st.tabs([
        "Monthly Trends", 
        "Job Types", 
        "Time Series Analysis", 
        "Company Distribution",
        "Geographical Distribution",
        "Remote vs On-site",
        "Predictions & Forecasts",
        "Salary Analytics",
        "Job Comparison",
        "Skill Demand",
        "Company Insights",
        "Market Health",
        "Live Data",
        "Resume Analysis",
        "Job Alerts",
        "Interview Tracker",
        "Compensation",
        "Career Paths",
        "Application Tracker",
        "Sentiment Analysis",
        "Networking",
        "Learning Resources",
        "Company Culture",
        "User Profiles",
        "Notifications"
    ])
    
    with tabs[0]:
        st.subheader("Job Postings by Month")
        fig1 = plot_jobs_by_month(display_data)
        st.plotly_chart(fig1, use_container_width=True)
    
    with tabs[1]:
        st.subheader("Job Postings by Type")
        fig2 = plot_jobs_by_type(display_data)
        st.plotly_chart(fig2, use_container_width=True)
    
    with tabs[2]:
        st.subheader("Job Posting Trends Over Time")
        fig3 = plot_jobs_trend(display_data)
        st.plotly_chart(fig3, use_container_width=True)
    
    with tabs[3]:
        st.subheader("Top Companies Hiring")
        fig4 = plot_company_distribution(display_data)
        st.plotly_chart(fig4, use_container_width=True)
        
    with tabs[4]:
        st.subheader("Geographical Distribution")
        fig5 = plot_geographical_distribution(display_data)
        st.plotly_chart(fig5, use_container_width=True)
        
        # Add help text explaining regions
        with st.expander("About Geographical Regions"):
            st.markdown("""
            **How regions are determined:**
            - **US West**: Includes California, Washington, Oregon, Colorado, Arizona, Utah, Nevada, and major cities like San Francisco, Seattle, Los Angeles, Denver, Portland
            - **US East**: Includes New York, Massachusetts, Georgia, Florida, North Carolina, Virginia, and major cities like NYC, Boston, Atlanta, Miami
            - **US Central**: Includes Texas, Illinois, Michigan, Minnesota, and major cities like Chicago, Austin, Dallas, Minneapolis, Detroit
            - **North America**: Includes Canada and major Canadian cities
            - **Europe**: Includes UK, Germany, France, Ireland, Netherlands and their major cities
            - **Asia**: Includes Singapore, Japan, India, South Korea, Hong Kong
            - **Australia**: Includes Sydney, Melbourne and other Australian locations
            - **Remote**: Jobs specifically marked as fully remote
            - **Hybrid**: Jobs with hybrid work arrangements
            - **Other**: Locations that don't fit into the above categories
            """)
    
    with tabs[5]:
        st.subheader("Job Types by Work Arrangement")
        fig6 = plot_location_type_distribution(display_data)
        st.plotly_chart(fig6, use_container_width=True)
        
    with tabs[6]:
        st.subheader("Predictive Analytics")
        
        # Only show predictions if we have enough data
        if len(display_data['month_year'].unique()) >= 3:
            # Forecasting options
            pred_col1, pred_col2 = st.columns([1, 3])
            
            with pred_col1:
                # Forecast period selection
                forecast_periods = st.slider(
                    "Forecast Periods (Months)",
                    min_value=1,
                    max_value=12,
                    value=6,
                    step=1,
                    help="Number of future months to forecast"
                )
                
                # Job type selection for specific forecasts
                job_type_options = ["All Jobs"] + display_data['job_type'].unique().tolist()
                selected_job_type = st.selectbox(
                    "Job Type to Forecast",
                    options=job_type_options
                )
                
                # Fix job type selection
                forecast_job_type = None if selected_job_type == "All Jobs" else selected_job_type
                
                st.write("### Insights")
                st.info("""
                **How it works:** The prediction model uses past job posting trends to forecast 
                future patterns. The forecast shows the expected number of job postings for 
                future months based on historical data patterns.
                
                Confidence intervals (shaded area) show the range of possible values, with wider 
                intervals indicating greater uncertainty.
                """)
                
                # Show accuracy disclaimer
                st.warning("""
                **Note:** Prediction accuracy depends on data quantity and quality. 
                More historical data provides better predictions.
                """)
            
            with pred_col2:
                # Job Posting Forecast
                try:
                    forecast_fig = plot_job_forecast(
                        display_data, 
                        periods=forecast_periods,
                        job_type=forecast_job_type
                    )
                    st.plotly_chart(forecast_fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error generating forecast: {e}")
                    st.info("Try selecting a different job type or adjusting the forecast period.")
            
            # Job Growth Prediction
            st.subheader("Predicted Job Type Growth")
            
            try:
                # Calculate growth rates
                growth_rates = predict_job_type_growth(display_data, periods=forecast_periods)
                
                # Plot growth rates
                growth_fig = plot_job_type_growth_forecast(growth_rates)
                st.plotly_chart(growth_fig, use_container_width=True)
                
                # Show detailed growth table
                st.write("#### Detailed Growth Projections")
                st.dataframe(growth_rates, use_container_width=True)
                
                # Highlight fastest growing job types
                if not growth_rates.empty:
                    fastest_growing = growth_rates.index[0]
                    growth_pct = growth_rates.loc[fastest_growing, 'Growth %']
                    
                    if growth_pct > 0:
                        st.success(f"🚀 **Fastest growing job type:** {fastest_growing} with projected growth of {growth_pct:.1f}%")
                    
                    # Highlight declining job types
                    declining = growth_rates[growth_rates['Growth %'] < 0]
                    if not declining.empty:
                        st.warning(f"📉 **{len(declining)} job types show declining trends** in the forecast period.")
            
            except Exception as e:
                st.error(f"Error generating job growth predictions: {e}")
                st.info("This may be due to insufficient data for certain job types.")
        else:
            st.warning("⚠️ Not enough data for predictions. At least 3 months of data is required.")
            st.info("Add more job postings across different months to enable predictive analytics.")
    
    # Job Market Analysis
    st.header("Job Market Analysis")
    
    # Prepare geographical distribution data
    geo_data = display_data.copy()
    geo_data['region'] = geo_data['location'].apply(extract_region)
    
    # Basic statistics in columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Job Postings", 
            value=len(display_data)
        )
    
    with col2:
        if not display_data.empty:
            most_common_type = display_data['job_type'].value_counts().idxmax()
            type_count = display_data['job_type'].value_counts().max()
            st.metric(
                label="Most Common Job Type", 
                value=f"{most_common_type} ({type_count})"
            )
        else:
            st.metric(label="Most Common Job Type", value="N/A")
    
    with col3:
        if not display_data.empty:
            monthly_trend = display_data.groupby(display_data['date'].dt.to_period('M')).size()
            if len(monthly_trend) >= 2:
                latest_month = monthly_trend.index[-1]
                prev_month = monthly_trend.index[-2]
                latest_count = monthly_trend[latest_month]
                prev_count = monthly_trend[prev_month]
                percent_change = ((latest_count - prev_count) / prev_count) * 100 if prev_count > 0 else 0
                
                st.metric(
                    label=f"Latest Month Trend ({latest_month})",
                    value=latest_count,
                    delta=f"{percent_change:.1f}%"
                )
            else:
                st.metric(
                    label="Latest Month Trend",
                    value=monthly_trend.iloc[0] if len(monthly_trend) > 0 else "N/A"
                )
        else:
            st.metric(label="Latest Month Trend", value="N/A")
            
    with col4:
        if not geo_data.empty:
            most_common_region = geo_data['region'].value_counts().idxmax()
            region_count = geo_data['region'].value_counts().max()
            region_percent = (region_count / len(geo_data)) * 100
            st.metric(
                label="Most Common Region", 
                value=most_common_region,
                delta=f"{region_percent:.1f}% of all jobs"
            )
        else:
            st.metric(label="Most Common Region", value="N/A")
    
    # Additional job market insights
    if not display_data.empty:
        st.subheader("Job Type Distribution")
        job_type_counts = display_data['job_type'].value_counts()
        st.bar_chart(job_type_counts)
        
        # Future Job Market Forecast
        if len(display_data['month_year'].unique()) >= 3:
            st.subheader("Future Job Market Forecast")
            
            forecast_col1, forecast_col2 = st.columns([3, 1])
            
            with forecast_col1:
                # Add a 3-month forecast for all jobs
                try:
                    quick_forecast_fig = plot_job_forecast(
                        display_data, 
                        periods=3,  # 3-month forecast
                        job_type=None  # All jobs
                    )
                    st.plotly_chart(quick_forecast_fig, use_container_width=True)
                except Exception as e:
                    st.error(f"Error generating quick forecast: {e}")
            
            with forecast_col2:
                # Show key insights
                try:
                    # Get growth rates for next 3 months
                    growth_rates = predict_job_type_growth(display_data, periods=3)
                    
                    if not growth_rates.empty:
                        st.write("### Key Growth Insights")
                        
                        # Get fastest growing job type
                        fastest_growing = growth_rates.index[0]
                        growth_pct = growth_rates.loc[fastest_growing, 'Growth %']
                        
                        st.metric(
                            label="Fastest Growing Job Type", 
                            value=fastest_growing,
                            delta=f"{growth_pct:.1f}%"
                        )
                        
                        # Get most declining job type (if any are declining)
                        declining = growth_rates[growth_rates['Growth %'] < 0]
                        if not declining.empty:
                            most_declining = declining.index[-1]
                            decline_pct = growth_rates.loc[most_declining, 'Growth %']
                            
                            st.metric(
                                label="Most Declining Job Type", 
                                value=most_declining,
                                delta=f"{decline_pct:.1f}%"
                            )
                        
                        # Overall market prediction
                        overall_growth = growth_rates['Growth %'].mean()
                        market_sentiment = "Growing" if overall_growth > 0 else "Declining"
                        
                        st.metric(
                            label="Overall Market Prediction", 
                            value=market_sentiment,
                            delta=f"{overall_growth:.1f}% avg"
                        )
                        
                        # Show note about predictions
                        st.info("These predictions are based on current trends and may change as new data becomes available.")
                
                except Exception as e:
                    st.error(f"Error generating growth insights: {e}")
                    st.info("Try adding more job posting data across a wider time range.")
                    
    # New Tabs Implementation
    with tabs[7]:  # Salary Analytics Tab
        st.subheader("Salary Analysis")
        
        # Process salary data
        salary_data = display_data.copy()
        try:
            salary_data = extract_salary_range(salary_data)
            
            # Check if we have any salary data
            if 'avg_salary' in salary_data.columns and not salary_data['avg_salary'].isna().all():
                # Display salary statistics
                salary_stats = get_salary_statistics(salary_data)
                if salary_stats['has_data']:
                    stats_col1, stats_col2, stats_col3 = st.columns(3)
                    
                    with stats_col1:
                        st.metric("Average Salary", f"${salary_stats['mean']:,.0f}")
                    
                    with stats_col2:
                        st.metric("Median Salary", f"${salary_stats['median']:,.0f}")
                    
                    with stats_col3:
                        if 'highest_paying_job_type' in salary_stats:
                            st.metric(
                                "Highest Paying Job Type", 
                                salary_stats['highest_paying_job_type']['job_type'],
                                f"${salary_stats['highest_paying_job_type']['mean_salary']:,.0f}"
                            )
                    
                    # Salary distribution by job type
                    st.subheader("Salary Distribution by Job Type")
                    salary_job_fig = plot_salary_by_job_type(salary_data)
                    st.plotly_chart(salary_job_fig, use_container_width=True)
                    
                    # Salary by region
                    st.subheader("Average Salary by Region")
                    salary_region_fig = plot_salary_by_region(salary_data)
                    st.plotly_chart(salary_region_fig, use_container_width=True)
                    
                    # Salary trends over time
                    if len(salary_data['month_year'].unique()) >= 2:
                        st.subheader("Salary Trends Over Time")
                        salary_trends_fig = plot_salary_trends(salary_data)
                        st.plotly_chart(salary_trends_fig, use_container_width=True)
                else:
                    st.info("No salary data available in the current dataset.")
                    st.write("To analyze salaries, add salary information to your job posting data.")
            else:
                st.info("No salary data available in the current dataset.")
                st.write("To analyze salaries, add salary information to your job posting data.")
        except Exception as e:
            st.error(f"Error analyzing salary data: {e}")
            st.info("This may be due to missing or improperly formatted salary information.")
            
    with tabs[8]:  # Job Comparison Tab
        st.subheader("Job Posting Comparison")
        
        comparison_col1, comparison_col2 = st.columns([1, 3])
        
        with comparison_col1:
            # Comparison type selection
            comparison_type = st.radio(
                "Compare by:",
                ["Job Type", "Company"],
                help="Choose whether to compare job types or companies"
            )
            
            if comparison_type == "Job Type":
                # Job type selection for comparison
                job_types_for_comparison = st.multiselect(
                    "Select Job Types to Compare",
                    options=display_data['job_type'].unique().tolist(),
                    default=display_data['job_type'].value_counts().nlargest(3).index.tolist()
                )
                companies_for_comparison = None
            else:
                # Company selection for comparison
                companies_for_comparison = st.multiselect(
                    "Select Companies to Compare",
                    options=display_data['company'].unique().tolist(),
                    default=display_data['company'].value_counts().nlargest(3).index.tolist()
                )
                job_types_for_comparison = None
            
            # Comparison visualization type
            viz_type = st.selectbox(
                "Visualization Type",
                ["Trend Over Time", "Side-by-Side", "Growth Rates", "Heatmap"],
                help="Choose the type of comparative visualization"
            )
        
        with comparison_col2:
            # Generate the selected comparison visualization
            try:
                if viz_type == "Trend Over Time":
                    fig = compare_job_postings_over_time(
                        display_data, 
                        job_types=job_types_for_comparison,
                        companies=companies_for_comparison
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                elif viz_type == "Side-by-Side":
                    if comparison_type == "Job Type" and job_types_for_comparison:
                        fig = create_side_by_side_comparison(
                            display_data,
                            items=job_types_for_comparison,
                            column='job_type'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    elif comparison_type == "Company" and companies_for_comparison:
                        fig = create_side_by_side_comparison(
                            display_data,
                            items=companies_for_comparison,
                            column='company'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Please select items to compare.")
                
                elif viz_type == "Growth Rates":
                    if comparison_type == "Job Type" and job_types_for_comparison:
                        fig = compare_growth_rates(
                            display_data,
                            items=job_types_for_comparison,
                            column='job_type'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    elif comparison_type == "Company" and companies_for_comparison:
                        fig = compare_growth_rates(
                            display_data,
                            items=companies_for_comparison,
                            column='company'
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Please select items to compare.")
                
                elif viz_type == "Heatmap":
                    if comparison_type == "Job Type":
                        fig = create_heatmap_comparison(display_data, rows='job_type', cols='region')
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        fig = create_heatmap_comparison(display_data, rows='company', cols='job_type')
                        st.plotly_chart(fig, use_container_width=True)
            
            except Exception as e:
                st.error(f"Error generating comparison: {e}")
                st.info("This may be due to insufficient data for comparison. Try selecting different items or visualization type.")
                
    with tabs[9]:  # Skill Demand Tab
        st.subheader("Skill Demand Analysis")
        
        # Extract skills from job titles
        skills_data = display_data.copy()
        
        try:
            # Check if skills already extracted, if not extract them
            if 'skills' not in skills_data.columns:
                skills_data = extract_skills_from_jobs(skills_data)
            
            # Check if we have any skill data
            if 'skills' in skills_data.columns and not skills_data['skills'].apply(lambda x: len(x) if isinstance(x, list) else 0).sum() == 0:
                # Top skills visualization
                st.subheader("Top Skills in Demand")
                
                skill_count_fig = plot_top_skills(skills_data, n=15)
                st.plotly_chart(skill_count_fig, use_container_width=True)
                
                # Skills by job type
                st.subheader("Skills Required by Job Type")
                skill_job_fig = skills_by_job_type(skills_data)
                st.plotly_chart(skill_job_fig, use_container_width=True)
                
                # Skill trends over time
                if len(skills_data['month_year'].unique()) >= 2:
                    st.subheader("Skill Popularity Trends")
                    skill_trend_fig = plot_skill_trends(skills_data)
                    st.plotly_chart(skill_trend_fig, use_container_width=True)
                
                # Emerging skills 
                if len(skills_data['month_year'].unique()) >= 2:
                    st.subheader("Emerging Skills")
                    emerging_fig = plot_emerging_skills(skills_data)
                    st.plotly_chart(emerging_fig, use_container_width=True)
                    
                    st.info("Emerging skills are those showing the highest growth rates in recent job postings. "
                           "These skills may represent new technologies or methodologies gaining traction in the industry.")
            else:
                st.info("No skill data could be extracted from the current dataset.")
                st.write("The system automatically extracts skills from job titles. Try adding more descriptive job titles or manually add skill information.")
        
        except Exception as e:
            st.error(f"Error analyzing skill demand: {e}")
            st.info("This may be due to an issue with extracting skills from the current dataset.")
            
    with tabs[10]:  # Company Insights Tab
        st.subheader("Company Hiring Patterns")
        
        company_col1, company_col2 = st.columns([1, 3])
        
        with company_col1:
            # Company selection for analysis
            company_options = ["All Top Companies"] + display_data['company'].value_counts().nlargest(20).index.tolist()
            selected_company = st.selectbox(
                "Select Company to Analyze",
                options=company_options,
                help="Choose a specific company or view top companies"
            )
            
            # Analysis type selection
            analysis_type = st.radio(
                "Analysis Type",
                ["Hiring Patterns", "Hiring Alerts", "Job Type Distribution", "Seasonality"],
                help="Choose the type of company analysis"
            )
            
            if analysis_type == "Hiring Patterns" and selected_company == "All Top Companies":
                top_n = st.slider("Number of Top Companies", 3, 10, 5)
            else:
                top_n = 5
        
        with company_col2:
            try:
                if analysis_type == "Hiring Patterns":
                    # If specific company selected
                    if selected_company != "All Top Companies":
                        fig = analyze_company_hiring_patterns(display_data, company=selected_company)
                    else:
                        fig = analyze_company_hiring_patterns(display_data, top_n=top_n)
                    
                    st.plotly_chart(fig, use_container_width=True)
                
                elif analysis_type == "Hiring Alerts":
                    # Detect hiring surges
                    surge_data = detect_hiring_surges(display_data)
                    
                    if not surge_data.empty:
                        fig = plot_hiring_alerts(display_data)
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Show detailed table of all changes
                        with st.expander("Detailed Hiring Activity"):
                            st.dataframe(surge_data.sort_values('pct_change', ascending=False, key=abs))
                    else:
                        st.info("No unusual hiring activity detected in the current dataset.")
                        st.write("This analysis requires at least two consecutive months of data.")
                
                elif analysis_type == "Job Type Distribution":
                    if selected_company != "All Top Companies":
                        companies_to_analyze = [selected_company]
                    else:
                        companies_to_analyze = display_data['company'].value_counts().nlargest(top_n).index.tolist()
                    
                    fig = compare_company_job_types(display_data, companies=companies_to_analyze)
                    st.plotly_chart(fig, use_container_width=True)
                
                elif analysis_type == "Seasonality" and selected_company != "All Top Companies":
                    fig = analyze_company_seasonality(display_data, company=selected_company)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    st.info("Seasonal patterns show how a company's hiring varies throughout the year. "
                           "This can help identify peak hiring seasons and plan job applications accordingly.")
                elif analysis_type == "Seasonality":
                    st.info("Please select a specific company to analyze seasonality.")
            
            except Exception as e:
                st.error(f"Error analyzing company insights: {e}")
                st.info("This may be due to insufficient data for the selected analysis.")
        
        # Calculate company growth rates
        if len(display_data['month_year'].unique()) >= 2:
            st.subheader("Company Growth Rates")
            
            try:
                growth_df = calculate_company_growth_rates(display_data)
                
                if not growth_df.empty:
                    # Display top growing companies
                    top_growth_df = growth_df.head(10).reset_index(drop=True)
                    
                    growth_col1, growth_col2 = st.columns([3, 2])
                    
                    with growth_col1:
                        # Create bar chart for growth rates
                        fig = px.bar(
                            top_growth_df,
                            y='company',
                            x='growth_pct',
                            orientation='h',
                            color='growth_pct',
                            color_continuous_scale='RdYlGn',
                            labels={'company': 'Company', 'growth_pct': 'Growth Rate (%)', 'total_count': 'Total Job Postings'},
                            title='Top Companies by Growth Rate',
                            hover_data=['recent_count', 'previous_count', 'total_count']
                        )
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with growth_col2:
                        # Show data table
                        st.write("#### Company Growth Details")
                        st.dataframe(
                            top_growth_df[['company', 'growth_pct', 'recent_count', 'previous_count']].rename(
                                columns={
                                    'growth_pct': 'Growth %', 
                                    'recent_count': 'Recent Jobs', 
                                    'previous_count': 'Previous Jobs'
                                }
                            ),
                            use_container_width=True
                        )
                        
                        # Show insights
                        if not top_growth_df.empty:
                            fastest_growing = top_growth_df.iloc[0]['company']
                            growth_pct = top_growth_df.iloc[0]['growth_pct']
                            
                            st.success(f"🚀 **Fastest growing company:** {fastest_growing} with {growth_pct:.1f}% growth")
                            
                            # Check for declining companies
                            declining = growth_df[growth_df['growth_pct'] < 0]
                            if not declining.empty:
                                st.warning(f"📉 **{len(declining)} companies show declining hiring** in recent periods.")
                else:
                    st.info("Insufficient data to calculate company growth rates.")
            
            except Exception as e:
                st.error(f"Error calculating company growth rates: {e}")
                st.info("This analysis requires data from multiple time periods.")
                
    with tabs[11]:  # Market Health Tab
        st.subheader("Job Market Health Index")
        
        # Create columns for overview
        health_col1, health_col2 = st.columns([2, 1])
        
        try:
            # Calculate market health index
            if len(display_data['month_year'].unique()) >= 2:
                health_data = calculate_job_market_health_index(display_data)
                
                if not health_data.empty:
                    with health_col1:
                        # Plot market health index
                        health_fig = plot_job_market_health_index(display_data)
                        st.plotly_chart(health_fig, use_container_width=True)
                    
                    with health_col2:
                        # Get market health insights
                        health_insights = get_market_health_insights(display_data)
                        
                        if health_insights['has_data']:
                            # Display market health dashboard
                            st.markdown(f"### Current Market: {health_insights['sentiment']}")
                            
                            # Create gauge chart for health index
                            current_index = health_insights['current_index']
                            
                            gauge_fig = go.Figure(go.Indicator(
                                mode = "gauge+number+delta",
                                value = current_index,
                                domain = {'x': [0, 1], 'y': [0, 1]},
                                title = {'text': "Market Health", 'font': {'size': 20}},
                                delta = {'reference': 50, 'position': "bottom"},
                                gauge = {
                                    'axis': {'range': [0, 100], 'tickwidth': 1},
                                    'bar': {'color': health_insights['color']},
                                    'steps': [
                                        {'range': [0, 30], 'color': 'firebrick'},
                                        {'range': [30, 45], 'color': 'darkorange'},
                                        {'range': [45, 55], 'color': 'cornflowerblue'},
                                        {'range': [55, 70], 'color': 'forestgreen'},
                                        {'range': [70, 100], 'color': 'darkgreen'},
                                    ],
                                    'threshold': {
                                        'line': {'color': "black", 'width': 2},
                                        'thickness': 0.75,
                                        'value': 50
                                    }
                                }
                            ))
                            
                            gauge_fig.update_layout(height=200, margin=dict(l=10, r=10, t=30, b=10))
                            st.plotly_chart(gauge_fig, use_container_width=True)
                            
                            # Add market description
                            st.info(health_insights['description'])
                            
                            # Add trend information
                            st.write(f"**Market Trend:** {health_insights['trend_icon']} {health_insights['trend']}")
                            st.write(health_insights['trend_description'])
                            
                            # Show when last updated
                            st.write(f"*Last updated: {health_insights['last_updated']}*")
                    
                    # Show market health components
                    st.subheader("Market Health Components")
                    component_fig = plot_market_health_components(display_data)
                    st.plotly_chart(component_fig, use_container_width=True)
                    
                    with st.expander("Understanding the Market Health Index"):
                        st.markdown("""
                        ### How the Market Health Index is Calculated
                        
                        The Job Market Health Index is a composite score based on several factors:
                        
                        - **Job Count**: Total number of job postings (40% weight)
                        - **Company Diversity**: Number of different companies posting jobs (20% weight)
                        - **Job Type Diversity**: Variety of job types available (20% weight)
                        - **Location Diversity**: Geographical distribution of opportunities (10% weight)
                        - **Remote Ratio**: Proportion of remote job opportunities (10% weight)
                        
                        The index is normalized to a 0-100 scale where:
                        - **0-30**: Very Weak market
                        - **30-45**: Weak market
                        - **45-55**: Stable market
                        - **55-70**: Strong market
                        - **70-100**: Very Strong market
                        
                        A higher index indicates a healthier job market with more opportunities and choices for job seekers.
                        """)
                    
                    # Regional health comparison if enough data
                    if len(display_data) >= 10:
                        st.subheader("Regional Market Health Comparison")
                        regional_fig = plot_regional_health_comparison(display_data)
                        st.plotly_chart(regional_fig, use_container_width=True)
                        
                        st.info("This analysis compares job market health across different regions. Higher values indicate regions with stronger job markets based on job counts, company diversity, and other factors.")
                else:
                    st.info("Insufficient data to calculate the job market health index.")
                    st.write("The market health analysis requires data across multiple time periods.")
            else:
                st.info("At least 2 months of data are required to calculate the job market health index.")
                st.write("Try adding more job postings across different months.")
        
        except Exception as e:
            st.error(f"Error analyzing market health: {e}")
            st.info("This analysis requires data with sufficient variability across time periods.")
            
    with tabs[12]:  # Live Data Tab
        st.subheader("Live Job Data Integration")
        
        # Create tabs for different live data sources
        live_tabs = st.tabs(["API Integration", "Web Scraping", "External Imports"])
        
        with live_tabs[0]:  # API Integration
            st.write("### Connect to External Job API")
            
            api_col1, api_col2 = st.columns([1, 1])
            
            with api_col1:
                # API configuration
                api_key = st.text_input("API Key", type="password", help="Enter your API key for the job data service")
                location = st.text_input("Location (optional)", help="Filter jobs by location")
                job_type_filter = st.selectbox(
                    "Job Type Filter",
                    ["All"] + display_data['job_type'].unique().tolist(),
                    help="Filter jobs by type"
                )
                
                # Convert "All" to None for the API
                job_type_api = None if job_type_filter == "All" else job_type_filter
                
            with api_col2:
                st.info("""
                **How API Integration Works:**
                
                1. Connect to external job posting APIs like LinkedIn, Indeed, or specialized tech job boards
                2. Automatically fetch and process new job postings
                3. Store in your database for analysis
                
                **Benefits:**
                - Real-time job market data
                - Automated data collection
                - Consistent formatting
                """)
                
                # Fetch button
                if st.button("Fetch Jobs from API"):
                    if not api_key:
                        st.warning("Please enter an API key to connect to the job data service.")
                    else:
                        with st.spinner("Fetching job data from API..."):
                            # Call the API function
                            try:
                                api_data = fetch_job_data_from_api(
                                    api_key=api_key,
                                    location=location,
                                    job_type=job_type_api
                                )
                                
                                if "error" in api_data:
                                    st.error(f"API Error: {api_data['error']}")
                                else:
                                    # Process API response
                                    api_df = process_api_response(api_data)
                                    
                                    if api_df is not None and not api_df.empty:
                                        st.success(f"Successfully fetched {len(api_df)} job postings!")
                                        
                                        # Show preview
                                        st.write("#### Job Data Preview")
                                        st.dataframe(api_df.head())
                                        
                                        # Option to add to database
                                        if st.button("Add Jobs to Database"):
                                            add_multiple_job_postings(api_df)
                                            st.success("Jobs added to database!")
                                            st.info("Refresh the page to see the updated data.")
                                    else:
                                        st.warning("No job data was returned from the API.")
                            except Exception as e:
                                st.error(f"Error connecting to API: {e}")
                
                # Auto-refresh options
                st.write("### Automated Data Refresh")
                refresh_interval = st.number_input("Refresh Interval (hours)", min_value=1, max_value=168, value=24)
                
                if st.button("Schedule Auto Refresh"):
                    if not api_key:
                        st.warning("Please enter an API key to schedule refresh.")
                    else:
                        refresh_status = schedule_data_refresh(
                            refresh_interval=refresh_interval,
                            api_key=api_key,
                            max_jobs=50
                        )
                        st.info(refresh_status)
        
        with live_tabs[1]:  # Web Scraping
            st.write("### Web Scraping Job Data")
            
            scrape_col1, scrape_col2 = st.columns([1, 1])
            
            with scrape_col1:
                # Scraping configuration
                website_url = st.text_input("Website URL", help="Enter the URL of the job board to scrape")
                max_jobs = st.slider("Maximum Jobs to Scrape", 10, 100, 30)
            
            with scrape_col2:
                st.info("""
                **Web Scraping Guidelines:**
                
                1. Only scrape public job postings
                2. Respect website terms of service
                3. Add delays between requests
                
                **Supported Job Boards:**
                - Job posting aggregators
                - Company career pages
                - Public job boards
                """)
                
                # Scrape button
                if st.button("Scrape Job Data"):
                    if not website_url:
                        st.warning("Please enter a website URL to scrape.")
                    else:
                        with st.spinner("Scraping job data..."):
                            try:
                                # Call the scraping function
                                scraped_df = scrape_jobs_from_website(website_url, max_jobs)
                                
                                if scraped_df is not None and not scraped_df.empty:
                                    st.success(f"Successfully scraped {len(scraped_df)} job postings!")
                                    
                                    # Show preview
                                    st.write("#### Scraped Job Data Preview")
                                    st.dataframe(scraped_df.head())
                                    
                                    # Option to add to database
                                    if st.button("Add Scraped Jobs to Database"):
                                        add_multiple_job_postings(scraped_df)
                                        st.success("Scraped jobs added to database!")
                                        st.info("Refresh the page to see the updated data.")
                                else:
                                    st.warning("No job data could be scraped from the website.")
                            except Exception as e:
                                st.error(f"Error scraping website: {e}")
        
        with live_tabs[2]:  # External Imports
            st.write("### Import from External Sources")
            
            import_col1, import_col2 = st.columns([1, 1])
            
            with import_col1:
                st.write("#### LinkedIn Jobs Export")
                linkedin_file = st.file_uploader("Upload LinkedIn Jobs CSV", type=["csv"])
                
                if linkedin_file is not None:
                    try:
                        linkedin_df = import_jobs_from_linkedin_export(linkedin_file)
                        
                        if linkedin_df is not None and not linkedin_df.empty:
                            st.success(f"Successfully imported {len(linkedin_df)} LinkedIn job postings!")
                            
                            # Show preview
                            st.write("#### LinkedIn Data Preview")
                            st.dataframe(linkedin_df.head())
                            
                            # Option to add to database
                            if st.button("Add LinkedIn Jobs to Database"):
                                add_multiple_job_postings(linkedin_df)
                                st.success("LinkedIn jobs added to database!")
                                st.info("Refresh the page to see the updated data.")
                        else:
                            st.warning("No job data could be imported from the LinkedIn file.")
                    except Exception as e:
                        st.error(f"Error importing LinkedIn data: {e}")
            
            with import_col2:
                st.write("#### Indeed Jobs Export")
                indeed_file = st.file_uploader("Upload Indeed Jobs CSV", type=["csv"])
                
                if indeed_file is not None:
                    try:
                        indeed_df = import_jobs_from_indeed_export(indeed_file)
                        
                        if indeed_df is not None and not indeed_df.empty:
                            st.success(f"Successfully imported {len(indeed_df)} Indeed job postings!")
                            
                            # Show preview
                            st.write("#### Indeed Data Preview")
                            st.dataframe(indeed_df.head())
                            
                            # Option to add to database
                            if st.button("Add Indeed Jobs to Database"):
                                add_multiple_job_postings(indeed_df)
                                st.success("Indeed jobs added to database!")
                                st.info("Refresh the page to see the updated data.")
                        else:
                            st.warning("No job data could be imported from the Indeed file.")
                    except Exception as e:
                        st.error(f"Error importing Indeed data: {e}")
            
            # General import information
            st.info("""
            **How to Export Jobs from LinkedIn/Indeed:**
            
            1. Save your job searches to a collection
            2. Use the export functionality in your jobs/applications section
            3. Download as CSV and upload here
            
            This feature allows you to incorporate your personal job search data into the analysis.
            """)
            
    with tabs[13]:  # Resume Analysis Tab
        st.subheader("Resume Skills Analysis")
        
        resume_col1, resume_col2 = st.columns([1, 2])
        
        with resume_col1:
            # Resume text input
            st.write("### Upload Your Resume")
            resume_text = st.text_area(
                "Paste resume text here",
                height=300,
                help="Copy and paste the text content of your resume here for analysis"
            )
            
            analyze_button = st.button("Analyze Resume Skills")
        
        with resume_col2:
            if analyze_button and resume_text:
                with st.spinner("Analyzing resume skills..."):
                    # Extract skills from resume
                    resume_skills = extract_resume_skills(resume_text)
                    
                    if resume_skills:
                        st.success(f"Found {len(resume_skills)} skills in your resume!")
                        
                        # Display skills
                        st.write("### Skills Found in Your Resume")
                        
                        # Create columns for skills
                        skill_cols = st.columns(3)
                        
                        for i, skill in enumerate(sorted(resume_skills)):
                            col_idx = i % 3
                            with skill_cols[col_idx]:
                                st.write(f"✓ {skill}")
                        
                        # Compare with market demand
                        st.write("### Market Demand Analysis")
                        
                        # Process data for skill analysis if needed
                        skill_data = display_data.copy()
                        if 'skills' not in skill_data.columns:
                            skill_data = extract_skills_from_jobs(skill_data)
                        
                        # Compare resume to market demand
                        market_analysis = compare_resume_to_market(resume_skills, skill_data)
                        
                        # Show match percentage
                        st.metric(
                            "Market Match Score", 
                            f"{market_analysis['match_percentage']:.1f}%",
                            help="How well your skills match current market demand"
                        )
                        
                        # Create skill gap visualization
                        gap_fig = plot_skill_gap_analysis(market_analysis)
                        st.plotly_chart(gap_fig, use_container_width=True)
                        
                        # Missing key skills
                        if market_analysis['missing_key_skills']:
                            st.write("### Missing High-Demand Skills")
                            st.info("Consider adding these high-demand skills to your resume or skillset:")
                            
                            missing_cols = st.columns(3)
                            for i, skill in enumerate(market_analysis['missing_key_skills'][:9]):  # Show top 9
                                col_idx = i % 3
                                with missing_cols[col_idx]:
                                    st.write(f"→ {skill}")
                        
                        # Find matching job types
                        matching_jobs = find_matching_job_types(resume_skills, skill_data)
                        
                        if not matching_jobs.empty:
                            st.write("### Best Matching Job Types for Your Skills")
                            
                            # Create bar chart of job type matches
                            job_match_fig = plot_job_type_matches(matching_jobs)
                            st.plotly_chart(job_match_fig, use_container_width=True)
                            
                            # Skill improvement recommendations
                            recommendations = generate_skill_improvement_recommendations(
                                {'resume_skills': resume_skills, 'job_type_matches': matching_jobs},
                                skill_data
                            )
                            
                            st.write("### Skill Improvement Recommendations")
                            
                            rec_col1, rec_col2 = st.columns(2)
                            
                            with rec_col1:
                                st.write("**High-Impact Skills to Add:**")
                                for skill in recommendations['high_impact_skills'][:5]:
                                    st.write(f"• {skill}")
                            
                            with rec_col2:
                                st.write("**Emerging Skills to Consider:**")
                                for skill in recommendations['emerging_skills'][:5]:
                                    st.write(f"• {skill}")
                    else:
                        st.warning("No skills were detected in your resume text.")
                        st.info("Try pasting more content or adding more technical details to your resume.")
            else:
                # Show help information when no resume is provided
                st.info("""
                ## Resume Skills Analyzer
                
                This tool analyzes your resume content to:
                
                1. **Extract technical skills** from your resume text
                2. **Compare your skills** to current job market demand
                3. **Identify skill gaps** based on job market trends
                4. **Recommend job types** matching your skill profile
                5. **Suggest skill improvements** to increase your marketability
                
                Paste your resume text in the box on the left and click "Analyze Resume Skills" to get started.
                """)
                
    with tabs[15]:  # Interview Tracker Tab
        st.subheader("Interview Difficulty Tracker")
        
        # Create tabs for different interview tracking features
        interview_tabs = st.tabs([
            "Company Difficulty Ratings", 
            "Interview Trends", 
            "Track New Interview", 
            "Preparation Tips"
        ])
        
        # Initialize interview data in session state if it doesn't exist
        if "interview_data" not in st.session_state:
            # Create sample interview data structure
            st.session_state.interview_data = pd.DataFrame({
                'company': display_data['company'].unique()[:10],  # Use some companies from job data
                'job_title': ['Software Engineer', 'Full Stack Developer', 'Frontend Engineer', 
                             'Backend Engineer', 'DevOps Engineer', 'Data Engineer', 
                             'ML Engineer', 'Product Manager', 'QA Engineer', 'Mobile Developer'],
                'date': pd.date_range(end=pd.Timestamp.today(), periods=10).date,
                'difficulty_rating': [4, 3, 5, 4, 2, 5, 4, 3, 2, 4],  # 1-5 scale
                'technical_difficulty': [4, 3, 5, 4, 3, 5, 5, 2, 3, 4],  # 1-5 scale
                'behavioral_difficulty': [3, 4, 3, 3, 2, 4, 3, 5, 2, 3],  # 1-5 scale
                'system_design': [5, 3, 4, 5, 2, 5, 4, 3, 1, 3],  # 1-5 scale
                'algorithms': [4, 3, 5, 4, 2, 4, 5, 2, 3, 4],  # 1-5 scale
                'outcome': ['Rejected', 'Offer', 'Pending', 'Rejected', 'Offer', 
                           'Pending', 'Offer', 'Rejected', 'Offer', 'Pending'],
                'rounds': [3, 4, 5, 3, 2, 5, 4, 3, 2, 3],
                'coding_languages': ['Python,Java', 'JavaScript,TypeScript', 'React,CSS', 'Python,Go', 
                                    'Bash,Python', 'Python,SQL', 'Python,TensorFlow', 'N/A', 
                                    'Java,Selenium', 'Swift,Kotlin'],
                'notes': ['Difficult system design question', 'Good interview experience', 
                         'Many algorithm questions', 'Intense technical screening',
                         'Simple interview process', 'Deep dive into past projects',
                         'Complex ML problems', 'Focus on product thinking',
                         'Test automation focus', 'Mobile-specific questions']
            })
        
        with interview_tabs[0]:  # Company Difficulty Ratings
            st.write("### Interview Difficulty by Company")
            
            # Company difficulty comparison
            difficulty_fig = plot_company_difficulty_comparison(st.session_state.interview_data)
            st.plotly_chart(difficulty_fig, use_container_width=True)
            
            # Show detailed ratings
            st.write("### Detailed Company Ratings")
            
            # Calculate company ratings
            company_ratings = calculate_company_difficulty_ratings(st.session_state.interview_data)
            
            if not company_ratings.empty:
                # Add badge emojis based on difficulty
                def difficulty_badge(difficulty):
                    if difficulty >= 4.5:
                        return "🔴 Very Hard"
                    elif difficulty >= 3.5:
                        return "🟠 Hard"
                    elif difficulty >= 2.5:
                        return "🟡 Moderate"
                    else:
                        return "🟢 Easy"
                
                company_ratings['Difficulty Level'] = company_ratings['avg_difficulty'].apply(difficulty_badge)
                
                # Show the ratings table
                st.dataframe(
                    company_ratings[['avg_difficulty', 'avg_technical', 'avg_behavioral', 'avg_system_design', 
                                   'avg_algorithms', 'avg_rounds', 'Difficulty Level']]
                    .sort_values('avg_difficulty', ascending=False)
                    .rename(columns={
                        'avg_difficulty': 'Overall Difficulty', 
                        'avg_technical': 'Technical', 
                        'avg_behavioral': 'Behavioral',
                        'avg_system_design': 'System Design',
                        'avg_algorithms': 'Algorithms',
                        'avg_rounds': 'Avg. Rounds'
                    }),
                    use_container_width=True
                )
            else:
                st.info("No interview data available yet.")
            
            # Compare interview components
            st.write("### Interview Component Comparison")
            component_fig = plot_interview_components_comparison(st.session_state.interview_data)
            st.plotly_chart(component_fig, use_container_width=True)
        
        with interview_tabs[1]:  # Interview Trends
            st.write("### Interview Difficulty Trends Over Time")
            
            trend_fig = plot_interview_difficulty_trend(st.session_state.interview_data)
            st.plotly_chart(trend_fig, use_container_width=True)
            
            # Success factors analysis
            st.write("### Success Factors in Interviews")
            success_fig = plot_interview_success_factors(st.session_state.interview_data)
            st.plotly_chart(success_fig, use_container_width=True)
            
            # Show insights
            st.write("### Interview Success Insights")
            
            # Calculate success rates
            offer_rate = (st.session_state.interview_data['outcome'] == 'Offer').mean() * 100
            
            # Calculate success rate by difficulty
            success_by_difficulty = st.session_state.interview_data.groupby('difficulty_rating')['outcome'].apply(
                lambda x: (x == 'Offer').mean() * 100
            ).reset_index()
            
            # Display insights in columns
            insight_col1, insight_col2 = st.columns(2)
            
            with insight_col1:
                st.metric("Overall Success Rate", f"{offer_rate:.1f}%")
                
                st.write("**Success Rate by Difficulty Level:**")
                for _, row in success_by_difficulty.iterrows():
                    difficulty = int(row['difficulty_rating'])
                    success_rate = row['outcome']
                    st.write(f"Difficulty {difficulty}: {success_rate:.1f}% success rate")
            
            with insight_col2:
                # Most successful languages or skills
                if 'coding_languages' in st.session_state.interview_data.columns:
                    # Flatten the languages list
                    all_languages = []
                    for langs in st.session_state.interview_data['coding_languages']:
                        if isinstance(langs, str) and langs != 'N/A':
                            all_languages.extend([l.strip() for l in langs.split(',')])
                    
                    # Count language frequencies
                    if all_languages:
                        lang_counts = pd.Series(all_languages).value_counts()
                        
                        st.write("**Most Requested Languages/Skills:**")
                        for lang, count in lang_counts.items():
                            st.write(f"• {lang}: {count} interviews")
                
                # Display notable insights
                st.write("**Key Factors for Success:**")
                st.write("• Technical preparation is critical for companies with difficulty > 4")
                st.write("• System design questions strongly correlate with interview success")
                st.write("• More interview rounds generally indicates a more rigorous process")
        
        with interview_tabs[2]:  # Track New Interview
            st.write("### Track a New Interview Experience")
            
            # Form for adding new interview data
            interview_col1, interview_col2 = st.columns(2)
            
            with interview_col1:
                # Basic interview details
                new_company = st.selectbox(
                    "Company",
                    options=sorted(display_data['company'].unique().tolist()),
                    help="Select the company you interviewed with"
                )
                
                new_job_title = st.text_input(
                    "Job Title",
                    help="Enter the job title you interviewed for"
                )
                
                interview_date = st.date_input(
                    "Interview Date",
                    value=datetime.datetime.now().date(),
                    help="Date of the interview"
                )
                
                # Interview difficulty ratings
                overall_difficulty = st.slider(
                    "Overall Difficulty (1-5)",
                    min_value=1,
                    max_value=5,
                    value=3,
                    help="How difficult was the overall interview process"
                )
                
                technical_difficulty = st.slider(
                    "Technical Difficulty (1-5)",
                    min_value=1,
                    max_value=5,
                    value=3,
                    help="How difficult were the technical questions"
                )
                
                behavioral_difficulty = st.slider(
                    "Behavioral Difficulty (1-5)",
                    min_value=1,
                    max_value=5,
                    value=3,
                    help="How difficult were the behavioral questions"
                )
            
            with interview_col2:
                # Additional interview details
                system_design = st.slider(
                    "System Design Difficulty (1-5)",
                    min_value=1,
                    max_value=5,
                    value=3,
                    help="How difficult were the system design questions"
                )
                
                algorithms = st.slider(
                    "Algorithms Difficulty (1-5)",
                    min_value=1,
                    max_value=5,
                    value=3,
                    help="How difficult were the algorithm questions"
                )
                
                rounds = st.number_input(
                    "Number of Interview Rounds",
                    min_value=1,
                    max_value=10,
                    value=3,
                    help="How many interview rounds did you go through"
                )
                
                outcome = st.selectbox(
                    "Interview Outcome",
                    options=["Pending", "Offer", "Rejected", "Withdrawn"],
                    help="What was the outcome of the interview"
                )
                
                coding_languages = st.text_input(
                    "Coding Languages/Skills Tested (comma-separated)",
                    help="What languages or skills were tested in the interview"
                )
                
                notes = st.text_area(
                    "Interview Notes",
                    height=100,
                    help="Add any notes or observations about the interview process"
                )
            
            # Submit button for the new interview
            if st.button("Save Interview Data"):
                if new_company and new_job_title:
                    # Create new interview entry
                    new_interview = pd.DataFrame({
                        'company': [new_company],
                        'job_title': [new_job_title],
                        'date': [interview_date],
                        'difficulty_rating': [overall_difficulty],
                        'technical_difficulty': [technical_difficulty],
                        'behavioral_difficulty': [behavioral_difficulty],
                        'system_design': [system_design],
                        'algorithms': [algorithms],
                        'outcome': [outcome],
                        'rounds': [rounds],
                        'coding_languages': [coding_languages],
                        'notes': [notes]
                    })
                    
                    # Add to existing data
                    st.session_state.interview_data = pd.concat(
                        [st.session_state.interview_data, new_interview], 
                        ignore_index=True
                    )
                    
                    st.success("Interview data saved successfully!")
                    st.info("Switch to the 'Company Difficulty Ratings' or 'Interview Trends' tab to see updated data.")
                else:
                    st.error("Please fill in both Company and Job Title fields.")
            
            # Option to upload CSV of interview data
            st.write("### Or Upload Interview Data")
            
            upload_interview = st.file_uploader(
                "Upload Interview Data CSV",
                type=["csv"],
                help="Upload a CSV file with interview data"
            )
            
            if upload_interview is not None:
                try:
                    interview_df = pd.read_csv(upload_interview)
                    # Validate the data
                    validated_df = validate_interview_data(interview_df)
                    
                    if validated_df is not None:
                        # Add to existing data
                        st.session_state.interview_data = pd.concat(
                            [st.session_state.interview_data, validated_df], 
                            ignore_index=True
                        )
                        st.success(f"Successfully loaded {len(validated_df)} interview records!")
                    else:
                        st.error("Invalid interview data format.")
                        st.info("The CSV should include: company, job_title, date, difficulty_rating, outcome")
                except Exception as e:
                    st.error(f"Error loading interview data: {e}")
        
        with interview_tabs[3]:  # Preparation Tips
            st.write("### Interview Preparation Tips")
            
            # Company selection for tips
            tip_company = st.selectbox(
                "Select Company",
                options=["All Companies"] + sorted(st.session_state.interview_data['company'].unique().tolist()),
                help="Select a company to get specific interview prep tips"
            )
            
            # Job title selection for tips
            job_options = ["All Job Titles"]
            if tip_company != "All Companies":
                company_jobs = st.session_state.interview_data[
                    st.session_state.interview_data['company'] == tip_company
                ]['job_title'].unique().tolist()
                job_options.extend(company_jobs)
            else:
                job_options.extend(st.session_state.interview_data['job_title'].unique().tolist())
            
            tip_job = st.selectbox(
                "Select Job Title",
                options=job_options,
                help="Select a job title to get specific interview prep tips"
            )
            
            # Generate tips
            if st.button("Generate Interview Preparation Tips"):
                # Fix company and job title for the tips function
                company_for_tips = None if tip_company == "All Companies" else tip_company
                job_for_tips = None if tip_job == "All Job Titles" else tip_job
                
                # Get tips
                tips = get_interview_preparation_tips(
                    company_for_tips, 
                    job_for_tips, 
                    st.session_state.interview_data
                )
                
                # Display tips
                st.write(f"### Preparation Tips for {tip_company if company_for_tips else 'All Companies'}")
                
                tips_col1, tips_col2 = st.columns(2)
                
                with tips_col1:
                    st.write("#### Technical Preparation")
                    st.info(tips['technical_tips'])
                    
                    st.write("#### System Design Focus")
                    st.info(tips['system_design_tips'])
                
                with tips_col2:
                    st.write("#### Behavioral Preparation")
                    st.info(tips['behavioral_tips'])
                    
                    st.write("#### Key Skills to Review")
                    if tips['skill_tips']:
                        for skill in tips['skill_tips']:
                            st.write(f"• {skill}")
                    else:
                        st.write("No specific skills data available.")
                
                # Show expected difficulty level
                st.write("#### Expected Interview Difficulty")
                
                # Create a gauge chart for expected difficulty
                difficulty_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number",
                    value = tips['expected_difficulty'],
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "Expected Difficulty"},
                    gauge = {
                        'axis': {'range': [0, 5], 'tickwidth': 1},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 2], 'color': "lightgreen"},
                            {'range': [2, 3.5], 'color': "yellow"},
                            {'range': [3.5, 5], 'color': "salmon"},
                        ]
                    }
                ))
                
                difficulty_gauge.update_layout(height=250)
                st.plotly_chart(difficulty_gauge, use_container_width=True)
                
                # Show common interview questions
                st.write("#### Common Interview Questions")
                for q in tips['common_questions']:
                    st.markdown(f"**Q:** {q}")
                
                # Show interview structure
                st.write("#### Typical Interview Process")
                st.info(tips['interview_structure'])
    
    with tabs[16]:  # Compensation Benchmarking
        st.subheader("Compensation Benchmarking")
        
        # Create tabs for different compensation analysis features
        comp_tabs = st.tabs([
            "Salary Trends", 
            "Total Compensation", 
            "Cost of Living Adjusted",
            "Experience-Based Progression"
        ])
        
        with comp_tabs[0]:  # Salary Trends
            st.write("### Salary Trends by Job Type and Location")
            
            # Job type selection for salary trends
            salary_job_types = st.multiselect(
                "Select Job Types to Compare",
                options=sorted(display_data['job_type'].unique().tolist()),
                default=sorted(display_data['job_type'].unique().tolist())[:3],
                help="Select job types to compare salary trends"
            )
            
            # Region selection for salary comparison
            geo_data = display_data.copy()
            geo_data['region'] = geo_data['location'].apply(extract_region)
            regions = sorted(geo_data['region'].unique().tolist())
            
            salary_regions = st.multiselect(
                "Select Regions to Compare",
                options=regions,
                default=regions[:3] if len(regions) >= 3 else regions,
                help="Select regions to compare salary trends"
            )
            
            # Generate salary trend visualization
            if salary_job_types and salary_regions:
                # Create filtered data for salary analysis
                salary_data = geo_data[geo_data['job_type'].isin(salary_job_types)]
                salary_data = salary_data[salary_data['region'].isin(salary_regions)]
                
                # Clean and process salary data
                salary_data['salary_numeric'] = salary_data['salary'].apply(lambda x: 
                    float(re.sub(r'[^\d.]', '', x.split('-')[0])) if isinstance(x, str) and re.search(r'\d', x) else None
                )
                
                # Remove rows without valid salary data
                salary_data = salary_data.dropna(subset=['salary_numeric'])
                
                if not salary_data.empty:
                    # Create salary trend charts
                    fig = px.box(
                        salary_data,
                        x="job_type",
                        y="salary_numeric",
                        color="region",
                        title="Salary Distribution by Job Type and Region",
                        labels={"salary_numeric": "Annual Salary ($)", "job_type": "Job Type", "region": "Region"},
                        category_orders={"job_type": sorted(salary_job_types)}
                    )
                    
                    fig.update_layout(height=500)
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Show average salaries by job type
                    st.write("### Average Salaries by Job Type")
                    avg_salaries = salary_data.groupby('job_type')['salary_numeric'].mean().sort_values(ascending=False)
                    
                    avg_fig = px.bar(
                        x=avg_salaries.index,
                        y=avg_salaries.values,
                        labels={"x": "Job Type", "y": "Average Annual Salary ($)"},
                        color=avg_salaries.values,
                        color_continuous_scale="Viridis"
                    )
                    
                    avg_fig.update_layout(height=400)
                    st.plotly_chart(avg_fig, use_container_width=True)
                    
                    # Show detailed salary statistics
                    st.write("### Detailed Salary Statistics")
                    salary_stats = salary_data.groupby('job_type')['salary_numeric'].agg([
                        ('Average', 'mean'),
                        ('Median', 'median'),
                        ('Min', 'min'),
                        ('Max', 'max'),
                        ('Count', 'count')
                    ]).sort_values('Average', ascending=False)
                    
                    # Format currency columns
                    for col in ['Average', 'Median', 'Min', 'Max']:
                        salary_stats[col] = salary_stats[col].apply(lambda x: f"${x:,.2f}")
                    
                    st.dataframe(salary_stats, use_container_width=True)
                else:
                    st.warning("No salary data available for the selected job types and regions.")
                    st.info("Ensure that jobs have salary information in the dataset.")
            else:
                st.info("Please select at least one job type and region to view salary trends.")
        
        with comp_tabs[1]:  # Total Compensation
            st.write("### Total Compensation Analysis")
            
            # Sample data for total compensation (in a real app, this would be from the database)
            comp_data = pd.DataFrame({
                'company': display_data['company'].unique()[:15],
                'job_level': ['Junior', 'Mid-level', 'Senior', 'Staff', 'Principal',
                             'Junior', 'Mid-level', 'Senior', 'Junior', 'Mid-level',
                             'Senior', 'Staff', 'Mid-level', 'Senior', 'Principal'],
                'base_salary': [85000, 120000, 160000, 185000, 210000,
                               90000, 125000, 165000, 80000, 115000,
                               155000, 180000, 130000, 170000, 205000],
                'bonus': [5000, 15000, 30000, 40000, 60000,
                         8000, 20000, 35000, 4000, 12000,
                         25000, 35000, 18000, 30000, 50000],
                'stock': [0, 20000, 50000, 90000, 150000,
                         10000, 30000, 60000, 0, 15000,
                         40000, 80000, 25000, 55000, 130000],
                'benefits': [15000, 20000, 25000, 30000, 35000,
                            15000, 20000, 25000, 15000, 20000,
                            25000, 30000, 20000, 25000, 35000]
            })
            
            # Calculate total compensation
            comp_data['total_comp'] = comp_data['base_salary'] + comp_data['bonus'] + comp_data['stock'] + comp_data['benefits']
            
            # Company selection for total comp analysis
            comp_companies = st.multiselect(
                "Select Companies to Compare",
                options=comp_data['company'].unique().tolist(),
                default=comp_data['company'].unique().tolist()[:5],
                help="Select companies to compare total compensation"
            )
            
            if comp_companies:
                filtered_comp = comp_data[comp_data['company'].isin(comp_companies)]
                
                # Create stacked bar chart for compensation breakdown
                fig = px.bar(
                    filtered_comp,
                    x="company",
                    y=["base_salary", "bonus", "stock", "benefits"],
                    title="Total Compensation Breakdown by Company",
                    labels={"value": "Amount ($)", "company": "Company", "variable": "Component"},
                    color_discrete_map={
                        "base_salary": "blue",
                        "bonus": "green",
                        "stock": "purple",
                        "benefits": "gold"
                    }
                )
                
                fig.update_layout(height=500, barmode='stack')
                st.plotly_chart(fig, use_container_width=True)
                
                # Show compensation by level across companies
                st.write("### Compensation by Level")
                
                level_fig = px.box(
                    filtered_comp,
                    x="job_level",
                    y="total_comp",
                    color="company",
                    title="Total Compensation by Job Level",
                    labels={"total_comp": "Total Compensation ($)", "job_level": "Job Level", "company": "Company"},
                    category_orders={"job_level": ["Junior", "Mid-level", "Senior", "Staff", "Principal"]}
                )
                
                level_fig.update_layout(height=500)
                st.plotly_chart(level_fig, use_container_width=True)
                
                # Show detailed compensation data
                st.write("### Detailed Compensation Data")
                comp_columns = ['company', 'job_level', 'base_salary', 'bonus', 'stock', 'benefits', 'total_comp']
                st.dataframe(filtered_comp[comp_columns].sort_values(['company', 'job_level']), use_container_width=True)
            else:
                st.info("Please select at least one company to view total compensation analysis.")
        
        with comp_tabs[2]:  # Cost of Living Adjusted
            st.write("### Cost of Living Adjusted Salaries")
            
            # Sample cost of living index data (100 = national average)
            col_data = {
                "US West": 140,
                "US East": 125,
                "US Central": 95,
                "North America": 110,
                "Europe": 120,
                "Asia": 90,
                "Australia": 130,
                "Remote": 100,  # Using national average for remote
                "Hybrid": 110,  # Slightly above average for hybrid
                "Other": 100    # Using national average for other
            }
            
            # Show COL index reference table
            st.write("#### Cost of Living Index by Region")
            
            # Create COL index dataframe for display
            col_df = pd.DataFrame(list(col_data.items()), columns=['Region', 'COL Index'])
            col_df = col_df.sort_values('COL Index', ascending=False)
            
            # Display the COL index table
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.dataframe(col_df, use_container_width=True)
                
                st.info("""
                **Note:** The Cost of Living (COL) Index shows relative living costs.
                * 100 = national average
                * Values above 100 indicate higher cost of living
                * Values below 100 indicate lower cost of living
                
                Adjusted salaries show the purchasing power in each region.
                """)
            
            with col2:
                # Create a choropleth map showing cost of living
                base_fig = go.Figure()
                
                # Add a bar chart for COL index
                base_fig.add_trace(go.Bar(
                    x=col_df['Region'],
                    y=col_df['COL Index'],
                    marker_color='darkblue',
                    name='COL Index'
                ))
                
                base_fig.update_layout(
                    title="Cost of Living Index by Region",
                    xaxis_title="Region",
                    yaxis_title="Cost of Living Index",
                    height=400
                )
                
                st.plotly_chart(base_fig, use_container_width=True)
            
            # Job type selection for COL-adjusted analysis
            col_job_type = st.selectbox(
                "Select Job Type",
                options=sorted(display_data['job_type'].unique().tolist()),
                help="Select a job type to view COL-adjusted salaries"
            )
            
            # Filter salary data for the selected job type
            geo_data = display_data.copy()
            geo_data['region'] = geo_data['location'].apply(extract_region)
            
            job_salary_data = geo_data[geo_data['job_type'] == col_job_type].copy()
            
            # Clean and process salary data
            job_salary_data['salary_numeric'] = job_salary_data['salary'].apply(lambda x: 
                float(re.sub(r'[^\d.]', '', x.split('-')[0])) if isinstance(x, str) and re.search(r'\d', x) else None
            )
            
            # Remove rows without valid salary data
            job_salary_data = job_salary_data.dropna(subset=['salary_numeric'])
            
            if not job_salary_data.empty:
                # Calculate regional average salaries
                region_salaries = job_salary_data.groupby('region')['salary_numeric'].mean().reset_index()
                
                # Add COL index and calculate adjusted salaries
                region_salaries['col_index'] = region_salaries['region'].map(col_data)
                region_salaries['adjusted_salary'] = region_salaries['salary_numeric'] * (100 / region_salaries['col_index'])
                
                # Display comparison of nominal vs. adjusted salaries
                st.write(f"### {col_job_type} Salaries: Nominal vs. COL-Adjusted")
                
                # Create a bar chart comparing nominal and adjusted salaries
                compare_fig = go.Figure()
                
                # Add nominal salary bars
                compare_fig.add_trace(go.Bar(
                    x=region_salaries['region'],
                    y=region_salaries['salary_numeric'],
                    name='Nominal Salary',
                    marker_color='blue'
                ))
                
                # Add adjusted salary bars
                compare_fig.add_trace(go.Bar(
                    x=region_salaries['region'],
                    y=region_salaries['adjusted_salary'],
                    name='COL-Adjusted Salary',
                    marker_color='green'
                ))
                
                # Update the layout
                compare_fig.update_layout(
                    title=f"{col_job_type} - Regional Salaries: Nominal vs. COL-Adjusted",
                    xaxis_title="Region",
                    yaxis_title="Annual Salary ($)",
                    height=500,
                    barmode='group'
                )
                
                st.plotly_chart(compare_fig, use_container_width=True)
                
                # Display the data table with both nominal and adjusted salaries
                st.write("### Detailed Salary Adjustment Data")
                
                # Format the data for display
                display_cols = ['region', 'salary_numeric', 'col_index', 'adjusted_salary']
                display_df = region_salaries[display_cols].sort_values('adjusted_salary', ascending=False)
                
                # Rename columns for better display
                display_df = display_df.rename(columns={
                    'region': 'Region',
                    'salary_numeric': 'Nominal Salary',
                    'col_index': 'COL Index',
                    'adjusted_salary': 'Adjusted Salary'
                })
                
                # Format currency columns
                display_df['Nominal Salary'] = display_df['Nominal Salary'].apply(lambda x: f"${x:,.2f}")
                display_df['Adjusted Salary'] = display_df['Adjusted Salary'].apply(lambda x: f"${x:,.2f}")
                
                st.dataframe(display_df, use_container_width=True)
                
                # Show insights about the best value regions
                st.write("### Regional Value Insights")
                
                # Identify the best value region (highest adjusted salary)
                best_value_region = region_salaries.loc[region_salaries['adjusted_salary'].idxmax(), 'region']
                best_value_adjustment = region_salaries.loc[region_salaries['adjusted_salary'].idxmax(), 'adjusted_salary'] / \
                                      region_salaries.loc[region_salaries['adjusted_salary'].idxmax(), 'salary_numeric']
                
                st.success(f"""
                **Best Value Region:** {best_value_region}
                
                In {best_value_region}, your salary has {best_value_adjustment:.2f}x the purchasing power compared to the nominal amount.
                This makes it potentially the most economically advantageous region for this job type when considering cost of living.
                """)
            else:
                st.warning(f"No salary data available for {col_job_type}.")
                st.info("Ensure that jobs have salary information in the dataset.")
        
        with comp_tabs[3]:  # Experience-Based Progression
            st.write("### Salary Progression by Experience Level")
            
            # Sample experience level data
            experience_data = pd.DataFrame({
                'company': np.repeat(display_data['company'].unique()[:5], 5),
                'job_type': np.tile(display_data['job_type'].unique()[:5], 5),
                'years_experience': np.tile([0, 2, 5, 8, 12], 5),
                'salary': [
                    # Company 1
                    80000, 100000, 130000, 160000, 190000,
                    # Company 2
                    85000, 105000, 135000, 165000, 195000,
                    # Company 3
                    75000, 95000, 125000, 155000, 185000,
                    # Company 4
                    90000, 110000, 140000, 170000, 200000,
                    # Company 5
                    82000, 102000, 132000, 162000, 192000
                ]
            })
            
            # Job type selection for progression analysis
            prog_job_type = st.selectbox(
                "Select Job Type for Progression Analysis",
                options=experience_data['job_type'].unique().tolist(),
                key="progression_job_type",
                help="Select a job type to view salary progression by experience"
            )
            
            # Filter data for the selected job type
            job_prog_data = experience_data[experience_data['job_type'] == prog_job_type]
            
            # Plot salary progression lines for each company
            prog_fig = px.line(
                job_prog_data,
                x="years_experience",
                y="salary",
                color="company",
                markers=True,
                title=f"Salary Progression by Years of Experience - {prog_job_type}",
                labels={"salary": "Annual Salary ($)", "years_experience": "Years of Experience", "company": "Company"}
            )
            
            prog_fig.update_layout(height=500)
            st.plotly_chart(prog_fig, use_container_width=True)
            
            # Add experience milestones explanation
            st.write("### Experience Level Milestones")
            
            milestone_col1, milestone_col2 = st.columns(2)
            
            with milestone_col1:
                st.info("""
                **Experience Level Definitions**
                
                * **Entry Level (0-2 years):** New graduates, junior positions
                * **Mid-Level (3-5 years):** Experienced professionals with some autonomy
                * **Senior (6-9 years):** Leadership roles, deep expertise in area
                * **Staff/Principal (10+ years):** Strategic leadership, company-wide impact
                """)
            
            with milestone_col2:
                # Calculate average progression rates
                baseline = job_prog_data[job_prog_data['years_experience'] == 0]['salary'].mean()
                
                # Calculate average salaries at each experience level
                avg_by_exp = job_prog_data.groupby('years_experience')['salary'].mean()
                
                # Calculate growth from baseline
                growth_rates = [(avg / baseline - 1) * 100 for avg in avg_by_exp]
                
                # Display growth metrics
                st.write("**Average Salary Growth from Entry Level**")
                
                for i, years in enumerate(sorted(job_prog_data['years_experience'].unique())):
                    if years == 0:
                        continue
                    
                    growth = growth_rates[i]
                    st.metric(
                        label=f"{years} Years Experience",
                        value=f"${avg_by_exp[years]:,.0f}",
                        delta=f"{growth:.1f}%"
                    )
            
            # Show table of experience-based progression data
            st.write("### Detailed Progression Data by Company")
            
            # Format the progression table
            prog_table = job_prog_data.pivot(index='company', columns='years_experience', values='salary')
            prog_table.columns = [f"{col} Years" for col in prog_table.columns]
            
            # Calculate growth percentages
            for company in prog_table.index:
                baseline = prog_table.loc[company, '0 Years']
                for col in prog_table.columns[1:]:
                    current = prog_table.loc[company, col]
                    growth_pct = (current / baseline - 1) * 100
                    prog_table.loc[company, f"{col} Growth"] = f"{growth_pct:.1f}%"
            
            # Reorder columns to alternate salary and growth
            new_cols = []
            for year in [0, 2, 5, 8, 12]:
                new_cols.append(f"{year} Years")
                if year > 0:
                    new_cols.append(f"{year} Years Growth")
            
            # Select and display the table
            display_prog = prog_table[new_cols]
            
            # Format salary columns
            for col in display_prog.columns:
                if "Growth" not in col:
                    display_prog[col] = display_prog[col].apply(lambda x: f"${x:,.0f}")
            
            st.dataframe(display_prog, use_container_width=True)
    
    with tabs[14]:  # Job Alerts Tab
        st.subheader("Personalized Job Alerts")
        
        # Create tabs for different alert features
        alert_tabs = st.tabs(["Create Alert", "Saved Alerts", "Matching Jobs"])
        
        with alert_tabs[0]:  # Create Alert tab
            st.write("### Create a New Job Alert")
            
            # Option to use natural language or detailed preferences
            preference_input = st.radio(
                "How would you like to set your preferences?",
                ["Natural Language Description", "Detailed Preferences"],
                help="Choose how to specify your job preferences"
            )
            
            if preference_input == "Natural Language Description":
                # Natural language input
                nl_description = st.text_area(
                    "Describe your ideal job",
                    height=150,
                    placeholder="E.g., I'm looking for a remote full-stack developer role using React and Node.js, preferably at a startup or tech company.",
                    help="Describe the type of job you're looking for in your own words"
                )
                
                extract_button = st.button("Extract Preferences")
                
                if extract_button and nl_description:
                    with st.spinner("Analyzing your preferences..."):
                        # Extract preferences from text
                        preferences = extract_user_preferences_from_text(nl_description)
                        
                        # Show extracted preferences
                        st.success("Successfully extracted your preferences!")
                        
                        # Display preferences in columns
                        pref_col1, pref_col2 = st.columns(2)
                        
                        with pref_col1:
                            st.write("#### Job Details")
                            if 'job_types' in preferences:
                                st.write(f"**Job Types:** {', '.join(preferences['job_types'])}")
                            if 'skills' in preferences:
                                st.write(f"**Skills:** {', '.join(preferences['skills'])}")
                            if 'experience_level' in preferences:
                                st.write(f"**Experience Level:** {preferences['experience_level']}")
                        
                        with pref_col2:
                            st.write("#### Company & Location")
                            if 'companies' in preferences:
                                st.write(f"**Preferred Companies:** {', '.join(preferences['companies'])}")
                            if 'locations' in preferences:
                                st.write(f"**Locations:** {', '.join(preferences['locations'])}")
                            if 'remote' in preferences:
                                st.write(f"**Remote Work:** {'Yes' if preferences['remote'] else 'No preference'}")
                        
                        # Option to save alert
                        alert_name = st.text_input("Alert Name", placeholder="E.g., Remote Full-Stack Jobs")
                        
                        if st.button("Save Alert") and alert_name:
                            saved = save_user_alert(preferences, alert_name)
                            if saved:
                                st.success(f"Alert '{alert_name}' saved successfully!")
                                st.info("You can view and manage your saved alerts in the 'Saved Alerts' tab.")
                            else:
                                st.error("Failed to save alert. Please try again with a different name.")
                                
                        # Show matching jobs
                        st.write("### Matching Jobs")
                        matching_jobs = create_job_alert(display_data, preferences)
                        
                        if not matching_jobs.empty:
                            st.success(f"Found {len(matching_jobs)} matching jobs!")
                            st.dataframe(matching_jobs)
                            
                            # Show distribution of matching jobs
                            st.write("### Match Distribution")
                            match_fig = plot_preference_match_distribution(display_data, preferences)
                            st.plotly_chart(match_fig, use_container_width=True)
                        else:
                            st.info("No matching jobs found for your preferences.")
                            st.write("Try broadening your preferences or adding more job postings to the database.")
            
            else:  # Detailed Preferences
                st.write("#### Set Your Job Preferences")
                
                # Create columns for preference inputs
                detail_col1, detail_col2 = st.columns(2)
                
                with detail_col1:
                    # Job type preferences
                    selected_job_types = st.multiselect(
                        "Job Types",
                        options=display_data['job_type'].unique().tolist(),
                        help="Select one or more job types you're interested in"
                    )
                    
                    # Skills preferences
                    skills_input = st.text_input(
                        "Required Skills (comma-separated)",
                        placeholder="E.g., Python, React, SQL, AWS",
                        help="Enter skills that you want to be mentioned in job postings"
                    )
                    
                    # Experience level
                    experience = st.selectbox(
                        "Experience Level",
                        ["Any", "Entry Level", "Mid Level", "Senior", "Lead/Manager"],
                        help="Select your preferred experience level"
                    )
                
                with detail_col2:
                    # Company preferences
                    selected_companies = st.multiselect(
                        "Preferred Companies",
                        options=display_data['company'].unique().tolist(),
                        help="Select one or more companies you're interested in"
                    )
                    
                    # Location preferences
                    regions = [
                        "Any", "US West", "US East", "US Central", 
                        "North America", "Europe", "Asia", "Australia"
                    ]
                    selected_regions = st.multiselect(
                        "Preferred Regions",
                        options=regions,
                        help="Select one or more regions you're interested in"
                    )
                    
                    # Remote preference
                    remote_preference = st.radio(
                        "Remote Work",
                        ["No Preference", "Remote Only", "Hybrid", "On-site"],
                        help="Select your remote work preference"
                    )
                
                # Build preferences dict
                if st.button("Create Alert from Preferences"):
                    manual_preferences = {}
                    
                    # Add selected preferences to dict
                    if selected_job_types:
                        manual_preferences['job_types'] = selected_job_types
                    
                    if skills_input:
                        manual_preferences['skills'] = [s.strip() for s in skills_input.split(',')]
                    
                    if experience != "Any":
                        manual_preferences['experience_level'] = experience
                    
                    if selected_companies:
                        manual_preferences['companies'] = selected_companies
                    
                    if selected_regions and "Any" not in selected_regions:
                        manual_preferences['locations'] = selected_regions
                    
                    if remote_preference == "Remote Only":
                        manual_preferences['remote'] = True
                    elif remote_preference == "On-site":
                        manual_preferences['remote'] = False
                    
                    # Create alert from manual preferences
                    alert_name = st.text_input("Alert Name", placeholder="E.g., Senior Dev Jobs")
                    
                    if alert_name:
                        saved = save_user_alert(manual_preferences, alert_name)
                        if saved:
                            st.success(f"Alert '{alert_name}' saved successfully!")
                            st.info("You can view and manage your saved alerts in the 'Saved Alerts' tab.")
                        else:
                            st.error("Failed to save alert. Please try again with a different name.")
                    
                    # Show matching jobs
                    matching_jobs = create_job_alert(display_data, manual_preferences)
                    
                    if not matching_jobs.empty:
                        st.success(f"Found {len(matching_jobs)} matching jobs!")
                        st.dataframe(matching_jobs)
                        
                        # Show distribution of matching jobs
                        st.write("### Match Distribution")
                        match_fig = plot_preference_match_distribution(display_data, manual_preferences)
                        st.plotly_chart(match_fig, use_container_width=True)
                    else:
                        st.info("No matching jobs found for your preferences.")
                        st.write("Try broadening your preferences or adding more job postings to the database.")
        
        with alert_tabs[1]:  # Saved Alerts tab
            st.write("### Your Saved Job Alerts")
            
            # Get saved alerts
            saved_alerts = get_saved_alerts()
            
            if saved_alerts:
                # Create columns for each alert
                for i, (alert_name, preferences) in enumerate(saved_alerts.items()):
                    with st.expander(f"Alert: {alert_name}"):
                        # Display alert details
                        st.write("#### Alert Details")
                        
                        # Build display of preferences
                        pref_details = []
                        
                        if 'job_types' in preferences:
                            pref_details.append(f"**Job Types:** {', '.join(preferences['job_types'])}")
                        
                        if 'skills' in preferences:
                            pref_details.append(f"**Skills:** {', '.join(preferences['skills'])}")
                        
                        if 'experience_level' in preferences:
                            pref_details.append(f"**Experience Level:** {preferences['experience_level']}")
                        
                        if 'companies' in preferences:
                            pref_details.append(f"**Preferred Companies:** {', '.join(preferences['companies'])}")
                        
                        if 'locations' in preferences:
                            pref_details.append(f"**Locations:** {', '.join(preferences['locations'])}")
                        
                        if 'remote' in preferences:
                            pref_details.append(f"**Remote Work:** {'Yes' if preferences['remote'] else 'No'}")
                        
                        # Display preferences
                        for detail in pref_details:
                            st.write(detail)
                        
                        # Alert actions
                        alert_col1, alert_col2 = st.columns(2)
                        
                        with alert_col1:
                            # Check for new matches
                            if st.button(f"Check for New Matches", key=f"check_{alert_name}"):
                                # Count matching jobs
                                matching_count = get_matching_job_count(display_data, preferences)
                                st.success(f"Found {matching_count} matching jobs!")
                        
                        with alert_col2:
                            # Delete alert
                            if st.button(f"Delete Alert", key=f"delete_{alert_name}"):
                                deleted = delete_user_alert(alert_name)
                                if deleted:
                                    st.success(f"Alert '{alert_name}' deleted!")
                                    st.rerun()
                                else:
                                    st.error("Failed to delete alert. Please try again.")
            else:
                st.info("You don't have any saved alerts yet.")
                st.write("Go to the 'Create Alert' tab to set up job alerts based on your preferences.")
        
        with alert_tabs[2]:  # Matching Jobs tab
            st.write("### Find Matching Jobs")
            
            # Select from saved alerts or create temp search
            search_options = ["Use Saved Alert"] + ["Create Temporary Search"]
            search_choice = st.radio("Search Method", search_options)
            
            if search_choice == "Use Saved Alert":
                # Get saved alerts
                saved_alerts = get_saved_alerts()
                
                if saved_alerts:
                    selected_alert = st.selectbox(
                        "Select Saved Alert",
                        options=list(saved_alerts.keys())
                    )
                    
                    if selected_alert and st.button("Find Matches"):
                        alert_preferences = saved_alerts[selected_alert]
                        
                        # Get ranked matches
                        ranked_matches = rank_job_matches(display_data, alert_preferences)
                        
                        if not ranked_matches.empty:
                            st.success(f"Found {len(ranked_matches)} matches for '{selected_alert}'!")
                            
                            # Show match quality distribution
                            match_fig = px.histogram(
                                ranked_matches,
                                x="match_score",
                                nbins=10,
                                labels={"match_score": "Match Score (%)", "count": "Number of Jobs"},
                                title="Job Match Quality Distribution",
                                color_discrete_sequence=["#3366CC"]
                            )
                            match_fig.update_layout(xaxis_range=[0, 100])
                            st.plotly_chart(match_fig, use_container_width=True)
                            
                            # Show ranked matches
                            st.write("#### Ranked Matching Jobs")
                            st.dataframe(
                                ranked_matches[['job_title', 'company', 'location', 'match_score', 'date']].sort_values('match_score', ascending=False)
                            )
                        else:
                            st.info("No matching jobs found for this alert.")
                            st.write("Try broadening your preferences or adding more job postings to the database.")
                else:
                    st.info("You don't have any saved alerts yet.")
                    st.write("Go to the 'Create Alert' tab to set up job alerts based on your preferences.")
            
            else:  # Create Temporary Search
                st.write("#### Quick Job Search")
                
                # Quick search fields
                search_job_types = st.multiselect(
                    "Job Types",
                    options=display_data['job_type'].unique().tolist(),
                    default=[display_data['job_type'].value_counts().index[0]],
                    help="Select one or more job types"
                )
                
                # Keyword search
                keywords = st.text_input(
                    "Keywords (comma-separated)",
                    placeholder="E.g., Python, cloud, senior",
                    help="Enter keywords to search for in job titles and descriptions"
                )
                
                # Company filter
                search_companies = st.multiselect(
                    "Companies (optional)",
                    options=display_data['company'].unique().tolist(),
                    help="Filter by specific companies (leave empty for all)"
                )
                
                # Search button
                if st.button("Search Jobs"):
                    # Build search preferences
                    search_preferences = {}
                    
                    if search_job_types:
                        search_preferences['job_types'] = search_job_types
                    
                    if keywords:
                        search_preferences['skills'] = [k.strip() for k in keywords.split(',')]
                    
                    if search_companies:
                        search_preferences['companies'] = search_companies
                    
                    # Get matching jobs
                    search_results = create_job_alert(display_data, search_preferences)
                    
                    if not search_results.empty:
                        st.success(f"Found {len(search_results)} matching jobs!")
                        
                        # Show results
                        st.write("#### Search Results")
                        st.dataframe(search_results)
                        
                        # Option to save as alert
                        save_search = st.checkbox("Save this search as an alert")
                        
                        if save_search:
                            alert_name = st.text_input("Alert Name", placeholder="E.g., Quick Search")
                            
                            if alert_name and st.button("Save as Alert"):
                                saved = save_user_alert(search_preferences, alert_name)
                                if saved:
                                    st.success(f"Alert '{alert_name}' saved successfully!")
                                else:
                                    st.error("Failed to save alert. Please try again with a different name.")
