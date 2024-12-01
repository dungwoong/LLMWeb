import re
import json
import os
from dotenv import load_dotenv

from langchain_openai.chat_models.base import ChatOpenAI
from selenium_tools.web_util import mark_page, scroll_window, take_screenshot, type_text


import time

script_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(script_dir, '..', '.env'))


class State:
    """
    Webdriver state info, and tools to use
    """

    def __init__(self, driver, start_site):
        self.driver = driver
        self.start_site = start_site
        self.driver.get(start_site)

        self.img = None  # b64 encoded screenshot of the page
        self.elements = []  # elements returned from mark_page

    def prep_browser_variables(self, **kwargs):
        self.elements = mark_page(self.driver)
        self.img = take_screenshot(self.driver, remove=False)

    def _get_ith_element(self, i):
        if i >= len(self.elements):
            return False, f'Index out of bounds, only {len(self.elements)} available'
        return True, self.elements[i]['element']

    def click(self, args):
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

    def type(self, args):
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

    def scroll(self, args):
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

    def wait(self, args):
        time.sleep(5)
        return True, None

    def ask_user(self, args):
        """
        Ask user a question
        """
        question = args.get('question', None)
        if question is None:
            return False, 'Question was not provided. Make sure to include "question" key.'
        answer = input(f'ANSWER THIS: {question} ?> ')
        return True, answer

    def go_back(self, args):
        self.driver.back()
        return True, None

    def restart(self, args):
        self.driver.get(self.start_site)
        return True, None


class LMModel:
    """
    LMM Model, tracks usage metadata
    """

    def __init__(self):
        self.model = ChatOpenAI(model="gpt-4o-mini",
                                temperature=0)
        self.metadata = {'input_tokens': 0,
                         'output_tokens': 0, 'total_tokens': 0}

    def _update_metadata(self, metadata):
        for key in self.metadata:
            # error if any keys don't exist
            self.metadata[key] += metadata[key]

    def __call__(self, prompt):
        output = self.model.invoke(prompt)
        self._update_metadata(output.usage_metadata)
        return output.content


def parse_output(text: str):
    """
    Parses text, extracting a JSON object from the text and returning
    the relevant list, if possible
    """
    try:
        pattern = r'\{.*\}'
        match = re.search(pattern, text, re.DOTALL)
        output = json.loads(match.group())
        return output
    except:
        return None