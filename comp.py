import streamlit as st
from azureml.opendatasets import PublicHolidays
import pandas as pd
from dateutil import parser
from datetime import datetime
import calendarific
import requests
import io
import itertools

# Set page configuration
st.set_page_config(page_title="Date Checker", layout="wide")

st.title("Comprehensive Date Checker")
st.markdown("Enter dates (single or list) to check for holidays and events.")

# Abstract API
@st.cache_data
def get_holidays_from_abstractapi(dates_df, country=["US", "CA", "MX"]):
    API_KEY = st.secrets["ABSTRACT_KEY"]
    results = []
    for _, row in dates_df.iterrows():
        date = row['Date']
        url = f"https://holidays.abstractapi.com/v1/?api_key={API_KEY}&country={country}&year={date.year}&month={date.month}&day={date.day}"
        response = requests.get(url)
        holidays = response.json() if response.status_code == 200 else []
        results.extend([{'Date': date, 'Holiday': holiday.get("name", "Unnamed Holiday"), 'Source': 'Abstract API'} for holiday in holidays])
    return pd.DataFrame(results)

# Calendarific API
@st.cache_data
def get_holidays_from_calendarific(date, country=["CA"]):
    calapi = calendarific.v2(st.secrets["CAL_KEY"])
    results = []
    for _, row in dates_df.iterrows():
        date = row['Date']
        parameters = {'country': country, 'year': date.year}
        response = calapi.holidays(parameters)
        holidays = response['response']['holidays'] if 'holidays' in response['response'] else []
        results.extend([{'Date': date.strftime("%Y-%m-%d"), 'Holiday': holiday.get("name", "Unnamed Holiday"), 'Source': 'Calendarific', 'Country': country} for holiday in holidays if holiday['date']['iso'] == date.strftime("%Y-%m-%d")])
    return pd.DataFrame(results)

# AzureML Public Holidays
@st.cache_data
def get_public_holidays(date):
    results = []
    for _, row in dates_df.iterrows():
        date = row['Date']
        public_holidays = PublicHolidays(start_date=date, end_date=date)
        holidays_df = public_holidays.to_pandas_dataframe().reset_index(drop=True)
        results.extend([{'Date': date, 'Holiday': row['holidayName'], 'Source': 'AzureML'} for _, row in holidays_df.iterrows()])
        st.write(holidays_df.columns)
    return pd.DataFrame(results)

# Separate function to validate and convert a single date string
def validate_and_convert_date(date_str):
    try:
        return parser.parse(date_str.strip()), None
    except ValueError:
        return None, f"Invalid date format: {date_str.strip()}"

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

#def process_dates(dates):
def process_dates(dates_df):
    results = []
    for _, row in dates_df.iterrows():
        date = row['Date']
        # Fetch from AzureML Public Holidays
        azure_holidays_df = get_public_holidays(dates_df)
        
        # Check if the DataFrame is not empty and the column exists
        if not azure_holidays_df.empty and 'countryOrRegion' in azure_holidays_df.columns:
            filtered_holidays = azure_holidays_df[azure_holidays_df['countryOrRegion'] == 'US']
            for _, holiday_row in filtered_holidays.iterrows():
                results.append({
                    "Date": date.strftime("%Y-%m-%d"),
                    "Holiday": holiday_row['holidayName'],
                    "Source": "AzureML"
                })
            continue

        # Check Abstract API
        abstract_holidays = get_holidays_from_abstractapi(dates_df)
        if not abstract_holidays.empty:
            for _, holiday in abstract_holidays.iterrows():                results.append({
                    "Date": date.strftime("%Y-%m-%d"),
                    "Holiday": holiday.get("name", "Unnamed Holiday"),
                    "Source": "Abstract API"
                })
            continue

        # Check Calendarific
        calendarific_holidays = get_holidays_from_calendarific(dates_df)
        if calendarific_holidays:
            for holiday in calendarific_holidays:
                results.append({
                    "Date": date.strftime("%Y-%m-%d"),
                    "Holiday": holiday.get("name", "Unnamed Holiday"),
                    "Source": "Calendarific"
                })
            continue

        # No holidays found
        results.append({
            "Date": date.strftime("%Y-%m-%d"),
            "Holiday": "No conflict, go ahead and schedule it",
            "Source": "None"
        })

    return pd.DataFrame(results)

# Streamlit input and processing
date_input = st.text_input("Enter dates (e.g., 2023-01-01, Jan 1 2023, 1st January 2023)")
if date_input:
    dates_df = create_dates_df(date_input)
    if not dates_df.empty:
        holidays_df = process_dates(dates_df)
        st.dataframe(holidays_df)


# Download button for Excel file
if not holidays_df.empty:
    towrite = io.BytesIO()
    holidays_df.to_excel(towrite, index=False, engine='xlsxwriter')  # Write to BytesIO buffer
    towrite.seek(0)  # Reset buffer's position to the beginning
    
    st.download_button(
        label="Download as Excel",
        data=towrite,
        file_name="holidays.xlsx",
        mime="application/vnd.ms-excel"
    )
