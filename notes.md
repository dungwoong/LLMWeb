# Selenium

- execute_script() does not persist. You must use window.var in order to create persistent variables

# TODOs

- check selenium-demo, it highlights stuff that isn't on the page. Low prio, remove those bboxes
- Try restarting if page hasn't changed in a long time

# Current Failure Modes
- Model can't see multiple webpages, so it can't tell when it's stuck
- Add like "if your output is similar to previous, try something different" to executor maybe
- The validator sometimes goes along with what the executor is writing in its logs