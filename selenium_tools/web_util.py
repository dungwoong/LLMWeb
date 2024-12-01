import os
import platform
import base64
from selenium.webdriver.common.keys import Keys

script_dir = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(script_dir, 'mark_page.js')) as f:
    mark_page_script = f.read()

def init_mark_page(driver):
    driver.execute_script(mark_page_script)

def mark_page(driver):
    init_mark_page(driver)
    out = driver.execute_script("return window.markPage();")
    return out

def unmark_page(driver):
    init_mark_page(driver)
    driver.execute_script("return window.unmarkPage();")

def type_text(element, text):
    select_all = (Keys.META + 'a') if platform.system() == "Darwin" else (Keys.LEFT_CONTROL + 'a') # TODO configure for other systems
    element.click()
    element.send_keys(select_all, Keys.BACKSPACE)
    element.send_keys(text)
    element.send_keys(Keys.ENTER)

def scroll_window(driver, element=None, amountRight=0, amountDown=0):
    if element is None or element == 'window':
        driver.execute_script(f"window.scrollBy({amountRight}, {amountDown})")
    else:
        driver.execute_script(f"arguments[0].scrollBy({amountRight}, {amountDown})", element)

def _image_to_base64(image_path):
    with open(image_path, 'rb') as f:
        image_data = f.read()
        encoded = base64.b64encode(image_data).decode('utf-8')
    return encoded

def take_screenshot(driver, remove=True):
    save_path = os.path.join(script_dir, 'tmp.png')
    driver.save_screenshot(save_path)
    out = _image_to_base64(save_path)
    if remove:
        os.remove(save_path)
    return out
