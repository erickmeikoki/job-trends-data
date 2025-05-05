import pandas as pd
import datetime
import requests
import re
import json
import time
from bs4 import BeautifulSoup
import streamlit as st
import trafilatura
from utils.database import add_multiple_job_postings

def fetch_job_data_from_api(api_key=None, location=None, job_type=None, page=1, results_per_page=25):
    """
    Fetch job data from an external API.
    
    Args:
        api_key: API key for authentication
        location: Location filter
        job_type: Job type filter
        page: Page number
        results_per_page: Number of results per page
        
    Returns:
        Dictionary with job data or error message
    """
    # Check if API key is provided
    if not api_key:
        return {"error": "API key is required. Please provide an API key in the settings."}
    
    # Example API endpoint (replace with actual API)
    # This is a placeholder URL for illustration
    api_url = "https://api.example.com/v1/jobs"
    
    # Prepare parameters
    params = {
        "api_key": api_key,
        "page": page,
        "results_per_page": results_per_page
    }
    
    # Add filters if provided
    if location:
        params["location"] = location
    if job_type:
        params["job_type"] = job_type
    
    try:
        # Send request to API
        response = requests.get(api_url, params=params, timeout=10)
        
        # Check if request was successful
        if response.status_code == 200:
            return response.json()
        else:
            return {"error": f"API request failed with status code {response.status_code}"}
    
    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {str(e)}"}
    
    except json.JSONDecodeError:
        return {"error": "Failed to parse API response"}

def process_api_response(api_data):
    """
    Process API response data and convert to DataFrame.
    
    Args:
        api_data: Response data from API
        
    Returns:
        DataFrame with processed job data or None if error
    """
    # Check if API returned an error
    if "error" in api_data:
        st.error(api_data["error"])
        return None
    
    # Check if API returned job data
    if "jobs" not in api_data:
        st.error("API response does not contain job data")
        return None
    
    # Extract job data
    jobs = api_data["jobs"]
    
    # Create DataFrame
    try:
        df = pd.DataFrame(jobs)
        
        # Ensure required columns exist
        required_columns = ["date", "job_title", "job_type", "company", "location"]
        for col in required_columns:
            if col not in df.columns:
                st.error(f"API response is missing required column: {col}")
                return None
        
        # Convert date strings to datetime
        df["date"] = pd.to_datetime(df["date"])
        
        # Add month_year column for consistency with existing data
        df["month_year"] = df["date"].dt.strftime("%Y-%m")
        
        return df
    
    except Exception as e:
        st.error(f"Failed to process API response: {str(e)}")
        return None

def scrape_jobs_from_website(url, max_jobs=50):
    """
    Scrape job data from a website.
    
    Args:
        url: URL of the website to scrape
        max_jobs: Maximum number of jobs to scrape
        
    Returns:
        DataFrame with scraped job data or None if error
    """
    try:
        # Download website content
        downloaded = trafilatura.fetch_url(url)
        if not downloaded:
            st.error(f"Failed to download content from {url}")
            return None
        
        # Extract HTML content
        html_content = downloaded
        
        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")
        
        # Find job listings (example - adjust selectors based on actual website structure)
        job_listings = soup.select(".job-listing")[:max_jobs]
        
        # If no job listings found, try alternative selectors
        if not job_listings:
            job_listings = soup.select(".job-card")[:max_jobs]
        
        # If still no job listings found, try to extract from plain text
        if not job_listings:
            text_content = trafilatura.extract(downloaded)
            if text_content:
                # Parse text content to extract job information
                return parse_jobs_from_text(text_content, max_jobs)
            else:
                st.error("No job listings found on the page")
                return None
        
        # Extract job information
        jobs = []
        
        for listing in job_listings:
            # Example extraction - adjust based on actual HTML structure
            try:
                job_title = listing.select_one(".job-title").text.strip()
                company = listing.select_one(".company-name").text.strip()
                location = listing.select_one(".location").text.strip()
                
                # Job type might not always be available
                job_type_elem = listing.select_one(".job-type")
                job_type = job_type_elem.text.strip() if job_type_elem else "Full-Time"
                
                # Use current date for scraped jobs
                date = datetime.datetime.now().strftime("%Y-%m-%d")
                
                jobs.append({
                    "date": date,
                    "job_title": job_title,
                    "job_type": job_type,
                    "company": company,
                    "location": location,
                    "salary": ""  # Often not available
                })
            except AttributeError:
                # Skip listings where we can't extract all required information
                continue
        
        # Create DataFrame
        if jobs:
            df = pd.DataFrame(jobs)
            
            # Convert date strings to datetime
            df["date"] = pd.to_datetime(df["date"])
            
            # Add month_year column for consistency with existing data
            df["month_year"] = df["date"].dt.strftime("%Y-%m")
            
            return df
        else:
            st.error("Failed to extract job information from the page")
            return None
    
    except Exception as e:
        st.error(f"Failed to scrape jobs: {str(e)}")
        return None

