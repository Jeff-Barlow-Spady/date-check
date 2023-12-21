import streamlit as st
from azureml.opendatasets import PublicHolidays
import pandas as pd
from dateutil import parser
#import calendarific
import requests
import io
import holidays

# Set page configuration
st.set_page_config(page_title="Date Checker", layout="wide")

st.title("Comprehensive Date Checker")
st.markdown("Enter dates (single or list) to check for holidays and events.")
COUNTRY = st.selectbox("Select Country", ["US", "CA", "MX", "IN", "UK", "FR"])
# Abstract API
#@st.cache_data
def get_holidays_from_abstractapi(date, country=COUNTRY):
    API_KEY = st.secrets["ABSTRACT_KEY"]
    url = f"https://holidays.abstractapi.com/v1/?api_key={API_KEY}&country={country}&year={date.year}&month={date.month}&day={date.day}"
    response = requests.get(url)
    holidays = response.json() if response.status_code == 200 else []
    return [{'Date': date, 'Holiday': holiday.get("name", "Unnamed Holiday"), 'Source': 'Abstract API'} for holiday in holidays]

# Calendarific API
#@st.cache_data
def get_holidays_from_calendarific(date, country=COUNTRY):
    API_KEY = st.secrets["CAL_KEY"]
    url = f"https://calendarific.com/api/v2/holidays?api_key={API_KEY}&country={country}&year={date.year}"
    response = requests.get(url)
    if response.status_code == 200:
        holidays = response.json().get('response', {}).get('holidays', [])
        return [{'Date': date.strftime("%Y-%m-%d"), 'Holiday': holiday.get("name", "Unnamed Holiday"), 'Source': 'Calendarific'} for holiday in holidays if holiday['date']['iso'] == date.strftime("%Y-%m-%d")]
    return []

# AzureML Public Holidays
#@st.cache_data
def get_public_holidays(date):
    country_holidays = holidays.CountryHoliday(COUNTRY)
    if date in country_holidays:
        return [{'Date': date, 'Holiday': country_holidays[date], 'Source': 'Custom Holidays'}]
    return []

# Separate function to validate and convert a single date string
def validate_and_convert_date(date_str):
    try:
        return parser.parse(date_str.strip()), None
    except ValueError:
        return None, f"Invalid date format: {date_str.strip()}"

def process_dates(dates_df):
    results = []
    for _, row in dates_df.iterrows():
        date = row['Date']
        
        # Initialize a flag to track if a holiday has been found
        holiday_found = False

        # Fetch from AzureML Public Holidays
        azure_holidays_df = get_public_holidays(date)
        if azure_holidays_df:
            results.append({
                "Date": date.strftime("%Y-%m-%d"),
                "Holiday": azure_holidays_df[0]['Holiday'],  # Take the first holiday
                "Source": "AzureML"
            })
            holiday_found = True

        # If no holiday found in AzureML, check Abstract API
        if not holiday_found:
            abstract_holidays = get_holidays_from_abstractapi(date)
            if abstract_holidays:
                results.append({
                    "Date": date.strftime("%Y-%m-%d"),
                    "Holiday": abstract_holidays[0]['Holiday'],  # Take the first holiday
                    "Source": "Abstract API"
                })
                holiday_found = True

        # If no holiday found in Abstract API, check Calendarific
        if not holiday_found:
            calendarific_holidays = get_holidays_from_calendarific(date)
            if calendarific_holidays:
                results.append({
                    "Date": date.strftime("%Y-%m-%d"),
                    "Holiday": calendarific_holidays[0]['Holiday'],  # Take the first holiday
                    "Source": "Calendarific"
                })
                holiday_found = True

        # If no holidays found in any API
        if not holiday_found:
            results.append({
                "Date": date.strftime("%Y-%m-%d"),
                "Holiday": "No conflict, go ahead and schedule it",
                "Source": "None"
            })
def process_dates(dates_df):
    results = []
    for _, row in dates_df.iterrows():
        date = row['Date']
        
        # Initialize a flag to track if a holiday has been found
        holiday_found = False

        # Fetch from AzureML Public Holidays
        azure_holidays_df = get_public_holidays(date)
        if azure_holidays_df:
            results.append({
                "Date": date.strftime("%Y-%m-%d"),
                "Holiday": azure_holidays_df[0]['Holiday'],  # Take the first holiday
                "Source": "AzureML"
            })
            holiday_found = True

        # If no holiday found in AzureML, check Abstract API
        if not holiday_found:
            abstract_holidays = get_holidays_from_abstractapi(date)
            if abstract_holidays:
                results.append({
                    "Date": date.strftime("%Y-%m-%d"),
                    "Holiday": abstract_holidays[0]['Holiday'],  # Take the first holiday
                    "Source": "Abstract API"
                })
                holiday_found = True

        # If no holiday found in Abstract API, check Calendarific
        if not holiday_found:
            calendarific_holidays = get_holidays_from_calendarific(date)
            if calendarific_holidays:
                results.append({
                    "Date": date.strftime("%Y-%m-%d"),
                    "Holiday": calendarific_holidays[0]['Holiday'],  # Take the first holiday
                    "Source": "Calendarific"
                })
                holiday_found = True

        # If no holidays found in any API
        if not holiday_found:
            results.append({
                "Date": date.strftime("%Y-%m-%d"),
                "Holiday": "No conflict, go ahead and schedule it",
                "Source": "None"
            })

    holidays_df = pd.DataFrame(results)
    holidays_df = holidays_df.drop_duplicates(subset='Holiday', keep='first')  # Remove duplicate holidays
    holidays_df = holidays_df.reset_index(drop=True)  # Reset index
    return holidays_df


# Function to parse input dates and create a DataFrame
def create_dates_df(input_text):
    date_strs = input_text.split(',')
    dates = []
    errors = []
    for date_str in date_strs:
        date, error = validate_and_convert_date(date_str)
        if date:
            dates.append(date)
        else:
            errors.append(error)
    
    if errors:
        st.error("Errors found: " + ", ".join(errors))
    
    return pd.DataFrame({'Date': dates})

# Streamlit input and processing
# Streamlit input and processing
date_input = st.text_input("Enter dates (e.g., 2023-01-01, Jan 1 2023, 1st January 2023)")

# Initialize an empty DataFrame for holidays
holidays_df = pd.DataFrame()

if date_input:
    dates_df = create_dates_df(date_input)
    if not dates_df.empty:
        holidays_df = process_dates(dates_df)
        st.dataframe(holidays_df)

# Download button for Excel file
if not holidays_df.empty:
    towrite = io.BytesIO()
    holidays_df.to_excel(towrite, index=False, engine='openpyxl')  # Write to BytesIO buffer
    towrite.seek(0)  # Reset buffer's position to the beginning
    
    st.download_button(
        label="Download as Excel",
        data=towrite,
        file_name="holidays.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
