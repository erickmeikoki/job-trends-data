from utils.job_scraper import create_sample_job_data

# Generate 50 sample job postings and save to CSV
csv_file = create_sample_job_data(num_entries=50, filename="job_postings.csv")
print(f"Generated job postings saved to {csv_file}")
print("You can now upload this file to the Streamlit app!")