def parse_jobs_from_text(text_content, max_jobs=50):
    """
    Parse job information from plain text content.
    
    Args:
        text_content: Plain text content with job information
        max_jobs: Maximum number of jobs to extract
        
    Returns:
        DataFrame with parsed job data or None if error
    """
    # Example patterns for job information
    job_title_pattern = r"(Software Engineer|Data Scientist|Product Manager|DevOps Engineer|Web Developer|UI/UX Designer|QA Engineer|Full Stack Developer|Front End Developer|Back End Developer)([^a-zA-Z0-9]|$)"
    company_pattern = r"at ([\w\s]+) in"
    location_pattern = r"in ([\w\s,]+)"
    
    # Find all job titles
    job_titles = re.findall(job_title_pattern, text_content)
    
    # Extract job information
    jobs = []
    count = 0
    
    for i, (title, _) in enumerate(job_titles):
        if count >= max_jobs:
            break
        
        # Find context around this job title
        title_pos = text_content.find(title, text_content.find(title) if i > 0 else 0)
        context = text_content[max(0, title_pos - 100):min(len(text_content), title_pos + 200)]
        
        # Extract company
        company_match = re.search(company_pattern, context)
        company = company_match.group(1).strip() if company_match else "Unknown Company"
        
        # Extract location
        location_match = re.search(location_pattern, context)
        location = location_match.group(1).strip() if location_match else "Unknown Location"
        
        # Use current date for scraped jobs
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        # Determine job type based on title keywords
        job_type = "Full-Time"  # Default
        if "intern" in title.lower():
            job_type = "Internship"
        elif "contract" in title.lower() or "freelance" in title.lower():
            job_type = "Contract"
        elif "part" in title.lower() and "time" in title.lower():
            job_type = "Part-Time"
        
        jobs.append({
            "date": date,
            "job_title": title.strip(),
            "job_type": job_type,
            "company": company,
            "location": location,
            "salary": ""  # Usually not available in plain text
        })
        
        count += 1
    
    # Create DataFrame
    if jobs:
        df = pd.DataFrame(jobs)
        
        # Convert date strings to datetime
        df["date"] = pd.to_datetime(df["date"])
        
        # Add month_year column for consistency with existing data
        df["month_year"] = df["date"].dt.strftime("%Y-%m")
        
        return df
    else:
        st.error("Failed to extract job information from the text")
        return None

def schedule_data_refresh(refresh_interval, api_key=None, url=None, max_jobs=50):
    """
    Schedule automatic data refresh from API or scraping.
    
    Args:
        refresh_interval: Interval in hours between refreshes
        api_key: API key for API-based refresh
        url: URL for web scraping-based refresh
        max_jobs: Maximum number of jobs to fetch/scrape
        
    Returns:
        Status message
    """
    # Get last refresh time from session state
    last_refresh = st.session_state.get("last_data_refresh")
    
    # Check if it's time for a refresh
    now = datetime.datetime.now()
    if last_refresh is None or (now - last_refresh).total_seconds() >= (refresh_interval * 3600):
        # Time for a refresh
        if api_key:
            # Refresh using API
            api_data = fetch_job_data_from_api(api_key=api_key, results_per_page=max_jobs)
            df = process_api_response(api_data)
        elif url:
            # Refresh using web scraping
            df = scrape_jobs_from_website(url, max_jobs=max_jobs)
        else:
            return "No API key or URL provided for data refresh"
        
        # If data was successfully retrieved
        if df is not None and not df.empty:
            # Add to database
            add_multiple_job_postings(df)
            
            # Update last refresh time
            st.session_state["last_data_refresh"] = now
            
            return f"Data refreshed successfully at {now.strftime('%Y-%m-%d %H:%M:%S')}"
        else:
            return "Failed to refresh data"
    else:
        # Not time for a refresh yet
        next_refresh = last_refresh + datetime.timedelta(hours=refresh_interval)
        return f"Next data refresh scheduled for {next_refresh.strftime('%Y-%m-%d %H:%M:%S')}"

