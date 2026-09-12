from openai import OpenAI


def generate(api_key, prompt, model="gpt-5.4"):
    client = OpenAI(api_key=api_key)
    response = client.responses.create(model=model, input=prompt, reasoning={"effort":"high"}, text={"verbosity":"high"})
    return response.output_text
