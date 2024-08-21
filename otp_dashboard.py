import streamlit as st
import pandas as pd
import phonenumbers
from phonenumbers import geocoder
import numpy as np
import pycountry
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px

def _max_width_(prcnt_width:int = 75):
    max_width_str = f"max-width: {prcnt_width}%;"
    st.markdown(f""" 
                <style> 
                .reportview-container .main .block-container{{{max_width_str}}}
                </style>    
                """, 
                unsafe_allow_html=True,
    )



# Title of the dashboard
st.title("Twilio OTP Analysis Dashboard")
st.markdown("This dashboard provides an analysis of SMS delivery performance across different countries, error codes, and time periods. ")

# Load the static Excel file
data = pd.read_excel('Twillio 3 months (May - Aug).xlsx', header=1)
data = data[~data.To.isnull()]
pd.set_option('display.float_format', lambda x: '%.0f' % x)
data.To = data.To.astype(str).str.split('.').apply(lambda x: x[0])
data.To = '+' + data.To 

# A dictionary mapping country codes to country names using pycountry
country_code_map = {country.alpha_2: country.name for country in pycountry.countries}

def get_country_from_number(phone_number): 
    try: 
        parsed_number = phonenumbers.parse(phone_number, None)
        country_code = parsed_number.country_code
        
        # Convert country code to ISO alpha-2 code
        country = phonenumbers.region_code_for_country_code(country_code)
        
        # Map the alpha-2 code to the full country name
        country_name = country_code_map.get(country, np.nan)
        return country_name
    except:
        return np.nan

data['Country'] = data.To.apply(lambda x: get_country_from_number(x))

# Section 1: SMS Distribution by Country
st.header("1. SMS Distribution by Country")
st.markdown("Y-axis is the number of requests, while the number on top of each bar is unique phone numbers/users.")

# Select the number of top countries to display
N = st.slider("Select the number of top countries to display", min_value=10, max_value=50, value=15, step=5)

# Optional: Shorten long country names to avoid collision
data['Country'] = data['Country'].replace({
    'United Arab Emirates': 'UAE',
    'United Kingdom': 'UK',
})

# Count occurrences of each country
country_counts = data['Country'].value_counts().head(N)

# Calculate the number of unique users per country
unique_users = data.groupby('Country')['To'].nunique()

# Filter unique users to only include the top N countries
unique_users_filtered = unique_users.loc[country_counts.index]

# Plotting with Seaborn
plt.figure(figsize=(16, 9))
ax = sns.barplot(x=country_counts.index, y=country_counts.values, palette="coolwarm")

# Set title and labels
plt.title(f'Top {N} SMS Distribution by Country', fontsize=20, weight='bold', pad=20)
plt.xlabel('Country', fontsize=14, labelpad=15)
plt.ylabel('Number of SMS', fontsize=14, labelpad=15)
plt.xticks(rotation=60, ha='right', fontsize=12)

# Adding unique user counts above the bars
for i, value in enumerate(country_counts):
    plt.text(i, value + 50, f'{unique_users_filtered.iloc[i]}', ha='center', fontsize=12, color='black', weight='bold')

# Adding a subtle background grid
ax.yaxis.grid(True, color='gray', linestyle='--', alpha=0.7)
st.pyplot(plt)

# Create a DataFrame with unique user counts for the heatmap
unique_user_counts = unique_users.reset_index()
unique_user_counts.columns = ['Country', 'unique_count']

# Set unique_count to 21 for countries with fewer than 20 unique numbers, so they appear in a lower range of the color scale
unique_user_counts['highlighted_count'] = unique_user_counts['unique_count'].apply(lambda x: x if x >= 20 else 0)

# Create a custom color scale that emphasizes differences above and below 20
color_scale = [
    [0, "lightgrey"],   # for counts of 0 to 20
    [0.00001, "lightgrey"],
    [0.0001, "lightblue"],  # Gradual transition to emphasize lower counts
    [0.1, "yellow"],
    [0.3, "orange"],
    [0.6, "red"],
    [1, "darkred"]      # for counts significantly above 20
]

# Create a choropleth map using Plotly for the unique numbers distribution
fig = px.choropleth(
    unique_user_counts,
    locations='Country',
    locationmode='country names',
    color='highlighted_count',
    color_continuous_scale=color_scale,
    labels={'highlighted_count': 'Unique Numbers'},
    title='Unique Phone Numbers Distribution by Country (20+ Only)'
)

# Adjust the color scale for better representation of the data range
fig.update_layout(coloraxis_colorbar=dict(
    title="Unique Numbers",
    ticks="outside",
    dtick=50,  # Adjust tick spacing for a more readable scale
))

st.plotly_chart(fig)


# Section 2: OTP Success vs. Unsuccessful Requests
st.header("2. OTP Success vs. Unsuccessful Requests")

