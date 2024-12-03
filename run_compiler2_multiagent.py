from agents.compiler2_multiagent.agent import MultiAgentState, Executor, Validator
from util.webdriver import chrome_new_webdriver
from util.agent import LMModel

import time
import json
# Always run from this file, or else imports get tricky

PROGRESS_THRESHOLD = 90
PROGRESS_LOWER_THRESHOLD = 80
RESTART_THRESHOLD = 80

# basic starting points
SITES = {'amazon': 'https://www.amazon.com',
         'google': 'https://www.google.com'}


task = input('Enter a Task: ')

# Get necessary objects
lm_model = LMModel()
state = MultiAgentState(chrome_new_webdriver(), SITES['google'])
executor = Executor(lm_model, state=state)
validator = Validator(task=task, state=state, lm_model=lm_model, executor=executor, loops_before_validate=3)

print('Starting...\n\n')
time.sleep(2)

should_continue = True
n_loops = 0
n_above_lower_threshold = 0
while not validator.answer and should_continue:
    n_loops += 1
    print(f"ITERATION {n_loops} ##########################################")
    
    # Run executor/validator loop
    for item in validator.run_one_iter():
        print(item)
    
    data = validator.last_parsed_output

    # Figure out what to do based on validator output
    if isinstance(data, dict):
        # no input validation for last parsed output
        if data.get("progress", 0) >= PROGRESS_LOWER_THRESHOLD:
            n_above_lower_threshold += 1
        if data.get("progress", 0) >= PROGRESS_THRESHOLD:
            print("\nFinishing due to high progress...")
            validator.answer = data.get("answer", "Done(No Response)")
            break
        elif data.get("shouldrestart", 0) >= RESTART_THRESHOLD:
            print("\nRestarting due to high shouldrestart score...")
            executor.state.restart(None)
        elif n_above_lower_threshold >= 2:
            # manual intervention
            validator.manual_feedback = input('Give Feedback To the Validator: ')
        executor.task = f"{task}\nTip: {data.get("feedback", "None")}"

    should_continue = input('Continue(y/n)? ') != "n"


print("ANSWER: ", validator.answer)
print(f'Performed {n_loops} loops')
print(f"LLM Info: {lm_model.metadata}")

cost_4o_mini = lm_model.metadata['input_tokens'] * (0.15/1000000) + lm_model.metadata['output_tokens'] * (0.6/1000000)
print(f"GPT-4o-mini cost: ${cost_4o_mini}")