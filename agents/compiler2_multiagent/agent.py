import json
import time
import re

from selenium_tools.web_util import mark_page, unmark_page, take_screenshot
from util.agent import State, LMModel, parse_output
from agents.compiler2_multiagent.prompt import get_executor_prompt, get_validator_prompt

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
    return f"Thought: {data.get('thought', None)}\n\nActions:\n{'\n'.join([format_action(x) for x in data.get('action', [])])}"


def get_evaluation(validator_data):
    s = "EVAL ###################################################\n\n"
    if not isinstance(validator_data, dict):
        s += "\tInvalid Response Given By LLM"
        return s
    s += f"Overview:\n\t{validator_data.get('description', 'None')}\n"
    criteria = validator_data.get("completioncriteria", [])
    if isinstance(criteria, list):
        s += f"Completion criteria:\n{'\n'.join([f"\t{c}" for c in criteria])}\n"
    else:
        s += f"Completion criteria:\n\t{criteria}\n"
    s += f"Feedback:\n\t{validator_data.get("feedback", "None")}\n\n"
    s += f"Progress: {validator_data.get("progress", "None")}% | ShouldRestart: {validator_data.get("shouldrestart", "None")}%\n"
    if validator_data.get("answer", "") != "":
        s += f"\nANSWER: {validator_data.get("answer")}"
    return s.strip()
    


class MultiAgentState(State):
    def __init__(self, driver, start_site):
        super().__init__(driver, start_site)

    def prep_browser_variables(self, **kwargs):
        mark = kwargs.get('mark', True)
        if mark:
            self.elements = mark_page(self.driver)
        else:
            unmark_page(self.driver)
            self.elements = []
        self.img = take_screenshot(self.driver, remove=False)


class Executor:
    def __init__(self, lm_model: LMModel, state: MultiAgentState):
        """
        Executor agent, much like in compiler1. However, LLM and state objects are now shared between many agents.
        """

        self.model = lm_model
        self._last_response = None
        self.last_parsed_output = None
        self.done = False
        self.past_thoughts = []
        self.command_results = []
        self.past_observation_summary = ''
        self.task = ''

        self.state = state
        self.args_dict = {'click': self.state.click,
                          'type': self.state.type,
                          'scroll': self.state.scroll,
                          'finish': self._finish}
    
    def run_one_iter(self):
        """
        Runs one iteration of creating/responding to a prompt, then executing appropriate commands
        """
        prompt = self._create_prompt()
        self._get_response(prompt)
        yield format_output_dict_as_string(self.last_parsed_output)
        yield '\nExecuting Commands...'
        self._execute_commands()
        yield '\n'.join([f'{format_action(c)} - {r}' for c, r in self.command_results]) if self.command_results else '\tNone'
        time.sleep(2)

    def _create_prompt(self):
        """
        Take screenshot, get bboxes, and create prompt for next WebVoyager iteration
        """
        self.state.prep_browser_variables(mark=True)
        prompt = get_executor_prompt(bboxes=self.state.elements, task=self.task,
                                     img=self.state.img, past_outputs=self.past_observation_summary)
        return prompt
    
    def _get_response(self, prompt):
        """
        Prompt the LLM and parse the output
        """
        self._last_response = self.model(prompt)
        self.last_parsed_output = parse_output(self._last_response)


    def _execute_commands(self):
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
    
    # def _execute_commands(self):
    #     """
    #     For each item in parsed output, execute the command, get return state if necessary,
    #     and update past observation with previous thoughts, etc.

    #     past_observation_summary will contain a list of previous thoughts,
    #     and a list of commands taken from the last step and their result
    #     """
    #     if not isinstance(self.last_parsed_output, dict) or 'action' not in self.last_parsed_output:
    #         return 'You provided invalid output. Please format using the JSON guidelines given.'

    #     # update thought
    #     if 'thought' in self.last_parsed_output:
    #         self.past_thoughts.append(self.last_parsed_output["thought"])

    #     # execute each command
    #     past_thoughts_formatted = '\n'.join([f'{i} - {thought}' for i, thought in enumerate(self.past_thoughts)])
    #     self.past_observation_summary = f'Previous Thoughts:\n{past_thoughts_formatted}\nActions from last step:\n'
        
    #     response_added = False
    #     execution_error = False
    #     for command in self.last_parsed_output['action']:
    #         if not execution_error:
    #             exit_state, response = self._execute_command(command)
    #             if response is not None:
    #                 self.past_observation_summary += f"{command} - {response}\n"
    #             else:
    #                 self.past_observation_summary += f"{command} - Executed"
    #             response_added = True
    #             execution_error = execution_error or not exit_state
    #         else:
    #             self.past_observation_summary += f"{command} - Execution halted before reaching this\n"
    #     if not response_added:
    #         self.past_observation_summary += "All actions executed successfully, no outputs.\n"

    def _execute_command(self, data):
        command_str = data['command'] if isinstance(data, dict) else None
        command = self.args_dict.get(
            command_str, None) if command_str is not None else None
        if command is None:
            return False, 'No command given. Make sure to include a "command" key!'
        return command(data)

    def _finish(self, args):
        self.done = True
        return True, None

class Validator:
    def __init__(self, task: str, state: MultiAgentState, lm_model: LMModel, executor: Executor, loops_before_validate=2):
        self.task = task
        self.state = state
        self.steps = []
        self.answer = None
        self.model = lm_model
        self.manual_feedback = ''
        self.executor = executor
        self.executor.task = self.task
        self.loops_before_validate = loops_before_validate

        self._last_response, self.last_parsed_output = None, None

    def run_one_iter(self):
        """
        Runs one iteration.

        Runs the executor self.loops_before_validate times, or until a 'finish' command is issued.
        Then, validates the outputs, storing self.last_parsed_output
        """
        self.executor.done = False
        for i in range(self.loops_before_validate):
            yield from self.executor.run_one_iter()
            if self.executor.done and i < self.loops_before_validate - 1:
                yield '\nFinish command issued, breaking loop...\n'
                break
        yield from self.evaluate()

    def evaluate(self):
        prompt = self._create_prompt()
        self._get_response(prompt)
        yield get_evaluation(self.last_parsed_output)


    def _create_prompt(self):
        """
        Take screenshot
        """
        self.state.prep_browser_variables(mark=False)
        # log = '\n'.join([f'{i}. {item}' for i, item in enumerate(self.executor.past_thoughts)])
        log = f'HUMAN FEEDBACK, FOLLOW CLOSELY: {self.manual_feedback}' # don't add past steps, it can reinforce the reasoning of the validator which is bad
        prompt = get_validator_prompt(img=self.state.img, log=log, task=self.task)
        return prompt
    
    def _get_response(self, prompt):
        """
        Prompt the LLM and parse the output
        """
        self._last_response = self.model(prompt)
        self.last_parsed_output = parse_output(self._last_response)
