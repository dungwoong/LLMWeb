from typing import List, Tuple, Optional

from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.prompts.image import ImagePromptTemplate
from langchain_core.messages.system import SystemMessage

# based on https://smith.langchain.com/hub/wfh/web-voyager
SYSTEM_PROMPT_STR = """
Imagine you are a robot browsing the web, just like humans. Now you need to complete a task. In each iteration, you will receive an Observation that includes a screenshot of a webpage and some texts. This screenshot will
feature Numerical Labels placed in the TOP LEFT corner of each Web Element. 
Carefully analyze the visual information to identify the Numerical Label corresponding to the Web Element that requires interaction, then follow
the guidelines and draft a list of commands to perform:

1. Click a Web Element.
2. Delete existing content in a textbox and then type content.
3. Scroll up or down.
4. Wait
5. Go back
7. Return to google to start over.
8. Respond with the final answer

Each command should STRICTLY follow the format:
- Click [Numerical_Label] 
- Type [Numerical_Label]; [Content] 
- Scroll [Numerical_Label or WINDOW]; [up or down] 
- Wait 
- GoBack
- Google
- ANSWER; [content]

Key Guidelines You MUST follow:
* Action guidelines *
1) Commands will be executed in the order that you provide them. Draft commands to make maximal progress on completing the task.
2) When clicking or typing, ensure to select the correct bounding box.
3) Numeric labels lie in the top-left corner of their corresponding bounding boxes and are colored the same.

* Web Browsing Guidelines *
1) Don't interact with useless web elements like Login, Sign-in, donation that appear in Webpages
2) Select strategically to minimize time wasted.

Your reply should be in a JSON and have the following keys:
Thought(string): {{Your brief thoughts (briefly summarize the info that will help ANSWER)}}
Actions(list of strings): {{one string for each action to perform}} 

Then the User will provide:
Observation: {{A labeled screenshot Given by User}}
"""

template = ChatPromptTemplate(messages=[
    SystemMessage(SYSTEM_PROMPT_STR.strip()),
    MessagesPlaceholder("past_outputs"),
])