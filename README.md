# Overview

An autonomous agent that can browse the web and perform tasks given by the user. Uses MultiModal LLMs and connects them to Selenium, allowing them to browse Chrome.

This is a reimplementation/potential enhancement of the [WebVoyager](https://arxiv.org/abs/2401.13919) paper.

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

## Next Steps
- Create new benchmark tasks. The ones given in the WebVoyager repo are quite simple, and do not require much reasoning/parallel function calling. eg. Finding convocation date at U of T, applying autonomously to a job
- Create a new dataset of reasoning tasks for fine-tuning. This dataset should require a pragmatic understanding of instructions, and require the LLM to determine if it's completing an underlying task rather than follow instructions blindly.
- Evaluate new agents on benchmarks given in WebVoyager paper.

## Running

These files are all configured for windows. Some requirements are in `requirements.txt`. Make sure to put OPENAI_API_KEY in a `.env` file.

- Single-Agent Demo: `python run_compiler1.py`
- Multi-Agent Demo: `python run_compiler2_multiagent.py`

## Sample Outputs

```
TASK: play ma meilleure ennemi youtube video

ITERATION 1 ##########################################

Current Page: I am on the Google homepage.

Thought: I need to search for the 'ma meilleure ennemi' YouTube video.

Actions:
        type idx=8 content=ma meilleure ennemi YouTube video
        click idx=13
        answer content=Done.

Execution Results:
        type idx=8 content=ma meilleure ennemi YouTube video - executed
        click idx=13 - Failed to click.
        answer content=Done. - Execution halted before reaching this
ITERATION 2 ##########################################

Current Page: I am on a Google search results page for 'ma meilleure ennemi YouTube video'.

Thought: I need to click on the video link to play it.

Actions:
        click idx=15
        answer content=Done.

Execution Results:
        click idx=15 - executed
        answer content=Done. - executed

###############################################################

ANSWER:  Done.
Performed 2 loops
LLM Info: {'input_tokens': 7361, 'output_tokens': 152, 'total_tokens': 7513}
GPT-4o-mini cost: 0.00119535
```

## How does the code work?

- How do we interact with OpenAI and encode images? `demo_chatopenai.py`
- How do we use Selenium? `demo_selenium.py`