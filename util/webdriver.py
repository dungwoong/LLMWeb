import os
import subprocess
import psutil
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

DEBUG_PORT = 9222
CHROME_PATH = os.path.join(r"C:\Program Files (x86)\Google\Chrome\Application", 'chrome.exe') # TODO optimize for other systems
assert os.path.exists(CHROME_PATH), 'Chrome path incorrect. Change util/webdriver.py'

def is_chrome_running():
    # Check if any Chrome processes are running
    for process in psutil.process_iter(['pid', 'name']):
        if 'chrome' in process.info['name'].lower():  # Adjust 'chrome' if necessary for your OS
            return True
    return False

# https://stackoverflow.com/questions/67738780/python-selenium-detach-option-not-working
# https://www.headspin.io/blog/ultimate-guide-chrome-remote-debugging
def chrome_remote_debug_webdriver():
    # Typically before starting this process, you must close chrome completely
    # TODO better way to do this?
    if is_chrome_running():
        raise PermissionError('Chrome detected. Please close all instances of Chrome to attach webdriver')
    print('Starting Chrome...')
    # f"--user-data-dir={os.path.join(os.getcwd(), 'tmp', 'chromeProfile')}"
    command = f'"{CHROME_PATH}" -remote-debugging-port={DEBUG_PORT}'
    subprocess.Popen(command)
    print('Chrome running in background. Connecting Selenium...')
    chrome_options = Options()
    chrome_options.page_load_strategy = 'eager'
    chrome_options.add_experimental_option('debuggerAddress', f'localhost:{DEBUG_PORT}')
    driver = webdriver.Chrome(options=chrome_options)
    print('Done')
    return driver

def chrome_new_webdriver():
    chrome_options = Options()
    # chrome_options.add_argument('--start-maximized')
    chrome_options.page_load_strategy = 'eager' # https://www.selenium.dev/documentation/webdriver/drivers/options/
    chrome_options.add_argument('--log-level=3') # 2=ERROR 3=FATAL
    chrome_options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(options=chrome_options)
    return driver
