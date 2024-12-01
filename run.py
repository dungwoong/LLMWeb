from agents.compiler1.agent import Agent, format_output_dict_as_string

# Always run from this file, or else imports get tricky

task = "Go on youtube and play me Kanye West Homecoming"
agent = Agent(task=task)
print(f"TASK:\n{task}\n\nStarting...\n")
n_loops = 0
while not agent.state.has_answer():
    n_loops += 1
    prompt = agent.create_prompt()
    agent.get_response(prompt)
    print(format_output_dict_as_string(agent.last_data))
    print('Executing...\n\n')
    agent.execute_commands()
    # print(agent.past_observation_summary)
    input('Continue?')
    print('Restarting Reasoning Loop...\n\n')
print("ANSWER: ", agent.state.ans)
print(f'Performed {n_loops} loops')
# print(prompt)