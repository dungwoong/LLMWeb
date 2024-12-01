import time
from util.webdriver import chrome_new_webdriver, chrome_remote_debug_webdriver
from selenium_tools.web_util import mark_page, unmark_page, type_text, take_screenshot, scroll_window

driver = chrome_new_webdriver()

def get_element(out, idx):
    return out[idx]['element']

# Fetch a page
driver.get("https://www.youtube.com")

# Look for search bar
out = mark_page(driver)
search_bar = get_element(out, 2)
type_text(search_bar, 'ma meilleur ennemi')
time.sleep(1)
search_button = get_element(out, 3)
search_button.click()
time.sleep(1)

# Look for correct video in the search results.
out = mark_page(driver)
video = None
for element in out:
    # aria-label helps screen-readers attach a label to HTML elements, these are often descriptive
    if "Ma Meilleure Ennemie" in element['ariaLabel'] and 'Riot Games Music' in element['ariaLabel']:
        video = element['element']
        break
if video is None:
    print("Could not find video.")
else:
    # Play the video
    video.click()
    unmark_page(driver)
    take_screenshot(driver)
    # input('Type any key to finish')

# don't call driver.quit() + options(detach, True) ==> browser stays open
# still a little messy as the output will print to console even AFTER the script is run, but we'll use it for now
# driver.quit()