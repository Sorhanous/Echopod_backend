structured_prompt = f"""To ensure all projects are captured and listed in the mentions section in json, you must consider the need for a comprehensive and exhaustive list of all mentioned projects, services, or products (i.e. coins in crypto, health products, books, etc) within each category, emphasizing the importance of not missing any mentions. Some videos(transcripts) will have 40 + mentions. I am seeking detailed analysis similar to what a human expert would provide. Please ensure the analysis is exhaustive and considerate of the context provided, as this will inform significant decisions based on the transcript's content.

The transcript given to you is in the following format:

Analyze the following transcript which is in json format:

{{
  "content": [
      {{
          "duration": 2.074,
          "start": 0.33,
          "text": "You absolute piece of."
      }},
      {{
          "duration": 1.678,
          "start": 2.405,
          "text": "Yes, I'm gonna give you exactly what"
      }}
      ]
  }}

 and read all the text from all the arrays to get the transcript and generate a structured response in JSON format covering the following points. 

Ensure you provide a comprehensive and exhaustive list of all mentioned projects, services, or products (i.e. coins in crypto, health products, books, tools, important people etc) within each category mentioned, categorized by their respective topics (e.g., health, gaming, gambling, AI, or "other" if no categories apply). It's crucial that you include every mention without omission, as my requirements depend on a complete accounting of these details. My decision-making relies on this information being accurate and all-encompassing. Don't omit any names or mentions of coins products or services. i.e. If 100 are mentioend, return all 100 of them, with a short description mentoend about them in the transcript (see json below). 

- Please format the "mentions" section (remember this is just a name they dont have to be advices, just mentions) as an array under each category (or "other if no category"), ensuring no project or mention is overlooked. 

- also include the "start" time stamp you see for each item and include them in the json format shown below.
It doesnt alwasy have to be actionable advice, but all that is mentioned will go under that category in the json shown below.

- Provide a concise summary of the key points discussed - needs to understand the context of the transcript and key points.


- Detail all actionable advice or mentions given, categorized by topic (or "other"). Include each piece of advice or mention of projects, services, etc., under the corresponding category. again, It's vital that all advice or mentions are captured. Dont include things like "the internet" or "the world" or "the world's best" or "the world's worst" or "youtube" or obvious things people already know or large legacy categories like "culture" or "entertainment" or "politics" or "science" or "sports" or "technology" or "health" or "finance" or "education" or "religion" or "art, etc. If its crypto mentions, include all . 

- Analyze the overall sentiment of the transcript (the underlying emotion)
- Evaluate the reliability of the given advice in the transcript based on your knowledge, noting any misinformation or inaccuracies.

Describe the political leaning of the message, if applicable.

Please format your response as follows (make sure the json returned has no syntax issues and the parameters are in order they are shown below) - make sure each item has its own line and not grouped even if they share the same explaination. For name, correct misspelling from the transcript. In your json dont mention the word transcript instead use "the speaker" or "video", whatever else makes sense. 

Json structure/format: (note: all mentions should not include the items metioend in actionable advice section. remove dupicates. also remove any advice that is too vague and broad)

{{
  "summary": "summary of the transcript (context is needed)",
  "all mentions": {{
    "<category 1>": [
      {{
        "name": " One of the items (item1) in the list of advice or projects in category 1,
        "description": "an understandable, Full sentences (atleast 2), contextual explanation mentioned in the transcript for item 1 - must have this""
        "start_time": 38.399
      }},
      {{
        "name": " One of the items (item2) in the list of advice or projects in category 1,
        "description": "an understandable, Full sentences (atleast 2), contextual  explanation mentioned in the transcript for item 2 - must have this""
        "start_time": 40
      }}
      ...
    ],
    "<category 2>": [
      {{
        "name": " One of the items (item1) in the list of advice or projects in category 2,
        "description": " an understandable, Full sentences (atleast 2), contextual  explanation mentioned in the transcript for item 1 - must have this""
        "start_time": 67.5
      }},
      {{
        "name": " One of the items (item2) in the list of advice or projects in category 2,
        "description": "an understandable, Full sentences (atleast 2), contextual explanation mentioned in the transcript for item 2 - must have this""
        "start_time": 105
      }}
      ...
    ]
    ...
  }},
  "all actionable advices": {{
    "<category 1>": [
      {{
        "name": " One of the items (item1) in the list of advice or projects in category 1,
        "description": "an understandable, Full sentences (atleast 2), contextual explanation mentioned in the transcript for item 1 - must have this""
        "start_time": 38.399
      }},
      {{
        "name": " One of the items (item2) in the list of advice or projects in category 1,
        "description": "an understandable, Full sentences (atleast 2), contextual  explanation mentioned in the transcript for item 2 - must have this""
        "start_time": 40
      }}
      ...
    ],
    "<category 2>": [
      {{
        "name": " One of the items (item1) in the list of advice or projects in category 2,
        "description": " an understandable, Full sentences (atleast 2), contextual  explanation mentioned in the transcript for item 1 - must have this""
        "start_time": 67.5
      }},
      {{
        "name": " One of the items (item2) in the list of advice or projects in category 2,
        "description": "an understandable, Full sentences (atleast 2), contextual explanation mentioned in the transcript for item 2 - must have this""
        "start_time": 105
      }}
      ...
    ]
    ...
  }},
  "sentiment_analysis": "The overall sentiment is...",
  "reliability_score": "The reliability of the advice is...",
  "political_leaning": "The political leaning is..."
}}


Please always return Json without any syntax errors.

  """