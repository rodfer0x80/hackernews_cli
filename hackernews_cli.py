#!/usr/bin/python3

# Author: trevalkov
# License: GPL3
# Dependencies: Python3 Standard Library


import datetime
import time
import requests
import subprocess
import os


def get_call(url):
    err = False
    try:
        res = requests.get(url)
    except:
        sys.stderr.write("[!] Connection problem, can't reach API")
        exit(1)
    if res.status_code != 200:
        err = True
        return f"[x] Response status code: res.status_code", err
    return res, err


def process_response(res):
    read_ids = res.json()
    reads = list()
    for read_id in read_ids[:30]:
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
    return reads


def show_menu():
    print('\033c')
    print("{x: int | x <= [1..30]  -  open read by ID")
    print("refresh / r  -  refresh news cache")
    print("help / h  -  display help menu")
    print("quit / q  -  quit program")
    print("")
    print("ENTER 'q' or 'quit' to quit menu")
    q = input(":")
    while q != "quit" or q != "q":
        show_menu()


def hackernews_cli(data, top_news):
    print('\033c')
    i = 0
    for line in data:
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
        hackernews_cli(data, top_news)
    if read == "quit" or read == "q":
        print("[*] Gracefully quitting ...")
        exit(0)
    if read == "r" or read == "refresh" :
        os.remove(top_news)
        fetch_api(top_news)
        hackernews_cli(data, top_news)
    if read == "h" or read == "help":
        show_menu()
        hackernews_cli(data, top_news)
    try:
        read = int(read)
    except ValueError:
        print("[!] Command must be an int x => [1..30]")
        time.sleep(1)
        hackernews_cli(data, top_news)
    return read


def check_cache(top_news):
    print('\033c')
    print("[+] Checking cache ...")
    data = ""
    if os.path.exists(top_news):
        with open(top_news, 'r') as fp:
            data = fp.read().split("\n")
        new_data = list()
        for line in data:
            if line != "":
                new_data.append(line)
        if len(new_data) == 0:
            sys.stderr.write("[!] Error parsing tempfile\n")
            data = fetch_api(top_news)
            return data[1:]
        data = new_data
        try:
            timestamp = int(data[0])
        except ValueError:
            sys.stderr.write("[!] Error reading tempfile timestamp\n")
            data = fetch_api(top_new)
            return data[1:]
        try:
            cw = int(round(time.time()))
        except:
            sys.stderr.write("[!] Error with system clock\n")
            exit(1)
        if cw - timestamp > 30 * 60:
            os.remove(top_news)
            data = fetch_api(top_news)
    else:
        data = fetch_api(top_news)     
    return data[1:]


def fetch_api(top_news):
    print('\033c')
    print("[+] Fetching HackerNews API ...")
    url = "https://hacker-news.firebaseio.com/v0/topstories.json"
    res, err = get_call(url)
    if err:
        sys.stderr.write(res)
        exit(1)
    reads = process_response(res)
    try:
        timestamp = int(round(time.time()))
    Except ValueError:
        sys.stderr.write("[!] Error with system clock\n")
        exit(1)
    try:
        with open(top_news, "w") as fp:
            data = f"{timestamp}\n"
            i = 1
            for read in reads:
                data += f"Rank: {i}\n"
                data += f"\tTitle: {read['title']}\n"
                data += f"\tTime: {read['time']}\n"
                data += f"\tLink: {read['link']}\n"
                data += f"\tComments: {read['comments']}\n"
                i += 1
            data += "\n"
            fp.write(data)
    except:
        sys.stderr.write("[!] Error writting to tempfile\n")
        continue
    new_data = list()
    for line in data.split("\n"):
        if line != "":
            new_data.append(line)
    data = new_data
    return data


def show_read(data, read, top_news):
    # read_input <= [1..30]
    # array_index_start = 0; read_input_start = 1; 
    # read_space_in_lines = 5 (each read occupies 5 lines in the logfile)
    # link_index = 3
    read_link = (read -1) * 5 + 3
    link = data[read_link]
    link = link[7:]
    cmd = ["open", f"{link}"]
    try:
        subprocess.call(cmd)
    except:
        sys.stderr.write("[!] Error calling subprocess\n")
        continue

if __name__ == '__main__':
    top_news = "/tmp/hackernews_cli.txt"
    data = check_cache(top_news)
    while True:
        read = hackernews_cli(data, top_news)
        show_read(data, read, top_news)
