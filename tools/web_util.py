import os

script_dir = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(script_dir, 'mark_page.js')) as f:
    mark_page_script = f.read()

def mark_page(driver):
    driver.execute_script(mark_page_script)
    out = driver.execute_script("return markPage();")
    return out