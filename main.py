# run_app.py
import streamlit as st
import pandas as pd
import requests
import openai
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables from .env file if they exist
load_dotenv()

# Fetch API keys from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")
scrapingbee_api_key = os.getenv("SCRAPINGBEE_API_KEY")

# Check if API keys are loaded correctly
if not openai.api_key or not scrapingbee_api_key:
    st.error("API keys for OpenAI or ScrapingBee are missing. Please set them in the environment.")
    st.stop()

# Title of the app
st.title("Excel Sheet and Web Scraper with GPT-3.5 Turbo (ScrapingBee)")

# Step 1: File uploader to upload Excel file
uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx", "xls"])

# Step 2: URL input for web scraping
news_url = st.text_input("Enter a URL to scrape and analyze:")

# If the user has uploaded a file and provided a URL
if uploaded_file is not None and news_url:
    # Read the Excel file to get the DataFrame and columns
    try:
        # Load the Excel file into a pandas DataFrame
        df = pd.read_excel(uploaded_file)

        # Display the existing data in Excel sheet
        st.write("### Current Data in Excel Sheet:")
        st.dataframe(df)

        # Extract column names
        columns = df.columns.tolist()
        st.write("### Column Names:")
        st.write(columns)
        
        # Step 3: Scrape the URL using ScrapingBee API
        try:
            scrapingbee_url = f"https://app.scrapingbee.com/api/v1/?api_key={scrapingbee_api_key}&url={news_url}&render_js=false"
            response = requests.get(scrapingbee_url)
            response.raise_for_status()  # Check for HTTP request errors
            
            # Parse the HTML content using BeautifulSoup
            soup = BeautifulSoup(response.content, "html.parser")
            paragraphs = soup.find_all('p')
            scraped_text = " ".join([para.get_text() for para in paragraphs])

            st.write(f"### Scraped Text Preview from {news_url}:")
            st.write(scraped_text[:500] + "...")  # Show the first 500 characters of the scraped text

            # Step 4: Use OpenAI GPT-3.5 Turbo to analyze the scraped text
            st.write("### Extracting information that matches the Excel sheet columns using GPT-3.5 Turbo...")

            # Prepare the prompt for GPT-3.5 Turbo
            messages = [
                {"role": "system", "content": "You are a helpful assistant that extracts information from text."},
                {"role": "user", "content": f"Based on the following columns: {columns}, extract relevant information from this text: {scraped_text}"}
            ]

            # Call the OpenAI GPT-3.5 Turbo API to process the text
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.7
            )

            # Get the model's response
            analysis = response['choices'][0]['message']['content'].strip()
            st.write("### AI Extracted Data:")
            st.write(analysis)

            # Step 5: Parse the extracted text and add it as a new row to the DataFrame
            new_row = dict()  # Initialize new row as a dictionary

            # For simplicity, let's assume that the extracted data is a comma-separated list of values matching the columns
            extracted_values = analysis.split(',')
            if len(extracted_values) == len(columns):
                for col, val in zip(columns, extracted_values):
                    new_row[col] = val.strip()  # Strip spaces and map values to columns

                # Append the new row to the DataFrame
                df = df.append(new_row, ignore_index=True)

                # Display the updated DataFrame
                st.write("### Updated Data in Excel Sheet:")
                st.dataframe(df)

                # Allow the user to download the updated DataFrame
                st.write("### Download the Updated Data as CSV:")
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download data as CSV",
                    data=csv,
                    file_name='updated_data.csv',
                    mime='text/csv'
                )
            else:
                st.error("The number of extracted values does not match the number of columns. Please review the extraction.")
        
        except Exception as e:
            st.error(f"Failed to scrape and analyze the URL: {e}")
    
    except Exception as e:
        st.error(f"Failed to load the Excel file: {e}")
else:
    if not uploaded_file:
        st.write("Please upload an Excel file.")
    if not news_url:
        st.write("Please provide a URL to scrape.")
