'''
Task: Create unique password for 30000 devices.
Output will be stored in a csv file. Use cat or head command to view the content.
You can also use numbers app to open the csv file.
Install netmiko, pandas on your machine using pip/pip3/pipx
'''
import os 
import secrets
import string
from netmiko import ConnectHandler, NetmikoAuthenticationException, NetmikoTimeoutException
import pandas as pd
from concurrent import futures
import time

def create_pass():
    password = string.ascii_letters+string.digits+string.punctuation
    return ''.join(secrets.choice(password) for i in range(12))

def config_worker(dev_list):
    try:
        new_pass = create_pass()
        # Remove comments from line 22 to 31 if you want to test in your LAB. 
        # dev_info = { 
        #     'ip': dev_list,
        #     'username': os.getenv('DEV_USER'),
        #     'password': os.getenv('DEV_KEY'),
        #     'device_type': 'cisco_ios'  #replace with juniper_junos for juniper
        # }
        # session = ConnectHandler(**dev_info)
        # output = session.send_config_set(f'username nanda privilege 15 password {new_pass}')
        # print(output)
        cred.update({dev_list:new_pass})

    except NetmikoTimeoutException:
        print('Maybe device is unreachable', dev_list)
    except NetmikoAuthenticationException:
        print('Invalid credentials on the device', dev_list)
    return

start_time = time.time()
cred = {}
dev_list = ['host'+str(i) for i in range(30001)] # hostname of 30000 devices. Modify with your actual hostname for testing
with futures.ThreadPoolExecutor(max_workers=1000) as executor: #multi threading using pooling
    executor.map(config_worker, dev_list)
df = pd.DataFrame(list((cred.items())), columns=["Devices", "Password"]) # creates dataframe 
df.to_csv('new_cred.csv', index=False) # write to CSV file
print('Time taken to generate codes and/or apply the changes is', time.time()-start_time)
print('Use linux utility command head new_cred.csv or cat new_cred.csv to view the content')