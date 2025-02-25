from netmiko import ConnectHandler
import pandas as pd
import os 
from concurrent.futures import ThreadPoolExecutor
from jinja2 import Environment, FileSystemLoader
import ipaddress
import sys

def get_vars (dev_vars):
    dev_dict = {
        's0_0' : ipaddress.IPv4Interface(dev_vars['s0_0']).ip,
        's0_1' : ipaddress.IPv4Interface(dev_vars['s0_1']).ip,
        'lo0' : ipaddress.IPv4Interface(dev_vars['lo0']).ip,
        'lo1' : ipaddress.IPv4Interface(dev_vars['lo1']).ip,
        'lo2' : ipaddress.IPv4Interface(dev_vars['lo2']).ip,
        'lo3' : ipaddress.IPv4Interface(dev_vars['lo3']).ip,
        'wan_mask' : ipaddress.IPv4Interface(dev_vars['s0_0']).netmask,
        'lan_mask' : ipaddress.IPv4Interface(dev_vars['lo3']).netmask,
        'wan_net1' : ipaddress.IPv4Interface(dev_vars['s0_0']).network[0],
        'wan_net2' : ipaddress.IPv4Interface(dev_vars['s0_1']).network[0],
        'lo0_net' : ipaddress.IPv4Interface(dev_vars['lo0']).network[0],
        'lo1_net' : ipaddress.IPv4Interface(dev_vars['lo1']).network[0],
        'lo2_net' : ipaddress.IPv4Interface(dev_vars['lo2']).network[0],
        'lo3_net' : ipaddress.IPv4Interface(dev_vars['lo3']).network[0],
        'asn' : dev_vars['asn']
    }
    return dev_dict

def config_worker(dev_list):
    df = pd.read_csv('../base_topology_data.csv')
    row = df[df['hostname'] == dev_list] 
    dev_vars = row.to_dict(orient='records')[0]
    dev_dict = get_vars(dev_vars)
    ENV = Environment(loader=FileSystemLoader('../jinja_templates'))
    int_config_tmp = ENV.get_template('base_topology_config.j2')
    int_config = int_config_tmp.render(dev_vars=dev_dict)
    login_info = {
        'ip': dev_list,
        'username': os.getenv('DEV_ADMIN'),
        'password': os.getenv('DEV_KEY'), 
        'device_type': 'cisco_ios'
    } 
    session = ConnectHandler(**login_info)
    # output = session.send_config_set(int_config)
    # print(output)
    bgp_config_tmp = ENV.get_template('bgp.j2')
    data = df.to_dict(orient='records')
    for row in data:
        if row ['hostname'] == 'r1':
            r1_dict = get_vars(row)
        if row ['hostname'] == 'r2':
            r2_dict = get_vars(row)
        if row ['hostname'] == 'r3':
            r3_dict = get_vars(row)
        if row ['hostname'] == 'r4':
            r4_dict = get_vars(row)
    if dev_list == 'r1':
        r1_dict.update({'nbr1':r2_dict['s0_0'], 'nbr2':r4_dict['s0_1'],
                        'nbr1_asn': r2_dict['asn'], 'nbr2_asn':r4_dict['asn']})
        j_dict = r1_dict
    if dev_list == 'r2':
        r2_dict.update({'nbr1':r1_dict['s0_0'], 'nbr2':r3_dict['s0_1'],
                        'nbr1_asn': r1_dict['asn'], 'nbr2_asn':r3_dict['asn']})
        j_dict = r2_dict
    if dev_list == 'r3':
        r3_dict.update({'nbr1':r4_dict['s0_0'], 'nbr2':r2_dict['s0_1'],
                        'nbr1_asn': r4_dict['asn'], 'nbr2_asn':r2_dict['asn']})
        j_dict = r3_dict
    if dev_list == 'r4':
        r4_dict.update({'nbr1':r3_dict['s0_0'], 'nbr2':r1_dict['s0_1'],
                        'nbr1_asn': r3_dict['asn'], 'nbr2_asn':r1_dict['asn']})
        j_dict = r4_dict
    print(j_dict)
    bgp_config = bgp_config_tmp.render(dict=j_dict)
    print(bgp_config)
    print('#'*5+' loggin to device '+dev_list+'#'*5)
    output = session.send_config_set(bgp_config)
    print(output)
    print('#'*20)
    return

dev_list = sys.argv[1:]
if dev_list[0] == 'all devices':
    dev_list = ['r1', 'r2', 'r3', 'r4']

print(dev_list)
with ThreadPoolExecutor(max_workers=10) as executor:
    executor.map(config_worker, dev_list)
