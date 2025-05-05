import os
import pandas as pd
from sqlalchemy import create_engine, Column, Integer, String, Float, Date, MetaData, Table, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Use the database URL from your provided connection string
DATABASE_URL = "postgresql://neondb_owner:npg_FnrGRS50uZxT@ep-spring-dawn-a4g9qr6u-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)

# Define job_postings table model
class JobPosting(Base):
    __tablename__ = 'job_postings'
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False)
    job_title = Column(String, nullable=False)
    job_type = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, nullable=False)
    salary = Column(String)
    
    def __repr__(self):
        return f"<JobPosting(id={self.id}, title={self.job_title}, company={self.company})>"

def init_db():
    """Initialize the database by creating all tables if they don't exist."""
    try:
        Base.metadata.create_all(engine)
        print("Database tables created successfully!")
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

def add_job_posting(date, job_title, job_type, company, location, salary=""):
    """Add a single job posting to the database."""
    session = Session()
    try:
        # Convert string date to date object if needed
        if isinstance(date, str):
            date = datetime.strptime(date, "%Y-%m-%d").date()
        
        job = JobPosting(
            date=date,
            job_title=job_title,
            job_type=job_type,
            company=company,
            location=location,
            salary=salary
        )
        session.add(job)
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error adding job posting: {e}")
        return False
    finally:
        session.close()

def add_multiple_job_postings(df):
    """Add multiple job postings from a pandas DataFrame."""
    success_count = 0
    error_count = 0
    
    for _, row in df.iterrows():
        try:
            # Handle potential missing values
            salary = row.get('salary', '')
            
            result = add_job_posting(
                date=row['date'],
                job_title=row['job_title'],
                job_type=row['job_type'],
                company=row['company'],
                location=row['location'],
                salary=salary
            )
            
            if result:
                success_count += 1
            else:
                error_count += 1
        except Exception as e:
            error_count += 1
            print(f"Error adding job posting: {e}")
    
    return success_count, error_count

def get_all_job_postings():
    """Retrieve all job postings from the database."""
    session = Session()
    try:
        job_postings = session.query(JobPosting).all()
        
        # Convert to DataFrame
        if job_postings:
            records = []
            for job in job_postings:
                records.append({
                    'id': job.id,
                    'date': job.date,
                    'job_title': job.job_title,
                    'job_type': job.job_type,
                    'company': job.company,
                    'location': job.location,
                    'salary': job.salary
                })
            return pd.DataFrame(records)
        else:
            return pd.DataFrame()
    except Exception as e:
        print(f"Error retrieving job postings: {e}")
        return pd.DataFrame()
    finally:
        session.close()

def delete_job_posting(job_id):
    """Delete a job posting by ID."""
    session = Session()
    try:
        job = session.query(JobPosting).filter(JobPosting.id == job_id).first()
        if job:
            session.delete(job)
            session.commit()
            return True
        return False
    except Exception as e:
        session.rollback()
        print(f"Error deleting job posting: {e}")
        return False
    finally:
        session.close()

def clear_all_job_postings():
    """Remove all job postings from the database."""
    session = Session()
    try:
        session.query(JobPosting).delete()
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        print(f"Error clearing job postings: {e}")
        return False
    finally:
        session.close()

def get_connection_status():
    """Check if database connection is working."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False

# Initialize the database
if __name__ == "__main__":
    init_db()