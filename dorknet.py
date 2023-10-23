#!/usr/bin/env python3

import argparse
import sys
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from blessings import Terminal

t = Terminal()

# Check for args, print logo and usage
if not len(sys.argv[1:]):
    print(t.cyan('''
 ____          _   _____     _   
|    \\ ___ ___| |_|   | |___| |_ 
|  |  | . |  _| '_| | | | -_|  _|
|____/|___|_| |_,_|_|___|___|_|  
                               
Welcome to DorkNet.

To start using this script please provide one or more command
line arguments and their corresponding value, where applicable.
To display all options available use -h or --help.

Example:
DorkNet.py -h
DorkNet.py -d inurl:show.php?id= --verbose
'''))
    sys.exit(0)

# Handle command line arguments
parser = argparse.ArgumentParser(description="Use this script and dorks to find vulnerable web applications.")
group = parser.add_mutually_exclusive_group()
group.add_argument("-d", "--dork", help="specify the dork you wish to use")
group.add_argument("-l", "--list", help="specify path to list with dorks")
parser.add_argument("-v", "--verbose", action="store_true", default=False, help="toggle verbosity")
args = parser.parse_args()

dork_list = []

# Dork list processing
if args.list:
    print("\\n[" + t.green("+") + "]Reading in list from: " + args.list)
    try:
        with open(args.list, "r") as ins:
            for line in ins:
                dork_list.append(line.strip())
                if args.verbose:
                    print("[" + t.magenta("~") + "]" + line.strip())
    except IOError as e:
        print("\\n[" + t.red("!") + "]Could not read dork list")
        if args.verbose:
            print("An IO Error was raised with the following error message:")
            print(e)
else:
    dork_list.append(args.dork)

print("\\n[" + t.green("+") + "]Would you like DorkNet to proxy its connection to the search engine?")
query = input("[Y]es/[N]o: ").lower()

if query == 'y':
    IP = input("\\n[" + t.green("+") + "]Please enter the proxy host IP: ")
    PORT = input("\\n[" + t.green("+") + "]Please enter the proxy port: ")
    set_proxy = True
elif query == 'n':
    print("\\n[" + t.green("+") + "]Establishing unproxied connection...")
    set_proxy = False
else:
    print("\\n[" + t.red("!") + "]Unhandled option, defaulting to unproxied connection...")
    set_proxy = False

# Web Driver Proxy
def proxy(PROXY_HOST,PROXY_PORT):
    fp = webdriver.FirefoxProfile()
    print("[" + t.green("+") + "]Proxy host set to: " + PROXY_HOST)
    print("[" + t.green("+") + "]Proxy port set to: " + PROXY_PORT)
    print("\\n[" + t.green("+") + "]Establishing connection...")
    fp.set_preference("network.proxy.type", 1)
    fp.set_preference("network.proxy.http", PROXY_HOST)
    fp.set_preference("network.proxy.http_port", int(PROXY_PORT))
    fp.set_preference("general.useragent.override", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36")
    fp.update_preferences()
    return webdriver.Firefox(firefox_profile=fp)

# Function to generate and process results based on input
def search():
    link_list = []
    if set_proxy:
        driver = proxy(IP, PORT)
    else:
        driver = webdriver.Firefox()
    
    for _ in range(1):
        try:
            driver.get("http://google.com")
        except Exception as e:
            print("\\n[" + t.red("!") + "]A connection could not be established")
            if args.verbose:
                print("An error was raised with the following error message:")
                print(e)
                break
                driver.quit()
                sys.exit(0)
        
        assert "Google" in driver.title
        for items in dork_list:
            elem = driver.find_element_by_name("q")
            elem.clear()
            elem.send_keys(items)
            elem.send_keys(Keys.RETURN)
            time.sleep(2.2)
        try:
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, "r")))
        except Exception as e:
            driver.quit()
            print("\\n[" + t.red("!") + "]Detecting page source elements failed/timed out.")
            if args.verbose:
                print("An error was raised with the following error message:")
                print(e)
            time.sleep(1)
            continue
                
        assert "No results found" not in driver.page_source
        if "No results found" in driver.page_source:
            continue

        links = driver.find_elements_by_xpath("//div[@data-hveid]/div/div/a[@onmousedown]")
        for elem in links:
            link_list.append(elem.get_attribute("href"))
                
    driver.quit()
    for url in link_list:
        if url.endswith("search"):
            link_list.remove(url)
    return link_list

proc_one = search()

with open("results.log", "a") as outfile:
    for item in proc_one:
        outfile.write("\\n" + item)

if args.verbose:    
    with open("results.log", "r") as infile:
        for line in infile:
            print("[" + t.magenta("~") + "]" + line.strip())

print("\\n\\n[" + t.green("+") + "]Done. Results have been saved to a textfile, in the current directory as results.log for further processing.")
