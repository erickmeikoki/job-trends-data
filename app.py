import streamlit as st
import pandas as pd
import io
from utils.data_processor import process_data, generate_sample_schema
from utils.visualizer import (
    plot_jobs_by_month,
    plot_jobs_by_type,
    plot_jobs_trend,
    plot_company_distribution
)

# Set page configuration
st.set_page_config(
    page_title="SWE Job Tracker",
    page_icon="💻",
    layout="wide"
)

# Initialize session state variables
if "data" not in st.session_state:
    st.session_state.data = None

# Application title
st.title("Software Engineering Job Posting Tracker")
st.write("Track and visualize software engineering job trends over time")

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
    
    if upload_file is not None:
        try:
            data = pd.read_csv(upload_file)
            st.session_state.data = process_data(data)
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
             "Machine Learning", "Mobile", "QA/Testing", "Other"]
        )
        
        company = st.text_input("Company")
        location = st.text_input("Location")
        salary = st.text_input("Salary (optional)")
        
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
                
                # Add to existing data or create new dataframe
                if st.session_state.data is not None:
                    st.session_state.data = pd.concat([st.session_state.data, new_entry], ignore_index=True)
                else:
                    st.session_state.data = process_data(new_entry)
                    
                st.sidebar.success("Job posting added!")
                st.rerun()

# Filtering options (only shown if data exists)
if st.session_state.data is not None:
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
if st.session_state.data is None:
    st.info("No data available. Please upload a CSV file or add job postings manually.")
    
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
        "Company Distribution"
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
    
    # Job Market Analysis
    st.header("Job Market Analysis")
    
    # Basic statistics in columns
    col1, col2, col3 = st.columns(3)
    
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
    
    # Additional job market insights
    if not display_data.empty:
        st.subheader("Job Type Distribution")
        job_type_counts = display_data['job_type'].value_counts()
        st.bar_chart(job_type_counts)
