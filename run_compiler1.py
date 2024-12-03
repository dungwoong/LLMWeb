import time

from agents.compiler1.agent import Agent

"""
Runs the agent in agents/compiler1.

This consists of a single agent that runs in a modified ReAct loop, inspired by the LLMCompiler paper.

In each iteration, the model can pick multiple commands to execute, based on the provided context.
"""

def format_action(x):
    if 'command' not in x:
        return f'\tINVALID COMMAND: {x}'
    else:
        args = [f"{k}={v}" for k, v in x.items() if k != 'command']
        return f'\t{x["command"]} {' '.join(args)}'

def format_output_dict_as_string(data):
    # purely for logging, etc.
    if data is None:
        return "Data from LLM was badly formatted."
    return f"Current Page: {data.get('page', None)}\n\nThought: {data.get('thought', None)}\n\nActions:\n{'\n'.join([format_action(x) for x in data.get('action', [])])}"

print('RUNNING COMPILER V1(Single Agent)')
task = input('Enter a Task: ')
if task == '':
    raise ValueError('Please provide a task.')

agent = Agent(task=task)
print(f"Starting...\n\n")
time.sleep(2)

should_continue = True
n_loops = 0
while not agent.ans and should_continue:
    print(f"ITERATION {n_loops+1} ##########################################\n")
    n_loops += 1

    # Query LLM
    prompt = agent.create_prompt()
    agent.get_response(prompt)
    print(format_output_dict_as_string(agent.last_parsed_output), '\n')
    
    # Execute the commands
    should_continue = input('Continue After this iteration?(y/n)?') != "n"
    agent.execute_commands()
    
    print('\nExecution Results:')
    print('\n'.join([f'{format_action(c)} - {r}' for c, r in agent.command_results]) if agent.command_results else '\tNone')


print("\n###############################################################\n")
print("ANSWER: ", agent.ans)
print(f'Performed {n_loops} loops')
print(f"LLM Info: {agent.model.metadata}")
cost_4o_mini = agent.model.metadata['input_tokens'] * (0.15/1000000) + agent.model.metadata['output_tokens'] * (0.6/1000000)
print(f"GPT-4o-mini cost: {cost_4o_mini}")
