import tarfile
import subprocess
import shutil
import os
import time

def extract_ova(type):

    if type == 'csr':
        csr_ova_path = '../csr1000v-universalk9.17.03.01a (VOIP Features).ova'
        extract_path = '../csr1000v/'
    elif type == 'yvm':
        csr_ova_path = '../yVM.ova'
        extract_path = '../yVM/'

    with tarfile.open(csr_ova_path, 'r') as tar:
        tar.extractall(path=extract_path)

def generate_vmx(vm_data, type):
    name = vm_data['name']

    if type == 'csr':
        ovf_path = '../csr1000v/csr1000v-universalk9.17.03.01a-vga.ovf'
    elif type == 'yvm':
        ovf_path = '../yVM/TinyVM.ovf'

    vm_output = f'../Virtual_Machines/{name}'
    ovftool = '../ovftool/ovftool.exe'

    subprocess.run([
        ovftool,
        f'--name={name}',
        ovf_path,
        vm_output,
    ])

    modify_vmx(vm_data, type)

def set_or_add(lines, key, value):
    for i, line in enumerate(lines):
        if line.startswith(key):
            lines[i] = f'{key} = "{value}"\n'
            return lines
    lines.append(f'{key} = "{value}"\n')
    return lines

def modify_vmx(vm_data, type):
    name = vm_data['name']
    vmx_path = f'../Virtual_Machines/{name}/{name}/{name}.vmx'

    if name == 'UTM-PH':
        iso_path = 'day0-utmph.iso' 
    elif name == 'UTM-JP':
        iso_path = 'day0-utmjp.iso'
    elif name == 'UTM':
        iso_path = 'day0-utm.iso'

    with open(vmx_path, 'r') as f:
        lines = f.readlines()

    if 'vnet_1' in vm_data:
        lines = set_or_add(lines, 'ethernet0.present', 'TRUE')

        if vm_data['vnet_1'] == 'nat':
            lines = set_or_add(lines, 'ethernet0.connectionType', vm_data['vnet_1'])
        else:
            lines = set_or_add(lines, 'ethernet0.connectionType', 'custom')
            lines = set_or_add(lines, 'ethernet0.vnet', vm_data['vnet_1'])

    if 'vnet_2' in vm_data:
        lines = set_or_add(lines, 'ethernet1.present', 'TRUE')
        lines = set_or_add(lines, 'ethernet1.connectionType', 'custom')
        lines = set_or_add(lines, 'ethernet1.vnet', vm_data['vnet_2'])

    if 'vnet_3' in vm_data:
        lines = set_or_add(lines, 'ethernet2.present', 'TRUE')
        lines = set_or_add(lines, 'ethernet2.connectionType', 'custom')
        lines = set_or_add(lines, 'ethernet2.vnet', vm_data['vnet_3'])

    if type != 'yvm':
        lines = set_or_add(lines, 'ide1:1.present', 'TRUE')
        lines = set_or_add(lines, 'ide1:1.fileName', iso_path)
        lines = set_or_add(lines, 'ide1:1.deviceType', 'cdrom-image')
        lines = set_or_add(lines, 'ide1:1.startConnected', 'TRUE')

        # Copy Day0 Configurations
        dst = f'../Virtual_Machines/{name}/{name}/{iso_path}'
        shutil.copy2(iso_path, dst)

    with open(vmx_path, 'w') as f:
        f.writelines(lines)
    
    run_vmx(vm_data)

def run_vmx(vm_data):
    name = vm_data['name']
    vmx_path = rf'..\Virtual_Machines\{name}\{name}\{name}.vmx'
    os.startfile(vmx_path)


if __name__ == "__main__":
    deploy = input('''
    Lab                     Entry
    ---                     ---
    x1 CSRouter . . . . . . 1
    x1 yVM  . . . . . . . . 2
    S2S-VPN Lab . . . . . . 3
    NAT-PAT Lab . . . . . . 4

Specify an Entry > ''')

    csr = 'csr'
    yvm = 'yvm'

    extract_ova(csr)
    extract_ova(yvm)

    if deploy == '1':
        vm_1 = {
            'name': 'UTM',
            'vnet_1': 'nat',
            'vnet_2': 'VMnet2',
            'vnet_3': 'VMnet3'
        }
        generate_vmx(vm_1, csr)

    elif deploy == '2':
        vm_1 = {
            'name': 'WEBS-1',
            'vnet_1': 'VMnet3'
        }
        generate_vmx(vm_1, yvm)

    elif deploy == '3':
        vm_1 = {
            'name': 'BLDG-PH',
            'vnet_1': 'VMnet3'
        }
        
        vm_2 = {
            'name': 'UTM-PH',
            'vnet_1': 'nat',
            'vnet_2': 'VMnet2',
            'vnet_3': 'VMnet3'
        }

        vm_3 = {
            'name': 'UTM-JP',
            'vnet_1': 'nat',
            'vnet_2': 'VMnet2',
            'vnet_3': 'VMnet4'
        }

        vm_4 = {
            'name': 'BLDG-JP',
            'vnet_1': 'VMnet4'
        }
        generate_vmx(vm_1, yvm)
        generate_vmx(vm_2, csr)
        generate_vmx(vm_3, csr)
        generate_vmx(vm_4, yvm)
    
    elif deploy == '4':
        vm_1 = {
            'name': 'UTM',
            'vnet_1': 'nat',
            'vnet_2': 'VMnet2',
            'vnet_3': 'VMnet3'
        }

        vm_2 = {
            'name': 'WEBS-1',
            'vnet_1': 'VMnet3'
        }

        vm_3 = {
            'name': 'WEBS-2',
            'vnet_1': 'VMnet3'
        }

        vm_4 = {
            'name': 'WEBS-3',
            'vnet_1': 'VMnet3'
        }
        generate_vmx(vm_1, csr)
        generate_vmx(vm_2, yvm)
        generate_vmx(vm_3, yvm)
        generate_vmx(vm_4, yvm)
    
    else:
        print('Invalid Entry. Ending Process')
        time.sleep(2)