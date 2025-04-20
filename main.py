import os
import sys
import requests
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any
import json

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

import sqlite3

import anthropic

# Read the .env file
load_dotenv()
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
DB_PATH = 'nba.sqlite'

def execute_sql_query(query, db_path=DB_PATH, test_mode=False):
    """
    Execute a SQL query against a SQLite database and return the results.
    
    Args:
        db_path (str): Path to the SQLite database file
        query (str): SQL query to execute
    
    Returns:
        list: Query results as a list of rows
        None: If there's an error executing the query
    """
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        return results
    except sqlite3.Error as e:
        if test_mode:
            print(f"Database error: {e}")
        return None

def read_prompt_json(question: str, path_to_prompt: str, db_path=DB_PATH) -> Dict[str, str]:
    """
    Read the prompt from a JSON file and format it with the given question.
    """
    if not os.path.exists(path_to_prompt):
        raise FileNotFoundError(f"Prompt file not found at {path_to_prompt}")
    if not path_to_prompt.endswith('.json'):
        raise ValueError("Prompt file must be a .json file")

    with open(path_to_prompt, 'r') as f:
        prompt = json.load(f)

    # Read the schema from the database
    schema = get_database_schema(db_path)

    if 'system' in prompt:
        system_prompt = prompt['system'].format(question=question, database_schema=schema)
    else:
        system_prompt = None

    if 'user' in prompt:
        user_prompt = prompt['user'].format(question=question)
    else:
        user_prompt = question

    return {
        'system': system_prompt,
        'user': user_prompt
    }

def get_database_schema(db_path: str=DB_PATH) -> Dict[str, List[Dict[str, Any]]]:
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Query to get all tables
    cursor.execute("SELECT * FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    schema_info = {}
    
    # For each table, get column information
    for table in tables:
        table_name = table[1]
        pragma = f"PRAGMA table_info('{table_name}');"
        cursor.execute(pragma)
        columns = cursor.fetchall()
        
        # Store column information
        schema_info[table_name] = [
            {
                "name": col[1],
                "type": col[2],
                "notnull": col[3],
                "default_value": col[4],
                "is_primary_key": col[5]
            }
            for col in columns
        ]
    
    conn.close()

    # Format the schema information
    for table, columns in schema_info.items():
        formatted_columns = []
        for col in columns:
            formatted_columns.append(f"{col['name']} ({col['type']})")
            if col['notnull']:
                formatted_columns[-1] += " NOT NULL"
            if col['is_primary_key']:
                formatted_columns[-1] += " PRIMARY KEY"
            if col['default_value'] is not None:
                formatted_columns[-1] += f" DEFAULT {col['default_value']}"
        schema_info[table] = ", ".join(formatted_columns)

    tables = list(schema_info.keys())

    ret_str = f"\t<tables>\n\t\t[{', '.join(tables)}]\n\t</tables>\n"
    ret_str += "\t<schema>\n"
    for table, columns in schema_info.items():
        ret_str += f"\t\t<{table}>\n"
        ret_str += f"\t\t\t{columns}\n"
        ret_str += f"\t\t</{table}>\n"
    ret_str += "</schema>\n"

    return ret_str

# Class to interact with the Claude API
# I used Claude to write the bulk of this class, and added a method at the end to call teh completion method and get the text from the response
class ClaudeAPI:
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-7-sonnet-20250219"):
        """
        Initialize the Claude API wrapper.
        
        Args:
            api_key: Your Anthropic API key. If not provided, will look for ANTHROPIC_API_KEY env variable
            model: The Claude model to use (defaults to Claude 3.7 Sonnet)
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("API key must be provided or set as ANTHROPIC_API_KEY environment variable")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model
        
    def completion(self, 
            user_prompt: str, 
            system_prompt: Optional[str] = None,
            max_tokens: int = 1024,
            temperature: float = 0.0, # Turn temperature down to 0.0 for deterministic results
            **kwargs) -> Dict[Any, Any]:
        """
        Send a completion request to Claude with system and user prompts.
        
        Args:
            user_prompt: The user's input prompt
            system_prompt: Optional system prompt to set context/instructions
            max_tokens: Maximum number of tokens to generate
            temperature: Controls randomness (0.0 to 1.0)
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            The complete response from the Claude API
        """
        messages = [{
            "role": "user",
            "content": user_prompt
        }]
        
        # Add the system message if provided
        if not system_prompt:
            system_prompt = ""
        
        # Call the Claude API
        response = self.client.messages.create(
            model=self.model,
            messages=messages,
            system=system_prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs
        )
        
        return response
    
    def get_response_text(self, response: Dict[Any, Any]) -> str:
        """
        Extract just the text content from a Claude API response.
        
        Args:
            response: The response from the Claude API
            
        Returns:
            The text content of Claude's response
        """
        if hasattr(response, "content"):
            contents = response.content
            if contents and len(contents) > 0:
                return contents[0].text
        
        return ""

    def generate_response(self, 
            user_prompt: str, 
            system_prompt: Optional[str] = None,
            max_tokens: int = 1024,
            temperature: float = 0.7,
            **kwargs) -> str:
        """
        Generate a response to a query using the Claude API.
        
        Args:
            user_prompt: The user's input prompt
            system_prompt: Optional system prompt to set context/instructions
            max_tokens: Maximum number of tokens to generate
            temperature: Controls randomness (0.0 to 1.0)
            **kwargs: Additional parameters to pass to the API
            
        Returns:
            The text response from the Claude API
        """
        response = self.completion(user_prompt, system_prompt, max_tokens, temperature, **kwargs)
        return self.get_response_text(response)

if __name__ == '__main__':
    # Check if the script is being run directly
    question = input("Enter your prompt: ")

    # Initialize the Claude API
    claude_api = ClaudeAPI(api_key=CLAUDE_API_KEY)

    # Read the prompt from the JSON file
    prompt_path = os.path.join(os.path.dirname(__file__), 'prompts', 'solution_prompt.json')
    prompt = read_prompt_json(question, prompt_path)

    # Generate a response using the Claude API
    response_text = claude_api.generate_response(
        user_prompt=prompt['user'],
        system_prompt=prompt['system']
    )

    # If the response is empty, print an error message
    if not response_text:
        print("Error: No response from Claude.")
        sys.exit(1)

    print(f'\nRunning Claude SQL:\n{response_text}\n')

    # Run the SQL query and print the results
    # try:
    results = execute_sql_query(response_text)
    try:
        if results is None:
            print("Error executing SQL query.")
            sys.exit(1)
        print("SQL Query Results:")
        for row in results:
            print('\t' + str(row))
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        sys.exit(1)