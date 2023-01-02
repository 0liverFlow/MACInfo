import requests
import re
import string
import random
import csv
"""
import string
def ishex(chars):
    for char in chars:
        if char not in string.hexdigits():
           return False
    return True
"""

def EUI48_to_EUI64(mac_address):
    return mac_address[:6] + 'FFFE' + mac_address[6:]


def get_oui(mac_address, block_size_assignment='MA-L'):

    match block_size_assignment:
        case 'MA-L':
            oui = hex(int(bin(int(mac_address[:6],16))[2:][-24:],2)).replace('0x','').upper()
            if len(oui) < 6 : oui = oui.zfill(6)
            return oui
        case 'MA-M':
            oui = hex(int(bin(int(mac_address[:6],16))[2:][-20:],2)).replace('0x','').upper()
            if len(oui) < 5 :  oui = oui.zfill(5)
            return oui
        case 'MA-S':
            oui = hex(int(bin(int(mac_address[:6],16))[2:][-12:],2)).replace('0x','').upper()
            if len(oui) < 3 :  oui = oui.zfill(3)
            return oui
        case _ :
            return 'undefined'


def get_transmission_type(mac_address):
    if int(mac_address[0],16) % 2 == 0:
        return 'Unicast'
    elif mac_address == 'f' * 12:
        return 'Broadcast'
    else:
        return 'Multicast'

def get_administration_type(mac_address):
    if mac_address[1] in ['2', '3', '6', '7', 'A', 'B', 'E', 'F']:
        return 'LAA'
    else:
        return 'UAA'

def get_nic_range(assignment_block_size):
    if assignment_block_size == 'MA-L':
        return 2 ** 24
    elif assignment_block_size == 'MA-M':
        return 2 ** 20
    else:
        return 2 ** 12

def display_dict_info(dict_values):
    for key,value in dict_values.items():
        print(f"*  {key}: {value}")

def check_if_virtual_machine(oui):
    with open('./Hypervisor_ouis.csv') as hypervisors_csv_file:
        csv_reader = csv.DictReader(hypervisors_csv_file, delimiter=';')
        for line in csv_reader:
            if line['OUI'] == oui:
                return line['Virtual Machine']
        return 'Not detected'


def mac_generator(mac_prefix=None):
    hexdigits_list = list(string.hexdigits)
    random.shuffle(hexdigits_list)
    if mac_prefix:
        mac_prefix = ''.join(re.findall('[A-F0-9]', mac_prefix, re.IGNORECASE)).upper()
        mac_prefix_length = len(mac_prefix)
        while mac_prefix_length < 12:
            mac_prefix += random.choice(hexdigits_list)
            mac_prefix_length += 1
        return mac_prefix.upper()
    else:
        return ''.join(random.sample(hexdigits_list, 12)).upper()

#url = 'https://api.macvendors.com/' + mac_address

def get_mac_vendor(mac_address):
    mac_address = ''.join(re.findall('[A-F0-9]', mac_address, re.IGNORECASE)).upper()
    #print(mac_address)
    EUI_type = 'EUI-48' if len(mac_address)==12 else 'EUI-64'

    if len(mac_address) == 12 or (len(mac_address) == 16 and mac_address[6:10].casefold() == 'fffe'):
        url = 'https://www.macvendorlookup.com/api/v2/' + mac_address
        header = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            'Accept-Encoding' : 'gzip, deflate, br',
            'Accept-Language' : 'en-US,en;q=0.9',
            'Cache-Control' : 'no-cache',
            'Dnt' : '1',
            'Upgrade-Insecure-Requests' : '1',
            'Pragma' : 'no-cache',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
            'Referer' : 'https://www.macvendorlookup.com',
            "User-Agent" : "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/525.36 (KHTML, like Gecko) Chrome/55.0.2704.103 Safari/530.25"
        }
        response = requests.get(url, headers=header)
        if response.status_code == 200:
            response_json_format = response.json()[0]
            oui = get_oui(mac_address, response_json_format['type'])
            #Mac vendor details
            vendor_details_dict = {
                                    'OUI' : oui,
                                    'CountryName' : response_json_format['country'],
                                    'CompanyName' : response_json_format['company'],
                                    'CompanyAddress' :  response_json_format['addressL1']       
                                  }
            print('*' * 50)
            print('*', '\t' * 2 ,'Vendor Details\n*')
            display_dict_info(vendor_details_dict)
            print("*\n*", end='')
            print("*" * 50)

            #Mac address details
            mac_address_details_dict = {
                                            f'{EUI_type}' : mac_address,
                                            'IsValid' : 'True',
                                            'AdministrationType' : get_administration_type(mac_address),
                                            'TransmissionType' : get_transmission_type(mac_address),
                                            'VirtualMachine' : check_if_virtual_machine(oui)
                                       }
            print("* ", "\t" * 2, "Mac Address Details\n*")
            display_dict_info(mac_address_details_dict)
            if EUI_type == 'EUI-48':
                print(f"*  EUI-64 format(used with ipv6): {EUI48_to_EUI64(mac_address)}")
            print("*\n*", end='')
            print("*" * 50)

            #Block Details
            print("* ", "\t\tBlock Details\n*")
            mac_address_block_detail_dict = {
                                                'AssignmentBlockSize' : response_json_format['type'],
                                                'FirstEUI' : response_json_format['startHex'],
                                                'LastEUI' : response_json_format['endHex'],
                                                'NICRange' : get_nic_range(response_json_format['type'])
                                            }
            display_dict_info(mac_address_block_detail_dict)
            print("*" * 50)
        elif response.status_code == 204:
            oui = get_oui(mac_address)
            print('*' * 50) 
            mac_address_info_dict = {
                                        f'{EUI_type}' : mac_address,
                                        'IsValid' : 'True',
                                        'AdministrationType' : get_administration_type(mac_address),
                                        'TransmissionType' : get_transmission_type(mac_address),
                                        'VirtualMachine' : check_if_virtual_machine(oui)                                   
                                    }
            display_dict_info(mac_address_info_dict)
            if EUI_type == 'EUI-48':
                print(f"*  EUI-64 format(used with ipv6): {EUI48_to_EUI64(mac_address)}")
            print("*" * 50)

        if input("Do you wanna generate a mac address [Yay/nay] : ").lower() in ['yay', 'y','']:
            mac_prefix = input("Enter a mac prefix (press only enter if you don't want it) : ")
            print(f"The generated mac address is : {mac_generator(mac_prefix)}")


get_mac_vendor("00:50:56FF6;BA5")