#!/usr/bin/python3

import csv
import os
import sys

# possible args - filenames: report-yesterday.csv report-today.csv


def count_colored_lines(list_of_lines, key_color):
    count = 0
    for item in list_of_lines:
        if key_color in item:
            count += 1
    return count


RowsToSkip = 6  # count from 0

# Define your file names:
#file1 = 'report-20230714.csv'
default_file1 = 'report-20240901.csv'
default_file2 = 'report-20241203.csv'
file1 = sys.argv[1] if len(sys.argv) > 1 else default_file1
file2 = sys.argv[2] if len(sys.argv) > 1 else default_file2

file1base = os.path.basename(file1)
file2base = os.path.basename(file2)


with open(file1, 'r') as f:
    lines_file1 = [line.strip() for line in f if "RUN_STATE_" in line]
    unique_lines_file1 = set(lines_file1)

with open(file2, 'r') as f:
    lines_file2 = [line.strip() for line in f if "RUN_STATE_" in line]
    unique_lines_file2 = set(lines_file2)


# Step 1: Parse the lines into CSV-like structures
csvlist1 = [line.split(',') for line in lines_file1[RowsToSkip:]]
csvlist2 = [line.split(',') for line in lines_file2[RowsToSkip:]]

# Step 2: Create key-value lists
kvlist1 = {row[0]: row[1:] for row in csvlist1}
kvlist2 = {row[0]: row[1:] for row in csvlist2}

# Step 3: Create sets of keys
set1 = set(kvlist1.keys())
set2 = set(kvlist2.keys())

# Step 4: Find created devices
created_keys = set2 - set1
created_devices = {key: kvlist2[key] for key in created_keys}

# Step 5: Find deleted devices
deleted_keys = set1 - set2
deleted_devices = {key: kvlist1[key] for key in deleted_keys}


common_lines = unique_lines_file1 & unique_lines_file2
unique_to_file1 = unique_lines_file1 - unique_lines_file2
unique_to_file2 = unique_lines_file2 - unique_lines_file1

len_unique_lines_file1 = len(unique_lines_file1)
len_unique_lines_file2 = len(unique_lines_file2)
delta_devices = len_unique_lines_file2 - len_unique_lines_file1
len_common_lines = len(common_lines)
len_unique_to_file1 = len(unique_to_file1)
len_unique_to_file2 = len(unique_to_file2)

#f1_green = count_colored_lines(lines_file1, "Green")
#f2_green = count_colored_lines(lines_file2, "Green")
#delta_green_devices = f2_green - f1_green

#print(file1, '-->', file2)
print(f"{file1base} --> {file2base}")
print(f"Total devices: {len_unique_lines_file1} --> {len_unique_lines_file2}, delta={delta_devices}")
for color in ['Green','Yellow','Orange','Red']:
  f1count = count_colored_lines(lines_file1, color)
  f2count = count_colored_lines(lines_file2, color)
  delta   = f2count - f1count
  print(f"Devices valuated as {color}: {f1count} --> {f2count}, delta={delta}")
print('Devices with the same status:', len_common_lines)
print('Devices with changed status: ', len_unique_to_file1)


# now detecting changes after Uniq_f1:

# Convert sets to lists
Uniq_f1_list = sorted(list(unique_to_file1))
f2_list = list(unique_lines_file2)

# Finding matching elements in f2_list and printing them
print('')
print(f"How devices' status changed between {file1base} and {file2base}:")
for element_f1 in Uniq_f1_list:
    nodename_f1 = str(element_f1).split(',')[0]
    runstate_f1 = str(element_f1).split(',')[1]
    for element_f2 in f2_list:
        nodename_f2 = str(element_f2).split(',')[0]
        runstate_f2 = str(element_f2).split(',')[1]
        appscount_f2 = str(element_f2).split(',')[2]
        ip_f2 = str(element_f2).split(',')[3]
        country_f2 = str(element_f2).split(',')[4]
        valuation_f2 = str(element_f2).split(',')[5]
        if nodename_f1 == nodename_f2:
            print(f"{element_f1} --> {runstate_f2},{appscount_f2},{ip_f2},{country_f2},{valuation_f2}")


print(f"\nCreated devices {file1base} --> {file2base} : {len(created_devices)}")
for key, value in created_devices.items():
    created_csv_line = ','.join([key] + value)
    print(created_csv_line)


print(f"\nDeleted devices {file1base} --> {file2base} : {len(deleted_devices)}")
for key, value in deleted_devices.items():
    deleted_csv_line = ','.join([key] + value)
    print(deleted_csv_line)

