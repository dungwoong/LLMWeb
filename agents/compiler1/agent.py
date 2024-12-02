from util.agent import LMModel, State
from util.agent import parse_output
from util.webdriver import chrome_new_webdriver
from agents.compiler1.prompt import get_prompt
from dotenv import load_dotenv
import os


"""
Our initial agent will comprise of a planner and executor.

Planner updates thoughts and gives actions for the state

Executor executes every action. If successful with no message, nothing is returned.
Otherwise, return message.
"""

class Agent:
    def __init__(self, task, start_site="https://www.google.com/"):
        self.task = task
        self.past_observation_summary = ''
        self.past_thoughts = []
        self.ans = None

        self.command_results = []
        
        # State
        driver = chrome_new_webdriver()
        self.state = State(driver, start_site=start_site)

        # Model
        self.model = LMModel()

        self.last_parsed_output = None
        self._last_response = None  # Debug

        self.args_dict = {'click': self.state.click,
                          'type': self.state.type,
                          'scroll': self.state.scroll,
                          'wait': self.state.wait,
                          'askuser': self.state.ask_user,
                          'goback': self.state.go_back,
                          'restart': self.state.restart,
                          'answer': self._answer}

    def create_prompt(self):
        """
        Take screenshot, get bboxes, and create prompt for next WebVoyager iteration
        """
        self.state.prep_browser_variables()
        prompt = get_prompt(bboxes=self.state.elements, task=self.task,
                            img=self.state.img, past_outputs=self.past_observation_summary)
        return prompt

    def get_response(self, prompt):
        """
        Prompt the LLM and parse the output
        """
        self._last_response = self.model(prompt)
        self.last_parsed_output = parse_output(self._last_response)

    def execute_commands(self):
        """
        For each item in parsed output, execute the command, get return state if necessary,
        and update past observation with previous thoughts, etc.
        """
        if not isinstance(self.last_parsed_output, dict) or 'action' not in self.last_parsed_output:
            return 'You provided invalid output. Please format using the JSON guidelines given to you.'

        # update thought
        if 'thought' in self.last_parsed_output:
            self.past_thoughts.append(self.last_parsed_output["thought"])
        
        # Execute commands and update command_results
        self.command_results = []
        execution_error = False
        for command in self.last_parsed_output['action']:
            if not execution_error:
                exit_state, response = self._execute_command(command)
                if response is not None:
                    self.command_results.append((command, response))
                else:
                    self.command_results.append((command, 'executed'))
                execution_error = execution_error or not exit_state
            else:
                # Halt execution after making one execution error
                self.command_results.append((command, 'Execution halted before reaching this'))

        # Update observation
        past_thoughts_formatted = '\n'.join([f'{i} - {thought}' for i, thought in enumerate(self.past_thoughts)])
        command_results_str = [f'{c} - {res}' for c, res in self.command_results] # format as string
        self.past_observation_summary = f'Previous Steps:\n{past_thoughts_formatted}\nActions from last step:\n{"\n".join(command_results_str) if command_results_str else "No Commands Executed"}'

    def _execute_command(self, data):
        command_str = data['command'] if isinstance(data, dict) else None
        command = self.args_dict.get(
            command_str, None) if command_str is not None else None
        if command is None:
            return False, 'No command given. Make sure to include a "command" key!'
        return command(data)
    
    def _answer(self, args):
        content = args.get('content', None)
        if content is None:
            return False, 'No content. Make sure to include a "content" key!'
        self.ans = content
        return True, None
