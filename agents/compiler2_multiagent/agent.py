import json
import time

from selenium_tools.web_util import mark_page, unmark_page, take_screenshot
from util.agent import State, LMModel, parse_output
from agents.compiler2_multiagent.prompt import get_executor_prompt, get_manager_prompt, get_validator_prompt


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
        self.model = lm_model
        self._last_response = None
        self.last_parsed_output = None
        self.done = False
        self.past_thoughts = []
        self.past_observation_summary = ''
        self.task = ''

        self.state = state
        self.args_dict = {'click': self.state.click,
                          'type': self.state.type,
                          'scroll': self.state.scroll,
                          'finish': self._finish}

    def reinitialize(self, task):
        self.task = task
        self._last_response = None
        self.last_parsed_output = None
        self.done = False
        self.past_thoughts = []
        self.past_observation_summary = ''
    
    def run_one_iter(self):
        prompt = self._create_prompt()
        self._get_response(prompt)
        print(json.dumps(self.last_parsed_output, indent=4))
        self._execute_commands()
        time.sleep(2)

    def _finish(self, args):
        self.done = True
        return True, None

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
            return 'You provided invalid output. Please format using the JSON guidelines given.'

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

class Validator:
    def __init__(self, task: str, state: MultiAgentState, lm_model: LMModel, executor: Executor, loops_before_validate=2):
        self.task = task
        self.state = state
        self.steps = []
        self.answer = None
        self.model = lm_model
        self.executor = executor
        self.executor.reinitialize(self.task)
        self.loops_before_validate = loops_before_validate

        self._last_response, self.last_parsed_output = None, None

    def run_one_iter(self):
        self.executor.done = False
        for _ in range(self.loops_before_validate):
            self.executor.run_one_iter()
            if self.executor.done:
                print('Executor finished, breaking loop...')
                break
        prompt = self._create_prompt()
        self._get_response(prompt)


    def _create_prompt(self):
        """
        Take screenshot and add steps in
        """
        self.state.prep_browser_variables(mark=False)
        # log = '\n'.join([f'{i}. {item}' for i, item in enumerate(self.executor.past_thoughts)])
        log = ''
        prompt = get_validator_prompt(img=self.state.img, log=log, task=self.task)
        return prompt
    
    def _get_response(self, prompt):
        """
        Prompt the LLM and parse the output
        """
        self._last_response = self.model(prompt)
        self.last_parsed_output = parse_output(self._last_response)


class Manager:
    def __init__(self, task: str, state: MultiAgentState, lm_model: LMModel, executor: Executor):
        self.task = task
        self.state = state
        self.steps = []
        self.model = lm_model
        self.ans = None

        self.last_parsed_output = None
        self._last_raw_output = None

        self.executor = executor

        self.args_dict = {'instruct': self._instruct,
                          'askuser': self.state.ask_user,
                          'restart': self.state.restart,
                          'answer': self._answer}
        
    def run_one_iter(self, verbose=False):
        prompt = self._create_prompt()
        self._get_response(prompt)
        if verbose:
            print(json.dumps(self.last_parsed_output))
            if input('Continue? y/n') == 'n':
                return
        self._execute_next_command()

    def format_steps(self):
        ret = 'STEPS:\n'
        if not self.steps:
            ret += 'No steps yet\n'
            return
        for step in self.steps:
            if 'command' not in step:
                ret += f'[INVALID]: {step}\n'
                continue
            step_description = ''
            if step.get('completed', False):
                step_description += '[COMPLETED] '
            step_description += step.get('command') + ' '
            step_description += ' '.join([f'{k}={v}' for k, v in step.items() if k not in ('command', 'reason', 'completed')])
            step_description += ' - ' + step.get('reason', 'no reason provided')
            step_description += '\n'
            ret += step_description
        return ret.strip()
        
    def _create_prompt(self):
        """
        Take screenshot and add steps in
        """
        self.state.prep_browser_variables(mark=False)
        prompt = get_manager_prompt(img=self.state.img, past_thoughts=self.format_steps(), task=self.task)
        return prompt
    
    def _get_response(self, prompt):
        """
        Prompt the LLM and parse the output
        """
        self._last_raw_output = self.model(prompt)
        self.last_parsed_output = parse_output(self._last_raw_output)

    def _instruct(self, args):
        # instruct executor to do something with a budget
        loops = min(args.get('nloops', 1), 2)
        instruction = args.get('instruction', None)
        if instruction is None:
            return False, 'No instruction provided with "instruction" key'
        
        self.executor.reinitialize(instruction)
        for _ in range(loops):
            if self.executor.done:
                break
            self.executor.run_one_iter()
        return True, None
    
    def _answer(self, args):
        self.ans = args.get('content', 'No Response')
        return True, None
    
    def _execute_next_command(self):
        # rewrite steps
        self.steps = list(filter(lambda x: x.get('completed', False), self.steps))
        if self.last_parsed_output is None or 'commands' not in self.last_parsed_output:
            return
        
        self.steps += self.last_parsed_output['commands'] # add new commands

        # execute the next incomplete command
        for step in self.steps:
            if step.get('completed', False):
                continue
            self._execute_command(step)
            break

    def _execute_command(self, data):
        if data.get('completed', False):
            return
        command_str = data['command'] if isinstance(data, dict) else None
        command = self.args_dict.get(
            command_str, None) if command_str is not None else None
        if command is None:
            return False, 'No command given. Make sure to include a "command" key!'
        data['completed'] = True
        _, response = command(data)
        data['output'] = response

