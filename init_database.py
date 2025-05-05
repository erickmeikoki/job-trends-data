import pandas as pd
from utils.database import init_db, add_multiple_job_postings, get_connection_status, clear_all_job_postings
from utils.data_processor import process_data

def initialize_database_with_sample_data():
    """Initialize the database and load sample data."""
    
    # Check database connection
    if not get_connection_status():
        print("Failed to connect to the database. Please check your connection settings.")
        return False
    
    # Initialize database tables
    print("Initializing database...")
    if not init_db():
        print("Failed to initialize database tables.")
        return False
    
    # Clear existing data (optional)
    print("Clearing existing data...")
    clear_all_job_postings()
    
    # Load sample data from CSV
    try:
        print("Loading sample data from job_postings.csv...")
        df = pd.read_csv('job_postings.csv')
        
        # Process data to ensure correct format
        processed_df = process_data(df)
        
        # Add to database
        print(f"Adding {len(processed_df)} job postings to database...")
        success_count, error_count = add_multiple_job_postings(processed_df)
        
        print(f"Database initialization complete!")
        print(f"Successfully added {success_count} job postings.")
        if error_count > 0:
            print(f"Failed to add {error_count} job postings.")
        
        return True
    except Exception as e:
        print(f"Error loading sample data: {e}")
        return False

if __name__ == "__main__":
    initialize_database_with_sample_data()