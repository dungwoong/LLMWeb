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

def format_output_dict_as_string(data):
    # purely for logging, etc.
    if data is None:
        return "Data was badly formatted."

    def format_action(x):
        if 'command' not in x:
            return f'INVALID COMMAND: {x}'
        else:
            args = [f"{k}={v}" for k, v in x.items() if k != 'command']
            return f'{x["command"]} {' '.join(args)}'
    return f"PAGE: {data.get('page', None)}\n\nTHOUGHT: {data.get('thought', None)}\n\nACTIONS:\n{'\n'.join([format_action(x) for x in data.get('action', [])])}"


class Agent:
    def __init__(self, task, start_site="https://www.google.com/"):
        self.task = task
        self.past_observation_summary = ''
        self.past_thoughts = []
        self.ans = None
        
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

        # execute each command
        past_thoughts_formatted = '\n'.join([f'{i} - {thought}' for i, thought in enumerate(self.past_thoughts)])
        self.past_observation_summary = f'Previous Steps:\n{past_thoughts_formatted}\nActions from last step:\n'
        
        response_added = False
        execution_error = False
        for command in self.last_parsed_output['action']:
            if not execution_error:
                exit_state, response = self._execute_command(command)
                if response is not None:
                    self.past_observation_summary += f"{command} - {response}\n"
                else:
                    self.past_observation_summary += f"{command} - Executed"
                response_added = True
                execution_error = execution_error or not exit_state
            else:
                self.past_observation_summary += f"{command} - Execution halted before reaching this\n"
        if not response_added:
            self.past_observation_summary += "All actions executed successfully, no outputs.\n"

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
