from utils.job_scraper import create_sample_job_data
from utils.database import init_db, clear_all_job_postings, add_multiple_job_postings
from utils.data_processor import process_data
import pandas as pd

# Number of job postings to generate
NUM_ENTRIES = 100

print(f"Generating {NUM_ENTRIES} diverse job postings...")
csv_file = create_sample_job_data(num_entries=NUM_ENTRIES, filename="diverse_job_postings.csv")

# Load and process the generated data
print("Processing data...")
df = pd.read_csv(csv_file)
processed_df = process_data(df)

# Initialize database if needed
print("Initializing database...")
init_db()

# Clear existing data
print("Clearing existing data from database...")
clear_all_job_postings()

# Add to database
print(f"Adding {len(processed_df)} job postings to database...")
success_count, error_count = add_multiple_job_postings(processed_df)

print(f"Successfully added {success_count} job postings to database.")
if error_count > 0:
    print(f"Failed to add {error_count} job postings.")

print("Done! You can now restart the Streamlit app to see the diverse job posting data.")