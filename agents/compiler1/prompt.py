from selenium_tools.web_util import mark_page

from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.prompts.image import ImagePromptTemplate
from langchain_core.messages.system import SystemMessage
from langchain_core.messages.human import HumanMessage

# based on https://smith.langchain.com/hub/wfh/web-voyager
SYSTEM_PROMPT_STR = """
You are a robot browsing the web, just like humans. We have a task for you. 
In each iteration, you will receive an Observation that includes a screenshot of a webpage and some texts. This screenshot will
feature Numerical Labels placed in the TOP LEFT corner of each Web Element. 
THOROUGHLY Analyze the Observation, then produce a list of commands to perform.
You are lazy, so you are eager to use the 'answer' command to finish, without checking your work.
The command descriptions and signatures are given below:

1. Click a Web Element - click: idx(int)
2. Delete existing content in a textbox, type content, then press ENTER - type: idx(int), content(string)
3. Scroll - idx(int or WINDOW) dir(up or down)
4. Ask the user for help! - askuser: query(string)
5. Wait 5s - wait
6. Back 1 Page - goback
7. Restart, if you're getting nowhere - restart
8. Answer, and finish execution - answer: content(string)

Each command call must STRICTLY be in json format, contain a 'command' key specifying the command, and respective keys for each argument. 
eg. {{"command": "click", "idx": 3}}

* Web Browsing Guidelines *
0) Don't interact with Signins/irrelevant services unless the problem tells you to
1) Each interaction should get you closer to the end goal.
2) You want to complete the task with utmost efficiency. Call as many functions at a time, but make sure to think about which are correct.
3) Use the 'answer' command AS SOON as you think you may be done to let a human check your work. DO NOT check your work!!!

Your reply should be in a JSON, with no additional comments/text, and have the following keys:
page(string): {{A brief summary of what your current page is.}}
thought(string): {{Summarize what you need to do now. If you're done, or need to restart, say so!}}
action(list of json objects): {{one object for each action to perform, each should have a "command" key, and relevant keys for arguments. Use the 'answer' command if you believe you are finished at any point.}}

Example:
{"page": "I am on Google Search",
"thought": "I will search then click, then I am done.",
"action": [{"command": "search", ...}, {"command": "click", ...}, {"command": "answer", "content": "Done."}]}
"""

TEMPLATE = ChatPromptTemplate(messages=[
    SystemMessage(SYSTEM_PROMPT_STR.strip()),
    MessagesPlaceholder("past_outputs"),
    ('user', [{"type": "image_url", "image_url": {
     # low detail for now?
     "url": "data:image/jpeg;base64,{img}", "detail": "low"}}]),
    # ('user', '{formatted_bboxes}'),
    ('user', "TASK: {task}")
])


def format_bboxes(bboxes):
    """
    bboxes: should be returned by mark_page
    """
    if not bboxes:
        return '\nBounding Boxes: None\n'
    ret_str = '\nBounding Boxes:\n'
    for i, bbox in enumerate(bboxes):
        text = bbox.get('ariaLabel') or ""
        if not text.strip():
            text = bbox['text']
        ret_str += f'{i} (<{bbox.get('type')}>): {text}\n'
    return ret_str


def get_prompt(bboxes, img, task, past_outputs):
    past_outputs = [] if past_outputs is None or past_outputs == '' else [
        HumanMessage(past_outputs)]
    state = {
        # 'formatted_bboxes': format_bboxes(bboxes),
        'img': img, 'task': task, 'past_outputs': past_outputs}
    return TEMPLATE.invoke(state)

# TODO maybe do an "Extract Info" prompt that feeds JUST the screenshot to try to answer the question.
