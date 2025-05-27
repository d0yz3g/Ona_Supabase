import asyncio
import json
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# File to store profiles
PROFILES_FILE = "user_profiles.json"

# Dictionary to store user profiles
user_profiles = {}

async def save_profiles_to_file():
    """
    Saves user profiles to file.
    """
    try:
        with open(PROFILES_FILE, 'w', encoding='utf-8') as f:
            json.dump(user_profiles, f, ensure_ascii=False, indent=4)
        logger.info(f"Profiles saved to file {PROFILES_FILE}")
        return True
    except Exception as e:
        logger.error(f"Error saving profiles to file: {e}")
        return False

async def load_profiles_from_file():
    """
    Loads user profiles from file.
    """
    global user_profiles
    try:
        if os.path.exists(PROFILES_FILE):
            with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
                user_profiles = json.load(f)
            logger.info(f"Loaded {len(user_profiles)} profiles from file {PROFILES_FILE}")
            return True
        else:
            logger.info(f"Profile file {PROFILES_FILE} not found. Creating a new one.")
            user_profiles = {}
            return False
    except Exception as e:
        logger.error(f"Error loading profiles from file: {e}")
        user_profiles = {}
        return False

async def create_test_profile():
    """
    Creates a test user profile.
    """
    # Create a sample user profile
    test_user_id = "123456789"
    
    # Sample profile data
    profile_data = {
        "answers": {
            "name": "Test User",
            "age": "30",
            "birthdate": "01.01.1990",
            "birthplace": "Test City",
            "timezone": "UTC+3"
        },
        "profile_completed": True,
        "profile_text": "This is a test profile for the persistence functionality.",
        "profile_details": "This is a detailed test profile for the persistence functionality.",
        "personality_type": "Интеллектуальный",
        "secondary_type": "Творческий",
        "type_counts": {
            "A": 10,
            "B": 5,
            "C": 8,
            "D": 7
        }
    }
    
    # Save the profile
    user_profiles[test_user_id] = profile_data
    
    # Save to file
    result = await save_profiles_to_file()
    
    return result

async def load_and_verify_profile():
    """
    Loads profiles from file and verifies if the test profile exists.
    """
    # Load profiles
    await load_profiles_from_file()
    
    # Check if test profile exists
    test_user_id = "123456789"
    if test_user_id in user_profiles:
        profile = user_profiles[test_user_id]
        logger.info("Test profile found:")
        logger.info(f"Name: {profile['answers'].get('name')}")
        logger.info(f"Personality type: {profile.get('personality_type')}")
        return True
    else:
        logger.error("Test profile not found!")
        return False

async def main():
    """
    Main function.
    """
    # Check if the profile file already exists
    file_exists = os.path.exists(PROFILES_FILE)
    logger.info(f"Profile file exists: {file_exists}")
    
    # If file exists, load and verify
    if file_exists:
        logger.info("Loading existing profiles...")
        result = await load_and_verify_profile()
        if result:
            logger.info("Test successful! Profile was loaded correctly.")
        else:
            logger.info("Test failed! Creating a new test profile...")
            result = await create_test_profile()
            if result:
                logger.info("Test profile created successfully. Please run the script again to verify persistence.")
    else:
        # Create test profile
        logger.info("Creating test profile...")
        result = await create_test_profile()
        if result:
            logger.info("Test profile created successfully. Please run the script again to verify persistence.")

if __name__ == "__main__":
    asyncio.run(main()) 