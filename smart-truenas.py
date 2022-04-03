import json
import socket
import subprocess
import sys, ipaddress

def ListDrives(smart_bin):
  try:
    AllDrives = []
    MyOut = subprocess.Popen([smart_bin, '-j', '--scan'], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT)
    stdout,stderr = MyOut.communicate()
    drive_json = json.loads(stdout.decode('UTF-8'))

    if 'devices' in drive_json.keys():
      for drive in drive_json['devices']:
        drive_json = ExecuteSMARTCTL(smart_bin, drive['name'])
        if drive_json is not None:
          AllDrives.append(drive_json)
    return AllDrives

  except:
    print ("failed to list drives, check smartctl path")


def ExecuteSMARTCTL(smart_bin, drive):
  ignoreList = ['ata_smart_self_test_log', 'ata_smart_selective_self_test_log', 'ata_sct_capabilities', 'ata_smart_error_log', 'ata_smart_data', 'ata_version', 'interface_speed', 'in_smartctl_database', 'json_format_version', 'ata_smart_selective_self_test_log']

  try:
    MyOut = subprocess.Popen([smart_bin, '-j', '-a', drive], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT)
    stdout,stderr = MyOut.communicate()
    drive_json = json.loads(stdout.decode('UTF-8'))

    if 'ata_smart_attributes' in drive_json.keys():
      drive_json = FilterJSON(drive_json)
    
    for i in ignoreList:
      if i in drive_json.keys():
        del drive_json[i]

    return drive_json
    
  except:
    print ("failed to get smart data for drive : %s" % drive)

 
def FilterJSON(drive_json):
  ignoreList = ['worst', 'thresh', 'updated', 'flags', 'when_failed', 'name']

  for item in drive_json['ata_smart_attributes']['table']:
    item_name = item['name']  
    #remove common values that do not change
    for i in ignoreList:
      if i in item.keys():
        item.pop(i)

    if item_name not in drive_json.keys():
      drive_json[item_name] = item

  drive_json['ata_smart_attributes'].pop('table', None) 

  return drive_json


def SendJSON(Drive, IP, Port):
  try:
    logstash = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    message = json.dumps( Drive ).encode('utf-8')
    logstash.connect((IP, Port))
    logstash.send(message)
    logstash.close()
  except:
    print ("Failed to send : %s" % Drive["device"]["name"])



def main():
  if len(sys.argv) == 3:
    IP = str(ipaddress.ip_address(sys.argv[1]))
    PORT = int(sys.argv[2])
    if (0 < PORT < 65535):

      #Get smart info for all drives
      AllDrives = ListDrives('smartctl')

      #send to logtash
      if AllDrives is not None:
        for Drive in AllDrives:
          SendJSON(Drive, IP, PORT)

    else:
      print ("Valid port range : 1 - 65535")
  else:
    print ("Usage: python3 smart-truenas.py [ip_address] [port]") 

if __name__ == '__main__':
  main()


