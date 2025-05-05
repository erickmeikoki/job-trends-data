import streamlit as st
import pandas as pd
import io
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
        "Predictions & Forecasts"
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
