from dataclasses import dataclass, asdict
import speedtest
from datetime import datetime
#from pythonping import ping
import requests
from ping3 import ping
from multiprocessing.pool import ThreadPool
from functools import partial
from statistics import mean, stdev
from pprint import pprint
import subprocess
import re
import os, sys
import json
import logging
from logging.handlers import RotatingFileHandler

logging.basicConfig(filename='/home/hugo/MEGA/scripts/get_connection_statistics/connectionchecker.log', level=logging.DEBUG)


log_formatter = logging.Formatter('%(asctime)s %(levelname)s %(funcName)s(%(lineno)d) %(message)s')

logFile = '/home/hugo/MEGA/scripts/get_connection_statistics/connectionchecker.log'

my_handler = RotatingFileHandler(logFile, mode='a', maxBytes=5*1024*1024,  backupCount=2, encoding=None, delay=0)
my_handler.setFormatter(log_formatter)
my_handler.setLevel(logging.DEBUG)

my_log = logging.getLogger('root')
my_log.setLevel(logging.INFO)

my_log.addHandler(my_handler)

# 
#TODO: logging

@dataclass
class PingData:
    host:str
    mean:float
    stdev:float
    nrpings:int

@dataclass
class NordVpnData:
    status:str
    server:str
    country:str
    city:str
    server_IP: str
    technology:str
    protocol:str
    received:tuple
    sent:tuple
    uptime:str #TODO parse uptime


@dataclass
class Connectiondata:
    collection_reason: str
    datetime: datetime
    connected: bool
    ip_adress: str   

    speedtest_up:float
    speedtest_down:float

    nordvpndata:NordVpnData
    
    pingdata:PingData
    
def do_speedtest():
    my_log.debug("do speedtest")
    try:
        s = speedtest.Speedtest()
    except Exception as e:
        my_log.error(e)
        sys.exit(1)

    my_log.debug("speedtest initialized")
    up = s.upload()
    my_log.debug(f"up {up}")
    down = s.download()
    my_log.debug(f"down {down}")
    
    return up, down
    
def is_connected(check_website="http://www.google.com?"):
    resp = requests.get(check_website)
    return resp.status_code == 200


def myping(host):
    print(f"\t\t-{host}")
    resp = ping(host)
    print(f"\t\t-{resp}")
    if resp == False:
        return False
    else:
        return resp
        
        
def multiping(host, times):
    pinglist = [myping(host) for _ in range(times)]
    
    return pinglist

def load_hostlist(hostlist_file = "hostlist.txt"):
    with open(hostlist_file, 'rt') as f:
        hostlist = f.readlines()
        hostlist = [host.strip() for host in hostlist]
    return hostlist


def get_pingdata(hostlist, nrpings):
    all_pingdata={}
    for host in hostlist:
        pinglist = multiping(host, nrpings)
        pinglist = [aping for aping in pinglist if aping]
        try:
            the_mean = mean(pinglist)
        except Exception:
            my_log.warning(f"Could not calculate mean for {host}")
            the_mean = None
            
        try:
            the_stdev = stdev(pinglist)
        except Exception:
            my_log.warning(f"Could not calculate stdev for {host}")
            the_stdev = None
            
        pingdata = PingData(host, the_mean, the_stdev, nrpings)
        all_pingdata[host] = pingdata
    return all_pingdata
    
def get_nordvpn_status():
    result = subprocess.check_output("nordvpn status", shell=True)
    result = result.decode("utf-8")
    result = re.sub('\r', '', result)
    result = result.split('\n')
    
    status = result[0].split(':')[-1].strip()

    if not status == "Connected":
        return NordVpnData(status, '', '', '', '', '', '', (), (), '')
    
    server = result[1].split(':')[-1].strip()
    country = result[2].split(':')[-1].strip()
    city = result[3].split(':')[-1].strip()
    server_ip = result[4].split(':')[-1].strip()
    technology = result[5].split(':')[-1].strip()
    protocol = result[6].split(':')[-1].strip()

    transfer = result[7].split(':')[-1].strip()
    received, sent = transfer.split(',')
    amount_received, unit_received, _ = received.split(' ')
    amount_received = float(amount_received.strip())
    unit_received = unit_received.strip()
    
    amount_sent, unit_sent, _ = sent.strip().split(' ')
    amount_sent = float(amount_sent.strip())
    unit_sent = unit_sent.strip()
    
    uptime = result[8].split(':')[-1].strip()
    
    data = NordVpnData(
        status=status,
        server=server,
        country=country,
        city = city,
        server_IP = server_ip,
        technology = technology,
        protocol = protocol,
        received = (amount_received, unit_received),
        sent = (amount_sent, unit_sent),
        uptime = uptime)
    return data

