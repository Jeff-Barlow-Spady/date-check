import streamlit as st
from dateutil import parser
import pandas as pd
import requests
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder
#import holidays
import json
import json
import json
from st_aggrid import AgGrid, GridOptionsBuilder, DataReturnMode, GridUpdateMode, JsCode

# Function to call the Abstract API with caching
@st.cache_data
def get_holidays(date, country='CA'):   
    API_KEY = st.secrets['API_KEY']  
    url = f'https://holidays.abstractapi.com/v1/?api_key={API_KEY}&country={country}&year={date.year}&month={date.month}&day={date.day}'    
    response = requests.get(url)    
    if response.status_code == 200:        
        # Extract the holiday names from the JSON response
        return response.json()
    else:      
        return []
#holidays.OPTIONAL_COUNTRIES = ['CA']
#@st.cache_data
#def get_holidays(date, country='CA'):
    # Create a holidays object for the specified country and year
   # country_holidays = holidays.CountryHoliday(country, years=date.year)

    # Check if the specified date is a holiday
   # if date in country_holidays:
        # If it is, return the holiday name
     #   return country_holidays.get(date)
    #else:
        # If it's not, return an empty list
    #    return []
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


# ...

uploaded_file = st.file_uploader("Upload your file (Excel or CSV)", type=['csv', 'xlsx'])
if uploaded_file:
    if uploaded_file.type == "text/csv":
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    #---------
    df['Date'] = df['Date'].apply(lambda x: validate_and_convert_date(x)[0])
    df['Holidays'] = df['Date'].apply(lambda x: get_holidays(datetime.strptime(x, '%Y-%m-%d')))
    if not df.empty:
        # AgGrid for displaying the dataframe
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_side_bar()
        gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum', editable=True)
        grid_options = gb.build()
        AgGrid(df, gridOptions=grid_options, enable_enterprise_modules=True)
    else:
        st.error("The DataFrame is empty. Please check your file's content.")
    # Download button    
    st.download_button(label='Download Results', data=df.to_csv(index=False), file_name='holidays_matched.csv', mime='text/csv')

date_input = st.text_input("Or enter a date (YYYY-MM-DD)")

if date_input:
    dates, error = validate_and_convert_date(date_input)
    if error:
        st.error(error)
    else:
        holidays = []
        for date in dates:
            holiday = get_holidays(datetime.strptime(date, '%Y-%m-%d'))
            holidays.append(holiday)
        
        # Convert holidays list to DataFrame
        holidays_df = pd.DataFrame(holidays)
    # Ensure the DataFrame is not empty before displaying
    if not holidays_df.empty:
        # Use AgGrid to display the holidays DataFrame
        gb = GridOptionsBuilder.from_dataframe(holidays_df)
        gb.configure_pagination(paginationAutoPageSize=True)
        gb.configure_side_bar()
        gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum', editable=True)
        grid_options = gb.build()
        AgGrid(holidays_df, gridOptions=grid_options, enable_enterprise_modules=True)
    else:
        st.error("No holidays found for the entered date.")
        # Display holidays DataFrame
        #st.dataframe(holidays_df)

        # Display JSON data in a table
        #json_data = {"country":"CA","date":"03/17/2023","date_day":"17","date_month":"03","date_year":"2023","description":"","language":"","location":"Canada","name":"St. Patrick's Day","name_local":"","type":"Observance","week_day":"Friday"}
        #json_df = pd.DataFrame.from_dict(json_data, orient='index', columns=['Value'])
        #st.dataframe(json_df)
