# Overview

A reimplementation/potential enhancement of the [WebVoyager](https://arxiv.org/abs/2401.13919) paper.

## Main issues found
These issues were found when testing the original prompt using GPT-4o-mini. Note that using GPT-4o may solve some of these. I chose a smaller model as there is more potential for fine-tuning, etc. Larger models will not always be the answer.

- The model doesn't correctly identify when to stop, and constantly clicks random elements
- Pragmatic misunderstanding, e.g. if we ask a model to play a youtube video, pulling it up is sufficient for completing the task. However, the model often wants to ensure that the video is playing, wasting API calls to do so.
- Lack of visibility for smaller elements causes the model to miss out on visual information
- Inefficiency, as only one action can be executed per iteration of the model.
- Lack of reasoning by the model, making it difficult to understand complex webpages(e.g. to reason that popups could contain info when clicked)
- Practically, we don't want this model to run unsupervised, or else it can waste API calls if it gets stuck.

## Main changes
- Replaced ReAct prompting with an [LLMCompiler](https://arxiv.org/abs/2312.04511) method that allows for multiple function calls per LLM invocation.
- Modified prompts to encourage answering as soon as possible.
- Removed original numeric labels on image. Seems like appending label descriptions to text is already enough.
- Added a multi-agent setup with a Validator and Executor, to try better validating and add better human intervention.

## Running

These files are all configured for windows. Some requirements are in `requirements.txt`.

- Single-Agent Demo: `python run_compiler1.py`
- Multi-Agent Demo: `python run_compiler2_multiagent.py`

## How does the code work?

- How do we interact with OpenAI and encode images? `demo_chatopenai.py`
- How do we use Selenium? `demo_selenium.py`