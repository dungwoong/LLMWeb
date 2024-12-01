from agents.compiler2_multiagent.agent import MultiAgentState, Executor, Validator
from util.webdriver import chrome_new_webdriver
from util.agent import LMModel

import time
import json
# Always run from this file, or else imports get tricky

PROGRESS_THRESHOLD = 90
PROGRESS_LOWER_THRESHOLD = 80
RESTART_THRESHOLD = 80

task = input('Enter a Task: ')
task = "Search an Xbox Wireless controller with green color and rated above 4 stars." if task == '' else task
lm_model = LMModel()
sites = {'amazon': 'https://www.amazon.com',
         'google': 'https://www.google.com'}
state = MultiAgentState(chrome_new_webdriver(), sites['google'])
executor = Executor(lm_model, state=state)
validator = Validator(task=task, state=state, lm_model=lm_model, executor=executor, loops_before_validate=3)
print('Starting...')
time.sleep(2)
should_continue = True
print(f"TASK:\n{task}\n")
n_loops = 0
n_above_lower_threshold = 0
while not validator.answer and should_continue:
    n_loops += 1
    validator.run_one_iter()
    data = validator.last_parsed_output
    print(json.dumps(data, indent=4))
    if isinstance(validator.last_parsed_output, dict):
        # no validation here for valid data types
        if data.get("progress", 0) >= PROGRESS_LOWER_THRESHOLD:
            n_above_lower_threshold += 1
        if data.get("progress", 0) >= PROGRESS_THRESHOLD:
            validator.answer = data.get("answer", "Done(No Response)")
            break
        elif data.get("shouldrestart", 0) >= RESTART_THRESHOLD:
            executor.state.restart(None)
        elif n_above_lower_threshold > 2:
            # TODO manual intervention here
            break
        executor.reinitialize(task=f"{task}\nTip: {data.get("feedback", "None")}")

    should_continue = input('Continue? Type "n" to stop') != "n"
    print('Restarting Reasoning Loop...\n\n')
print("ANSWER: ", validator.answer)
print(f'Performed {n_loops} loops')
print(f"LLM Info: {lm_model.metadata}")
# print(prompt)