#!/usr/bin/python3


# pip install requests pyfiglet
import requests

try:
    import pyfiglet
    BANNER = True
except:
    BANNER = False

import datetime, time, subprocess,os, sys


try:
    BROWSER = os.environ['BROWSER']
except KeyError:
    sys.stderr.write("[!] Flag $BROWSER not set\n")
    exit(1)

try:
    os.system("echo 'test' > /temp/hn_cli_test.txt && rm -f /tmp/hn_cli_test.txt")
except:
    sys.stderr.write("[!] Script needs read and write permission to /tmp\n")
    exit(1)

TOP_NEWS = "/tmp/hackernews_cli.txt"

READS_SIZE = 70

PAGE_SIZE = 7

CACHE_TIMEOUT = 30 * 60 # seconds
try:
    _ = int(CACHE_TIMEOUT)
except:
    sys.stderr.write("[!] CACHE_TIMEOUT must be and integer of seconds\n")
    exit(1)

#######################################
# User IO
#######################################

def banner():
    global BANNER
    print('\033c')
    if BANNER:
        ascii_banner = pyfiglet.figlet_format("Fetching HackerNews API ... \n")
    else:
        ascii_banner = "Fetching HackNews API ...\n"
    print(ascii_banner)


def show_menu():
    global READS_SIZE
    print('\033c')
    print("******** HackerNews CLI Menu ********")
    print("")
    print(f"(x: int | x <= [1..{READS_SIZE}])  --  open read by ID")
    print(f"(&x: int | x <= [1..{READS_SIZE}])  --  open comments by ID")
    print("j[n]  --  scroll reader up .n [page limit 0] where n is number of pages to move")
    print(f"k[n]  --  scroll reader down .n [page limit {READS_SIZE//5}] where n is the numbe rof pages to move")
    print("r  --  refresh news cache")
    print("help / h  --  display help menu")
    print("quit / q  --  quit program")
    print("")
    print("********---------------------********")
    print("")
    print("")


#######################################
# Open links for reads and comments
# Use brower set by flag $BROWER
#######################################

def show_comments(data, comment):
    global BROWSER, READS_SIZE, PAGE_SIZE
    if comment != 0:
        comments = (comment -1) * PAGE_SIZE + 4
        if comment  > READS_SIZE:
            return 1
        link = data[comments]
        _, link = link.split(": ")
        cmd = [BROWSER, f"{link}"]
        try:
            subprocess.call(cmd)
        except:
            sys.stderr.write("[!] Error calling subprocess\n")
    return 0


# read_input <= [1..30]
# array_index_start = 0; read_input_start = 1; 
# read_space_in_lines = 5 (each read occupies 5 lines in the logfile)
# link_index = 3
def show_read(data, read):
    global BROWSER, READS_SIZE, PAGE_SIZE
    if read != 0:
        read_link = (read -1) * PAGE_SIZE + 3
        if read > READS_SIZE:
            return 1
        link = data[read_link]
        _, link = link.split(": ")
        cmd = [BROWSER, f"{link}"]
        try:
            subprocess.call(cmd)
        except:
            sys.stderr.write("[!] Error calling subprocess\n")
    return 0


def show_feed(data, handle):
    global PAGE_SIZE
    print('\033c')
    i = 0
    len_data = len(data)
    for line in data[handle*PAGE_SIZE*5:(handle+1)*PAGE_SIZE*5]:
        print(line)
        i += 1
        # post block has length 5 lines 
        if i == 5:
            print("\n")
            i = 0
    return 0


#######################################
# Make GET calls to fetch API
# Parse data 
# Cache and read from cache
#######################################

def get_call(url):
    err = False
    try:
        res = requests.get(url)
    except Exception as e:
        sys.stderr.write(f"[!] Connection problem, can't reach API -- {e}\n")
        exit(1)
    if res.status_code != 200:
        err = True
        return f"[x] Response status code: {res.status_code} -- ", err
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
        if cw - timestamp > CACHE_TIMEOUT:
            os.remove(TOP_NEWS)
            return list()
        return data[1:]
    return list()


################################
# Event Handler
################################

def hackernews_cli(data, handle):
    global TOP_NEWS, READS_SIZE
    if len(data) == 0:
        data = fetch_api()
    show_feed(data, handle)
    try:
        read = input(">>> ")
    except:
        print("[!] Error reading command")
        print("Type 'help' or 'h' to see help menu")
        time.sleep(1)
    if read == "quit" or read == "q":
        print("[*] Gracefully quitting ...")
        exit(0)
    elif len(read) == 0:
        show_menu()
        print("[!] Invalid command\n")
        time.sleep(2)
        return data, handle
    elif read[0] == "&":
        try:
            comment = int(read[1:])
            if show_comments(data, comment) != 0:
                sys.stderr.write("[!] Read input out of bounds for data size\n")
                _ = int("IndexOutOfRange")
        except ValueError:
            show_menu()
            print("[!] Invalid command\n")
            time.sleep(2)
            return data, handle
    elif read[0] == "k" and handle > 0:
        try:
            c = int(read[1:])
        except:
            c = 1
        handle -=  c
        if handle < 0:
            handle = 0
    elif read[0] == "j" and handle < (READS_SIZE//5):
        try:
            c = int(read[1:])
        except:
            c = 1
        handle += c
        if handle > (READS_SIZE//5)-1:
            handle = (READS_SIZE//5)-1
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
            if show_read(data, read) != 0:
                sys.stderr.write("[!] Read input out of bounds for data size\n")
                _ = int("IndexOutOfRange")
        except ValueError:
            show_menu()
            print("[!] Invalid command\n")
            time.sleep(2)
            return data, handle

    return data, handle


#######################################
# main
#######################################

def bootstrap():
    handle  = 0
    data = check_cache()
    banner()
    time.sleep(1)
    while True:
        data, handle = hackernews_cli(data, handle)


if __name__ == '__main__':
    bootstrap()