# Pie chart for OTP success vs. unsuccessful requests
status_mapping = {
    'delivered': 'successful',
    'sent': 'successful',
    'failed': 'unsuccessful',
    'undelivered': 'unsuccessful'
}
data['Mapped_Status'] = data['Status'].map(status_mapping)

status_counts = data['Mapped_Status'].value_counts()
plt.figure(figsize=(10, 10))
plt.pie(
    status_counts, 
    labels=status_counts.index, 
    autopct='%1.1f%%', 
    colors=sns.color_palette("RdYlGn", len(status_counts)),
    startangle=140, 
    wedgeprops={'edgecolor': 'black'}
)
plt.title('Distribution of OTP Success vs. Unsuccessful Requests', fontsize=18, fontweight='bold', pad=20)
st.pyplot(plt)

# Section 3: Distribution of SMS Error Codes
st.header("3. Distribution of SMS Error Codes")
st.markdown("This bar chart shows the distribution of different error codes encountered during SMS delivery.")

# Error codes distribution
error_code_mapping = {
    0: "Successful Delivery",
    21612: "Message cannot be sent with the current combination of 'To' and/or 'From' parameters",
    21408: "Permission to send an SMS or MMS has not been enabled for the region indicated by the 'To' number",
    30450: "Message delivery blocked",
    30008: "Unknown Error",
    21211: "Invalid To Phone Number",
    30005: "Unknown destination handset",
    30003: "Unreachable destination handset",
    21614: "To number is not a valid mobile number",
    30004: "Message blocked",
    30036: "Validity Period Expired",
    30007: "Message filtered",
    21635: "To number cannot be a landline"
}
data['Error_Description'] = data['ErrorCode'].map(error_code_mapping)

error_counts = data['Error_Description'].value_counts()
plt.figure(figsize=(14, 10))
ax = error_counts.plot(kind='barh', color=['#2ecc71' if desc == "Successful Delivery" else '#e74c3c' for desc in error_counts.index], edgecolor='black')
ax.bar_label(ax.containers[0], label_type='edge', padding=5, fontsize=12, weight='bold', color='black')
plt.title('Distribution of SMS Error Codes with Descriptions', fontsize=20, fontweight='bold', pad=20)
st.pyplot(plt)

# Section 4: Country-Specific Error Code Distribution
st.header("4. Country-Specific Error Code Distribution")
st.markdown("Select a country from the dropdown menu to see the distribution of error codes specific to that country.")

# Dropdown to select a country
country = st.selectbox("Select a country to view error code distribution", data['Country'].unique())

# Filter data for the selected country
country_data = data[data['Country'] == country]

# Calculate error counts and their percentages
country_error_counts = country_data['Error_Description'].value_counts()
country_error_percentages = (country_error_counts / country_error_counts.sum()) * 100

# Plotting
plt.figure(figsize=(14, 10))
ax = country_error_counts.plot(kind='barh', color='#FF8C00', edgecolor='black')

# Adding counts and percentages to the bars
for i, (count, percentage) in enumerate(zip(country_error_counts, country_error_percentages)):
    ax.text(count + 2, i, f'{count} ({percentage:.1f}%)', va='center', fontsize=12, color='black', weight='bold')

# Set title and labels
plt.title(f'Error Code Distribution for {country}', fontsize=22, fontweight='bold', pad=20)
plt.xlabel('Number of Occurrences', fontsize=16, labelpad=10)
plt.ylabel('Error Description', fontsize=16, labelpad=10)

# Display the plot in Streamlit
st.pyplot(plt)

# Section 5: Top N Countries by Number of SMS Messages
st.header("5. Success Ratio of our Top N Countries by Number of Messages")

# Allow the user to select the number of top countries to display
N = st.slider("Select the number of top countries to display by SMS Success Ratio", min_value=5, max_value=30, value=10, step=1)

# Calculate the total number of SMS messages per country
total_messages = data.groupby('Country').size()

# Get the top N countries by the total number of SMS messages
top_n_countries = total_messages.nlargest(N).index

# Calculate the success ratio for the top N countries
top_n_success_ratio = data.groupby(['Country', 'Mapped_Status']).size().unstack(fill_value=0).loc[top_n_countries]['successful'] / data.groupby(['Country', 'Mapped_Status']).size().unstack(fill_value=0).loc[top_n_countries].sum(axis=1)

# Plot the success ratio for the top N countries, sorted by total messages
plt.figure(figsize=(14, 10))
ax = top_n_success_ratio.plot(kind='barh', color='green', edgecolor='black')
ax.bar_label(ax.containers[0], fmt='%.2f', label_type='edge', fontsize=12, padding=3)

# Set the title and labels
plt.title(f'Top {N} Countries by SMS Success Ratio (Sorted by Number of Messages)', fontsize=20, fontweight='bold', pad=20)
plt.xlabel('Success Ratio', fontsize=16, labelpad=10)
plt.ylabel('Country', fontsize=16, labelpad=10)

