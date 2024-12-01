# Selenium

- execute_script() does not persist. You must use window.var in order to create persistent variables

# TODOs

- clean up code
- make a script that better reports what's happening
- check selenium-demo, it highlights stuff that isn't on the page. Low prio, remove those bboxes
- Try restarting if page hasn't changed in a long time
- WRITE DOWN what strings are being sent where in the multiagent

# Current Failure Modes
- work on memory, either using screenshots, or updating scratchpad better.
- Model can't see multiple webpages, so it can't tell when it's stuck
- Add like "if your output is similar to previous, try something different" to executor maybe
- The validator sometimes goes along with what the executor is writing in its logs