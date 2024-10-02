
from databases import Database
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Retrieve the PostgreSQL URL from the environment variable
postgres_url = os.getenv('POSTGRES_URL')

# Initialize the database connection
database = Database(postgres_url)
