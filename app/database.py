from databases import Database
from dotenv import load_dotenv
import os
import asyncio
import logging

# Load environment variables from .env file
load_dotenv()

# Retrieve the PostgreSQL URL from the environment variable
postgres_url = os.getenv('POSTGRES_URL')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Enhanced database configuration with connection pool settings
if postgres_url:
    # Add connection pool parameters for better reliability
    database = Database(
        postgres_url,
        min_size=1,  # Minimum number of connections in the pool
        max_size=10,  # Maximum number of connections in the pool
        max_queries=50,  # Maximum number of queries per connection
        max_inactive_connection_lifetime=300,  # 5 minutes
        timeout=30,  # Connection timeout in seconds
        command_timeout=60,  # Command timeout in seconds
    )
else:
    logger.error("POSTGRES_URL environment variable not set!")
    database = None

async def get_database():
    """Get database connection with retry logic."""
    if database is None:
        raise RuntimeError("Database not configured - POSTGRES_URL missing")
    
    max_retries = 3
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            if not database.is_connected:
                await database.connect()
            return database
        except Exception as e:
            logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                logger.error("All database connection attempts failed")
                raise

async def execute_with_retry(query, values=None):
    """Execute database query with retry logic."""
    db = await get_database()
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            if values:
                return await db.execute(query=query, values=values)
            else:
                return await db.execute(query=query)
        except Exception as e:
            logger.warning(f"Query execution attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error("All query execution attempts failed")
                raise

async def fetch_with_retry(query, values=None):
    """Fetch database results with retry logic."""
    db = await get_database()
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            if values:
                return await db.fetch_all(query=query, values=values)
            else:
                return await db.fetch_all(query=query)
        except Exception as e:
            logger.warning(f"Query fetch attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error("All query fetch attempts failed")
                raise

async def fetch_one_with_retry(query, values=None):
    """Fetch single database result with retry logic."""
    db = await get_database()
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            if values:
                return await db.fetch_one(query=query, values=values)
            else:
                return await db.fetch_one(query=query)
        except Exception as e:
            logger.warning(f"Query fetch_one attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
                retry_delay *= 2
            else:
                logger.error("All query fetch_one attempts failed")
                raise
