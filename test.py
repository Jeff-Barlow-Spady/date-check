import streamlit as st
from dateutil import parser
import pandas as pd
from datetime import datetime
from st_aggrid import AgGrid, GridOptionsBuilder
from azureml.opendatasets import PublicHolidays, HolidayEnricher
H
PublicHolidays.get_enricher(self=self)
@st.cache_data
def get_events(date, country='CA'):
    # Load the PublicHolidays dataset
    ph = PublicHolidays()
    events_df = ph.to_pandas_dataframe()

    # Filter the dataset for the specified country and date
    filtered_df = events_df[(events_df['countryOrRegion'] == country) & (events_df['date'] == date.strftime('%Y-%m-%d'))]

    # If the filtered dataset is not empty, return the event name(s)
    if not filtered_df.empty:
        return filtered_df['eventName'].tolist()
    else:
        # If it's empty, return an empty list
        return []

# Function to validate and convert various date formats
def validate_and_convert_date(date_str):
    try:
        return parser.parse(date_str).strftime('%Y-%m-%d'), None
    except ValueError:
        return None, "Invalid date format."

uploaded_file = st.file_uploader("Upload your file (Excel or CSV)", type=['csv', 'xlsx'])
if uploaded_file:
    if uploaded_file.type == "text/csv":
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)
    #---------
    df['Date'] = df['Date'].apply(lambda x: validate_and_convert_date(x)[0])

    # Define events_df and country variables
    events_df = ph.get_tabular_dataset().to_pandas_dataframe()
    country = 'CA'

    # Filter the dataset for the specified country and date
    filtered_df = events_df[(events_df['countryOrRegion'] == country) & (events_df['date'].dt.date == date.date())]

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_pagination(paginationAutoPageSize=True)
    gb.configure_side_bar()
    gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, aggFunc='sum', editable=True)
    grid_options = gb.build()
    AgGrid(df, gridOptions=grid_options, enable_enterprise_modules=True)

    # Download button
    st.download_button(label='Download Results', data=df.to_csv(index=False), file_name='events_matched.csv', mime='text/csv')

date_input = st.text_input("Or enter a date (YYYY-MM-DD)")
if date_input:
    date, error = validate_and_convert_date(date_input)
    if error:
        st.error(error)
    else:
        events = get_events(datetime.strptime(date, '%Y-%m-%d'))
        st.write(f"Events on {date}: {events}")
