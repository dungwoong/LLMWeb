from langchain_core.prompts.image import ImagePromptTemplate
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.prompts import HumanMessagePromptTemplate
from langchain_openai.chat_models.base import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.messages.human import HumanMessage
from dotenv import load_dotenv
import os
import base64

# https://platform.openai.com/docs/guides/vision?lang=python Low or high fidelity image understanding
# https://python.langchain.com/docs/how_to/multimodal_prompts/ multimodal prompts

load_dotenv('.env')
openai_api_key = os.getenv('OPENAI_API_KEY')

def image_to_base64(image_path):
    with open(image_path, 'rb') as f:
        image_data = f.read()
        encoded = base64.b64encode(image_data).decode('utf-8')
    return encoded

prompt = ChatPromptTemplate.from_messages([
    ('system', 'you are a bot that prepends every answer with the word "nong". Answer every question given.'),
    # note that eg. if you make this a question, the model will fail to realize there's 2 questions in total.
    # you should move the user image above all the questions in that case.
    MessagesPlaceholder('placeholder'),
    ('user', [{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64,{img}", "detail": "low"}}]), # low detail
    ('user', "QUESTION: what is the color of each person's hair?")
])

encoded_image = image_to_base64('res/sample_img.jpg')
model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
chain = prompt | model | StrOutputParser()
output = chain.invoke({'img': encoded_image, 'placeholder': [HumanMessage('Also, append "gong" to every answer you give.')]})
print(output)

# nong The person on the left has white or light gray hair, while the person on the right has blue hair with purple highlights. gong
