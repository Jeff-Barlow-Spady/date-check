import streamlit as st
from dateutil import parser
import pandas as pd
import requests
from datetime import datetime
from st_aggrid import AgGrid
import openpyxl

# Set page configuration
st.set_page_config(page_title="Scheduling Conflict Check", layout="wide")

# Title and Instructions
st.title("Date Conflict Checker")
st.markdown("Upload a file with dates to check for holiday conflicts, or enter dates manually.")
st.divider()

#@st.cache_data
def get_holidays(date, country="CA"):
    API_KEY = st.secrets["API_KEY"]
    url = f"https://holidays.abstractapi.com/v1/?api_key={API_KEY}&country={country}&year={date.year}&month={date.month}&day={date.day}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return []

def validate_and_convert_date(date_item):
    if pd.isna(date_item):
        return "", "Invalid date (NaN found)"
    try:
        parsed_date = parser.parse(str(date_item).strip())
        converted_date = parsed_date.strftime("%Y-%m-%d")
        return converted_date, None
    except ValueError as e:
        return "", f"Invalid date format: {date_item.strip()}"


def process_dates(dates):
    holidays_data = []
    for date in dates:
        if date:  # Ensure date is not None
            converted_date = date[0]  # Extract the converted date from the tuple
            holidays = get_holidays(datetime.strptime(converted_date, "%Y-%m-%d"))
            for holiday in holidays:
                holidays_data.append({
                    "Date": converted_date,
                    "Holiday": holiday.get("name", "No Name"),
                    "Location": holiday.get("location", "No Location"),
                })
        else:
            holidays_data.append({"Date": date, "Holiday": "No conflict, schedule away", "Location": ""})
    return pd.DataFrame(holidays_data)


# Upload and process file
uploaded_file = st.file_uploader("Upload your file (Excel or CSV)", type=["csv", "xlsx"])
if uploaded_file:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith(".xlsx"):
            df = pd.read_excel(uploaded_file)
        
        if "Date" not in df.columns:
            st.error("No 'Date' column found in the file.")

        df["Converted Dates"], df["Errors"] = zip(*df["Date"].apply(validate_and_convert_date))
        df = df.dropna(subset=["Converted Dates"])

        holidays_df = process_dates(df["Converted Dates"].tolist())
        AgGrid(holidays_df)

        st.download_button(
            label="Download Results",
            data=holidays_df.to_csv(index=False),
            file_name="events_matched.csv",
            mime="text/csv",
        )
    except Exception as e:
        st.error(f"An error occurred: {e}")

date_input = st.text_input("Or enter a date (YYYY-MM-DD)")
if date_input:
    converted_date = validate_and_convert_date(date_input)
    if converted_date is None:
        st.error("Invalid date format.")
    else:
        holidays_df = process_dates([converted_date])
        AgGrid(holidays_df)

