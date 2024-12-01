import time
import re
import json
from selenium_tools.web_util import mark_page, type_text, scroll_window, take_screenshot
from util.webdriver import chrome_new_webdriver
from agents.compiler1.prompt import get_prompt
from dotenv import load_dotenv
import os

from langchain_openai.chat_models.base import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(script_dir, '..', '..', '.env'))
# print(os.environ['OPENAI_API_KEY'])

"""
Our initial agent will comprise of a planner and executor.

Planner updates thoughts and gives actions for the state

Executor executes every action. If successful with no message, nothing is returned.
Otherwise, return message.
"""


def parse_output(text: str):
    """
    Parses text, extracting a JSON-formatted list from the text and returning
    the relevant list, if possible
    """
    try:
        pattern = r'\{.*\}'
        match = re.search(pattern, text, re.DOTALL)
        output = json.loads(match.group())
        return output
    except:
        return None


def check_output(data):
    # not very in-depth check
    if 'thought' in data and 'nextsteps' in data and 'action' in data and isinstance(data['action'], list):
        return True
    return False


def format_output_dict_as_string(data):
    # purely for logging, etc.
    if data is None:
        return "BADLY FORMATTED"
    def format_action(x):
        if 'command' not in x:
            return f'INVALID: {x}'
        else:
            args = [f"{k}={v}" for k, v in x.items() if k != 'command']
            return f'{x["command"]} {' '.join(args)}'
    return f"PAST ACTIONS: {data.get('thought', None)}\n\nACTIONS:\n{'\n'.join([format_action(x) for x in data.get('action', [])])}\n\nNEXT STEPS: {data.get('nextsteps', None)}"


class State:
    """
    Include the state info and tools.
    """

    def __init__(self, driver, start_site):
        self.driver = driver
        self.start_site = start_site
        self.driver.get(start_site)

        self.img = None  # b64 encoded screenshot of the page
        self.elements = []  # elements returned from mark_page
        self.ans = None
        self.args_dict = {'click': self._click, 'type': self._type, 'scroll': self._scroll, 'wait': self._wait,
                          'askuser': self._ask_user, 'goback': self._go_back, 'restart': self._restart, 'answer': self._answer}

    def execute_command(self, data):
        command_str = data['command'] if isinstance(data, dict) else None
        command = self.args_dict.get(command_str, None) if command_str is not None else None
        if command is None:
            return False, 'No command given. Make sure to include a "command" key!'
        return command(data)

    def prep_browser_variables(self):
        self.elements = mark_page(self.driver)
        self.img = take_screenshot(self.driver, remove=False)

    def has_answer(self):
        return self.ans is not None

    def _get_ith_element(self, i):
        if i >= len(self.elements):
            return False, f'Index out of bounds, only {len(self.elements)} available'
        return True, self.elements[i]['element']

    def _click(self, args):
        idx = args.get('idx', None)
        if idx is None:
            return False, 'No idx provided.'

        idx_exists, element = self._get_ith_element(idx)
        if not idx_exists:
            return False, element
        try:
            element.click()
            return True, None
        except:
            return False, 'Failed to click.'

    def _type(self, args):
        idx = args.get('idx', None)
        content = args.get('content', None)
        if idx is None or content is None:
            return False, 'Invalid arguments to command.'

        idx_exists, element = self._get_ith_element(idx)
        if not idx_exists:
            return False, element

        try:
            type_text(element, content)
            return True, None
        except:
            return False, 'Failed to type.'

    def _scroll(self, args):
        idx = args.get('idx', None)
        dir = args.get('dir', None)
        if dir not in ['up', 'down']:
            return False, 'idx is none, or dir is not one of (up, down)'

        idx_exists, element = self._get_ith_element(
            idx) if isinstance(idx, int) else (True, None)
        if not idx_exists:
            return False, element

        amountDown = -400 if dir == 'up' else 400
        try:
            scroll_window(self.driver, element, amountDown=amountDown)
            return True, None
        except:
            return False, 'Failed to scroll'

    def _wait(self, args):
        time.sleep(5)
        return True, None

    def _ask_user(self, args):
        """
        Ask user a question
        """
        question = args.get('question', None)
        if question is None:
            return False, 'Question was not provided. Make sure to include "question" key.'
        answer = input(f'{question} ?> ')
        return True, answer

    def _go_back(self, args):
        self.driver.back()
        return True, None

    def _restart(self, args):
        self.driver.get(self.start_site)
        return True, None

    def _answer(self, args):
        content = args.get('content', None)
        if content is None:
            return False, 'No content. Make sure to include a "content" key!'
        self.ans = content
        return True, None


class Agent:
    def __init__(self, task, start_site="https://www.google.com/"):
        self.task = task
        self.past_observation_summary = ''
        self.past_thoughts = []
        driver = chrome_new_webdriver()
        self.state = State(driver, start_site=start_site)

        self.model = ChatOpenAI(model="gpt-4o-mini",
                                temperature=0) | StrOutputParser()

        self.last_data = None

        # debug
        self._last_response = None

    def create_prompt(self):
        self.state.prep_browser_variables()
        prompt = get_prompt(bboxes=self.state.elements, task=self.task,
                            img=self.state.img, past_outputs=self.past_observation_summary)
        return prompt

    def get_response(self, prompt):
        self._last_response = self.model.invoke(prompt)
        self.last_data = parse_output(self._last_response)

    def execute_commands(self):
        # execute commands and set in past observations.
        if not isinstance(self.last_data, dict) or 'action' not in self.last_data:
            return 'You provided invalid output. Please format using the JSON guidelines given to you.'
        
        # update thought
        if 'thought' in self.last_data:
            self.past_thoughts.append(self.last_data["thought"])

        # execute each command
        self.past_observation_summary = f'Past Actions:\n{'\n'.join(self.past_thoughts)}\nActions:\n'
        added_response = False
        execution_error = False
        for command in self.last_data['action']:
            if not execution_error:
                exit_state, response = self.state.execute_command(command)
                if response is not None:
                    self.past_observation_summary += f"{command} - {response}\n"
                    added_response = True
                execution_error = execution_error or not exit_state
            else:
                self.past_observation_summary += f"{command} - Execution halted before reaching this\n"
        if not added_response:
            self.past_observation_summary += "All actions executed successfully, no outputs.\n"
        self.past_observation_summary += f'Next Steps: {self.last_data.get('nextsteps', None)}'