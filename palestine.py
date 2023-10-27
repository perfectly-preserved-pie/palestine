from dotenv import load_dotenv
from google.cloud import translate_v2 as translate
from loguru import logger
import pandas as pd

# Load environment variables from .env file
load_dotenv()

def translate_text(text: str, row_number: int, target_language: str = 'en') -> str:
    """
    Translate text into a target language using Google Cloud Translation API.
    
    Parameters:
        text (str): Text to translate.
        row_number (int): The row number for logging.
        target_language (str): ISO 639-1 language code of the target language.
        
    Returns:
        str: Translated text.
    """
    # Initialize the Google Cloud Translate client
    # The client will automatically use the service account key from the environment variable
    translate_client = translate.Client()
    
    # Perform translation
    try:
        result = translate_client.translate(text, target_language=target_language)
        logger.success(f"Translated row {row_number}: {text} -> {result['translatedText']}")
    except Exception as e:
        logger.error(f"Error translating row {row_number}: {text}")
        logger.error(e)
    
    return result['translatedText']

# Use the function
# This assumes that the GOOGLE_APPLICATION_CREDENTIALS environment variable has been set
# either manually or through the .env file
#translated_text = translate_text("مرحبا", 0, "en")
#print(translated_text)

# Load the CSV and set the header
df = pd.read_csv('extracted.csv')

# Drop the first column
df.drop(df.columns[0], axis=1, inplace=True)

# Drop all empty rows
df.dropna(how='all', inplace=True)

# Run the translation function on the 'Name' column and save the result in a new column called 'English Name'
# The 'enumerate' function provides both the index (row number) and the value for each row
df['English Name'] = [translate_text(name, i) for i, name in enumerate(df['Name'])]

# Save the translated data to a Parquet file
df.to_parquet('translated.parquet', index=False)