def import_jobs_from_linkedin_export(file):
    """
    Import job data from LinkedIn Jobs export CSV file.
    
    Args:
        file: Uploaded CSV file object
        
    Returns:
        DataFrame with imported job data or None if error
    """
    try:
        # Read CSV file
        df = pd.read_csv(file)
        
        # Check if file has expected columns
        required_columns = ["Job Title", "Company", "Date", "Location"]
        
        # LinkedIn might use different column names, so try to match
        linkedin_columns = {
            "Job Title": ["Job Title", "Position", "Title", "Role"],
            "Company": ["Company", "Company Name", "Organization"],
            "Date": ["Date", "Date Posted", "Posted Date", "Posting Date"],
            "Location": ["Location", "Job Location", "Place"]
        }
        
        # Map actual columns to expected columns
        column_mapping = {}
        for expected, alternatives in linkedin_columns.items():
            for alt in alternatives:
                if alt in df.columns:
                    column_mapping[alt] = expected
                    break
        
        # Rename columns
        if column_mapping:
            df = df.rename(columns=column_mapping)
        
        # Check if we have all required columns after mapping
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(f"The LinkedIn export is missing required columns: {', '.join(missing_columns)}")
            return None
        
        # Convert to expected format
        formatted_df = pd.DataFrame({
            "date": pd.to_datetime(df["Date"]),
            "job_title": df["Job Title"],
            "company": df["Company"],
            "location": df["Location"],
            "job_type": "Full-Time",  # LinkedIn doesn't always include job type
            "salary": ""  # LinkedIn rarely includes salary
        })
        
        # Add month_year column for consistency with existing data
        formatted_df["month_year"] = formatted_df["date"].dt.strftime("%Y-%m")
        
        return formatted_df
    
    except Exception as e:
        st.error(f"Failed to import LinkedIn data: {str(e)}")
        return None

def import_jobs_from_indeed_export(file):
    """
    Import job data from Indeed Jobs export CSV file.
    
    Args:
        file: Uploaded CSV file object
        
    Returns:
        DataFrame with imported job data or None if error
    """
    try:
        # Read CSV file
        df = pd.read_csv(file)
        
        # Check if file has expected columns
        required_columns = ["Job Title", "Company", "Date", "Location"]
        
        # Indeed might use different column names, so try to match
        indeed_columns = {
            "Job Title": ["Job Title", "Position", "Title"],
            "Company": ["Company", "Company Name"],
            "Date": ["Date", "Date Posted", "Created"],
            "Location": ["Location", "Job Location"]
        }
        
        # Map actual columns to expected columns
        column_mapping = {}
        for expected, alternatives in indeed_columns.items():
            for alt in alternatives:
                if alt in df.columns:
                    column_mapping[alt] = expected
                    break
        
        # Rename columns
        if column_mapping:
            df = df.rename(columns=column_mapping)
        
        # Check if we have all required columns after mapping
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            st.error(f"The Indeed export is missing required columns: {', '.join(missing_columns)}")
            return None
        
        # Convert to expected format
        formatted_df = pd.DataFrame({
            "date": pd.to_datetime(df["Date"]),
            "job_title": df["Job Title"],
            "company": df["Company"],
            "location": df["Location"],
            "job_type": "Full-Time",  # Default value
            "salary": ""  # Default value
        })
        
        # Extract job type from job title if possible
        formatted_df["job_type"] = formatted_df["job_title"].apply(extract_job_type_from_title)
        
        # Add month_year column for consistency with existing data
        formatted_df["month_year"] = formatted_df["date"].dt.strftime("%Y-%m")
        
        return formatted_df
    
    except Exception as e:
        st.error(f"Failed to import Indeed data: {str(e)}")
        return None

def extract_job_type_from_title(title):
    """
    Extract job type from job title.
    
    Args:
        title: Job title
        
    Returns:
        Extracted job type
    """
    title_lower = title.lower()
    
    # Check for internship
    if "intern" in title_lower:
        return "Internship"
    
    # Check for contract
    if "contract" in title_lower or "contractor" in title_lower:
        return "Contract"
    
    # Check for part-time
    if "part-time" in title_lower or "part time" in title_lower:
        return "Part-Time"
    
    # Check for freelance
    if "freelance" in title_lower or "freelancer" in title_lower:
        return "Freelance"
    
    # Default to full-time
    return "Full-Time"