def to_json(connectiondata, root_output_folder, timestamp):
    outfolder = f'{root_output_folder}/{timestamp.year:04d}/{timestamp.month:02d}/{timestamp.day:02d}/'
    if not os.path.exists(outfolder):
        os.makedirs(outfolder)
    
    outfile = timestamp.strftime('%H_%M_%S') + '.json'
    outfile = os.path.join(outfolder, outfile)
    with open(outfile, 'wt') as out:
        json.dump(asdict(connectiondata), out)
    my_log.info(f"Data saved at {outfile}")


if __name__ == "__main__":
    current_time = datetime.now()
    print(current_time)
    with open("/home/hugo/MEGA/scripts/get_connection_statistics/started.txt", 'wt') as out:
        out.write(current_time.strftime("%m/%d/%Y, %H:%M:%S"))
    try:
        reason = sys.argv[1]
    except IndexError:
        reason = "Run script manually."
    my_log.info(f'Check connection at {current_time.strftime("%m/%d/%Y, %H:%M:%S")}. Reason: {reason} ')

    prev_wd = os.getcwd()
    os.chdir(sys.path[0])
    my_log.info(f"wd changed from {prev_wd} to {os.getcwd()}")
    connected = is_connected()
    
    if connected:
        print("connection found")
    else:
        print("we are not connected")
    # with open("/home/hugo/MEGA/scripts/get_connection_statistics/connection_tested.txt", 'wt') as out:    
    #     out.write(current_time.strftime("%m/%d/%Y, %H:%M:%S"))
    my_log.info(f'connected: {connected}')

    if not connected:
        connectiondata = Connectiondata(
            collection_reason = reason,
            datetime=current_time.strftime("%m/%d/%Y, %H:%M:%S"),
            connected = connected,
            ip_adress = '',
            speedtest_up = None,
            speedtest_down = None,
            nordvpndata = None,
            pingdata = None)
    else:
        ip_addr = '' #TODO
        
        print("run speedtest")
        try:
            up, down = do_speedtest()
            my_log.info(f'speedtest done')
        except Exception as e:
            my_log.warning(f"Speedtest failed. {e}")
            up, down = None, None

        # with open("/home/hugo/MEGA/scripts/get_connection_statistics/speedtest_done.txt", 'wt') as out:    
        #     out.write(current_time.strftime("%m/%d/%Y, %H:%M:%S"))
        
        try:
            hostlist = load_hostlist(hostlist_file='/home/hugo/MEGA/scripts/get_connection_statistics/hostlist.txt')
        except Exception as e:
            my_log.error(f"Cound not load hostlist. {e}")
            sys.exit(1)

        try:
            print("run pingtest")
            pingdata = get_pingdata(hostlist, 20)
            print("check vpn status")
        except Exception as e:
            my_log.error(f"Cound not do pingtest: {e}")
            sys.exit(1)
            
        my_log.info(f'pingtest done')

        try:
            nordvpn_status = get_nordvpn_status()
        except Exception as e:
            my_log.error(f"Could not check nordvpn status {e}")
        
        my_log.info(f'nordvpn status checked')

        connectiondata = Connectiondata(
            collection_reason = reason,
            datetime=current_time.strftime("%m/%d/%Y, %H:%M:%S"),
            connected = connected,
            ip_adress = ip_addr,
            speedtest_up = up,
            speedtest_down = down,
            nordvpndata = nordvpn_status,
            pingdata = pingdata)
            
    pprint(asdict(connectiondata))
    to_json(connectiondata, 'data', current_time)
    my_log.info(f'script completed at {datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}')
