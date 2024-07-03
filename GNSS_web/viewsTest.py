from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse
from datetime import datetime
import pandas as pd
import json
from django.http import JsonResponse
from django import forms
import random
import csv
import re
import subprocess
import base64
from django.http import HttpResponse
from django.views.decorators.http import require_GET
import os
import numpy as np
import codecs
import functools
import binascii
import io
from django.http import FileResponse
from django.conf import settings


#from io import StringIO



data = {
    '0'
}


def ping(request):
    if request.method == 'POST':
        ip_address = json.loads(request.body)['text']
        #baasPassword = "#MdWiJu2023!"
        password = "Embe1mpls"
        baasPassword="#MdWiJu2023!"
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip_address):
            try:
                subprocess.check_call(['ping', '-c', '1', ip_address], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                #password = input("Enter the router password: ") # Prompt user for password
                ip_command = f'scp root@{ip_address}:/var/log/gnss_receiver.log .'
                ip_process = subprocess.Popen(ip_command.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                stdout, stderr = ip_process.communicate(input=password.encode('utf-8'))
                if ip_process.returncode != 0:
                    return JsonResponse({'status': 'scperror', 'error_message': stderr.decode('utf-8')})
            except subprocess.CalledProcessError:
                return JsonResponse({'status': 'pingerror'})
                #ip_result = subprocess.run(ip_command.split(), input=password, text=True)
            #except subprocess.CalledProcessError:
             #   return JsonResponse({'status': 'pingerror'})
        else:
            baas_command = f'ssh bng-baas-shell.juniper.net'
            baas_result = subprocess.run(baas_command.split(), text=True, input=baasPassword)
            #ping_command = f'ping {ip_address}'
            #ping_result = subprocess.run(ping_command.split(), text=True)
            ssh_command = f'ssh-copy-id root@{ip_address}'
            baas_result = subprocess.run(ssh_command.split(), text=True)
            scp_command = f'scp -i ~/.ssh/id_rsa.pub root@{ip_address}:/var/log/gnss_receiver.log .'
            result = subprocess.run(scp_command.split(), text=True, capture_output=True)
        filename = 'gnss_receiver.log'
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                contents = f.read()
                encoded_data = base64.b64encode(contents).decode('utf-8')
            return JsonResponse({'encoded_data': encoded_data})
        else:
            JsonResponse({'status': 'fileNotfound'})


def home(request):
    if request.method == "POST":
        print("home")
    return render(request, 'GNSS_web/test.html')


def chart(request):
    if request.method == "POST":
        json_data = json.loads(request.body)
        #list2 = json_data['fileContent'].rstrip().split("\r\n\n")
        list2 = re.split(r'\r\n\n|\r\n|\n|\r|\r\n\n\n', json_data['fileContent'])
        list2 = [line.strip() for line in list2]
        list2 = [line for line in list2 if line]

        if len(list2) > settings.DATA_UPLOAD_MAX_MEMORY_SIZE:
            return JsonResponse({'data': 'File size limit'})

        dropdown1_value = json_data['dropdown1_value']
        dropdown2_value = json_data['dropdown2_value']
        dropdown3_value = json_data['dropdown3_value']
        dropdown4_value = json_data['dropdown4_value']
        advanced_text_1 = json_data['advanced_text_1']
        advanced_text_2 = json_data['advanced_text_2']

        if dropdown1_value == "TB-01":
            # Pandas data frame splitting with :

            df = pd.DataFrame.from_records([sub.split(" : ") for sub in list2], columns=['Date and Time', 'Description'])

            #for extracting the data between $ and *
            mask = df['Description'].str.contains(r'\$', regex=True) & df['Description'].str.contains(r'\*', regex=True)
            df = df[mask]
            data = df['Description'].str.extract('\$(.*?)\*')[0]
            df['data'] = data

            # for splitting all columns of main data
            main_columns = data.str.split(",", n=21, expand=True).fillna(0).replace('', 0)
            for i in range(0, 21):
                if main_columns[i].any():
                    df["column" + str(i)] = main_columns[i]
                else:
                    df["column" + str(i)] = 0;
            perdcry_receiver_antenna_list = []
            perdcry_receiver_spoofing_list = []
            perdcry_receiver_energization_list = []

            if dropdown2_value == "PERDCRW":
                #Make a new df for PERDCRW
                perdcrw_df = df.loc[df['column0'] == 'PERDCRW', :]
                if perdcrw_df.empty:
                    return JsonResponse({'data': None})

                # time
                string = perdcrw_df['column2'].astype(str)
                dt = string.apply(lambda x: datetime.strptime(x, '%Y%m%d%H%M%S'))
                total_seconds = dt.apply(lambda x: (x - datetime(1970, 1, 1)).total_seconds())
                perdcrw_time_list = total_seconds.astype(float).tolist()
                time_diff = dt.diff().fillna(pd.Timedelta(seconds=0)).apply(lambda x: x.total_seconds())
                perdcrw_time_diff_list = time_diff.astype(float).tolist()

                # temp
                string = perdcrw_df['column9'].astype(int)
                ver2 = (string / 100).astype(float)
                perdcrw_temp_list = ver2.tolist()

                #perdcrw status list
                perdcrw_status_list = ['Date and time:\nPresent date and time year, month, day, hour, minute, second. It is output at RTC, GPS, UTC time according to positioning status, synchronization setting status, parameter acquisition status and so on. 60 seconds is displayed only when the leap is inserted\nRange: 14 bytes\nExample: 20120303062722 is formatted as 2012/03/03 06:27:22.', 'Time Difference', 'Time Status:\nPresent time status of output sentence\n0: Before time fix\n1: Leap second unknown or leap second ignored\n2: Leap second fix\nRange: 0 to 2(1 byte)', 'PPS Status:\nPresent PPS is synced with the follow.\n0: RTC\n1: GPS\n2: UTC (USNO)\n3: UTC (SU)\n4: UTC (EU)\n5: UTC (NICT)\n Range: 0 to 5(1 byte)', 'Drift:\nClock drift [ppb]\nRange: 10 bytes', 'Temperature:\nThe ambient temperature is displayed as 100 times the value of [°C]\nRange: 5 bytes']


                if dropdown4_value != "":
                    perdcrw_df.loc[:, 'time difference'] = perdcrw_time_diff_list
                    perdcrw_df.loc[:, 'column2'] = perdcrw_time_list
                    perdcrw_df.loc[:, 'column9'] = perdcrw_temp_list

                    if dropdown4_value == "Time status":
                        perdcrw_new_df = perdcrw_df.loc[(perdcrw_df['column3'].astype(float) >= float(advanced_text_1)) & (perdcrw_df['column3'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "Time difference":
                        perdcrw_new_df = perdcrw_df.loc[(perdcrw_df['time difference'].astype(float) >= float(advanced_text_1)) & (perdcrw_df['time difference'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "PPS status":
                        perdcrw_new_df = perdcrw_df.loc[(perdcrw_df['column7'].astype(float) >= float(advanced_text_1)) & (perdcrw_df['column7'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "Drift":
                        perdcrw_new_df = perdcrw_df.loc[(perdcrw_df['column8'].astype(float) >= float(advanced_text_1)) & (perdcrw_df['column8'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "Temperature":
                        perdcrw_new_df = perdcrw_df.loc[(perdcrw_df['column9'].astype(float) >= float(advanced_text_1)) & (perdcrw_df['column9'].astype(float) <= float(advanced_text_2)), :]
                    if perdcrw_new_df.empty:
                        return JsonResponse({'data': None})

                    #checksum
                    data = perdcrw_new_df['data'].values.astype('S')
                    extra_data_int = np.fromiter((int(x, 16) for x in perdcrw_new_df['Description'].str.split('*', expand=True)[1]),dtype=np.uint8)
                    checksum = np.fromiter((functools.reduce(lambda x, y: x ^ y, bytes(d)) for d in data), dtype=np.uint8)
                    checksum_list = np.where(checksum != extra_data_int)[0].tolist()

                    # range list
                    PERDCRW = list(range(len(perdcrw_new_df)))

                    # date and time
                    date_time_list1 = perdcrw_new_df['Date and Time'].tolist()

                    #time list
                    perdcrw_time_list = perdcrw_new_df['column2'].astype(float).tolist()

                    # time status
                    perdcrw_time_status_list = perdcrw_new_df['column3'].astype(float).tolist()

                    # pps status
                    perdcrw_pps_status_list = perdcrw_new_df['column7'].astype(float).tolist()

                    # clock drift
                    perdcrw_clock_list = perdcrw_new_df['column8'].astype(float).tolist()

                    #temperature
                    perdcrw_temp_list = perdcrw_new_df['column9'].astype(float).tolist()

                    #time difference
                    perdcrw_time_diff_list = perdcrw_new_df['time difference'].astype(float).tolist()

                    # Calculate the maximum value
                    max_val1 = np.max(perdcrw_time_list)
                    max_val2 = np.max(perdcrw_time_diff_list)
                    max_val3 = np.max(perdcrw_time_status_list)
                    max_val4 = np.max(perdcrw_pps_status_list)
                    max_val5 = np.max(perdcrw_clock_list)
                    max_val6 = np.max(perdcrw_temp_list)

                    # Calculate the minimum value
                    min_val1 = np.min(perdcrw_time_list)
                    min_val2 = np.min(perdcrw_time_diff_list)
                    min_val3 = np.min(perdcrw_time_status_list)
                    min_val4 = np.min(perdcrw_pps_status_list)
                    min_val5 = np.min(perdcrw_clock_list)
                    min_val6 = np.min(perdcrw_temp_list)

                    # Calculate the standard deviation
                    std_val1 = np.std(perdcrw_time_list)
                    std_val2 = np.std(perdcrw_time_diff_list)
                    std_val3 = np.std(perdcrw_time_status_list)
                    std_val4 = np.std(perdcrw_pps_status_list)
                    std_val5 = np.std(perdcrw_clock_list)
                    std_val6 = np.std(perdcrw_temp_list)

                    # Calculate the 75th percentile value
                    pct_75_val1 = np.percentile(perdcrw_time_list, 75)
                    pct_75_val2 = np.percentile(perdcrw_time_diff_list, 75)
                    pct_75_val3 = np.percentile(perdcrw_time_status_list, 75)
                    pct_75_val4 = np.percentile(perdcrw_pps_status_list, 75)
                    pct_75_val5 = np.percentile(perdcrw_clock_list, 75)
                    pct_75_val6 = np.percentile(perdcrw_temp_list, 75)

                    # Calculate the median value
                    median_val1 = np.median(perdcrw_time_list)
                    median_val2 = np.median(perdcrw_time_diff_list)
                    median_val3 = np.median(perdcrw_time_status_list)
                    median_val4 = np.median(perdcrw_pps_status_list)
                    median_val5 = np.median(perdcrw_clock_list)
                    median_val6 = np.median(perdcrw_temp_list)

                    # Calculate the variance
                    var_val1 = np.var(perdcrw_time_list)
                    var_val2 = np.var(perdcrw_time_diff_list)
                    var_val3 = np.var(perdcrw_time_status_list)
                    var_val4 = np.var(perdcrw_pps_status_list)
                    var_val5 = np.var(perdcrw_clock_list)
                    var_val6 = np.var(perdcrw_temp_list)

                else:
                    #checksum
                    data = perdcrw_df['data'].values.astype('S')
                    extra_data_int = np.fromiter((int(x, 16) for x in perdcrw_df['Description'].str.split('*', expand=True)[1]), dtype=np.uint8)
                    checksum = np.fromiter((functools.reduce(lambda x, y: x ^ y, bytes(d)) for d in data), dtype=np.uint8)
                    checksum_list = np.where(checksum != extra_data_int)[0].tolist()

                    #range list
                    PERDCRW = list(range(len(perdcrw_df)))

                    #date and time
                    date_time_list1 = perdcrw_df['Date and Time'].tolist()

                    #time status
                    perdcrw_time_status_list = perdcrw_df['column3'].astype(float).tolist()

                    # pps status
                    perdcrw_pps_status_list = perdcrw_df['column7'].astype(float).tolist()

                    # clock drift
                    perdcrw_clock_list = perdcrw_df['column8'].astype(float).tolist()

                    # Calculate the maximum value
                    max_val1 = np.max(perdcrw_time_list)
                    max_val2 = np.max(perdcrw_time_diff_list)
                    max_val3 = np.max(perdcrw_time_status_list)
                    max_val4 = np.max(perdcrw_pps_status_list)
                    max_val5 = np.max(perdcrw_clock_list)
                    max_val6 = np.max(perdcrw_temp_list)

                    # Calculate the minimum value
                    min_val1 = np.min(perdcrw_time_list)
                    min_val2 = np.min(perdcrw_time_diff_list)
                    min_val3 = np.min(perdcrw_time_status_list)
                    min_val4 = np.min(perdcrw_pps_status_list)
                    min_val5 = np.min(perdcrw_clock_list)
                    min_val6 = np.min(perdcrw_temp_list)

                    # Calculate the standard deviation
                    std_val1 = np.std(perdcrw_time_list)
                    std_val2 = np.std(perdcrw_time_diff_list)
                    std_val3 = np.std(perdcrw_time_status_list)
                    std_val4 = np.std(perdcrw_pps_status_list)
                    std_val5 = np.std(perdcrw_clock_list)
                    std_val6 = np.std(perdcrw_temp_list)

                    # Calculate the 75th percentile value
                    pct_75_val1 = np.percentile(perdcrw_time_list, 75)
                    pct_75_val2 = np.percentile(perdcrw_time_diff_list, 75)
                    pct_75_val3 = np.percentile(perdcrw_time_status_list, 75)
                    pct_75_val4 = np.percentile(perdcrw_pps_status_list, 75)
                    pct_75_val5 = np.percentile(perdcrw_clock_list, 75)
                    pct_75_val6 = np.percentile(perdcrw_temp_list, 75)

                    # Calculate the median value
                    median_val1 = np.median(perdcrw_time_list)
                    median_val2 = np.median(perdcrw_time_diff_list)
                    median_val3 = np.median(perdcrw_time_status_list)
                    median_val4 = np.median(perdcrw_pps_status_list)
                    median_val5 = np.median(perdcrw_clock_list)
                    median_val6 = np.median(perdcrw_temp_list)

                    # Calculate the variance
                    var_val1 = np.var(perdcrw_time_list)
                    var_val2 = np.var(perdcrw_time_diff_list)
                    var_val3 = np.var(perdcrw_time_status_list)
                    var_val4 = np.var(perdcrw_pps_status_list)
                    var_val5 = np.var(perdcrw_clock_list)
                    var_val6 = np.var(perdcrw_temp_list)

                perdcrw_info_list =['Statistics about the chart:\nmax: ' + str(max_val1) + '\nmin: ' + str(min_val1) + '\nstandard deviation: ' + str(std_val1) + '\nmedian: ' + str(median_val1) + '\nVariance: ' + str(var_val1) + '\n75th percentile value: ' + str(pct_75_val1), 'Statistics about the chart:\nmax: ' + str(max_val2) + '\nmin: ' + str(min_val2) + '\nstandard deviation: ' + str(std_val2) + '\nmedian: ' + str(median_val2) + '\nVariance: ' + str(var_val2) + '\n75th percentile value: ' + str(pct_75_val2), 'Statistics about the chart:\nmax: ' + str(max_val3) + '\nmin: ' + str(min_val3) + '\nstandard deviation: ' + str(std_val3) + '\nmedian: ' + str(median_val3) + '\nVariance: ' + str(var_val3) + '\n75th percentile value: ' + str(pct_75_val3), 'Statistics about the chart:\nmax: ' + str(max_val4) + '\nmin: ' + str(min_val4) + '\nstandard deviation: ' + str(std_val4) + '\nmedian: ' + str(median_val4) + '\nVariance: ' + str(var_val4) + '\n75th percentile value: ' + str(pct_75_val4), 'Statistics about the chart:\nmax: ' + str(max_val6) + '\nmin: ' + str(min_val6) + '\nstandard deviation: ' + str(std_val6) + '\nmedian: ' + str(median_val6) + '\nVariance: ' + str(var_val6) + '\n75th percentile value: ' + str(pct_75_val6), 'Statistics about the chart:\nmax: ' + str(max_val5) + '\nmin: ' + str(min_val5) + '\nstandard deviation: ' + str(std_val5) + '\nmedian: ' + str(median_val5) + '\nVariance: ' + str(var_val5) + '\n75th percentile value: ' + str(pct_75_val5)]

                data = {
                    'PERDCRW': date_time_list1,
                    'checksum': checksum_list,
                    'perdcrw_status_list': perdcrw_status_list,
                    'perdcrw_info_list': perdcrw_info_list,
                    'PERDCRW Date & Time': perdcrw_time_list,
                    'PERDCRW Time difference': perdcrw_time_diff_list,
                    'PERDCRW Time status': perdcrw_time_status_list,
                    'PERDCRW PPS status': perdcrw_pps_status_list,
                    'PERDCRW Drift': perdcrw_clock_list,
                    'PERDCRW Temperature': perdcrw_temp_list,
                }

            elif dropdown2_value == "GPGSV":
                x=12;
                gpgsv_df = df.loc[df['column0'] == 'GPGSV', :]
                if gpgsv_df.empty:
                    return JsonResponse({'data': None})

                gpgsv_status_list = ['satellite strength']

                if dropdown4_value != "":
                    print("do nothing")
                else:
                    # checksum
                    data = gpgsv_df['data'].values.astype('S')
                    extra_data_int = np.fromiter(
                        (int(x, 16) for x in gpgsv_df['Description'].str.split('*', expand=True)[1]), dtype=np.uint8)
                    checksum = np.fromiter((functools.reduce(lambda x, y: x ^ y, bytes(d)) for d in data),
                                           dtype=np.uint8)
                    checksum_list = np.where(checksum != extra_data_int)[0].tolist()

                    # range list
                    #GPGSV = list(range(len(gpgsv_df)))

                    # date and time
                    #date_time_list25 = gpgsv_df['Date and Time'].tolist()

                    #take 4,8,12,16
                    # Define the columns to check and the corresponding value columns
                    columns_to_check = [4, 8, 12, 16]
                    value_columns = [7, 11, 15, 19]

                    # Initialize a list to store the extracted values
                    extracted_values = []
                    extracted_dates = []

                    # Iterate through the rows of the DataFrame
                    for index, row in gpgsv_df.iterrows():
                        # Initialize a variable to store the extracted value
                        value = None

                        # Iterate through the columns to check
                        for col_to_check, value_col in zip(columns_to_check, value_columns):
                            # Check if the current column contains the value 11
                            value_to_check = int(row[f'column{col_to_check}'])
                            if value_to_check == x:
                                # Extract the value from the corresponding value column
                                value = int(row[f'column{value_col}'])
                                date = row['Date and Time']
                                break  # Break the loop once a value is found

                        # Append the extracted value to the list
                        if value!= None:
                            extracted_values.append(value)
                            extracted_dates.append(date)
                    #GPGSV = list(range(len(extracted_values)))

                    max_val1 = np.max(extracted_values)
                    min_val1 = np.min(extracted_values)
                    std_val1 = np.std(extracted_values)
                    pct_75_val1 = np.percentile(extracted_values, 75)
                    median_val1 = np.median(extracted_values)
                    var_val1 = np.var(extracted_values)

                    gpgsv_info_list = ['Statistics about the chart:\nmax: ' + str(max_val1) + '\nmin: ' + str(min_val1) + '\nstandard deviation: ' + str(std_val1) + '\nmedian: ' + str(median_val1) + '\nVariance: ' + str(var_val1) + '\n75th percentile value: ' + str(pct_75_val1)]

                data = {
                        'GPGSV satellite ' + str(x): extracted_dates,
                    'checksum': checksum_list,
                    'gpgsv_status_list': gpgsv_status_list,
                    'gpgsv_info_list': gpgsv_info_list,
                    'Satellite strength of ' + str(x): extracted_values
                }


            elif dropdown2_value == "GNRMC":
                gnrmc_df = df.loc[df['column0'] == 'GNRMC', :]
                if gnrmc_df.empty:
                    return JsonResponse({'data': None})

                # latitude
                string = gnrmc_df['column3'].astype(str)
                ver1 = string.str[:2].astype(int)
                ver2 = string.str[2:4].astype(int)
                ver3 = string.str[5:].astype(int)
                ver4 = ((ver3 / 3600) + (ver2 / 60) + ver1).astype(float)
                gnrmc_lat_list = ver4.tolist()

                # longitude
                string = gnrmc_df['column5'].astype(str)
                ver1 = string.str[:3].astype(int)
                ver2 = string.str[3:5].astype(int)
                ver3 = string.str[6:].astype(int)
                ver4 = ((ver3 / 3600) + (ver2 / 60) + ver1).astype(float)
                gnrmc_lon_list = ver4.tolist()

                # gnrmc status
                gnrmc_status_list = ['Latitude:\ndd: [degree], mm.mmmm: [minute]\nRange: 0000.0000 to 9000.0000\nDefault: All 0\nExample: 3442.8266 means 34 deg 42.8266 min\ndegrees, minutes, seconds converted to decimal degrees and then plotted\nCalculations: 34 deg 42.8266 is converted to 34 + (42/60) + (8266/3600) = 36.99611 degrees', 'Longitude:\nddd: [degree], mm.mmmm: [minute]\nRange: 00000.0000 to 18000.0000\nDefault: All 0\nExample: 13520.1235 means 135 deg 20.1235 min\ndegrees, minutes, seconds converted to decimal degrees and then plotted\nCalculations: 135 deg 20.1235 min is converted to 135 + (20/60) + (1235/3600) = 135.6764 degrees']

                if dropdown4_value != "":
                    gnrmc_df.loc[:, 'column3'] = gnrmc_lat_list
                    gnrmc_df.loc[:, 'column5'] = gnrmc_lon_list
                    if dropdown4_value == "Latitude":
                        gnrmc_new_df = gnrmc_df.loc[(gnrmc_df['column3'].astype(float) >= float(advanced_text_1)) & (gnrmc_df['column3'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "Longitude":
                        gnrmc_new_df = gnrmc_df.loc[(gnrmc_df['column5'].astype(float) >= float(advanced_text_1)) & (gnrmc_df['column5'].astype(float) <= float(advanced_text_2)), :]
                    if gnrmc_new_df.empty:
                        return JsonResponse({'data': None})

                    #checksum
                    data = gnrmc_new_df['data'].values.astype('S')
                    extra_data_int = np.fromiter((int(x, 16) for x in gnrmc_new_df['Description'].str.split('*', expand=True)[1]),dtype=np.uint8)
                    checksum = np.fromiter((functools.reduce(lambda x, y: x ^ y, bytes(d)) for d in data),dtype=np.uint8)
                    checksum_list = np.where(checksum != extra_data_int)[0].tolist()

                    #checksum_list = np.where(checksum != extra_data_int, np.arange(len(gnrmc_new_df)), -1)
                    #print(checksum_list)
                    # range
                    GNRMC = list(range(len(gnrmc_new_df)))
                    # date and time
                    date_time_list2 = gnrmc_new_df['Date and Time'].tolist()
                    # latitude
                    gnrmc_lat_list = gnrmc_new_df['column3'].tolist()
                    # longitude
                    gnrmc_lon_list = gnrmc_new_df['column5'].tolist()

                    # Calculate the maximum value
                    max_val1 = np.max(gnrmc_lat_list)
                    max_val2 = np.max(gnrmc_lon_list)

                    # Calculate the minimum value
                    min_val1 = np.min(gnrmc_lat_list)
                    min_val2 = np.min(gnrmc_lon_list)

                    # Calculate the standard deviation
                    std_val1 = np.std(gnrmc_lat_list)
                    std_val2 = np.std(gnrmc_lon_list)

                    # Calculate the 75th percentile value
                    pct_75_val1 = np.percentile(gnrmc_lat_list, 75)
                    pct_75_val2 = np.percentile(gnrmc_lon_list, 75)

                    # Calculate the median value
                    median_val1 = np.median(gnrmc_lat_list)
                    median_val2 = np.median(gnrmc_lon_list)

                    # Calculate the variance
                    var_val1 = np.var(gnrmc_lat_list)
                    var_val2 = np.var(gnrmc_lon_list)

                else:
                    #checksum
                    data = gnrmc_df['data'].values.astype('S')
                    extra_data_int = np.fromiter((int(x, 16) for x in gnrmc_df['Description'].str.split('*', expand=True)[1]), dtype=np.uint8)
                    checksum = np.fromiter((functools.reduce(lambda x, y: x ^ y, bytes(d)) for d in data), dtype=np.uint8)
                    checksum_list = np.where(checksum != extra_data_int)[0].tolist()

                    # range list
                    GNRMC = list(range(len(gnrmc_df)))

                    # date and time
                    date_time_list2 = gnrmc_df['Date and Time'].tolist()

                    # Calculate the maximum value
                    max_val1 = np.max(gnrmc_lat_list)
                    max_val2 = np.max(gnrmc_lon_list)

                    # Calculate the minimum value
                    min_val1 = np.min(gnrmc_lat_list)
                    min_val2 = np.min(gnrmc_lon_list)

                    # Calculate the standard deviation
                    std_val1 = np.std(gnrmc_lat_list)
                    std_val2 = np.std(gnrmc_lon_list)

                    # Calculate the 75th percentile value
                    pct_75_val1 = np.percentile(gnrmc_lat_list, 75)
                    pct_75_val2 = np.percentile(gnrmc_lon_list, 75)

                    # Calculate the median value
                    median_val1 = np.median(gnrmc_lat_list)
                    median_val2 = np.median(gnrmc_lon_list)

                    # Calculate the variance
                    var_val1 = np.var(gnrmc_lat_list)
                    var_val2 = np.var(gnrmc_lon_list)

                gnrmc_info_list = ['Statistics about the chart:\nmax: ' + str(max_val1) + '\nmin: ' + str(min_val1) + '\nstandard deviation: ' + str(std_val1) + '\nmedian: ' + str(median_val1) + '\nVariance: ' + str(var_val1) + '\n75th percentile value: ' + str(pct_75_val1), 'Statistics about the chart:\nmax: ' + str(max_val2) + '\nmin: ' + str(min_val2) + '\nstandard deviation: ' + str(std_val2) + '\nmedian: ' + str(median_val2) + '\nVariance: ' + str(var_val2) + '\n75th percentile value: ' + str(pct_75_val2)]
                data = {
                    'GNMRC': date_time_list2,
                    'checksum': checksum_list,
                    'gnrmc_status_list': gnrmc_status_list,
                    'gnrmc_info_list': gnrmc_info_list,
                    'GNRMC Latitude': gnrmc_lat_list,
                    'GNRMC Longitude': gnrmc_lon_list,
                }

            elif dropdown2_value == "GNGNS":
                gngns_df = df.loc[df['column0'] == 'GNGNS', :]
                if gngns_df.empty:
                    return JsonResponse({'data': None})
                gngns_df.to_csv('final.csv')

                # latitude
                string = gngns_df['column2'].astype(str)
                ver1 = string.str[:2].astype(int)
                ver2 = string.str[2:4].astype(int)
                ver3 = string.str[5:].astype(int)
                ver4 = ((ver3 / 3600) + (ver2 / 60) + ver1).astype(float)
                gngns_lat_list = ver4.tolist()

                # longitude
                string = gngns_df['column4'].astype(str)
                ver1 = string.str[:3].astype(int)
                ver2 = string.str[3:5].astype(int)
                ver3 = string.str[6:].astype(int)
                ver4 = ((ver3 / 3600) + (ver2 / 60) + ver1).astype(float)
                gngns_lon_list = ver4.tolist()

                gngns_status_list = ['Latitude:\ndd: [degree], mm.mmmm: [minute]\nRange: 0000.0000 to 9000.0000\nDefault: All 0\nExample: 3442.8266 means 34 deg 42.8266 min\ndegrees, minutes, seconds converted to decimal degrees and then plotted\nCalculations: 34 deg 42.8266 is converted to 34 + (42/60) + (8266/3600) = 36.99611 degrees','Longitude:\nddd: [degree], mm.mmmm: [minute]\nRange: 00000.0000 to 18000.0000\nDefault: All 0\nExample: 13520.1235 means 135 deg 20.1235 min\ndegrees, minutes, seconds converted to decimal degrees and then plotted\nCalculations: 135 deg 20.1235 min is converted to 135 + (20/60) + (1235/3600) = 135.6764 degrees','Sea Level Altitude [meter]:\nDefault: -18.0','Number of satellites in use:\nRange: 00 to 32\nDefault: 00','Horizontal dilution of precision (HDOP).\nA null field is output while positioning is interrupted.\nRange: 0.0 to 50.0 or NULL\nDefault: NULL','Geoidal Height [meter]:\nDefault: 18.0']

                if dropdown4_value != "":
                    gngns_df.loc[:, 'column2'] = gngns_lat_list
                    gngns_df.loc[:, 'column4'] = gngns_lon_list
                    if dropdown4_value == "Number of satellites":
                        number_sat_df = gngns_df.loc[(gngns_df['column7'].astype(float) >= float(advanced_text_1)) & (gngns_df['column7'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "Latitude":
                        number_sat_df = gngns_df.loc[(gngns_df['column2'].astype(float) >= float(advanced_text_1)) & (gngns_df['column2'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "Longitude":
                        number_sat_df = gngns_df.loc[(gngns_df['column4'].astype(float) >= float(advanced_text_1)) & (gngns_df['column4'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "Sea level altitude":
                        number_sat_df = gngns_df.loc[(gngns_df['column9'].astype(float) >= float(advanced_text_1)) & (gngns_df['column9'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "HDOP":
                        number_sat_df = gngns_df.loc[(gngns_df['column8'].astype(float) >= float(advanced_text_1)) & (gngns_df['column8'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "Geoidal height":
                        number_sat_df = gngns_df.loc[(gngns_df['column10'].astype(float) >= float(advanced_text_1)) & (gngns_df['column10'].astype(float) <= float(advanced_text_2)), :]
                    if number_sat_df.empty:
                        return JsonResponse({'data': None})

                    # checksum
                    data = number_sat_df['data'].values.astype('S')
                    extra_data_int = np.fromiter((int(x, 16) for x in number_sat_df['Description'].str.split('*', expand=True)[1]),dtype=np.uint8)
                    checksum = np.fromiter((functools.reduce(lambda x, y: x ^ y, bytes(d)) for d in data), dtype=np.uint8)
                    checksum_list = np.where(checksum != extra_data_int)[0].tolist()

                    # range
                    GNGNS = list(range(len(number_sat_df)))
                    # date and time
                    date_time_list3 = number_sat_df['Date and Time'].tolist()
                    # latitude
                    gngns_lat_list = number_sat_df['column2'].tolist()
                    # longitude
                    gngns_lon_list = number_sat_df['column4'].tolist()
                    # Sea level altitude
                    gngns_sea_list = number_sat_df['column9'].astype(float).tolist()

                    # Number of sats
                    gngns_sat_list = number_sat_df['column7'].astype(float).tolist()

                    # geo
                    gngns_geo_list = number_sat_df['column10'].astype(float).tolist()

                    # hdop
                    gngns_hdop_list = number_sat_df['column8'].astype(float).tolist()

                    # Calculate the maximum value
                    max_val1 = np.max(gngns_lat_list)
                    max_val2 = np.max(gngns_lon_list)
                    max_val3 = np.max(gngns_sea_list)
                    max_val4 = np.max(gngns_sat_list)
                    max_val5 = np.max(gngns_geo_list)
                    max_val6 = np.max(gngns_hdop_list)

                    # Calculate the minimum value
                    min_val1 = np.min(gngns_lat_list)
                    min_val2 = np.min(gngns_lon_list)
                    min_val3 = np.min(gngns_sea_list)
                    min_val4 = np.min(gngns_sat_list)
                    min_val5 = np.min(gngns_geo_list)
                    min_val6 = np.min(gngns_hdop_list)


                    # Calculate the standard deviation
                    std_val1 = np.std(gngns_lat_list)
                    std_val2 = np.std(gngns_lon_list)
                    std_val3 = np.std(gngns_sea_list)
                    std_val4 = np.std(gngns_sat_list)
                    std_val5 = np.std(gngns_geo_list)
                    std_val6 = np.std(gngns_hdop_list)

                    # Calculate the 75th percentile value
                    pct_75_val1 = np.percentile(gngns_lat_list, 75)
                    pct_75_val2 = np.percentile(gngns_lon_list, 75)
                    pct_75_val3 = np.percentile(gngns_sea_list, 75)
                    pct_75_val4 = np.percentile(gngns_sat_list, 75)
                    pct_75_val5 = np.percentile(gngns_geo_list, 75)
                    pct_75_val6 = np.percentile(gngns_hdop_list, 75)


                    # Calculate the median value
                    median_val1 = np.median(gngns_lat_list)
                    median_val2 = np.median(gngns_lon_list)
                    median_val3 = np.median(gngns_sea_list)
                    median_val4 = np.median(gngns_sat_list)
                    median_val5 = np.median(gngns_geo_list)
                    median_val6 = np.median(gngns_hdop_list)


                    # Calculate the variance
                    var_val1 = np.var(gngns_lat_list)
                    var_val2 = np.var(gngns_lon_list)
                    var_val3 = np.var(gngns_sea_list)
                    var_val4 = np.var(gngns_sat_list)
                    var_val5 = np.var(gngns_geo_list)
                    var_val6 = np.var(gngns_hdop_list)


                else:
                    # checksum
                    data = gngns_df['data'].values.astype('S')
                    extra_data_int = np.fromiter((int(x, 16) for x in gngns_df['Description'].str.split('*', expand=True)[1]), dtype=np.uint8)
                    checksum = np.fromiter((functools.reduce(lambda x, y: x ^ y, bytes(d)) for d in data), dtype=np.uint8)
                    checksum_list = np.where(checksum != extra_data_int)[0].tolist()

                    # range list
                    GNGNS = list(range(len(gngns_df)))

                    # date and time
                    date_time_list3 = gngns_df['Date and Time'].tolist()

                    #gngns status

                    # Sea level altitude
                    gngns_sea_list = gngns_df['column9'].astype(float).tolist()

                    # Number of sats
                    gngns_sat_list = gngns_df['column7'].astype(float).tolist()

                    # geo
                    gngns_geo_list = gngns_df['column10'].astype(float).tolist()

                    # hdop
                    gngns_hdop_list = gngns_df['column8'].astype(float).tolist()

                    # Calculate the maximum value
                    max_val1 = np.max(gngns_lat_list)
                    max_val2 = np.max(gngns_lon_list)
                    max_val3 = np.max(gngns_sea_list)
                    max_val4 = np.max(gngns_sat_list)
                    max_val5 = np.max(gngns_geo_list)
                    max_val6 = np.max(gngns_hdop_list)

                    # Calculate the minimum value
                    min_val1 = np.min(gngns_lat_list)
                    min_val2 = np.min(gngns_lon_list)
                    min_val3 = np.min(gngns_sea_list)
                    min_val4 = np.min(gngns_sat_list)
                    min_val5 = np.min(gngns_geo_list)
                    min_val6 = np.min(gngns_hdop_list)

                    # Calculate the standard deviation
                    std_val1 = np.std(gngns_lat_list)
                    std_val2 = np.std(gngns_lon_list)
                    std_val3 = np.std(gngns_sea_list)
                    std_val4 = np.std(gngns_sat_list)
                    std_val5 = np.std(gngns_geo_list)
                    std_val6 = np.std(gngns_hdop_list)

                    # Calculate the 75th percentile value
                    pct_75_val1 = np.percentile(gngns_lat_list, 75)
                    pct_75_val2 = np.percentile(gngns_lon_list, 75)
                    pct_75_val3 = np.percentile(gngns_sea_list, 75)
                    pct_75_val4 = np.percentile(gngns_sat_list, 75)
                    pct_75_val5 = np.percentile(gngns_geo_list, 75)
                    pct_75_val6 = np.percentile(gngns_hdop_list, 75)

                    # Calculate the median value
                    median_val1 = np.median(gngns_lat_list)
                    median_val2 = np.median(gngns_lon_list)
                    median_val3 = np.median(gngns_sea_list)
                    median_val4 = np.median(gngns_sat_list)
                    median_val5 = np.median(gngns_geo_list)
                    median_val6 = np.median(gngns_hdop_list)

                    # Calculate the variance
                    var_val1 = np.var(gngns_lat_list)
                    var_val2 = np.var(gngns_lon_list)
                    var_val3 = np.var(gngns_sea_list)
                    var_val4 = np.var(gngns_sat_list)
                    var_val5 = np.var(gngns_geo_list)
                    var_val6 = np.var(gngns_hdop_list)

                if dropdown3_value == "scatter":
                    data = {
                        'GNGNS Latitude': gngns_lat_list,
                        'checksum': checksum_list,
                        'date_time_list3': date_time_list3,
                        'gngns_status_list': gngns_status_list,
                        'GNGNS Longitude': gngns_lon_list,
                    }
                else:
                    gngns_info_list = ['Statistics about the chart:\nmax: ' + str(max_val1) + '\nmin: ' + str(min_val1) + '\nstandard deviation: ' + str(std_val1) + '\nmedian: ' + str(median_val1) + '\nVariance: ' + str(var_val1) + '\n75th percentile value: ' + str(pct_75_val1), 'Statistics about the chart:\nmax: ' + str(max_val2) + '\nmin: ' + str(min_val2) + '\nstandard deviation: ' + str(std_val2) + '\nmedian: ' + str(median_val2) + '\nVariance: ' + str(var_val2) + '\n75th percentile value: ' + str(pct_75_val2), 'Statistics about the chart:\nmax: ' + str(max_val3) + '\nmin: ' + str(min_val3) + '\nstandard deviation: ' + str(std_val3) + '\nmedian: ' + str(median_val3) + '\nVariance: ' + str(var_val3) + '\n75th percentile value: ' + str(pct_75_val3), 'Statistics about the chart:\nmax: ' + str(max_val4) + '\nmin: ' + str(min_val4) + '\nstandard deviation: ' + str(std_val4) + '\nmedian: ' + str(median_val4) + '\nVariance: ' + str(var_val4) + '\n75th percentile value: ' + str(pct_75_val4), 'Statistics about the chart:\nmax: ' + str(max_val6) + '\nmin: ' + str(min_val6) + '\nstandard deviation: ' + str(std_val6) + '\nmedian: ' + str(median_val6) + '\nVariance: ' + str(var_val6) + '\n75th percentile value: ' + str(pct_75_val6), 'Statistics about the chart:\nmax: ' + str(max_val5) + '\nmin: ' + str(min_val5) + '\nstandard deviation: ' + str(std_val5) + '\nmedian: ' + str(median_val5) + '\nVariance: ' + str(var_val5) + '\n75th percentile value: ' + str(pct_75_val5)]
                    data = {
                        'GNGNS': date_time_list3,
                        'checksum': checksum_list,
                        'gngns_status_list': gngns_status_list,
                        'gngns_info_list': gngns_info_list,
                        'GNGNS Latitude': gngns_lat_list,
                        'GNGNS Longitude': gngns_lon_list,
                        'GNGNS Sea-level altitude': gngns_sea_list,
                        'GNGNS Number of satellites in use': gngns_sat_list,
                        'GNGNS HDOP': gngns_hdop_list,
                        'GNGNS Geoidal height': gngns_geo_list,
                    }

            elif dropdown2_value == "GNGSA":
                gngsa_df = df.loc[df['column0'] == 'GNGSA', :]
                if gngsa_df.empty:
                    return JsonResponse({'data': None})

                # gngsa status
                gngsa_status_list = ['PDOP:\nA null field is output unless 3D-positioning is performed.\nRange: 0.0 to 50.0 or NULL\nDefault: NULL', 'VDOP:\nA null field is output unless 3D-positioning is performed.\nRange: 0.0 to 50.0, or NULL\n Default: NULL']

                if dropdown4_value != "":
                    if dropdown4_value == "VDOP":
                        gngsa_new_df = gngsa_df.loc[(gngsa_df['column17'].astype(float) >= float(advanced_text_1)) & (gngsa_df['column17'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "PDOP":
                        gngsa_new_df = gngsa_df.loc[(gngsa_df['column15'].astype(float) >= float(advanced_text_1)) & (gngsa_df['column15'].astype(float) <= float(advanced_text_2)), :]
                    if gngsa_new_df.empty:
                        return JsonResponse({'data': None})

                    # checksum
                    data = gngsa_new_df['data'].values.astype('S')
                    extra_data_int = np.fromiter((int(x, 16) for x in gngsa_new_df['Description'].str.split('*', expand=True)[1]), dtype=np.uint8)
                    checksum = np.fromiter((functools.reduce(lambda x, y: x ^ y, bytes(d)) for d in data), dtype=np.uint8)
                    checksum_list = np.where(checksum != extra_data_int)[0].tolist()

                    # range list
                    GNGSA = list(range(len(gngsa_new_df)))

                    # date and time
                    date_time_list4 = gngsa_new_df['Date and Time'].tolist()

                    # pdop
                    gngsa_pdop_list = gngsa_new_df['column15'].astype(float).tolist()

                    # vdop
                    gngsa_vdop_list = gngsa_new_df['column17'].astype(float).tolist()

                    # Calculate the maximum value
                    max_val1 = np.max(gngsa_pdop_list)
                    max_val2 = np.max(gngsa_vdop_list)

                    # Calculate the minimum value
                    min_val1 = np.min(gngsa_pdop_list)
                    min_val2 = np.min(gngsa_vdop_list)

                    # Calculate the standard deviation
                    std_val1 = np.std(gngsa_pdop_list)
                    std_val2 = np.std(gngsa_vdop_list)

                    # Calculate the 75th percentile value
                    pct_75_val1 = np.percentile(gngsa_pdop_list, 75)
                    pct_75_val2 = np.percentile(gngsa_vdop_list, 75)

                    # Calculate the median value
                    median_val1 = np.median(gngsa_pdop_list)
                    median_val2 = np.median(gngsa_vdop_list)

                    # Calculate the variance
                    var_val1 = np.var(gngsa_pdop_list)
                    var_val2 = np.var(gngsa_vdop_list)

                else:
                    # checksum
                    data = gngsa_df['data'].values.astype('S')
                    extra_data_int = np.fromiter((int(x, 16) for x in gngsa_df['Description'].str.split('*', expand=True)[1]), dtype=np.uint8)
                    checksum = np.fromiter((functools.reduce(lambda x, y: x ^ y, bytes(d)) for d in data), dtype=np.uint8)
                    checksum_list = np.where(checksum != extra_data_int)[0].tolist()

                    # range list
                    GNGSA = list(range(len(gngsa_df)))

                    # date and time
                    date_time_list4 = gngsa_df['Date and Time'].tolist()

                    # pdop
                    gngsa_pdop_list = gngsa_df['column15'].astype(float).tolist()

                    # vdop
                    gngsa_vdop_list = gngsa_df['column17'].astype(float).tolist()

                    # Calculate the maximum value
                    max_val1 = np.max(gngsa_pdop_list)
                    max_val2 = np.max(gngsa_vdop_list)

                    # Calculate the minimum value
                    min_val1 = np.min(gngsa_pdop_list)
                    min_val2 = np.min(gngsa_vdop_list)

                    # Calculate the standard deviation
                    std_val1 = np.std(gngsa_pdop_list)
                    std_val2 = np.std(gngsa_vdop_list)

                    # Calculate the 75th percentile value
                    pct_75_val1 = np.percentile(gngsa_pdop_list, 75)
                    pct_75_val2 = np.percentile(gngsa_vdop_list, 75)

                    # Calculate the median value
                    median_val1 = np.median(gngsa_pdop_list)
                    median_val2 = np.median(gngsa_vdop_list)

                    # Calculate the variance
                    var_val1 = np.var(gngsa_pdop_list)
                    var_val2 = np.var(gngsa_vdop_list)

                gngsa_info_list =['Statistics about the chart:\nmax: ' + str(max_val1) + '\nmin: ' + str(min_val1) + '\nstandard deviation: ' + str(std_val1) + '\nmedian: ' + str(median_val1) + '\nVariance: ' + str(var_val1) + '\n75th percentile value: ' + str(pct_75_val1), 'Statistics about the chart:\nmax: ' + str(max_val2) + '\nmin: ' + str(min_val2) + '\nstandard deviation: ' + str(std_val2) + '\nmedian: ' + str(median_val2) + '\nVariance: ' + str(var_val2) + '\n75th percentile value: ' + str(pct_75_val2)]
                data = {
                    'GNGSA': date_time_list4,
                    'checksum': checksum_list,
                    'gngsa_status_list': gngsa_status_list,
                    'gngsa_info_list': gngsa_info_list,
                    'GNGSA PDOP': gngsa_pdop_list,
                    'GNGSA VDOP': gngsa_vdop_list,
                }

            elif dropdown2_value == "PERDCRX":
                perdcrx_df = df.loc[df['column0'] == 'PERDCRX', :]
                if perdcrx_df.empty:
                    return JsonResponse({'data': None})

                # perdcrx status
                perdcrx_status_list = ['PPS cable delay [nsec]\nRange: -100000 to +100000(7bytes)\nDefault: -57', 'Estimated accuracy:\nDisplays the estimation accuracy of the GNSS time being calculated.\nRange: 0000 to 9999(4 bytes)\nDefault: 9999']

                if dropdown4_value != "":
                    if dropdown4_value == "Cable delay":
                        perdcrx_new_df = perdcrx_df.loc[(perdcrx_df['column6'].astype(float) >= float(advanced_text_1)) & (perdcrx_df['column6'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "Estimated accuracy":
                        perdcrx_new_df = perdcrx_df.loc[(perdcrx_df['column9'].astype(float) >= float(advanced_text_1)) & (perdcrx_df['column9'].astype(float) <= float(advanced_text_2)), :]
                    if perdcrx_new_df.empty:
                        return JsonResponse({'data': None})

                    # checksum
                    data = perdcrx_new_df['data'].values.astype('S')
                    extra_data_int = np.fromiter((int(x, 16) for x in perdcrx_new_df['Description'].str.split('*', expand=True)[1]), dtype=np.uint8)
                    checksum = np.fromiter((functools.reduce(lambda x, y: x ^ y, bytes(d)) for d in data), dtype=np.uint8)
                    checksum_list = np.where(checksum != extra_data_int)[0].tolist()

                    # range list
                    PERDCRX = list(range(len(perdcrx_new_df)))

                    # date and time
                    date_time_list5 = perdcrx_new_df['Date and Time'].tolist()

                    # cable delay
                    perdcrx_cable_list = perdcrx_new_df['column6'].astype(float).tolist()
                
                    # estimated accuracy
                    perdcrx_accuracy_list = perdcrx_new_df['column9'].astype(float).tolist()

                    # Calculate the maximum value
                    max_val1 = np.max(perdcrx_cable_list.astype(float))
                    max_val2 = np.max(perdcrx_accuracy_list)

                    # Calculate the minimum value
                    min_val1 = np.min(perdcrx_cable_list)
                    min_val2 = np.min(perdcrx_accuracy_list)

                    # Calculate the standard deviation
                    std_val1 = np.std(perdcrx_cable_list)
                    std_val2 = np.std(perdcrx_accuracy_list)

                    # Calculate the 75th percentile value
                    pct_75_val1 = np.percentile(perdcrx_cable_list, 75)
                    pct_75_val2 = np.percentile(perdcrx_accuracy_list, 75)

                    # Calculate the median value
                    median_val1 = np.median(perdcrx_cable_list)
                    median_val2 = np.median(perdcrx_accuracy_list)

                    # Calculate the variance
                    var_val1 = np.var(perdcrx_cable_list)
                    var_val2 = np.var(perdcrx_accuracy_list)

                else:
                    # checksum
                    data = perdcrx_df['data'].values.astype('S')
                    extra_data_int = np.fromiter((int(x, 16) for x in perdcrx_df['Description'].str.split('*', expand=True)[1]), dtype=np.uint8)
                    checksum = np.fromiter((functools.reduce(lambda x, y: x ^ y, bytes(d)) for d in data), dtype=np.uint8)
                    checksum_list = np.where(checksum != extra_data_int)[0].tolist()

                    # range list
                    PERDCRX = list(range(len(perdcrx_df)))

                    # date and time
                    date_time_list5 = perdcrx_df['Date and Time'].tolist()

                    # cable delay
                    perdcrx_cable_list = perdcrx_df['column6'].astype(float).tolist()

                    # estimated accuracy
                    perdcrx_accuracy_list = perdcrx_df['column9'].astype(float).tolist()

                    # Calculate the maximum value
                    max_val1 = np.max(perdcrx_cable_list)
                    max_val2 = np.max(perdcrx_accuracy_list)

                    # Calculate the minimum value
                    min_val1 = np.min(perdcrx_cable_list)
                    min_val2 = np.min(perdcrx_accuracy_list)

                    # Calculate the standard deviation
                    std_val1 = np.std(perdcrx_cable_list)
                    std_val2 = np.std(perdcrx_accuracy_list)

                    # Calculate the 75th percentile value
                    pct_75_val1 = np.percentile(perdcrx_cable_list, 75)
                    pct_75_val2 = np.percentile(perdcrx_accuracy_list, 75)

                    # Calculate the median value
                    median_val1 = np.median(perdcrx_cable_list)
                    median_val2 = np.median(perdcrx_accuracy_list)

                    # Calculate the variance
                    var_val1 = np.var(perdcrx_cable_list)
                    var_val2 = np.var(perdcrx_accuracy_list)

                perdcrx_info_list=['Statistics about the chart:\nmax: ' + str(max_val1) + '\nmin: ' + str(min_val1) + '\nstandard deviation: ' + str(std_val1) + '\nmedian: ' + str(median_val1) + '\nVariance: ' + str(var_val1) + '\n75th percentile value: ' + str(pct_75_val1), 'Statistics about the chart:\nmax: ' + str(max_val2) + '\nmin: ' + str(min_val2) + '\nstandard deviation: ' + str(std_val2) + '\nmedian: ' + str(median_val2) + '\nVariance: ' + str(var_val2) + '\n75th percentile value: ' + str(pct_75_val2)]
                data = {
                    'PERDCRX': date_time_list5,
                    'checksum': checksum_list,
                    'perdcrx_status_list': perdcrx_status_list,
                    'perdcrx_info_list': perdcrx_info_list,
                    'PERDCRX Cable delay': perdcrx_cable_list,
                    'PERDCRX Estimated accuracy': perdcrx_accuracy_list,
                }


            elif dropdown2_value == "PERDCRY":
                perdcry_df = df.loc[df['column0'] == 'PERDCRY', :]
                if perdcry_df.empty:
                    return JsonResponse({'data': None})

                # perdcry status
                perdcry_status_list = ['Positioning mode:\n0: NAV mode\n1: SS mode\n2: Reserved\n3: TO mode\nRange: 0 to 3(1 byte)\nDefault: 1', 'Position Difference:\nDifference between the fixed position (or the estimated position) and the calculated position calculated by the positioning calculation in this second. [meter]\nRange: 0000 to 9999(4 bytes)\nDefault: 1000', 'Sigma threshold which changes automatically to TO mode. [meter]\nWhen the threshold value is 0, it is not used.\nRange: 000 to 255(3 bytes)\nDefault: 000', 'Time:\nCurrent update times of estimated position. This value increments by 1 during 3D positioning.\n Range: 000000 to 999999(6 bytes)\nDefault: 000000', 'Time threshold:\nSurvey time threshold which changes automatically to TO mode.\nWhen the threshold value is 0, it is not used.\nRange: 000000 to 604800(6 bytes)\nDefault: 000000', 'TRAIM solution:\n0: OK1: ALARM\n2: Insufficient satellites being tracked\nRange: 0 to 2(1 byte)\n Default: 2', 'TRAIM status:\n0: There are enough number of satellites in use\n1: There are a number of satellites for alarm determination\n2: Not enough satellites\nRange: 0 to 2(1 byte)\nDefault: 2', 'Number of satellites removed by TRAIM\nRange: 00 to 03(2 bytes)\nDefault: 00', 'Receiver status\n Range: 10 bytes\nDefault: 0x00000000\nAntenna Current detection\nBit: 00 to 03\n0: Normal\n1: Antenna short\n2: Antenna open\n3: No antenna voltage', 'Receiver status\n Range: 10 bytes\nDefault: 0x00000000\nSpoofing signal detection\nBit: 04 to 07\nNotify when a spoofing signal is detected.\n0: Spoofing signal is not detected.\n1: Spoofing signal is being detected.', 'Receiver status\n Range: 10 bytes\nDefault: 0x00000000\nEnergization time\nBit: 12 to 15\nTotal energization time since turning on the power supply of this product\n0: Less than 1 hour\n1: 1 hour elapsed\n2: 1 day elapsed 3: 7 days elapsed\n4: 30 days elapsed']

                # receiver status
                # Convert the entire list of hex strings to binary using list comprehension
                string = perdcry_df['column10'].tolist()
                binary_list = [bin(int(hex_num, 16))[2:].zfill(16) for hex_num in string]

                # Extract the relevant bits using slicing and convert to integers using int()
                perdcry_receiver_antenna_list = [int(binary_num[-4:], 2) for binary_num in binary_list]
                perdcry_receiver_spoofing_list = [int(binary_num[-8:-4], 2) for binary_num in binary_list]
                perdcry_receiver_energization_list = [int(binary_num[-13:-8], 2) for binary_num in binary_list]

                if dropdown4_value != "":
                    perdcry_df.loc[:, 'receiver antenna'] = perdcry_receiver_antenna_list
                    perdcry_df.loc[:, 'receiver spoofing'] = perdcry_receiver_spoofing_list
                    perdcry_df.loc[:, 'receiver energization'] = perdcry_receiver_energization_list
                    if dropdown4_value == "Position mode":
                        perdcry_new_df = perdcry_df.loc[(perdcry_df['column2'].astype(float) >= float(advanced_text_1)) & (perdcry_df['column2'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "Position difference":
                        perdcry_new_df = perdcry_df.loc[(perdcry_df['column3'].astype(float) >= float(advanced_text_1)) & (perdcry_df['column3'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "Sigma threshold":
                        perdcry_new_df = perdcry_df.loc[(perdcry_df['column4'].astype(float) >= float(advanced_text_1)) & (perdcry_df['column4'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "Time":
                        perdcry_new_df = perdcry_df.loc[(perdcry_df['column5'].astype(float) >= float(advanced_text_1)) & (perdcry_df['column5'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "Time threshold":
                        perdcry_new_df = perdcry_df.loc[(perdcry_df['column6'].astype(float) >= float(advanced_text_1)) & (perdcry_df['column6'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "TRAIM solution":
                        perdcry_new_df = perdcry_df.loc[(perdcry_df['column7'].astype(float) >= float(advanced_text_1)) & (perdcry_df['column7'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "TRAIM status":
                        perdcry_new_df = perdcry_df.loc[(perdcry_df['column8'].astype(float) >= float(advanced_text_1)) & (perdcry_df['column8'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "Removed Satellites":
                        perdcry_new_df = perdcry_df.loc[(perdcry_df['column9'].astype(float) >= float(advanced_text_1)) & (perdcry_df['column9'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "antenna current detection":
                        perdcry_new_df = perdcry_df.loc[(perdcry_df['receiver antenna'].astype(float) >= float(advanced_text_1)) & (perdcry_df['receiver antenna'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "spoofing signal detection":
                        perdcry_new_df = perdcry_df.loc[(perdcry_df['receiver spoofing'].astype(float) >= float(advanced_text_1)) & (perdcry_df['receiver spoofing'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "Energization time":
                        perdcry_new_df = perdcry_df.loc[(perdcry_df['receiver energization'].astype(float) >= float(advanced_text_1)) & (perdcry_df['receiver energization'].astype(float) <= float(advanced_text_2)), :]
                    if perdcry_new_df.empty:
                        return JsonResponse({'data': None})

                    # checksum
                    data = perdcry_new_df['data'].values.astype('S')
                    extra_data_int = np.fromiter((int(x, 16) for x in perdcry_new_df['Description'].str.split('*', expand=True)[1]), dtype=np.uint8)
                    checksum = np.fromiter((functools.reduce(lambda x, y: x ^ y, bytes(d)) for d in data), dtype=np.uint8)
                    checksum_list = np.where(checksum != extra_data_int)[0].tolist()

                    # range list
                    PERDCRY = list(range(len(perdcry_new_df)))

                    # date and time
                    date_time_list6 = perdcry_new_df['Date and Time'].tolist()
                    # pos mode
                    perdcry_pos_mode_list = perdcry_new_df['column2'].astype(float).tolist()
                    # pos diff
                    perdcry_pos_diff_list = perdcry_new_df['column3'].astype(float).tolist()
                    # sigma
                    perdcry_sigma_list = perdcry_new_df['column4'].astype(float).tolist()
                    # time
                    perdcry_time_list = perdcry_new_df['column5'].astype(float).tolist()
                    # threshold time
                    perdcry_time_threshold = perdcry_new_df['column6'].astype(float).tolist()
                    # traim solution
                    perdcry_traim_sol_list = perdcry_new_df['column7'].astype(float).tolist()
                    # traim status
                    perdcry_traim_status_list = perdcry_new_df['column8'].astype(float).tolist()
                    # removed svs
                    perdcry_removes_svs_list = perdcry_new_df['column9'].astype(float).tolist()
                    #receiver antenna
                    perdcry_receiver_antenna_list = perdcry_new_df['receiver antenna'].astype(float).tolist()
                    #receiver spoofing
                    perdcry_receiver_spoofing_list = perdcry_new_df['receiver spoofing'].astype(float).tolist()
                    #receiver energization
                    perdcry_receiver_energization_list = perdcry_new_df['receiver energization'].astype(float).tolist()

                    # Calculate the maximum value
                    max_val1 = np.max(perdcry_pos_mode_list)
                    max_val2 = np.max(perdcry_pos_diff_list)
                    max_val3 = np.max(perdcry_sigma_list)
                    max_val4 = np.max(perdcry_time_list)
                    max_val5 = np.max(perdcry_time_threshold)
                    max_val6 = np.max(perdcry_traim_sol_list)
                    max_val7 = np.max(perdcry_traim_status_list)
                    max_val8 = np.max(perdcry_removes_svs_list)
                    max_val9 = np.max(perdcry_receiver_antenna_list)
                    max_val10 = np.max(perdcry_receiver_spoofing_list)
                    max_val11 = np.max(perdcry_receiver_energization_list)

                    # Calculate the minimum value
                    min_val1 = np.min(perdcry_pos_mode_list)
                    min_val2 = np.min(perdcry_pos_diff_list)
                    min_val3 = np.min(perdcry_sigma_list)
                    min_val4 = np.min(perdcry_time_list)
                    min_val5 = np.min(perdcry_time_threshold)
                    min_val6 = np.min(perdcry_traim_sol_list)
                    min_val7 = np.min(perdcry_traim_status_list)
                    min_val8 = np.min(perdcry_removes_svs_list)
                    min_val9 = np.min(perdcry_receiver_antenna_list)
                    min_val10 = np.min(perdcry_receiver_spoofing_list)
                    min_val11 = np.min(perdcry_receiver_energization_list)

                    # Calculate the standard deviation
                    std_val1 = np.std(perdcry_pos_mode_list)
                    std_val2 = np.std(perdcry_pos_diff_list)
                    std_val3 = np.std(perdcry_sigma_list)
                    std_val4 = np.std(perdcry_time_list)
                    std_val5 = np.std(perdcry_time_threshold)
                    std_val6 = np.std(perdcry_traim_sol_list)
                    std_val7 = np.std(perdcry_traim_status_list)
                    std_val8 = np.std(perdcry_removes_svs_list)
                    std_val9 = np.std(perdcry_receiver_antenna_list)
                    std_val10 = np.std(perdcry_receiver_spoofing_list)
                    std_val11 = np.std(perdcry_receiver_energization_list)

                    # Calculate the 75th percentile value
                    pct_75_val1 = np.percentile(perdcry_pos_mode_list, 75)
                    pct_75_val2 = np.percentile(perdcry_pos_diff_list, 75)
                    pct_75_val3 = np.percentile(perdcry_sigma_list, 75)
                    pct_75_val4 = np.percentile(perdcry_time_list, 75)
                    pct_75_val5 = np.percentile(perdcry_time_threshold, 75)
                    pct_75_val6 = np.percentile(perdcry_traim_sol_list, 75)
                    pct_75_val7 = np.percentile(perdcry_traim_status_list, 75)
                    pct_75_val8 = np.percentile(perdcry_removes_svs_list, 75)
                    pct_75_val9 = np.percentile(perdcry_receiver_antenna_list, 75)
                    pct_75_val10 = np.percentile(perdcry_receiver_spoofing_list, 75)
                    pct_75_val11 = np.percentile(perdcry_receiver_energization_list, 75)

                    # Calculate the median value
                    median_val1 = np.median(perdcry_pos_mode_list)
                    median_val2 = np.median(perdcry_pos_diff_list)
                    median_val3 = np.median(perdcry_sigma_list)
                    median_val4 = np.median(perdcry_time_list)
                    median_val5 = np.median(perdcry_time_threshold)
                    median_val6 = np.median(perdcry_traim_sol_list)
                    median_val7 = np.median(perdcry_traim_status_list)
                    median_val8 = np.median(perdcry_removes_svs_list)
                    median_val9 = np.median(perdcry_receiver_antenna_list)
                    median_val10 = np.median(perdcry_receiver_spoofing_list)
                    median_val11 = np.median(perdcry_receiver_energization_list)

                    # Calculate the variance
                    var_val1 = np.var(perdcry_pos_mode_list)
                    var_val2 = np.var(perdcry_pos_diff_list)
                    var_val3 = np.var(perdcry_sigma_list)
                    var_val4 = np.var(perdcry_time_list)
                    var_val5 = np.var(perdcry_time_threshold)
                    var_val6 = np.var(perdcry_traim_sol_list)
                    var_val7 = np.var(perdcry_traim_status_list)
                    var_val8 = np.var(perdcry_removes_svs_list)
                    var_val9 = np.var(perdcry_receiver_antenna_list)
                    var_val10 = np.var(perdcry_receiver_spoofing_list)
                    var_val11 = np.var(perdcry_receiver_energization_list)


                else:
                    # checksum
                    data = perdcry_df['data'].values.astype('S')
                    extra_data_int = np.fromiter((int(x, 16) for x in perdcry_df['Description'].str.split('*', expand=True)[1]), dtype=np.uint8)
                    checksum = np.fromiter((functools.reduce(lambda x, y: x ^ y, bytes(d)) for d in data),dtype=np.uint8)
                    checksum_list = np.where(checksum != extra_data_int)[0].tolist()

                    # range list
                    PERDCRY = list(range(len(perdcry_df)))

                    # date and time
                    date_time_list6 = perdcry_df['Date and Time'].tolist()
                    # pos mode
                    perdcry_pos_mode_list = perdcry_df['column2'].astype(float).tolist()
                    # pos diff
                    perdcry_pos_diff_list = perdcry_df['column3'].astype(float).tolist()
                    # sigma
                    perdcry_sigma_list = perdcry_df['column4'].astype(float).tolist()
                    # time
                    perdcry_time_list = perdcry_df['column5'].astype(float).tolist()
                    # threshold time
                    perdcry_time_threshold = perdcry_df['column6'].astype(float).tolist()
                    # traim solution
                    perdcry_traim_sol_list = perdcry_df['column7'].astype(float).tolist()
                    # traim status
                    perdcry_traim_status_list = perdcry_df['column8'].astype(float).tolist()
                    # removed svs
                    perdcry_removes_svs_list = perdcry_df['column9'].astype(float).tolist()

                    # Calculate the maximum value
                    max_val1 = np.max(perdcry_pos_mode_list)
                    max_val2 = np.max(perdcry_pos_diff_list)
                    max_val3 = np.max(perdcry_sigma_list)
                    max_val4 = np.max(perdcry_time_list)
                    max_val5 = np.max(perdcry_time_threshold)
                    max_val6 = np.max(perdcry_traim_sol_list)
                    max_val7 = np.max(perdcry_traim_status_list)
                    max_val8 = np.max(perdcry_removes_svs_list)
                    max_val9 = np.max(perdcry_receiver_antenna_list)
                    max_val10 = np.max(perdcry_receiver_spoofing_list)
                    max_val11 = np.max(perdcry_receiver_energization_list)

                    # Calculate the minimum value
                    min_val1 = np.min(perdcry_pos_mode_list)
                    min_val2 = np.min(perdcry_pos_diff_list)
                    min_val3 = np.min(perdcry_sigma_list)
                    min_val4 = np.min(perdcry_time_list)
                    min_val5 = np.min(perdcry_time_threshold)
                    min_val6 = np.min(perdcry_traim_sol_list)
                    min_val7 = np.min(perdcry_traim_status_list)
                    min_val8 = np.min(perdcry_removes_svs_list)
                    min_val9 = np.min(perdcry_receiver_antenna_list)
                    min_val10 = np.min(perdcry_receiver_spoofing_list)
                    min_val11 = np.min(perdcry_receiver_energization_list)

                    # Calculate the standard deviation
                    std_val1 = np.std(perdcry_pos_mode_list)
                    std_val2 = np.std(perdcry_pos_diff_list)
                    std_val3 = np.std(perdcry_sigma_list)
                    std_val4 = np.std(perdcry_time_list)
                    std_val5 = np.std(perdcry_time_threshold)
                    std_val6 = np.std(perdcry_traim_sol_list)
                    std_val7 = np.std(perdcry_traim_status_list)
                    std_val8 = np.std(perdcry_removes_svs_list)
                    std_val9 = np.std(perdcry_receiver_antenna_list)
                    std_val10 = np.std(perdcry_receiver_spoofing_list)
                    std_val11 = np.std(perdcry_receiver_energization_list)

                    # Calculate the 75th percentile value
                    pct_75_val1 = np.percentile(perdcry_pos_mode_list, 75)
                    pct_75_val2 = np.percentile(perdcry_pos_diff_list, 75)
                    pct_75_val3 = np.percentile(perdcry_sigma_list, 75)
                    pct_75_val4 = np.percentile(perdcry_time_list, 75)
                    pct_75_val5 = np.percentile(perdcry_time_threshold, 75)
                    pct_75_val6 = np.percentile(perdcry_traim_sol_list, 75)
                    pct_75_val7 = np.percentile(perdcry_traim_status_list, 75)
                    pct_75_val8 = np.percentile(perdcry_removes_svs_list, 75)
                    pct_75_val9 = np.percentile(perdcry_receiver_antenna_list, 75)
                    pct_75_val10 = np.percentile(perdcry_receiver_spoofing_list, 75)
                    pct_75_val11 = np.percentile(perdcry_receiver_energization_list, 75)

                    # Calculate the median value
                    median_val1 = np.median(perdcry_pos_mode_list)
                    median_val2 = np.median(perdcry_pos_diff_list)
                    median_val3 = np.median(perdcry_sigma_list)
                    median_val4 = np.median(perdcry_time_list)
                    median_val5 = np.median(perdcry_time_threshold)
                    median_val6 = np.median(perdcry_traim_sol_list)
                    median_val7 = np.median(perdcry_traim_status_list)
                    median_val8 = np.median(perdcry_removes_svs_list)
                    median_val9 = np.median(perdcry_receiver_antenna_list)
                    median_val10 = np.median(perdcry_receiver_spoofing_list)
                    median_val11 = np.median(perdcry_receiver_energization_list)

                    # Calculate the variance
                    var_val1 = np.var(perdcry_pos_mode_list)
                    var_val2 = np.var(perdcry_pos_diff_list)
                    var_val3 = np.var(perdcry_sigma_list)
                    var_val4 = np.var(perdcry_time_list)
                    var_val5 = np.var(perdcry_time_threshold)
                    var_val6 = np.var(perdcry_traim_sol_list)
                    var_val7 = np.var(perdcry_traim_status_list)
                    var_val8 = np.var(perdcry_removes_svs_list)
                    var_val9 = np.var(perdcry_receiver_antenna_list)
                    var_val10 = np.var(perdcry_receiver_spoofing_list)
                    var_val11 = np.var(perdcry_receiver_energization_list)

                perdcry_info_list = ['Statistics about the chart:\nmax: ' + str(max_val1) + '\nmin: ' + str(min_val1) + '\nstandard deviation: ' + str(std_val1) + '\nmedian: ' + str(median_val1) + '\nVariance: ' + str(var_val1) + '\n75th percentile value: ' + str(pct_75_val1), 'Statistics about the chart:\nmax: ' + str(max_val2) + '\nmin: ' + str(min_val2) + '\nstandard deviation: ' + str(std_val2) + '\nmedian: ' + str(median_val2) + '\nVariance: ' + str(var_val2) + '\n75th percentile value: ' + str(pct_75_val2), 'Statistics about the chart:\nmax: ' + str(max_val3) + '\nmin: ' + str(min_val3) + '\nstandard deviation: ' + str(std_val3) + '\nmedian: ' + str(median_val3) + '\nVariance: ' + str(var_val3) + '\n75th percentile value: ' + str(pct_75_val3), 'Statistics about the chart:\nmax: ' + str(max_val4) + '\nmin: ' + str(min_val4) + '\nstandard deviation: ' + str(std_val4) + '\nmedian: ' + str(median_val4) + '\nVariance: ' + str(var_val4) + '\n75th percentile value: ' + str(pct_75_val4), 'Statistics about the chart:\nmax: ' + str(max_val5) + '\nmin: ' + str(min_val5) + '\nstandard deviation: ' + str(std_val5) + '\nmedian: ' + str(median_val5) + '\nVariance: ' + str(var_val5) + '\n75th percentile value: ' + str(pct_75_val5), 'Statistics about the chart:\nmax: ' + str(max_val6) + '\nmin: ' + str(min_val6) + '\nstandard deviation: ' + str(std_val6) + '\nmedian: ' + str(median_val6) + '\nVariance: ' + str(var_val6) + '\n75th percentile value: ' + str(pct_75_val6), 'Statistics about the chart:\nmax: ' + str(max_val7) + '\nmin: ' + str(min_val7) + '\nstandard deviation: ' + str(std_val7) + '\nmedian: ' + str(median_val7) + '\nVariance: ' + str(var_val7) + '\n75th percentile value: ' + str(pct_75_val7), 'Statistics about the chart:\nmax: ' + str(max_val8) + '\nmin: ' + str(min_val8) + '\nstandard deviation: ' + str(std_val8) + '\nmedian: ' + str(median_val8) + '\nVariance: ' + str(var_val8) + '\n75th percentile value: ' + str(pct_75_val8), 'Statistics about the chart:\nmax: ' + str(max_val9) + '\nmin: ' + str(min_val9) + '\nstandard deviation: ' + str(std_val9) + '\nmedian: ' + str(median_val9) + '\nVariance: ' + str(var_val9) + '\n75th percentile value: ' + str(pct_75_val9), 'Statistics about the chart:\nmax: ' + str(max_val10) + '\nmin: ' + str(min_val10) + '\nstandard deviation: ' + str(std_val10) + '\nmedian: ' + str(median_val10) + '\nVariance: ' + str(var_val10) + '\n75th percentile value: ' + str(pct_75_val10), 'Statistics about the chart:\nmax: ' + str(max_val11) + '\nmin: ' + str(min_val11) + '\nstandard deviation: ' + str(std_val11) + '\nmedian: ' + str(median_val11) + '\nVariance: ' + str(var_val11) + '\n75th percentile value: ' + str(pct_75_val11)]
                data = {
                    'PERDCRY': date_time_list6,
                    'checksum': checksum_list,
                    'perdcry_status_list': perdcry_status_list,
                    'perdcry_info_list': perdcry_info_list,
                    'PERDCRY Pos mode': perdcry_pos_mode_list,
                    'PERDCRY Pos diff': perdcry_pos_diff_list,
                    'PERDCRY Sigma threshold': perdcry_sigma_list,
                    'PERDCRY Time': perdcry_time_list,
                    'PERDCRY Time threshold': perdcry_time_threshold,
                    'PERDCRY TRAIM solution': perdcry_traim_sol_list,
                    'PERDCRY TRAIM status': perdcry_traim_status_list,
                    'PERDCRY Removed SVs': perdcry_removes_svs_list,
                    'PERDCRY Receiver antenna current detection': perdcry_receiver_antenna_list,
                    'PERDCRY Receiver spoofing signal detection': perdcry_receiver_spoofing_list,
                    'PERDCRY Receiver energization time': perdcry_receiver_energization_list,
                }

            elif dropdown2_value == "PERDACK":
                perdack_df = df.loc[df['column0'] == 'PERDACK', :]
                if perdack_df.empty:
                    return JsonResponse({'data': None})

                # perdack status
                perdack_status_list = ['The number of times successful for the reception.It is added 1 whenever it succeeds in command reception, and 0 to 255 is repeated. When command reception is failed, -1 is returned.\nThe positive number means ACK, and the negative number means NACK.\nRange: -1 to 255\nDefault:0']

                if dropdown4_value != "":
                    perdack_new_df = perdack_df.loc[(perdack_df['column2'].astype(float) >= float(advanced_text_1)) & (perdack_df['column2'].astype(float) <= float(advanced_text_2)), :]
                    if perdack_new_df.empty:
                        return JsonResponse({'data': None})

                    # checksum
                    data = perdack_new_df['data'].values.astype('S')
                    extra_data_int = np.fromiter((int(x, 16) for x in perdack_new_df['Description'].str.split('*', expand=True)[1]), dtype=np.uint8)
                    checksum = np.fromiter((functools.reduce(lambda x, y: x ^ y, bytes(d)) for d in data), dtype=np.uint8)
                    checksum_list = np.where(checksum != extra_data_int)[0].tolist()

                    # range list
                    PERDACK = list(range(len(perdack_new_df)))

                    # date and time
                    date_time_list7 = perdack_new_df['Date and Time'].tolist()

                    # sequence
                    perdack_seq_list = perdack_new_df['column2'].astype(float).tolist()

                    # Calculate the maximum value
                    max_val1 = np.max(perdack_seq_list)

                    # Calculate the minimum value
                    min_val1 = np.min(perdack_seq_list)

                    # Calculate the standard deviation
                    std_val1 = np.std(perdack_seq_list)

                    # Calculate the 75th percentile value
                    pct_75_val1 = np.percentile(perdack_seq_list, 75)

                    # Calculate the median value
                    median_val1 = np.median(perdack_seq_list)

                    # Calculate the variance
                    var_val1 = np.var(perdack_seq_list)

                else:
                    # checksum
                    data = perdack_df['data'].values.astype('S')
                    extra_data_int = np.fromiter((int(x, 16) for x in perdack_df['Description'].str.split('*', expand=True)[1]), dtype=np.uint8)
                    checksum = np.fromiter((functools.reduce(lambda x, y: x ^ y, bytes(d)) for d in data), dtype=np.uint8)
                    checksum_list = np.where(checksum != extra_data_int)[0].tolist()

                    # range list
                    PERDACK = list(range(len(perdack_df)))

                    # date and time
                    date_time_list7 = perdack_df['Date and Time'].tolist()

                    # sequence
                    perdack_seq_list = perdack_df['column2'].astype(float).tolist()

                    # Calculate the maximum value
                    max_val1 = np.max(perdack_seq_list)

                    # Calculate the minimum value
                    min_val1 = np.min(perdack_seq_list)

                    # Calculate the standard deviation
                    std_val1 = np.std(perdack_seq_list)

                    # Calculate the 75th percentile value
                    pct_75_val1 = np.percentile(perdack_seq_list, 75)

                    # Calculate the median value
                    median_val1 = np.median(perdack_seq_list)

                    # Calculate the variance
                    var_val1 = np.var(perdack_seq_list)

                perdack_info_list =['Statistics about the chart:\nmax: ' + str(max_val1) + '\nmin: ' + str(min_val1) + '\nstandard deviation: ' + str(std_val1) + '\nmedian: ' + str(median_val1) + '\nVariance: ' + str(var_val1) + '\n75th percentile value: ' + str(pct_75_val1)]
                data = {
                    'PERDACK': date_time_list7,
                    'checksum': checksum_list,
                    'perdack_status_list': perdack_status_list,
                    'perdack_info_list': perdack_info_list,
                    'PERDACK Sequence': perdack_seq_list,
                }

            elif dropdown2_value == "PERDCRZ":
                perdcrz_df = df.loc[df['column0'] == 'PERDCRZ', :]
                if perdcrz_df.empty:
                    return JsonResponse({'data': None})

                # perdcrz status
                perdcrz_status_list = ['Frequency mode\nRange:0 to 5(1 byte)\nDefault: 0\n0: Warm up\n1: Pull-in\n2: Coarse lock\n3: Fine lock\n4: Holdover\n5: Out of holdover', 'PPS timing error:\nTime difference between the timing of the synchronization target and the PPS generated by the oscillator [nsec]\nWhen the frequency mode is WARM UP, PULL IN, COARSE LOCK, FINE LOCK, the smaller this value, the more the 1PPS generated by the oscillator is synchronized with the synchronization target.Range: -999999999 to +999999999(10 bytes)\nDefault: 0', 'Alarm\nRange: 00 to FF(2 bytes)\nDefault: 00', 'Frequency error:\nVCLK frequency deviation [ppb]\nWhen the frequency mode is WARM UP, PULL IN, COARSE LOCK, FINE LOCK, the smaller this value, the closer the frequency output by the oscillator is to the nominal frequency.\nRange: -99999 to +99999(6 bytes)\nDefault: 0']

                # alarm
                perdcrz_alarm_list = perdcrz_df['column4'].values
                decimal_data = np.array([int(hex_value, 16) for hex_value in perdcrz_alarm_list], dtype=np.uint16)
                perdcrz_alarm_list = decimal_data.tolist()

                if dropdown4_value != "":
                    perdcrz_df.loc[:, 'column4'] = perdcrz_alarm_list

                    if dropdown4_value == "Frequency mode":
                        perdcrz_new_df = perdcrz_df.loc[(perdcrz_df['column2'].astype(float) >= float(advanced_text_1)) & (perdcrz_df['column2'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "PPS timing error":
                        perdcrz_new_df = perdcrz_df.loc[(perdcrz_df['column6'].astype(float) >= float(advanced_text_1)) & (perdcrz_df['column6'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "Alarm":
                        perdcrz_new_df = perdcrz_df.loc[(perdcrz_df['column4'].astype(float) >= float(advanced_text_1)) & (perdcrz_df['column4'].astype(float) <= float(advanced_text_2)), :]
                    elif dropdown4_value == "Frequency error":
                        perdcrz_new_df = perdcrz_df.loc[(perdcrz_df['column7'].astype(float) >= float(advanced_text_1)) & (perdcrz_df['column7'].astype(float) <= float(advanced_text_2)), :]
                    if perdcrz_new_df.empty:
                        return JsonResponse({'data': None})

                    # checksum
                    data = perdcrz_new_df['data'].values.astype('S')
                    extra_data_int = np.fromiter((int(x, 16) for x in perdcrz_new_df['Description'].str.split('*', expand=True)[1]), dtype=np.uint8)
                    checksum = np.fromiter((functools.reduce(lambda x, y: x ^ y, bytes(d)) for d in data),dtype=np.uint8)
                    checksum_list = np.where(checksum != extra_data_int)[0].tolist()

                    # range list
                    PERDCRZ = list(range(len(perdcrz_new_df)))

                    # date and time
                    date_time_list8 = perdcrz_new_df['Date and Time'].tolist()

                    # frequency
                    perdcrz_freq_list = perdcrz_new_df['column2'].astype(float).tolist()

                    # pps timing error
                    perdcrz_pps_list = perdcrz_new_df['column6'].astype(float).tolist()

                    # frequency error
                    perdcrz_freq_error_list = perdcrz_new_df['column7'].astype(float).tolist()

                    # Calculate the maximum value
                    max_val1 = np.max(perdcrz_freq_list)
                    max_val2 = np.max(perdcrz_pps_list)
                    max_val3 = np.max(perdcrz_freq_error_list)

                    # Calculate the minimum value
                    min_val1 = np.min(perdcrz_freq_list)
                    min_val2 = np.min(perdcrz_pps_list)
                    min_val3 = np.min(perdcrz_freq_error_list)

                    # Calculate the standard deviation
                    std_val1 = np.std(perdcrz_freq_list)
                    std_val2 = np.std(perdcrz_pps_list)
                    std_val3 = np.std(perdcrz_freq_error_list)

                    # Calculate the 75th percentile value
                    pct_75_val1 = np.percentile(perdcrz_freq_list, 75)
                    pct_75_val2 = np.percentile(perdcrz_pps_list, 75)
                    pct_75_val3 = np.percentile(perdcrz_freq_error_list, 75)

                    # Calculate the median value
                    median_val1 = np.median(perdcrz_freq_list)
                    median_val2 = np.median(perdcrz_pps_list)
                    median_val3 = np.median(perdcrz_freq_error_list)

                    # Calculate the variance
                    var_val1 = np.var(perdcrz_freq_list)
                    var_val2 = np.var(perdcrz_pps_list)
                    var_val3 = np.var(perdcrz_freq_error_list)

                else:
                    # checksum
                    data = perdcrz_df['data'].values.astype('S')
                    extra_data_int = np.fromiter((int(x, 16) for x in perdcrz_df['Description'].str.split('*', expand=True)[1]), dtype=np.uint8)
                    checksum = np.fromiter((functools.reduce(lambda x, y: x ^ y, bytes(d)) for d in data), dtype=np.uint8)
                    checksum_list = np.where(checksum != extra_data_int)[0].tolist()

                    # range list
                    PERDCRZ = list(range(len(perdcrz_df)))

                    # date and time
                    date_time_list8 = perdcrz_df['Date and Time'].tolist()

                    # frequency
                    perdcrz_freq_list = perdcrz_df['column2'].astype(float).tolist()

                    # pps timing error
                    perdcrz_pps_list = perdcrz_df['column6'].astype(float).tolist()

                    # frequency error
                    perdcrz_freq_error_list = perdcrz_df['column7'].astype(float).tolist()

                    # Calculate the maximum value
                    max_val1 = np.max(perdcrz_freq_list)
                    max_val2 = np.max(perdcrz_pps_list)
                    max_val3 = np.max(perdcrz_freq_error_list)

                    # Calculate the minimum value
                    min_val1 = np.min(perdcrz_freq_list)
                    min_val2 = np.min(perdcrz_pps_list)
                    min_val3 = np.min(perdcrz_freq_error_list)

                    # Calculate the standard deviation
                    std_val1 = np.std(perdcrz_freq_list)
                    std_val2 = np.std(perdcrz_pps_list)
                    std_val3 = np.std(perdcrz_freq_error_list)

                    # Calculate the 75th percentile value
                    pct_75_val1 = np.percentile(perdcrz_freq_list, 75)
                    pct_75_val2 = np.percentile(perdcrz_pps_list, 75)
                    pct_75_val3 = np.percentile(perdcrz_freq_error_list, 75)

                    # Calculate the median value
                    median_val1 = np.median(perdcrz_freq_list)
                    median_val2 = np.median(perdcrz_pps_list)
                    median_val3 = np.median(perdcrz_freq_error_list)

                    # Calculate the variance
                    var_val1 = np.var(perdcrz_freq_list)
                    var_val2 = np.var(perdcrz_pps_list)
                    var_val3 = np.var(perdcrz_freq_error_list)

                perdcry_info_list =['Statistics about the chart:\nmax: ' + str(max_val1) + '\nmin: ' + str(min_val1) + '\nstandard deviation: ' + str(std_val1) + '\nmedian: ' + str(median_val1) + '\nVariance: ' + str(var_val1) + '\n75th percentile value: ' + str(pct_75_val1), 'Statistics about the chart:\nmax: ' + str(max_val2) + '\nmin: ' + str(min_val2) + '\nstandard deviation: ' + str(std_val2) + '\nmedian: ' + str(median_val2) + '\nVariance: ' + str(var_val2) + '\n75th percentile value: ' + str(pct_75_val2), 'Statistics about the chart:\nmax: ' + str(max_val3) + '\nmin: ' + str(min_val3) + '\nstandard deviation: ' + str(std_val3) + '\nmedian: ' + str(median_val3) + '\nVariance: ' + str(var_val3) + '\n75th percentile value: ' + str(pct_75_val3)]

                data = {
                    'PERDCRZ': date_time_list8,
                    'checksum': checksum_list,
                    'perdcrz_status_list': perdcrz_status_list,
                    'perdcry_info_list': perdcry_info_list,
                    'PERDCRZ Frequency mode': perdcrz_freq_list,
                    'PERDCRZ PPS timing error': perdcrz_pps_list,
                    'PERDCRZ Alarm': perdcrz_alarm_list,
                    'PERDCRZ Freq error': perdcrz_freq_error_list,
                }

            '''elif dropdown2_value == "all":
                x_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                y1_data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
                y2_data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
                y3_data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
                y4_data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
                y5_data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
                date_data = ['June 2020', 'July 2024', 'July 2025', 'August 2022', 'July 2021', 'Test']
                all_status_list=['example status']
                all_info_list=[]
                checksum_list=[]
                data = {
                    'date_data': date_data,
                    'checksum': checksum_list,
                    'all_status_list': all_status_list,
                    'all_info_list': all_info_list,
                    'y1_data': y1_data,
                    'y2_data': y2_data,
                    'y3_data': y3_data,
                    'y4_data': y4_data,
                    'y5_data': y5_data,
                }'''

            return JsonResponse({'data': data})



def CSV(request):
    if request.method == "POST":
        #file_content = request.body.decode('utf-8')
        json_data = json.loads(request.body)
        list2 = json_data['fileContent'].rstrip().split("\r\n\n")

        dropdown1_value = json_data['dropdown1_value']

        if dropdown1_value == "TB-01":
            # Pandas data frame splitting with :
            df = pd.DataFrame.from_records([sub.split(" : ") for sub in list2], columns=['Date and Time', 'Description'])

            # for extracting the data between $ and *
            data = df['Description'].str.extract('\$(.*?)\*')[0]
            df['data'] = data

            # for splitting all columns of main data
            main_columns = data.str.split(",", n=21, expand=True).fillna(0).replace('', 0)
            for i in range(0, 21):
                df["column" + str(i)] = main_columns[i]

            # Create CSV file from dataframe
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, quoting=csv.QUOTE_NONNUMERIC)
            csv_buffer.seek(0)

            response = HttpResponse(csv_buffer, content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="GNSS-{dropdown1_value}.csv"'

            # Disable browser cache
            response['Cache-Control'] = 'no-cache'
            response['Expires'] = '0'
            response = FileResponse(df.to_csv(index=False), as_attachment=True, filename=f'GNSS-{dropdown1_value}.csv')

            return response

        return render(request, 'GNSS_web/test.html')