# Display the plot in Streamlit
st.pyplot(plt)


# Section 6: SMS Volume by Day of the Week
st.header("6. SMS Volume by Day of the Week")
st.markdown("This bar chart shows the volume of SMS messages sent on each day of the week.")

# Extract day of the week from the 'SentDate' column
data['DayOfWeek'] = pd.to_datetime(data['SentDate']).dt.day_name()

day_of_week_counts = data['DayOfWeek'].value_counts().reindex(
    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])

# Plotting SMS volume by day of week
plt.figure(figsize=(10, 6))
day_of_week_counts.plot(kind='bar', color='blue')
plt.title('SMS Volume by Day of the Week', fontsize=16, fontweight='bold')
plt.xlabel('Day of the Week', fontsize=14)
plt.ylabel('Number of SMS', fontsize=14)
plt.xticks(rotation=45)

plt.tight_layout()
st.pyplot(plt)


# Section 7: SMS Success Rate by Month
st.header("7. SMS Success Rate by Month")
st.markdown("This line chart shows the SMS success rate for each month in the dataset.")

# Extract the month and year from the 'SentDate' column
data['MonthYear'] = pd.to_datetime(data['SentDate']).dt.to_period('M')

# Calculate the number of successful and unsuccessful SMS by month
monthly_success = data.groupby(['MonthYear', 'Mapped_Status']).size().unstack(fill_value=0)

# Calculate the success rate for each month
monthly_success_rate = monthly_success['successful'] / monthly_success.sum(axis=1)

# Plotting the success rate by month with a controlled figure size
fig, ax = plt.subplots(figsize=(10, 6))  # Use subplots to have better control

# Plot the success rate
ax.plot(monthly_success_rate.index.astype(str), monthly_success_rate, marker='o', color='green', linewidth=2)

# Adding percentage labels to each point
for i, (month, rate) in enumerate(monthly_success_rate.items()):
    ax.text(i, rate, f'{rate:.2%}', ha='center', va='bottom', fontsize=10, color='black', weight='bold')

# Set title and labels
ax.set_title('Monthly SMS Success Rate', fontsize=20, fontweight='bold', pad=20)
ax.set_xlabel('Month', fontsize=16, labelpad=10)
ax.set_ylabel('Success Rate', fontsize=16, labelpad=10)
ax.set_xticklabels(monthly_success_rate.index.astype(str), rotation=45)

# Ensure that the layout is tight to avoid clipping
plt.tight_layout()

# Display the plot in Streamlit
st.pyplot(fig)



# Section: SMS Message Length and Delivery Status Analysis
st.header("8. Message Length Distribution by Delivery Status")
st.markdown("This section analyzes the distribution of OTP message lengths and their success rates, focusing on the top 4 most common message lengths.")

# Calculate the length of each SMS message
data['Message_Length'] = data['Body'].apply(len)

# Count the occurrences of each message length for successful and unsuccessful deliveries
length_success = data[data['Mapped_Status'] == 'successful']['Message_Length'].value_counts()
length_unsuccess = data[data['Mapped_Status'] == 'unsuccessful']['Message_Length'].value_counts()

# Identify the top 4 most common message lengths
top_bins = (length_success + length_unsuccess).nlargest(4).index

# Filter the counts to include only these top 4 lengths
length_success_filtered = length_success[length_success.index.isin(top_bins)]
length_unsuccess_filtered = length_unsuccess[length_unsuccess.index.isin(top_bins)]

# Retrieve the corresponding message for each length
top_messages = data[data['Message_Length'].isin(top_bins)].groupby('Message_Length')['Body'].first()

# Convert message lengths to strings for categorical plotting
labels = top_bins.astype(str)

# Plotting
plt.figure(figsize=(12, 6))
bar_width = 0.4  # Width of the bars

# Plot bars with categorical x-axis
plt.bar(labels, length_success_filtered.values, width=bar_width, color='green', alpha=0.7, label='Successful')
plt.bar(labels, length_unsuccess_filtered.values, width=bar_width, color='red', alpha=0.7, label='Unsuccessful', bottom=length_success_filtered.values)

plt.title('Message Length Distribution by Delivery Status (Top 4 Bins)')
plt.xlabel('Message Length (characters)')
plt.ylabel('Frequency')
plt.legend(title='Status')

# Annotate the bars with the corresponding message text, staggered to avoid collision
for i, label in enumerate(labels):
    # Stagger the text position by alternating the height
    height_offset = max(length_success_filtered.values[i], length_unsuccess_filtered.values[i]) * 0.1
    plt.text(i, max(length_success_filtered.values[i], length_unsuccess_filtered.values[i]) + height_offset, 
             top_messages[top_bins[i]], ha='center', fontsize=8, wrap=True, rotation=30)

plt.grid(True)
st.pyplot(plt)
