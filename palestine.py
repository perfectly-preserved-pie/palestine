from dotenv import load_dotenv, find_dotenv
from loguru import logger
import openai
import os
import pandas as pd

# Load environment variables from .env file
load_dotenv(find_dotenv())

import openai
import os
from loguru import logger

from typing import Optional

def translate_text(text: str, row_number: int, common_component: Optional[str] = None, target_language: str = 'en') -> str:
    """
    Translate text into a target language using ChatGPT API.
    
    Parameters:
        text (str): Text to translate.
        row_number (int): The row number for logging.
        common_component (Optional[str]): Common component to keep consistent.
        target_language (str): ISO 639-1 language code of the target language (only 'en' is supported here).
        
    Returns:
        str: Translated text.
    """
    # Initialize your ChatGPT prompt for translation. 
    if common_component:
        prompt = f"Here is an Arabic name starting with the common component '{common_component}'. Please provide the most accurate and consistent transliteration of the name into English characters. Make sure to keep the common component consistent: {text}."
    else:
        prompt = f"Here is an Arabic name. Please provide the most accurate and consistent transliteration of the name into English characters: {text}."

    try:
        # Perform translation using the ChatGPT API
        model_engine = "gpt-4"  # Replace with any engine from https://beta.openai.com/docs/api-reference/engines
        openai.api_key = os.getenv("OPENAI_API_KEY")

        response = openai.ChatCompletion.create(
            model=model_engine,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extract the translated text from the API response
        translated_text = response['choices'][0]['message']['content'].strip()
        logger.success(f"Translated row {row_number}: {text} -> {translated_text}")
        
        return translated_text
    
    except Exception as e:
        logger.error(f"Error translating row {row_number}: {text}")
        logger.error(e)
        return None  # Return None if translation fails

# Load the CSV and set the header
df = pd.read_csv('extracted.csv')

# Drop the first column
df.drop(df.columns[0], axis=1, inplace=True)

# Drop all empty rows
df.dropna(how='all', inplace=True)

# Run the translation function on the 'Name' column and save the result in a new column called 'English Name'
# The 'enumerate' function provides both the index (row number) and the value for each row
#df['English Name'] = [translate_text(name, i) for i, name in enumerate(df['Name'])]

df.loc[:16, 'English Name'] = [translate_text(name, i) for i, name in enumerate(df['Name'].iloc[:16])]


# Save the translated data to a Parquet file
df.to_parquet('translated.parquet', index=False)