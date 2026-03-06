#!/usr/bin/python3

import pandas as pd
import pycountry
import sys


def df_to_string(df):
    return '\n'.join(df.to_string(index=False).split('\n')).lstrip()

def get_country_name(country_code):
    try:
        return pycountry.countries.get(alpha_2=country_code).name
    except AttributeError:  # If country code not found in pycountry database
        return 'Unknown'



# Define your file names:
countryfile = 'countries42.csv'

default_reportfile = 'report-20231019.csv'
reportfile = sys.argv[1] if len(sys.argv) > 1 else default_reportfile



# This script first loads the csv files into dataframes, then finds the desired subsets of countries and prints them. 
# The ~ operator is used to negate the condition, isin() checks if the value is in the given list, and loc[] is used 
# to access a group of rows and columns by label(s) or a boolean array.


# Define the number of rows to skip
skip_rows = 7  # Set the number of rows you want to skip

# Load the csv files into pandas dataframes
report = pd.read_csv(reportfile, skiprows=skip_rows, header=None)
countries = pd.read_csv(countryfile, header=None)


# Rename the columns for easier referencing
#report.columns = ["Name", "Status", "AppsCount", "IP", "CountryCode", "Valuation"]
default_columns_names = ["Name", "Status", "AppsCount", "IP", "CountryCode", "Valuation"]
columnsnum=len(report.columns)
if columnsnum == 6:
  report.columns = default_columns_names
if columnsnum > 6:
  additional_columns=[]
  for columnindex in range(7, columnsnum+1):
    additional_columns = additional_columns + ["Column"+str(columnindex)]
  report.columns = default_columns_names+additional_columns

countries.columns = ["Country", "CountryCode"]


# All countries in report.csv
all_countries = report['CountryCode'].unique()

# subset of countries that are included in the report
countries_in_report     = countries.loc[countries['CountryCode'].isin(report['CountryCode'])]

# subset of countries that are not included in the report
countries_not_in_report = countries.loc[~countries['CountryCode'].isin(report['CountryCode'])]

#####

# subset of countries that are included in the report and with at least one Green valuation:
green_countries     = report[report['Valuation'] == 'Green']['CountryCode'].unique()

# subset of countries that are included in the report, but with zero Green valuations
non_green_countries = list(set(all_countries) - set(green_countries))

#####

# Find the subset of countries that are included in the report but have at least one devices with 'Green' valuation
green_countries_in_report         = countries[countries['CountryCode'].isin(green_countries)]

# Find the subset of countries that are included in the report but have zero devices with 'Green' valuation
countries_in_report_but_not_green = countries[countries['CountryCode'].isin(non_green_countries)]

#####

# Find the subset of countries that are included in the report and not included in the country42 list:
country_codes_in_report_not_in_countries = report.loc[~report['CountryCode'].isin(countries['CountryCode'])]['CountryCode'].drop_duplicates().dropna()



# Print the results

len_countries_in_report=len(countries_in_report)
print("\nUNECE countries with devices (regardless devices' state):",len_countries_in_report)
#print(countries_in_report.to_string(index=False, justify='left'))
for index, row in countries_in_report.iterrows():
    country_code = row['CountryCode']
    country_name = get_country_name(row['CountryCode'])
    country_count=len(report[report['CountryCode'] == country_code])
    print(f"{country_name} ({row['CountryCode']}): {country_count}")

len_countries_not_in_report=len(countries_not_in_report)
print("\nUNECE countries without devices:",len_countries_not_in_report)
print(countries_not_in_report.to_string(index=False, justify='left'))

#####

len_green_countries_in_report=len(green_countries_in_report)
print("\nUNECE countries with devices and having at least one device with 'Green' valuation:", len_green_countries_in_report)
#print(green_countries_in_report.to_string(index=False, justify='left'))
print("Countries and numbers of devices with 'Green' valuation (i.e. online, with 2 apps, not at factory):")
for index, row in green_countries_in_report.iterrows():
    country_code = row['CountryCode']
    country_name = get_country_name(row['CountryCode'])
    country_count=len(report[(report['CountryCode'] == country_code) & (report['Valuation'] == 'Green')])
    print(f"{country_name} ({row['CountryCode']}): {country_count}")

len_countries_in_report_but_not_green=len(countries_in_report_but_not_green)
print("\nUNECE countries with devices but having zero devices with 'Green' valuation:", len_countries_in_report_but_not_green)
print(countries_in_report_but_not_green.to_string(index=False, justify='left'))

#####

len_country_codes_in_report_not_in_countries=len(country_codes_in_report_not_in_countries)
print(f"\n Countries with devices, but not listed in the {countryfile} list:", len_country_codes_in_report_not_in_countries)
print("Countries and numbers of devices with 'Green' valuation (i.e. online, with 2 apps, not at factory):")
for code in sorted(country_codes_in_report_not_in_countries):
    country_count=len(report[(report['CountryCode'] == code) & (report['Valuation'] == 'Green')])
    print(f"{get_country_name(code)} ({code}): {country_count}")
