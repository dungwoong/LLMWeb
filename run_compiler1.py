from agents.compiler1.agent import Agent, format_output_dict_as_string

# Always run from this file, or else imports get tricky

task = input('Enter a Task: ')
task = "Go on youtube and play me Kanye West Homecoming" if task == '' else task
agent = Agent(task=task)
should_continue = True
print(f"TASK:\n{task}\n\nStarting...\n")
n_loops = 0
while not agent.ans and should_continue:
    n_loops += 1
    prompt = agent.create_prompt()
    agent.get_response(prompt)
    print(format_output_dict_as_string(agent.last_parsed_output))
    should_continue = input('Continue? Type "n" to stop') != "n"
    print('Executing...\n\n')
    agent.execute_commands()
    # print(agent.past_observation_summary)
    print('Done\n\n')
print("ANSWER: ", agent.ans)
print(f'Performed {n_loops} loops')
print(f"LLM Info: {agent.model.metadata}")
# print(prompt)