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

from pipenv.patched.safety.alerts import alert

data = {
    '0'
}

def ring(request):
    if request.method == 'POST':
        ip_address = json.loads(request.body)['text']
        print(ip_address)
        baas_command = f'ssh bng-baas-shell.juniper.net'
        try:
            subprocess.run(baas_command.split(), check=True, text=True)
        except subprocess.CalledProcessError as e:
            return JsonResponse({'error': str(e)})

        ssh_command = f'ssh-copy-id root@{ip_address}'
        try:
            subprocess.run(ssh_command.split(), check=True, text=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            return JsonResponse({'error': str(e)})

        scp_command = f'scp root@{ip_address}:/var/log/gnss_receiver.log .'
        try:
            subprocess.run(scp_command.split(), check=True, text=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            return JsonResponse({'error': str(e)})

        filename = 'gnss_receiver.log'
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                contents = f.read()
                encoded_data = base64.b64encode(contents).decode('utf-8')
                return JsonResponse({'encoded_data': encoded_data})
        else:
            return JsonResponse({'error': f'File {filename} does not exist.'})

def ping(request):
    if request.method == 'POST':
        ip_address = json.loads(request.body)['text']
        #baasPassword = "#MdWiJu2023!"
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', ip_address):
            try:
                subprocess.check_call(['ping', '-c', '1', ip_address], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                ip_command = f'scp root@{ip_address}:/var/log/gnss_receiver.log .'
                ip_result = subprocess.run(ip_command.split(), text=True)
            except subprocess.CalledProcessError:
                return JsonResponse({'status': 'pingerror'})

        else:
            command = "ifconfig | grep utun3"
            result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                # VPN is connected
                baas_command = f'ssh bng-baas-shell.juniper.net'
                baas_result = subprocess.run(baas_command.split(), text=True)
                #ping_command = f'ping {ip_address}'
                #ping_result = subprocess.run(ping_command.split(), text=True)
                ssh_command = f'ssh-copy-id root@{ip_address}'
                baas_result = subprocess.run(ssh_command.split(), text=True, capture_output=True)
                scp_command = f'scp -i ~/.ssh/id_rsa.pub root@{ip_address}:/var/log/gnss_receiver.log .'
                result = subprocess.run(scp_command.split(), text=True, capture_output=True)
            else:
                # VPN is not connected
                print("VPN is not connected")
                return JsonResponse({'status': 'vpnerror'})


        filename = 'gnss_receiver.log'
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                contents = f.read()
                encoded_data = base64.b64encode(contents).decode('utf-8')
        return JsonResponse({'encoded_data': encoded_data})



def home(request):
    if request.method == "POST":
        print("home")
    return render(request, 'GNSS_web/test.html')

def chart(request):
    if request.method == "POST":
        #file_content = request.body.decode('utf-8')
        file_content = json.loads(request.body)['fileContent']
        list = file_content.split("\r\n\n")

        #list = file_content.decode()
        #print(list)
        list2 = []
        i = 0
        for i in range(1, len(list)):
            if list[i] == '':
                i = i + 1
                continue
            else:
                list2.append(list[i])

        dropdown1_value = json.loads(request.body)['dropdown1_value']
        dropdown2_value = json.loads(request.body)['dropdown2_value']
        if dropdown1_value == "TB-01":
            # Pandas data frame splitting with :
            df = pd.DataFrame([sub.split(" : ") for sub in list2])
            df.columns = ['Date and Time', 'Description']

            # print(df['Date and Time'])
            # Date and Time Split
            # print(str(df['Date and Time']))
            # Date_Time = pd.to_datetime(str(df['Date and Time']), format='%b %d %H:%M:%S')
            # print(DateTime_Split)

            # for splitting Received status and main data
            new = df["Description"].str.split(": ", n=1, expand=True)
            # print(new)
            df["status"] = new[0]

            # for splitting main data and \n
            slash = new[1].str.split("\r\n", n=1, expand=True)
            # df["Main Data"]=slash[0]

            # for splitting all columns of main data
            main_columns = slash[0].str.split(",", n=21, expand=True)
            for i in range(0, 21):
                df["column" + str(i)] = main_columns[i]

            #print(request.META.get('HTTP_REFERER'))


            # calculating checksum
            checksum_list =[]
            checksum=0
            for i in range(1, len(slash)):
                start_index = int(slash[0][i - 1].index("$")) + 1
                end_index = int(slash[0][i - 1].index("*"))
                # extract the 8-bit data between "$" and "*"
                xor_data = slash[0][i - 1][start_index:end_index]
                check_data = slash[0][i - 1][(end_index + 1):]

                # XOR the 8-bit data
                xor_result = 0
                for char in xor_data:
                    xor_result ^= ord(char)
                # convert the XOR result to 2 bytes of hexadecimal letters
                xor_hex = format(xor_result, '02X')
                if xor_hex != check_data:
                    checksum = checksum + 1
                    checksum_list.append(checksum)

            n = 0
            c = 0
            d = 0
            e = 0
            f = 0
            g = 0
            h = 0
            i = 0
            k = 0
            time_sepc = 0
            perdcrw_time_diff_list = []
            perdcrw_time_list = []
            perdcrw_time_status_list = []
            perdcrw_pps_status_list = []
            perdcrw_clock_list = []
            perdcrw_temp_list = []
            perdcrx_cable_list = []
            perdcrx_accuracy_list = []
            perdcry_pos_mode_list = []
            perdcry_pos_diff_list = []
            perdcry_sigma_list = []
            perdcry_time_list = []
            perdack_seq_list = []
            perdcry_time_threshold = []
            perdcry_traim_sol_list = []
            perdcry_traim_status_list = []
            perdcry_removes_svs_list = []
            perdcry_receiver_antenna_list = []
            perdcry_receiver_spoofing_list = []
            perdcry_receiver_energization_list = []
            perdcrz_freq_list = []
            perdcrz_alarm_list = []
            perdcrz_pps_list = []
            perdcrz_freq_error_list = []
            gnrmc_lat_list = []
            gnrmc_lon_list = []
            gngns_lat_list = []
            gngns_lon_list = []
            gngns_sea_list = []
            gngns_sat_list = []
            gngns_geo_list = []
            gngns_hdop_list = []
            gngsa_pdop_list = []
            gngsa_vdop_list = []
            PERDCRW = []
            GNRMC = []
            GNGNS= []
            GNGSA = []
            PERDCRX = []
            PERDCRY = []
            PERDCRZ = []
            PERDACK = []
            date_time_list1 = []
            date_time_list2 = []
            date_time_list3 = []
            date_time_list4 = []
            date_time_list5 = []
            date_time_list6 = []
            date_time_list7 = []
            date_time_list8 = []
            t=0
            for j in df['column0']:
                t=t+1
                print(t)
                if j == '$PERDCRW' and dropdown2_value == "PERDCRW":
                    PERDCRW.append(int(c))
                    date_time_list1.append(df['Date and Time'][n])
                    # time
                    string = str(df['column2'][n])
                    dt = datetime.strptime(string, '%Y%m%d%H%M%S')
                    ver4 = int((dt - datetime(1970, 1, 1)).total_seconds())
                    time_sepc = ver4 - time_sepc
                    perdcrw_time_list.append(ver4)
                    perdcrw_time_diff_list.append(time_sepc)

                    # time status
                    perdcrw_time_status_list.append(int(df['column3'][n]))
                    # pps status
                    perdcrw_pps_status_list.append(int(df['column7'][n]))
                    # clock drift
                    perdcrw_clock_list.append(float(df['column8'][n]))
                    # temp
                    string = str(df['column9'][n])
                    ver1 = int(string[1:3])
                    ver2 = (string[3:5])
                    ver3 = int(len(ver2))
                    ver4 = pow(10, ver3)
                    ver5 = float(ver1 + float(int(ver2) / ver4))
                    perdcrw_temp_list.append(ver5)
                    c = c + 1

                if j == '$GNRMC' and dropdown2_value == "GNRMC":
                    if df['column2'][n] == 'A':
                        GNRMC.append(int(d))
                        date_time_list2.append(df['Date and Time'][n])
                        # latitude
                        string = str(df['column3'][n])
                        # print(string)
                        ver1 = int(string[:2])
                        ver2 = int(string[2:4])
                        ver3 = int(string[5:])
                        ver4 = (ver3 / 3600) + (ver2 / 60) + ver1
                        gnrmc_lat_list.append(float(ver4))

                        # longitude
                        string = str(df['column5'][n])
                        ver1 = int(string[:3])
                        ver2 = int(string[3:5])
                        ver3 = int(string[6:])
                        ver4 = (ver3 / 3600) + (ver2 / 60) + ver1
                        gnrmc_lon_list.append(float(ver4))
                        d = d + 1

                if j == '$GNGNS' and dropdown2_value == "GNGNS":
                    GNGNS.append(int(e))
                    date_time_list3.append(df['Date and Time'][n])
                    # latitude
                    string = str(df['column2'][n])

                    ver1 = int(string[:2])
                    ver2 = int(string[2:4])
                    ver3 = int(string[5:])
                    ver4 = (ver3 / 3600) + (ver2 / 60) + ver1
                    # print(ver4)
                    gngns_lat_list.append(float(ver4))

                    # longitude
                    string = str(df['column4'][n])
                    # print(string)
                    ver1 = int(string[:3])
                    ver2 = int(string[3:5])
                    ver3 = int(string[6:])
                    ver4 = (ver3 / 3600) + (ver2 / 60) + ver1
                    # print(ver4)
                    gngns_lon_list.append(float(ver4))

                    # Sea level altitude
                    gngns_sea_list.append(float(df['column9'][n]))

                    # Number of sats
                    gngns_sat_list.append(int(df['column7'][n]))

                    # geo
                    gngns_geo_list.append(float(df['column10'][n]))

                    # hdop
                    gngns_hdop_list.append((df['column8'][n]))

                    e = e + 1

                if j == '$GNGSA' and dropdown2_value == "GNGSA":
                    GNGSA.append(int(f))
                    date_time_list4.append(df['Date and Time'][n])
                    # pdop
                    gngsa_pdop_list.append((df['column15'][n]))

                    # vdop
                    gngsa_vdop_list.append((df['column17'][n]))
                    f = f + 1

                if j == '$PERDCRX' and dropdown2_value == "PERDCRX":
                    PERDCRX.append(int(g))
                    date_time_list5.append(df['Date and Time'][n])
                    # cable delay
                    perdcrx_cable_list.append(int(df['column6'][n]))
                    # estimated accuracy
                    perdcrx_accuracy_list.append(int(df['column9'][n]))
                    g = g + 1

                if j == '$PERDCRY' and dropdown2_value == "PERDCRY":
                    PERDCRY.append(int(h))
                    date_time_list6.append(df['Date and Time'][n])
                    # pos mode
                    perdcry_pos_mode_list.append(int(df['column2'][n]))
                    # pos diff
                    perdcry_pos_diff_list.append(int(df['column3'][n]))
                    # sigma
                    perdcry_sigma_list.append(int(df['column4'][n]))
                    # time
                    perdcry_time_list.append(int(df['column5'][n]))
                    # threshold time
                    perdcry_time_threshold.append(int(df['column6'][n]))
                    # traim solution
                    perdcry_traim_sol_list.append(int(df['column7'][n]))
                    # traim status
                    perdcry_traim_status_list.append(int(df['column8'][n]))
                    # removed svs
                    perdcry_removes_svs_list.append(int(df['column9'][n]))
                    # receiver status
                    ver4 = int(df['column10'][n], 16)
                    mask_1 = bin(ver4)
                    per1 = str(mask_1)[::-1]
                    per2 = per1[0:4]
                    per3 = per2[::-1]
                    per4 = int(per3, 2)
                    perdcry_receiver_antenna_list.append(per4)
                    per5 = per1[4:8]
                    per6 = per5[::-1]
                    per7 = int(per6, 2)
                    perdcry_receiver_spoofing_list.append(per7)
                    per8 = per1[12:16]
                    per9 = per8[::-1]
                    per10 = int(per9, 2)
                    perdcry_receiver_energization_list.append(per10)

                    h = h + 1

                if j == '$PERDACK' and dropdown2_value == "PERDACK":
                    PERDACK.append(int(i))
                    date_time_list7.append(df['Date and Time'][n])
                    # sequence
                    perdack_seq_list.append(int(df['column2'][n]))
                    i = i + 1

                if j == "$PERDCRZ" and dropdown2_value == "PERDCRZ":
                    PERDCRZ.append(int(k))
                    date_time_list8.append(df['Date and Time'][n])
                    # frequency
                    perdcrz_freq_list.append(int(df['column2'][n]))
                    # alarm
                    res = int(df['column4'][n], 16)
                    print(res)
                    perdcrz_alarm_list.append(res)
                    # pps timing error
                    perdcrz_pps_list.append(int(df['column6'][n]))
                    # frequency error
                    perdcrz_freq_error_list.append(int(df['column7'][n]))
                    k = k + 1

                n = n + 1
            x_data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            y_data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
            date_data = ['June 2020', 'July 2024', 'July 2025', 'August 2022', 'July 2021', 'Test']

            if dropdown2_value == "GNGNS":
                data = {
                    'GNGNS': GNGNS,
                    'checksum': checksum_list,
                    'date_time_list3': date_time_list3,
                    'GNGNS Latitude': gngns_lat_list,
                    'GNGNS Longitude': gngns_lon_list,
                    'GNGNS Sea-level altitude': gngns_sea_list,
                    'GNGNS Number of satellites in use': gngns_sat_list,
                    'GNGNS HDOP': gngns_hdop_list,
                    'GNGNS Geoidal height': gngns_geo_list,
                }
                # return render(request, 'GNSS_web/index.html', {'data': data})

            if dropdown2_value == "PERDCRW":
                data = {
                    'PERDCRW': PERDCRW,
                    'checksum': checksum_list,
                    'date_time_list1': date_time_list1,
                    'PERDCRW Date & Time': perdcrw_time_list,
                    'PERDCRW Time difference': perdcrw_time_diff_list,
                    'PERDCRW Time status': perdcrw_time_status_list,
                    'PERDCRW PPS status': perdcrw_pps_status_list,
                    'PERDCRW Temperature': perdcrw_temp_list,
                    'PERDCRW Drift': perdcrw_clock_list,
                }
                # return render(request, 'GNSS_web/index.html', {'data': data})

            if dropdown2_value == "GNRMC":
                data = {
                    'GNRMC': GNRMC,
                    'checksum': checksum_list,
                    'date_time_list2': date_time_list2,
                    'GNRMC Latitude': gnrmc_lat_list,
                    'GNRMC Longitude': gnrmc_lon_list,
                }
                # return render(request, 'GNSS_web/index.html', {'data': data})

            if dropdown2_value == "GNGSA":
                data = {
                    'GNGSA': GNGSA,
                    'checksum': checksum_list,
                    'date_time_list4': date_time_list4,
                    'GNGSA VDOP': gngsa_vdop_list,
                    'GNGSA PDOP': gngsa_pdop_list,
                }
                # return render(request, 'GNSS_web/index.html', {'data': data})

            if dropdown2_value == "PERDCRX":
                data = {
                    'PERDCRX': PERDCRX,
                    'checksum': checksum_list,
                    'date_time_list5': date_time_list5,
                    'PERDCRX Cable delay': perdcrx_cable_list,
                    'PERDCRX Estimated accuracy': perdcrx_accuracy_list,
                }
                # return render(request, 'GNSS_web/index.html', {'data': data})

            if dropdown2_value == "PERDCRY":
                data = {
                    'PERDCRY': PERDCRY,
                    'checksum': checksum_list,
                    'date_time_list6': date_time_list6,
                    'PERDCRY Time': perdcry_time_list,
                    'PERDCRY Pos diff': perdcry_pos_diff_list,
                    'PERDCRY TRAIM status': perdcry_traim_status_list,
                    'PERDCRY Sigma threshold': perdcry_sigma_list,
                    'PERDCRY Receiver energization time': perdcry_receiver_energization_list,
                    'PERDCRY Receiver spoofing signal detection': perdcry_receiver_spoofing_list,
                    'PERDCRY Receiver antenna current detection': perdcry_receiver_antenna_list,
                    'PERDCRY Removed SVs': perdcry_removes_svs_list,
                    'PERDCRY Time threshold': perdcry_time_threshold,
                    'PERDCRY Pos mode': perdcry_pos_mode_list,
                    'PERDCRY TRAIM solution': perdcry_traim_sol_list,
                }
                # return render(request, 'GNSS_web/index.html', {'data': data})

            if dropdown2_value == "PERDACK":
                data = {
                    'PERDACK': PERDACK,
                    'checksum': checksum_list,
                    'date_time_list7': date_time_list7,
                    'PERDACK Sequence': perdack_seq_list,
                }
                # return render(request, 'GNSS_web/index.html', {'data': data})

            if dropdown2_value == "PERDCRZ":
                data = {
                    'PERDCRZ': PERDCRZ,
                    'checksum': checksum_list,
                    'date_time_list8': date_time_list8,
                    'PERDCRZ Frequency mode': perdcrz_freq_list,
                    'PERDCRZ PPS timing error': perdcrz_pps_list,
                    'PERDCRZ Alarm': perdcrz_alarm_list,
                    'PERDCRZ Freq error': perdcrz_freq_error_list,
                }
                # return render(request, 'GNSS_web/index.html', {'data': data})

            if dropdown2_value == "all":
                data = {
                    'x_data': x_data,
                    'checksum': checksum_list,
                    'date_data': date_data,
                    'y_data': y_data,
                }
            #json_data = json.dumps(data)
            return JsonResponse({'data': data})


def CSV(request):
    if request.method == "POST":
        print("CSV here")
        #file_content = request.body.decode('utf-8')
        file_content = json.loads(request.body)['fileContent']

        list = file_content.split("\r\n\n")

        #list = file_content.decode()
        #print(list)
        list2 = []
        i = 0
        for i in range(1, len(list)):
            if list[i] == '':
                i = i + 1
                continue
            else:
                list2.append(list[i])

        dropdown1_value = json.loads(request.body)['dropdown1_value']
        dropdown2_value = json.loads(request.body)['dropdown2_value']
        if dropdown1_value == "TB-01":
            # Pandas data frame splitting with :
            df = pd.DataFrame([sub.split(" : ") for sub in list2])
            df.columns = ['Date and Time', 'Description']

            # print(df['Date and Time'])
            # Date and Time Split
            # print(str(df['Date and Time']))
            # Date_Time = pd.to_datetime(str(df['Date and Time']), format='%b %d %H:%M:%S')
            # print(DateTime_Split)

            # for splitting Received status and main data
            new = df["Description"].str.split(": ", n=1, expand=True)
            # print(new)
            df["status"] = new[0]

            # for splitting main data and \n
            slash = new[1].str.split("\r\n", n=1, expand=True)
            # df["Main Data"]=slash[0]

            # for splitting all columns of main data
            main_columns = slash[0].str.split(",", n=21, expand=True)
            for i in range(0, 21):
                df["column" + str(i)] = main_columns[i]

            df.to_csv('GNSS-' + dropdown1_value + '.csv')
        return render(request, 'GNSS_web/test.html')

