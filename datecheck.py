import streamlit as st
from dateutil import parser
import pandas as pd
import requests
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder


# Set page configuration
st.set_page_config(page_title="Holiday Scheduler", layout="wide")

# Title and Instructions
st.title("Holiday Scheduler")
st.markdown("Upload a file with dates to check for holiday conflicts, or enter dates manually.")

# Function definitions (get_holidays, validate_and_convert_date, create_holiday_df) go here...

# Sidebar for User Inputs
with st.sidebar:
    st.header("Upload File")
    uploaded_file = st.file_uploader("Choose a file (Excel or CSV)", type=['csv', 'xlsx'])

    st.header("Or Enter Date")
    date_input = st.text_input("Date (YYYY-MM-DD)")

# Function to call the Abstract API with caching
@st.cache_data
def get_holidays(date, country='CA'):
    API_KEY = st.secrets['API_KEY']
    url = f'https://holidays.abstractapi.com/v1/?api_key={API_KEY}&country={country}&year={date.year}&month={date.month}&day={date.day}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return []

# Function to validate and convert various date formats
def validate_and_convert_date(date_str):
    dates = date_str.split(',')
    converted_dates = []
    errors = []
    for date in dates:
        try:
            converted_dates.append(parser.parse(date.strip()).strftime('%Y-%m-%d'))
        except ValueError:
            errors.append(f"Invalid date format: {date.strip()}")
    return converted_dates, errors

# Function to create a DataFrame from holiday data
def create_holiday_df(holidays_data):
    holidays_list = []
    for holiday in holidays_data:
        holidays_list.append({'name': holiday.get('name', 'No Name'),
                              'location': holiday.get('location', 'No Location'),
                              'date': holiday.get('date', 'No Date')})
    return pd.DataFrame(holidays_list)

# Upload and process file
#uploaded_file = st.file_uploader("Upload your file (Excel or CSV)", type=['csv', 'xlsx'])
if uploaded_file:
    if uploaded_file.type == "text/csv":
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    df['Date'] = df['Date'].apply(lambda x: validate_and_convert_date(x)[0])
    df['Holidays'] = df['Date'].apply(lambda x: get_holidays(datetime.strptime(x, '%Y-%m-%d')))
    df = df.explode('Holidays')
    df = df.join(df['Holidays'].apply(lambda x: create_holiday_df(x)).reset_index(drop=True))
    df.drop(columns=['Holidays'], inplace=True)

    # AgGrid for displaying the dataframe
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_side_bar()
    gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum', editable=True)
    grid_options = gb.build()
    AgGrid(df, gridOptions=grid_options, enable_enterprise_modules=True)

    # Download button
    st.download_button(label='Download Results', data=df.to_csv(index=False), file_name='holidays_matched.csv', mime='text/csv')

# Manual date input
date_input = st.text_input("Or enter a date (YYYY-MM-DD)")

if date_input:
    dates, error = validate_and_convert_date(date_input)
    if error:
        st.error(error)
    else:
        holidays = []
        for date in dates:
            holiday_data = get_holidays(datetime.strptime(date, '%Y-%m-%d'))
            if holiday_data:
                holidays.extend(holiday_data)
            else:
                holidays.append({'name': 'No conflict, schedule away', 'location': '', 'date': date})

        holidays_df = create_holiday_df(holidays)
        AgGrid(holidays_df)
