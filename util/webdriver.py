from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def get_webdriver():
    chrome_options = Options()
    chrome_options.add_argument('--start-maximized')
    driver = webdriver.Chrome(options=chrome_options)
    return driver
