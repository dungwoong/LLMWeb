import time
from util.webdriver import get_driver
from tools.web_util import mark_page

driver = get_driver()

# Fetch a page
driver.get("https://www.cs.toronto.edu/~kianoosh/courses/csc309/")

# mark the page
out = mark_page(driver)
for i in range(10):
    out[i % 3]['element'].click()
    time.sleep(1)
driver.quit()