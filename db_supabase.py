import os
import logging
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize Supabase client
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    logger.error("SUPABASE_URL or SUPABASE_KEY environment variables are not set")
    raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")

try:
    supabase: Client = create_client(supabase_url, supabase_key)
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    raise

class SupabaseDB:
    """Class for handling Supabase database operations."""
    
    @staticmethod
    async def get_user_profile(user_id: int) -> dict:
        """
        Retrieve a user profile from Supabase.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            dict: User profile data or empty dict if not found
        """
        try:
            response = supabase.table("profiles").select("*").eq("user_id", user_id).execute()
            
            if response.data and len(response.data) > 0:
                logger.info(f"Retrieved profile for user {user_id}")
                return response.data[0]
            else:
                logger.info(f"No profile found for user {user_id}")
                return {}
                
        except Exception as e:
            logger.error(f"Error retrieving user profile for {user_id}: {e}")
            return {}
    
    @staticmethod
    async def save_user_profile(user_id: int, profile_data: dict) -> bool:
        """
        Save or update a user profile in Supabase.
        
        Args:
            user_id: Telegram user ID
            profile_data: Profile data to save
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add user_id to the profile data
            profile_data["user_id"] = user_id
            
            # Check if profile exists
            existing_profile = await SupabaseDB.get_user_profile(user_id)
            
            if existing_profile:
                # Update existing profile
                response = supabase.table("profiles").update(profile_data).eq("user_id", user_id).execute()
                logger.info(f"Updated profile for user {user_id}")
            else:
                # Insert new profile
                response = supabase.table("profiles").insert(profile_data).execute()
                logger.info(f"Created new profile for user {user_id}")
                
            return True
            
        except Exception as e:
            logger.error(f"Error saving user profile for {user_id}: {e}")
            return False
    
    @staticmethod
    async def save_survey_response(user_id: int, question_id: str, answer: str) -> bool:
        """
        Save a survey response to Supabase.
        
        Args:
            user_id: Telegram user ID
            question_id: Question identifier
            answer: User's answer
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response_data = {
                "user_id": user_id,
                "question_id": question_id,
                "answer": answer,
                "created_at": "now()"
            }
            
            response = supabase.table("survey_responses").insert(response_data).execute()
            logger.info(f"Saved survey response for user {user_id}, question {question_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving survey response for user {user_id}, question {question_id}: {e}")
            return False
    
    @staticmethod
    async def get_survey_responses(user_id: int) -> list:
        """
        Get all survey responses for a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            list: List of survey responses
        """
        try:
            response = supabase.table("survey_responses").select("*").eq("user_id", user_id).execute()
            
            if response.data:
                logger.info(f"Retrieved {len(response.data)} survey responses for user {user_id}")
                return response.data
            else:
                logger.info(f"No survey responses found for user {user_id}")
                return []
                
        except Exception as e:
            logger.error(f"Error retrieving survey responses for user {user_id}: {e}")
            return []
    
    @staticmethod
    async def save_reminder(user_id: int, reminder_data: dict) -> bool:
        """
        Save a reminder to Supabase.
        
        Args:
            user_id: Telegram user ID
            reminder_data: Reminder data
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add user_id to the reminder data
            reminder_data["user_id"] = user_id
            
            response = supabase.table("reminders").insert(reminder_data).execute()
            logger.info(f"Saved reminder for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving reminder for user {user_id}: {e}")
            return False
    
    @staticmethod
    async def get_reminders(user_id: int) -> list:
        """
        Get all reminders for a user.
        
        Args:
            user_id: Telegram user ID
            
        Returns:
            list: List of reminders
        """
        try:
            response = supabase.table("reminders").select("*").eq("user_id", user_id).execute()
            
            if response.data:
                logger.info(f"Retrieved {len(response.data)} reminders for user {user_id}")
                return response.data
            else:
                logger.info(f"No reminders found for user {user_id}")
                return []
                
        except Exception as e:
            logger.error(f"Error retrieving reminders for user {user_id}: {e}")
            return []
    
    @staticmethod
    async def delete_reminder(reminder_id: str) -> bool:
        """
        Delete a reminder from Supabase.
        
        Args:
            reminder_id: Reminder ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = supabase.table("reminders").delete().eq("id", reminder_id).execute()
            logger.info(f"Deleted reminder {reminder_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting reminder {reminder_id}: {e}")
            return False
            
    @staticmethod
    async def update_meditation_count(user_id: int, meditation_type: str) -> int:
        """
        Update meditation count for a user.
        
        Args:
            user_id: Telegram user ID
            meditation_type: Type of meditation
            
        Returns:
            int: New count or -1 if error
        """
        try:
            # Get current user stats
            response = supabase.table("user_stats").select("*").eq("user_id", user_id).execute()
            
            if response.data and len(response.data) > 0:
                # Update existing stats
                current_stats = response.data[0]
                meditation_count = current_stats.get("meditation_count", 0) + 1
                
                update_data = {
                    "meditation_count": meditation_count,
                    "last_meditation_type": meditation_type,
                    "last_meditation_at": "now()"
                }
                
                supabase.table("user_stats").update(update_data).eq("user_id", user_id).execute()
                logger.info(f"Updated meditation count for user {user_id} to {meditation_count}")
                return meditation_count
            else:
                # Create new stats
                new_stats = {
                    "user_id": user_id,
                    "meditation_count": 1,
                    "last_meditation_type": meditation_type,
                    "last_meditation_at": "now()"
                }
                
                supabase.table("user_stats").insert(new_stats).execute()
                logger.info(f"Created new stats for user {user_id} with meditation count 1")
                return 1
                
        except Exception as e:
            logger.error(f"Error updating meditation count for user {user_id}: {e}")
            return -1 