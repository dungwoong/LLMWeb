import os
from selenium.webdriver.common.keys import Keys

script_dir = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(script_dir, 'mark_page.js')) as f:
    mark_page_script = f.read()

def init_mark_page(driver):
    driver.execute_script(mark_page_script)

def mark_page(driver):
    init_mark_page(driver)
    out = driver.execute_script("return markPage();")
    return out

def unmark_page(driver):
    driver.execute_script("unmarkPage();")

def type_text(element, text):
    element.click()
    element.send_keys(Keys.BACKSPACE * 20 + text)

def scroll_window(driver, amountRight=0, amountDown=0):
    driver.execute_script(f"window.scrollBy({amountRight}, {amountDown})")
