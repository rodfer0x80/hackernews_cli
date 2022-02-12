#!/usr/bin/python3


import requests, pyfiglet
import datetime, time, subprocess,os, sys


BROWSER = "firefox"
TOP_NEWS = "/tmp/hackernews_cli.txt"
READS_SIZE = 50

def banner():
    print('\033c')
    ascii_banner = pyfiglet.figlet_format("Fetching HackerNews API ... \n")
    print(ascii_banner)


def get_call(url):
    err = False
    try:
        res = requests.get(url)
    except:
        sys.stderr.write("[!] Connection problem, can't reach API\n")
        exit(1)
    if res.status_code != 200:
        err = True
        return f"[x] Response status code: res.status_code", err
    return res, err


def process_response(res):
    global READS_SIZE
    read_ids = res.json()
    reads = list()
    for read_id in read_ids[:READS_SIZE]:
        url = f"https://hacker-news.firebaseio.com/v0/item/{read_id}.json"
        res, err = get_call(url)
        if not err:
            res_dict = res.json()
            try:
                link = res_dict['url']
            except:
                link = "<no_link>"
            read = {
                    'title': res_dict['title'],
                    'time': datetime.datetime.fromtimestamp(res_dict['time']).strftime("%A, %B %d, %Y %I:%M:%S"),
                    'link': link,
                    'comments': f"https://news.ycombinator.com/item?id={read_id}",
            }
            reads.append(read)
        else:
            sys.stderr.write(err)
    return reads


def show_menu():
    global READS_SIZE
    print('\033c')
    print("******** HackerNews CLI Menu ********")
    print("")
    print(f"(x: int | x <= [1..{READS_SIZE}])  -  open read by ID")
    print("up / w  -  scroll reader up x [page limit 0]")
    print("down / s  -  scroll reader down [page limit 4]")
    print("refresh / r  -  refresh news cache")
    print("help / h  -  display help menu")
    print("quit / q  -  quit program")
    print("")
    print("********---------------------********")
    print("")
    print("")


def hackernews_cli(data, handle):
    global TOP_NEWS, READS_SIZE
    if len(data) == 0:
        data = fetch_api()
    print('\033c')
    i = 0
    len_data = len(data)
    for line in data[handle*5*5:(handle+1)*5*5]:
        print(line)
        i += 1
        # post block has length 5 lines 
        if i == 5:
            print("")
            i = 0
    try:
        read = input(">>> ")
    except:
        print("[!] Error reading command")
        print("Type 'help' or 'h' to see help menu")
        time.sleep(1)
    if read == "quit" or read == "q":
        print("[*] Gracefully quitting ...")
        exit(0)
    elif (read == "k" or read == "up") and handle > 0:
        handle -= 1
    elif (read == "j" or read == "down") and handle < (READS_SIZE/5)-1:
        handle += 1
    elif read == "r" or read == "refresh" :
        try:
            os.remove(TOP_NEWS)
        except:
            pass
        finally:
            data = fetch_api()
            return hackernews_cli(data, 0)
    elif read == "h" or read == "help":
        show_menu()
        time.sleep(2)
    else:
        try:
            read = int(read)
        except ValueError:
            show_menu()
            print("[!] Invalid command\n")
            time.sleep(2)
            return data, 0, handle
    
    try:
        read = int(read)
    except ValueError:
        return data, 0, handle
    return data, read, handle


def check_cache():
    global TOP_NEWS
    if os.path.exists(TOP_NEWS):
        with open(TOP_NEWS, 'r') as fp:
            data = fp.read().split("\n")
        new_data = list()
        for line in data:
            if line != "":
                new_data.append(line)
        if len(new_data) == 0:
            sys.stderr.write("[!] Error parsing tempfile\n")
            return data
        data = new_data
        try:
            timestamp = int(data[0])
        except ValueError:
            sys.stderr.write("[!] Error reading tempfile timestamp\n")
            return data
        try:
            cw = int(round(time.time()))
        except:
            sys.stderr.write("[!] Error with system clock\n")
            exit(1)
        if cw - timestamp > 30 * 60:
            os.remove(TOP_NEWS)
            return list()
        return data[1:]
    return list()


def fetch_api():
    global TOP_NEWS
    url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    res, err = get_call(url)
    if err:
        sys.stderr.write(res)
        exit(1)
    # multithread for each each and write to cache file using mutex
    # then read file, remove timestamp and return to cli inteface
    reads = process_response(res)
    timestamp = int(round(time.time()))
    data = f"{timestamp}\n"
    i = 1
    for read in reads:
        data += f"Rank: {i}\n"
        data += f"\tTitle: {read['title']}\n"
        data += f"\tTime: {read['time']}\n"
        data += f"\tLink: {read['link']}\n"
        data += f"\tComments: {read['comments']}\n"
        i += 1
    new_data = list()
    with open(TOP_NEWS, "w") as fp:
        fp.write(data)
    for line in data.splitlines():
        if line != "":
            new_data.append(line)
    return new_data[1:]


def show_read(data, read):
    global BROWSER
    # read_input <= [1..30]
    # array_index_start = 0; read_input_start = 1; 
    # read_space_in_lines = 5 (each read occupies 5 lines in the logfile)
    # link_index = 3
    if read != 0:
        read_link = (read -1) * 5 + 3
        link = data[read_link]
        link = link[7:]
        cmd = [BROWSER, f"{link}"]
        try:
            subprocess.call(cmd)
        except:
            sys.stderr.write("[!] Error calling subprocess\n")
    return 0


if __name__ == '__main__':
    handle  = 0
    data = check_cache()
    banner()
    time.sleep(1)
    while True:
        data, read, handle = hackernews_cli(data, handle)
        show_read(data, read)
