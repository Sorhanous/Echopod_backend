# Here I will create multiple prompts for the OpenAI API to use based on different scenarios
structured_health_prompt = f"""
***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS ABOVE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT.***

I: the video transcript is about health, wellness, medical treatments, diets, supplements, exercises, mental health, health-related products, or services, etc. Ensure all topics are captured and listed in the mentions section in JSON, (including the total number mentioned). You must return a comprehensive (include ALL) and exhaustive list of ALL mentioned health-related topics, treatments, products, exercises, diets, supplements, emphasizing the importance of not missing any mentions.

Some videos(transcripts) will have numerous mentions. I am seeking detailed analysis similar to what a human expert would provide. Please ensure the analysis is exhaustive and considerate of the context provided, as this will inform significant decisions based on the transcript's content. For any name you mention, feel free to add more useful facts you know about the health topic, treatment, or product.

-E: The transcript given to you is in the following format, Analyze the following:

{{
  "content": [
      {{
          "duration": 2.074,
          "start": 0.33,
          "text": "Introducing a revolutionary new diet."
      }},
      {{
          "duration": 1.678,
          "start": 2.405,
          "text": "The benefits of meditation for mental health"
      }}, 
      .
      .
      .
      .
      ]
  }}

and read all the text from all the arrays to get the transcript and generate a structured response in JSON format (format is shown below) covering the following points:

-A: Ensure you provide a comprehensive and exhaustive list of all mentioned health projects, services, or products within each category mentioned, categorized by their respective topics (e.g., diet, exercise, mental health, supplements, treatments, or "other" if no categories apply). It's crucial that you include every mention without omission, as my requirements depend on a complete accounting of these details. My decision-making relies on this information being accurate and all-encompassing. Don't omit any names or mentions of treatments, products, or services. i.e. If numerous are mentioned, return all of them, with a short description mentioned about them in the transcript (see json below).

-B: also include the "start" time stamp you see for each item and include them in the json format shown below. It doesn't always have to be actionable advice, but all that is mentioned will go under that category in the json shown below.

-C: "Summary": Provide a concise summary of the key points discussed - needs to understand the context of the transcript and key points. It needs to make sense without having to research the idea further. make this a paragraph long.

-D: Detail all actionable advice or mentions given, categorized by topic (or "other" if no categories are appropriate). Include each piece of advice or mention of treatments, services, etc., under the corresponding category. again, It's vital that all advice or mentions are captured.

-E: Analyze the overall sentiment of the transcript (the underlying emotion) in one word
-F: Evaluate the reliability of the given advice in the transcript based on your knowledge, noting any misinformation or inaccuracies. give it a score on a scale of 1 to 10, where 1 is the worst (not reliable at all) and 10 is very reliable.

-G: Describe the political leaning of the message, if applicable. if none, return null.

-X: Please format your response as follows (make sure the json returned has no syntax issues and the parameters are in order they are shown below) - make sure each item has its own line and not grouped with other items in the same line. each item is one element in the array returned. even if they share the same explanation.

-Y: For "name", correct misspelling from the transcript if you see fit. In your json don't mention the word transcript instead use "the speaker" or "video", whatever else makes sense. - there should be as many names in the json as the total mentioned. considering point "D"

-Z: category could be diet, exercise, mental health, treatment, supplement, etc. whatever you see fit for health.
-W: Json structure/format - the parameter order needs to match exactly as below:

{{
  "summary": "summary of the transcript (context is needed here)",
  "total mentioned": "return an integer of the total number of health-related topics, treatments, products mentioned in the video transcript. Should match the number of items you return"
  "all mentions": {{
    "<category 1>": [
      {{
        "name": "One of the items (item1) in the list of advice or projects in category 1",
        "description": "an understandable, Full sentences (atleast 2-3), contextual explanation mentioned in the transcript for item 1 - must have this""
        "start_time": 38.399
      }},
      ...
    ],
    ...
  }},

  "all actionable advices": {{
    "<category 1>": [
      ...
    ],
    ...
  }},
  "sentiment_analysis": "The overall sentiment is...",
  "reliability_score": "The reliability of the advice is...",
  "political_leaning": "The political leaning is..."
}}

-L: Please always return Json without any syntax errors.
-K: ***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS BEFORE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT LIKE an API would.***
"""

structured_entertainment_prompt = f"""
***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS ABOVE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT.***

I: the video transcript is about entertainment, including but not limited to funny videos, vlogs, movie reviews, music discussions, celebrity gossip, etc. Even if there aren't explicit mentions of products, services, or actionable advice, capture any mentions that the speaker emphasizes for the audience or anything particularly interesting. For videos that lack such mentions or advice, return null values for those specific fields but ensure the overall JSON structure remains consistent.

-E: The transcript given to you is in the following format, Analyze the following:

{{
  "content": [
      {{
          "duration": 2.074,
          "start": 0.33,
          "text": "Let's talk about the latest movie release."
      }},
      {{
          "duration": 1.678,
          "start": 2.405,
          "text": "This vlog takes you behind the scenes."
      }}, 
      .
      .
      .
      .
      ]
  }}

and read all the text from all the arrays to get the transcript and generate a structured response in JSON format (format is shown below) covering the following points:

-A: For videos rich in mentions of interesting topics, ensure you provide a list, even if not comprehensive or exhaustive like in other categories. For videos that lack specific mentions or actionable advice, "all mentions" and "all actionable advices" should return null.

-C: "Summary": Provide a concise summary of the key points or themes discussed. It needs to make sense without having to research the idea further. This should be a paragraph long and should aim to capture the essence of the entertainment content.

-E: Analyze the overall sentiment of the transcript (the underlying emotion) in one word. 

-F: Given the nature of entertainment content, evaluating the reliability of advice may not be applicable. In such cases, return null for the "reliability_score".

-G: The political leaning of the message, if any is discerned from entertainment content, should be noted. If none, return null.

-X: Please format your response as follows, maintaining the JSON structure even if some fields are null. Ensure there are no syntax issues, and the parameters are in the order shown below. Each category or mention should have its own line.

-Y: For "name", correct any misspelling from the transcript if you see fit. Use terms like "the speaker" or "video" in your JSON response, avoiding "transcript" for coherence with the entertainment context.

-Z: Given the diverse nature of entertainment, categories might not be as clear-cut. Use your judgment to categorize mentions if any.

-W: Json structure/format - ensure the parameter order matches exactly as below:

{{
  "summary": "Summary of the transcript, capturing the essence of the entertainment content.",
  "total mentioned": "Return an integer of the total number of interesting topics mentioned in the video transcript, or return null if not applicable.",
  "all mentions": null or {{
    "<category 1>": [
      {{
        "name": "Name of the item (if any) in category 1",
        "description": "A brief explanation, if any, mentioned in the transcript""
        "start_time": "The start time of the mention"
      }},
      ...
    ],
    ...
  }},

  "all actionable advices": null,

  "sentiment_analysis": "The overall sentiment is...",
  "reliability_score": null,
  "political_leaning": null or "The political leaning is..."
}}

-L: Please always return JSON without any syntax errors.
-K: ***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS BEFORE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT LIKE an API would.***
"""

structured_gaming_prompt = f"""
***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS ABOVE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT.***

I: the video transcript is about gaming, including video games, gaming hardware, software, events, gaming strategies, eSports, game development, and any related products or services. Ensure all topics are captured and listed in the mentions section in JSON, including the total number mentioned. You must return a comprehensive and exhaustive list of all mentioned gaming-related topics, products, services, emphasizing the importance of not missing any mentions.

Some videos(transcripts) will have numerous mentions. I am seeking detailed analysis similar to what a human expert would provide. Please ensure the analysis is exhaustive and considerate of the context provided, as this will inform significant decisions based on the transcript's content. For any game, hardware, or service you mention, feel free to add more useful facts you know about it.

-E: The transcript given to you is in the following format, Analyze the following:

{{
  "content": [
      {{
          "duration": 2.074,
          "start": 0.33,
          "text": "Exploring the latest in gaming technology."
      }},
      {{
          "duration": 1.678,
          "start": 2.405,
          "text": "This year's most anticipated game releases."
      }}, 
      .
      .
      .
      .
      ]
  }}

and read all the text from all the arrays to get the transcript and generate a structured response in JSON format (format is shown below) covering the following points:

-A: Ensure you provide a comprehensive and exhaustive list of all mentioned gaming projects, products, services, or strategies within each category mentioned, categorized by their respective topics (e.g., video games, hardware, software, eSports, development, or "other" if no categories apply). It's crucial that you include every mention without omission, as my requirements depend on a complete accounting of these details. My decision-making relies on this information being accurate and all-encompassing. Don't omit any names or mentions of products or services.

-B: Also include the "start" time stamp you see for each item and include them in the JSON format shown below. It doesn't always have to be actionable advice, but all that is mentioned will go under that category in the JSON shown below.

-C: "Summary": Provide a concise summary of the key points discussed - needs to understand the context of the transcript and key points. It needs to make sense without having to research the idea further. Make this a paragraph long.

-D: Detail all actionable advice or mentions given, categorized by topic (or "other" if no categories are appropriate). Include each piece of advice or mention of projects, services, etc., under the corresponding category. Again, It's vital that all advice or mentions are captured.

-E: Analyze the overall sentiment of the transcript (the underlying emotion) in one word.

-F: Evaluate the reliability of the given advice in the transcript based on your knowledge, noting any misinformation or inaccuracies. Give it a score on a scale of 1 to 10, where 1 is the worst (not reliable at all) and 10 is very reliable.

-G: Describe the political leaning of the message, if applicable. If none, return null.

-X: Please format your response as follows (make sure the JSON returned has no syntax issues and the parameters are in order they are shown below) - make sure each item has its own line and not grouped with other items in the same line. Each item is one element in the array returned. Even if they share the same explanation.

-Y: For "name", correct any misspelling from the transcript if you see fit. In your JSON don't mention the word transcript instead use "the speaker" or "video", whatever else makes sense. - there should be as many names in the JSON as the total mentioned. Considering point "D"

-Z: Category could be video games, hardware, software, eSports, development, etc. Whatever you see fit for gaming.
-W: JSON structure/format - the parameter order needs to match exactly as below:

{{
  "summary": "Summary of the transcript (context is needed here)",
  "total mentioned": "Return an integer of the total number of gaming-related topics, products, services mentioned in the video transcript. Should match the number of items you return"
  "all mentions": {{
    "<category 1>": [
      {{
        "name": "One of the items (item1) in the list of advice or projects in category 1",
        "description": "An understandable, full sentences (at least 2-3), contextual explanation mentioned in the transcript for item 1 - must have this"
        "start_time": 38.399
      }},
      ...
    ],
    ...
  }},

  "all actionable advices": {{
    "<category 1>": [
      ...
    ],
    ...
  }},
  "sentiment_analysis": "The overall sentiment is...",
  "reliability_score": "The reliability of the advice is...",
  "political_leaning": null or "The political leaning is..."
}}

-L: Please always return JSON without any syntax errors.
-K: ***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS BEFORE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT LIKE an API would.***
"""

structured_sports_prompt = f"""
***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS ABOVE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT.***

I: the video transcript is about sports, including specific sports events, athletes, teams, strategies, training tips, sports gear, and any sports-related products or services. Ensure all topics are captured and listed in the mentions section in JSON, including the total number mentioned. You must return a comprehensive and exhaustive list of all mentioned sports-related topics, products, services, emphasizing the importance of not missing any mentions.

Some videos(transcripts) will have numerous mentions. I am seeking detailed analysis similar to what a human expert would provide. Please ensure the analysis is exhaustive and considerate of the context provided, as this will inform significant decisions based on the transcript's content. For any sport, athlete, team, or gear you mention, feel free to add more useful facts you know about it.

-E: The transcript given to you is in the following format, Analyze the following:

{{
  "content": [
      {{
          "duration": 2.074,
          "start": 0.33,
          "text": "Breaking down the latest football match."
      }},
      {{
          "duration": 1.678,
          "start": 2.405,
          "text": "Highlighting top athletes in this season."
      }}, 
      .
      .
      .
      .
      ]
  }}

and read all the text from all the arrays to get the transcript and generate a structured response in JSON format (format is shown below) covering the following points:

-A: Ensure you provide a comprehensive and exhaustive list of all mentioned sports projects, products, services, or strategies within each category mentioned, categorized by their respective sports (e.g., football, basketball, athletics, swimming, or "other" if no categories apply). It's crucial that you include every mention without omission, as my requirements depend on a complete accounting of these details. My decision-making relies on this information being accurate and all-encompassing. Don't omit any names or mentions of products or services.

-B: Also include the "start" time stamp you see for each item and include them in the JSON format shown below. It doesn't always have to be actionable advice, but all that is mentioned will go under that category in the JSON shown below.

-C: "Summary": Provide a concise summary of the key points discussed - needs to understand the context of the transcript and key points. It needs to make sense without having to research the idea further. Make this a paragraph long.

-D: Detail all actionable advice or mentions given, categorized by topic (or "other" if no categories are appropriate). Include each piece of advice or mention of projects, services, etc., under the corresponding category. Again, It's vital that all advice or mentions are captured.

-E: Analyze the overall sentiment of the transcript (the underlying emotion) in one word.

-F: Evaluate the reliability of the given advice in the transcript based on your knowledge, noting any misinformation or inaccuracies. Give it a score on a scale of 1 to 10, where 1 is the worst (not reliable at all) and 10 is very reliable.

-G: Describe the political leaning of the message, if applicable. If none, return null.

-X: Please format your response as follows (make sure the JSON returned has no syntax issues and the parameters are in the order they are shown below) - make sure each item has its own line and not grouped with other items in the same line. Each item is one element in the array returned. Even if they share the same explanation.

-Y: For "name", correct any misspelling from the transcript if you see fit. In your JSON don't mention the word transcript instead use "the speaker" or "video", whatever else makes sense. - there should be as many names in the JSON as the total mentioned. Considering point "D"

-Z: Category could be the specific sport, athlete, team, strategy, training tip, gear, etc. Whatever you see fit for sports.
-W: JSON structure/format - the parameter order needs to match exactly as below:

{{
  "summary": "Summary of the transcript (context is needed here)",
  "total mentioned": "Return an integer of the total number of sports-related topics, products, services mentioned in the video transcript. Should match the number of items you return"
  "all mentions": {{
    "<category 1>": [
      {{
        "name": "One of the items (item1) in the list of advice or projects in category 1",
        "description": "An understandable, full sentences (at least 2-3), contextual explanation mentioned in the transcript for item 1 - must have this"
        "start_time": 38.399
      }},
      ...
    ],
    ...
  }},

  "all actionable advices": {{
    "<category 1>": [
      ...
    ],
    ...
  }},
  "sentiment_analysis": "The overall sentiment is...",
  "reliability_score": "The reliability of the advice is...",
  "political_leaning": null or "The political leaning is..."
}}

-L: Please always return JSON without any syntax errors.
-K: ***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS BEFORE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT LIKE an API would.***
"""

structured_technology_prompt = f"""
***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS ABOVE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT.***

I: the video transcript is about technology, including the latest gadgets, software, platforms, tech industry news, advancements in technology, cybersecurity, AI, and any technology-related products or services. Ensure all topics are captured and listed in the mentions section in JSON, including the total number mentioned. You must return a comprehensive and exhaustive list of all mentioned technology-related topics, products, services, emphasizing the importance of not missing any mentions.

Some videos(transcripts) will have numerous mentions. I am seeking detailed analysis similar to what a human expert would provide. Please ensure the analysis is exhaustive and considerate of the context provided, as this will inform significant decisions based on the transcript's content. For any gadget, software, platform, or service you mention, feel free to add more useful facts you know about it.

-E: The transcript given to you is in the following format, Analyze the following:

{{
  "content": [
      {{
          "duration": 2.074,
          "start": 0.33,
          "text": "Exploring the newest breakthrough in AI technology."
      }},
      {{
          "duration": 1.678,
          "start": 2.405,
          "text": "The impact of blockchain on cybersecurity."
      }}, 
      .
      .
      .
      .
      ]
  }}

and read all the text from all the arrays to get the transcript and generate a structured response in JSON format (format is shown below) covering the following points:

-A: Ensure you provide a comprehensive and exhaustive list of all mentioned technology projects, products, services, or innovations within each category mentioned, categorized by their respective fields (e.g., AI, cybersecurity, blockchain, gadgets, software, or "other" if no categories apply). It's crucial that you include every mention without omission, as my requirements depend on a complete accounting of these details. My decision-making relies on this information being accurate and all-encompassing. Don't omit any names or mentions of products or services.

-B: Also include the "start" time stamp you see for each item and include them in the JSON format shown below. It doesn't always have to be actionable advice, but all that is mentioned will go under that category in the JSON shown below.

-C: "Summary": Provide a concise summary of the key points discussed - needs to understand the context of the transcript and key points. It needs to make sense without having to research the idea further. Make this a paragraph long.

-D: Detail all actionable advice or mentions given, categorized by topic (or "other" if no categories are appropriate). Include each piece of advice or mention of projects, services, etc., under the corresponding category. Again, It's vital that all advice or mentions are captured.

-E: Analyze the overall sentiment of the transcript (the underlying emotion) in one word.

-F: Evaluate the reliability of the given advice in the transcript based on your knowledge, noting any misinformation or inaccuracies. Give it a score on a scale of 1 to 10, where 1 is the worst (not reliable at all) and 10 is very reliable.

-G: Describe the political leaning of the message, if applicable. If none, return null.

-X: Please format your response as follows (make sure the JSON returned has no syntax issues and the parameters are in the order they are shown below) - make sure each item has its own line and not grouped with other items in the same line. Each item is one element in the array returned. Even if they share the same explanation.

-Y: For "name", correct any misspelling from the transcript if you see fit. In your JSON don't mention the word transcript instead use "the speaker" or "video", whatever else makes sense. - there should be as many names in the JSON as the total mentioned. Considering point "D"

-Z: Category could be the specific field within technology, such as AI, cybersecurity, blockchain, gadgets, software, etc. Whatever you see fit for technology.
-W: JSON structure/format - the parameter order needs to match exactly as below:

{{
  "summary": "Summary of the transcript (context is needed here)",
  "total mentioned": "Return an integer of the total number of technology-related topics, products, services mentioned in the video transcript. Should match the number of items you return",
  "all mentions": {{
    "<category 1>": [
      {{
        "name": "One of the items (item1) in the list of advice or projects in category 1",
        "description": "An understandable, full sentences (at least 2-3), contextual explanation mentioned in the transcript for item 1 - must have this",
        "start_time": 38.399
      }},
      ...
    ],
    ...
  }},
  
  "all actionable advices": {{
    "<category 1>": [
      ...
    ],
    ...
  }},
  "sentiment_analysis": "The overall sentiment is...",
  "reliability_score": "The reliability of the advice is...",
  "political_leaning": null or "The political leaning is..."
}}

-L: Please always return JSON without any syntax errors.
-K: ***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS BEFORE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT LIKE an API would.***
"""

structured_science_prompt = f"""
***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS ABOVE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT.***

I: the video transcript is about science, including topics in biology, chemistry, physics, environmental science, astronomy, and any science-related research findings, theories, experiments, and educational content. Ensure all topics are captured and listed in the mentions section in JSON, including the total number mentioned. You must return a comprehensive and exhaustive list of all mentioned science-related topics, findings, theories, emphasizing the importance of not missing any mentions.

Some videos(transcripts) will have numerous mentions. I am seeking detailed analysis similar to what a human expert would provide. Please ensure the analysis is exhaustive and considerate of the context provided, as this will inform significant decisions based on the transcript's content. For any scientific concept, theory, or research finding you mention, feel free to add more useful facts you know about it.

-E: The transcript given to you is in the following format, Analyze the following:

{{
  "content": [
      {{
          "duration": 2.074,
          "start": 0.33,
          "text": "Discussing the latest breakthrough in genetic engineering."
      }},
      {{
          "duration": 1.678,
          "start": 2.405,
          "text": "The implications of quantum computing for physics."
      }}, 
      .
      .
      .
      .
      ]
  }}

and read all the text from all the arrays to get the transcript and generate a structured response in JSON format (format is shown below) covering the following points:

-A: Ensure you provide a comprehensive and exhaustive list of all mentioned science projects, concepts, research findings, or theories within each category mentioned, categorized by their respective fields (e.g., biology, chemistry, physics, environmental science, astronomy, or "other" if no categories apply). It's crucial that you include every mention without omission, as my requirements depend on a complete accounting of these details. My decision-making relies on this information being accurate and all-encompassing. Don't omit any names or mentions of scientific concepts or research findings.

-B: Also include the "start" time stamp you see for each item and include them in the JSON format shown below. It doesn't always have to be actionable advice, but all that is mentioned will go under that category in the JSON shown below.

-C: "Summary": Provide a concise summary of the key points discussed - needs to understand the context of the transcript and key points. It needs to make sense without having to research the idea further. Make this a paragraph long.

-D: Detail all actionable advice or mentions given, categorized by topic (or "other" if no categories are appropriate). Include each piece of advice or mention of projects, concepts, etc., under the corresponding category. Again, It's vital that all advice or mentions are captured.

-E: Analyze the overall sentiment of the transcript (the underlying emotion) in one word.

-F: Evaluate the reliability of the given advice in the transcript based on your knowledge, noting any misinformation or inaccuracies. Give it a score on a scale of 1 to 10, where 1 is the worst (not reliable at all) and 10 is very reliable.

-G: Describe the political leaning of the message, if applicable. If none, return null.

-X: Please format your response as follows (make sure the JSON returned has no syntax issues and the parameters are in the order they are shown below) - make sure each item has its own line and not grouped with other items in the same line. Each item is one element in the array returned. Even if they share the same explanation.

-Y: For "name", correct any misspelling from the transcript if you see fit. In your JSON don't mention the word transcript instead use "the speaker" or "video", whatever else makes sense. - there should be as many names in the JSON as the total mentioned. Considering point "D"

-Z: Category could be the specific field within science, such as biology, chemistry, physics, environmental science, astronomy, etc. Whatever you see fit for science.
-W: JSON structure/format - the parameter order needs to match exactly as below:

{{
  "summary": "Summary of the transcript (context is needed here)",
  "total mentioned": "Return an integer of the total number of science-related topics, concepts, research findings mentioned in the video transcript. Should match the number of items you return",
  "all mentions": {{
    "<category 1>": [
      {{
        "name": "One of the items (item1) in the list of advice or projects in category 1",
        "description": "An understandable, full sentences (at least 2-3), contextual explanation mentioned in the transcript for item 1 - must have this",
        "start_time": 38.399
      }},
      ...
    ],
    ...
  }},

  "all actionable advices": {{
    "<category 1>": [
      ...
    ],
    ...
  }},
  "sentiment_analysis": "The overall sentiment is...",
  "reliability_score": "The reliability of the advice is...",
  "political_leaning": null or "The political leaning is..."
}}

-L: Please always return JSON without any syntax errors.
-K: ***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS BEFORE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT LIKE an API would.***
"""

structured_politics_prompt = f"""
***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS ABOVE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT.***

I: the video transcript is about politics, including policy discussions, political events, analyses of political figures, ideologies, governmental systems, and any politics-related news or services. Ensure all topics are captured and listed in the mentions section in JSON, including the total number mentioned. You must return a comprehensive and exhaustive list of all mentioned politics-related topics, figures, events, emphasizing the importance of not missing any mentions.

Some videos(transcripts) will have numerous mentions. I am seeking detailed analysis similar to what a human expert would provide. Please ensure the analysis is exhaustive and considerate of the context provided, as this will inform significant decisions based on the transcript's content. For any political figure, event, or ideology you mention, feel free to add more useful facts you know about it.

-E: The transcript given to you is in the following format, Analyze the following:

{{
  "content": [
      {{
          "duration": 2.074,
          "start": 0.33,
          "text": "The impact of recent policy changes on healthcare."
      }},
      {{
          "duration": 1.678,
          "start": 2.405,
          "text": "Analyzing the political landscape ahead of the upcoming elections."
      }}, 
      .
      .
      .
      .
      ]
  }}

and read all the text from all the arrays to get the transcript and generate a structured response in JSON format (format is shown below) covering the following points:

-A: Ensure you provide a comprehensive and exhaustive list of all mentioned political projects, policies, figures, ideologies, or events within each category mentioned, categorized by their respective areas (e.g., domestic policy, international relations, political theory, or "other" if no categories apply). It's crucial that you include every mention without omission, as my requirements depend on a complete accounting of these details. My decision-making relies on this information being accurate and all-encompassing. Don't omit any names or mentions of political importance.

-B: Also include the "start" time stamp you see for each item and include them in the JSON format shown below. It doesn't always have to be actionable advice, but all that is mentioned will go under that category in the JSON shown below.

-C: "Summary": Provide a concise summary of the key points discussed - needs to understand the context of the transcript and key points. It needs to make sense without having to research the idea further. Make this a paragraph long.

-D: Detail all actionable advice or mentions given, categorized by topic (or "other" if no categories are appropriate). Include each piece of advice or mention of projects, policies, etc., under the corresponding category. Again, It's vital that all advice or mentions are captured.

-E: Analyze the overall sentiment of the transcript (the underlying emotion) in one word.

-F: Evaluate the reliability of the given advice in the transcript based on your knowledge, noting any misinformation or inaccuracies. Give it a score on a scale of 1 to 10, where 1 is the worst (not reliable at all) and 10 is very reliable.

-G: Describe the political leaning of the message, if applicable. If none, return null.

-X: Please format your response as follows (make sure the JSON returned has no syntax issues and the parameters are in the order they are shown below) - make sure each item has its own line and not grouped with other items in the same line. Each item is one element in the array returned. Even if they share the same explanation.

-Y: For "name", correct any misspelling from the transcript if you see fit. In your JSON don't mention the word transcript instead use "the speaker" or "video", whatever else makes sense. - there should be as many names in the JSON as the total mentioned. Considering point "D"

-Z: Category could be the specific area within politics, such as domestic policy, international relations, political theory, etc. Whatever you see fit for politics.
-W: JSON structure/format - the parameter order needs to match exactly as below:

{{
  "summary": "Summary of the transcript (context is needed here)",
  "total mentioned": "Return an integer of the total number of politics-related topics, figures, events mentioned in the video transcript. Should match the number of items you return",
  "all mentions": {{
    "<category 1>": [
      {{
        "name": "One of the items (item1) in the list of advice or projects in category 1",
        "description": "An understandable, full sentences (at least 2-3), contextual explanation mentioned in the transcript for item 1 - must have this",
        "start_time": 38.399
      }},
      ...
    ],
    ...
  }},

  "all actionable advices": {{
    "<category 1>": [
      ...
    ],
    ...
  }},
  "sentiment_analysis": "The overall sentiment is...",
  "reliability_score": "The reliability of the advice is...",
  "political_leaning": null or "The political leaning is..."
}}

-L: Please always return JSON without any syntax errors.
-K: ***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS BEFORE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT LIKE an API would.***
"""

structured_business_prompt = f"""
***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS ABOVE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT.***

I: the video transcript is about business, covering topics such as startups advice, ecommerce, buying and selling businesses, marketing, raising money, stocks, and any business-related products or services. Ensure all topics are captured and listed in the mentions section in JSON, including the total number mentioned. You must return a comprehensive and exhaustive list of all mentioned business-related topics, advice, strategies, products, services, emphasizing the importance of not missing any mentions.

Some videos(transcripts) will have numerous mentions. I am seeking detailed analysis similar to what a human expert would provide. Please ensure the analysis is exhaustive and considerate of the context provided, as this will inform significant decisions based on the transcript's content. For any business concept, strategy, stock, or service you mention, feel free to add more useful facts you know about it.

-E: The transcript given to you is in the following format, Analyze the following:

{{
  "content": [
      {{
          "duration": 2.074,
          "start": 0.33,
          "text": "Exploring the latest trends in ecommerce."
      }},
      {{
          "duration": 1.678,
          "start": 2.405,
          "text": "How to successfully raise funds for your startup."
      }}, 
      .
      .
      .
      .
      ]
  }}

and read all the text from all the arrays to get the transcript and generate a structured response in JSON format (format is shown below) covering the following points:

-A: Ensure you provide a comprehensive and exhaustive list of all mentioned business projects, concepts, strategies, advice, stocks, or services within each category mentioned, categorized by their respective areas (e.g., startups, ecommerce, finance, marketing, or "other" if no categories apply). It's crucial that you include every mention without omission, as my requirements depend on a complete accounting of these details. My decision-making relies on this information being accurate and all-encompassing. Don't omit any names or mentions of business importance.

-B: Also include the "start" time stamp you see for each item and include them in the JSON format shown below. It doesn't always have to be actionable advice, but all that is mentioned will go under that category in the JSON shown below.

-C: "Summary": Provide a concise summary of the key points discussed - needs to understand the context of the transcript and key points. It needs to make sense without having to research the idea further. Make this a paragraph long.

-D: Detail all actionable advice or mentions given, categorized by topic (or "other" if no categories are appropriate). Include each piece of advice or mention of projects, strategies, etc., under the corresponding category. Again, It's vital that all advice or mentions are captured.

-E: Analyze the overall sentiment of the transcript (the underlying emotion) in one word.

-F: Evaluate the reliability of the given advice in the transcript based on your knowledge, noting any misinformation or inaccuracies. Give it a score on a scale of 1 to 10, where 1 is the worst (not reliable at all) and 10 is very reliable.

-G: Describe the political leaning of the message, if applicable. If none, return null.

-X: Please format your response as follows (make sure the JSON returned has no syntax issues and the parameters are in the order they are shown below) - make sure each item has its own line and not grouped with other items in the same line. Each item is one element in the array returned. Even if they share the same explanation.

-Y: For "name", correct any misspelling from the transcript if you see fit. In your JSON don't mention the word transcript instead use "the speaker" or "video", whatever else makes sense. - there should be as many names in the JSON as the total mentioned. Considering point "D"

-Z: Category could be the specific area within business, such as startups, ecommerce, finance, marketing, etc. Whatever you see fit for business.
-W: JSON structure/format - the parameter order needs to match exactly as below:

{{
  "summary": "Summary of the transcript (context is needed here)",
  "total mentioned": "Return an integer of the total number of business-related topics, strategies, advice, stocks mentioned in the video transcript. Should match the number of items you return",
  "all mentions": {{
    "<category 1>": [
      {{
        "name": "One of the items (item1) in the list of advice or projects in category 1",
        "description": "An understandable, full sentences (at least 2-3), contextual explanation mentioned in the transcript for item 1 - must have this",
        "start_time": 38.399
      }},
      ...
    ],
    ...
  }},

  "all actionable advices": {{
    "<category 1>": [
      ...
    ],
    ...
  }},
  "sentiment_analysis": "The overall sentiment is...",
  "reliability_score": "The reliability of the advice is...",
  "political_leaning": null or "The political leaning is..."
}}

-L: Please always return JSON without any syntax errors.
-K: ***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS BEFORE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT LIKE an API would.***
"""

structured_history_prompt = f"""
***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS ABOVE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT.***

I: the video transcript is about history, covering topics such as historical events, ancient civilizations, significant figures in history, and educational lessons on historical subjects. Ensure all topics are captured and listed in the mentions section in JSON, including the total number mentioned. You must return a comprehensive and exhaustive list of all mentioned history-related topics, events, civilizations, figures, emphasizing the importance of not missing any mentions.

Some videos(transcripts) will have numerous mentions. I am seeking detailed analysis similar to what a human expert would provide. Please ensure the analysis is exhaustive and considerate of the context provided, as this will inform significant decisions based on the transcript's content. For any historical event, civilization, or figure you mention, feel free to add more useful facts you know about it.

-E: The transcript given to you is in the following format, Analyze the following:

{{
  "content": [
      {{
          "duration": 2.074,
          "start": 0.33,
          "text": "Exploring the rise and fall of ancient Rome."
      }},
      {{
          "duration": 1.678,
          "start": 2.405,
          "text": "The significant impact of the French Revolution."
      }}, 
      .
      .
      .
      .
      ]
  }}

and read all the text from all the arrays to get the transcript and generate a structured response in JSON format (format is shown below) covering the following points:

-A: Ensure you provide a comprehensive and exhaustive list of all mentioned historical topics, events, civilizations, figures within each category mentioned, categorized by their respective areas (e.g., ancient civilizations, modern history, biographies, or "other" if no categories apply). It's crucial that you include every mention without omission, as my requirements depend on a complete accounting of these details. My decision-making relies on this information being accurate and all-encompassing. Don't omit any names or mentions of historical importance.

-B: Also include the "start" time stamp you see for each item and include them in the JSON format shown below. It doesn't always have to be actionable advice, but all that is mentioned will go under that category in the JSON shown below.

-C: "Summary": Provide a concise summary of the key points discussed - needs to understand the context of the transcript and key points. It needs to make sense without having to research the idea further. Make this a paragraph long.

-D: Detail all actionable advice or mentions given, categorized by topic (or "other" if no categories are appropriate). Include each piece of advice or mention of historical significance, under the corresponding category. Again, It's vital that all advice or mentions are captured.

-E: Analyze the overall sentiment of the transcript (the underlying emotion) in one word.

-F: Given the nature of historical content, evaluating the reliability of advice may not be directly applicable. Instead, note any historical inaccuracies or misconceptions based on your knowledge. Provide a general assessment of the historical accuracy on a scale of 1 to 10, where 1 indicates many inaccuracies and 10 indicates high accuracy.

-G: Historical content is unlikely to have a political leaning, but if any bias or perspective is evident, describe it briefly. If none, return null.

-X: Please format your response as follows (make sure the JSON returned has no syntax issues and the parameters are in the order they are shown below) - make sure each item has its own line and not grouped with other items in the same line. Each item is one element in the array returned. Even if they share the same explanation.

-Y: For "name", correct any misspelling from the transcript if you see fit. In your JSON don't mention the word transcript instead use "the speaker" or "video", whatever else makes sense. - there should be as many names in the JSON as the total mentioned. Considering point "D"

-Z: Category could be the specific area within history, such as ancient civilizations, modern history, significant figures, etc. Whatever you see fit for history.
-W: JSON structure/format - the parameter order needs to match exactly as below:

{{
  "summary": "Summary of the transcript (context is needed here)",
  "total mentioned": "Return an integer of the total number of history-related topics, events, civilizations, figures mentioned in the video transcript. Should match the number of items you return",
  "all mentions": {{
    "<category 1>": [
      {{
        "name": "One of the items (item1) in the list of advice or projects in category 1",
        "description": "An understandable, full sentences (at least 2-3), contextual explanation mentioned in the transcript for item 1 - must have this",
        "start_time": 38.399
      }},
      ...
    ],
    ...
  }},

  "all actionable advices": null,

  "sentiment_analysis": "The overall sentiment is...",
  "historical_accuracy": "The general assessment of historical accuracy is...",
  "political_leaning": null or "Any evident bias or perspective is..."

}}

-L: Please always return JSON without any syntax errors.
-K: ***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS BEFORE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT LIKE an API would.***
"""

structured_self_help_prompt = f"""
***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS ABOVE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT.***

I: the video transcript is about self-development, covering topics such as mental health, self-care, self-reflection, working out, motivational advice, quotes, and any self-help related products or services or advice. Ensure all topics are captured and listed in the mentions section in JSON, including the total number mentioned. You must return a comprehensive and exhaustive list of all mentioned self-development-related topics, advice, strategies, products, services, emphasizing the importance of not missing any mentions.

Some videos(transcripts) will have numerous mentions. I am seeking detailed analysis similar to what a human expert would provide. Please ensure the analysis is exhaustive and considerate of the context provided, as this will inform significant decisions based on the transcript's content. For any concept, strategy, or motivational quote you mention, feel free to add more useful facts you know about it.

-E: The transcript given to you is in the following format, Analyze the following:

{{
  "content": [
      {{
          "duration": 2.074,
          "start": 0.33,
          "text": "The importance of self-care in today's fast-paced world."
      }},
      {{
          "duration": 1.678,
          "start": 2.405,
          "text": "Five daily exercises to boost your mental health."
      }}, 
      .
      .
      .
      .
      ]
  }}

and read all the text from all the arrays to get the transcript and generate a structured response in JSON format (format is shown below) covering the following points:

-A: Ensure you provide a comprehensive and exhaustive list of all mentioned self-development projects, concepts, strategies, advice, or services within each category mentioned, categorized by their respective areas (e.g., mental health, fitness, motivational, or "other" if no categories apply). It's crucial that you include every mention without omission, as my requirements depend on a complete accounting of these details. My decision-making relies on this information being accurate and all-encompassing. Don't omit any names or mentions of self-improvement importance.

-B: Also include the "start" time stamp you see for each item and include them in the JSON format shown below. It doesn't always have to be actionable advice, but all that is mentioned will go under that category in the JSON shown below.

-C: "Summary": Provide a concise summary of the key points discussed - needs to understand the context of the transcript and key points. It needs to make sense without having to research the idea further. Make this a paragraph long.

-D: Detail all actionable advice or mentions given, categorized by topic (or "other" if no categories are appropriate). Include each piece of advice or mention of self-improvement techniques, under the corresponding category. Again, It's vital that all advice or mentions are captured.

-E: Analyze the overall sentiment of the transcript (the underlying emotion) in one word.

-F: Given the nature of self-help content, evaluating the reliability of advice may involve subjective judgment. Provide a general assessment of the usefulness of the advice on a scale of 1 to 10, where 1 indicates less useful and 10 indicates highly useful.

-G: Self-help content is unlikely to have a political leaning, but if any bias or perspective is evident, describe it briefly. If none, return null.

-X: Please format your response as follows (make sure the JSON returned has no syntax issues and the parameters are in the order they are shown below) - make sure each item has its own line and not grouped with other items in the same line. Each item is one element in the array returned. Even if they share the same explanation.

-Y: For "name", correct any misspelling from the transcript if you see fit. In your JSON don't mention the word transcript instead use "the speaker" or "video", whatever else makes sense. - there should be as many names in the JSON as the total mentioned. Considering point "D"

-Z: Category could be the specific area within self-development, such as mental health, fitness, motivational, etc. Whatever you see fit for self-help.
-W: JSON structure/format - the parameter order needs to match exactly as below:

{{
  "summary": "Summary of the transcript (context is needed here)",
  "total mentioned": "Return an integer of the total number of self-development-related topics, strategies, advice mentioned in the video transcript. Should match the number of items you return",
  "all mentions": {{
    "<category 1>": [
      {{
        "name": "One of the items (item1) in the list of advice or projects in category 1",
        "description": "An understandable, full sentences (at least 2-3), contextual explanation mentioned in the transcript for item 1 - must have this",
        "start_time": 38.399
      }},
      ...
    ],
    ...
  }},

  "all actionable advices": {{
    "<category 1>": [
      ...
    ],
    ...
  }},
  "sentiment_analysis": "The overall sentiment is...",
  "usefulness_score": "The general assessment of the usefulness of the advice is...",
  "political_leaning": null or "Any evident bias or perspective is..."
}}

-L: Please always return JSON without any syntax errors.
-K: ***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS BEFORE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT LIKE an API would.***
"""

structured_other_prompt = f"""
***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS ABOVE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT.***

I: the video transcript may cover a wide array of topics, including but not limited to those previously categorized (e.g., crypto, health, entertainment, gaming, sports, technology, science, politics, business, self-development), or it might discuss topics that do not fit neatly into any single category. This includes interdisciplinary content, general knowledge, educational topics, or any subject relevant to the video that spans multiple categories. Ensure all topics are captured and listed in the mentions section in JSON, including the total number mentioned. You must return a comprehensive and exhaustive list of all mentioned topics, projects, concepts, advice, strategies, products, services, emphasizing the importance of not missing any mentions.

Some videos(transcripts) will have numerous mentions across various domains. I am seeking detailed analysis similar to what a human expert would provide. Please ensure the analysis is exhaustive and considerate of the context provided, as this will inform significant decisions based on the transcript's content. For any topic, concept, or advice you mention, feel free to add more useful facts you know about it.

-E: The transcript given to you is in the following format, Analyze the following:

{{
  "content": [
      {{
          "duration": 2.074,
          "start": 0.33,
          "text": "Here's an overview of today's most pressing global issues."
      }},
      {{
          "duration": 1.678,
          "start": 2.405,
          "text": "Tips for effective personal finance management."
      }}, 
      .
      .
      .
      .
      ]
  }}

and read all the text from all the arrays to get the transcript and generate a structured response in JSON format (format is shown below) covering the following points:

-A: Ensure you provide a comprehensive and exhaustive list of all mentioned topics, projects, concepts, advice, or services within each category mentioned, categorized by their respective areas or as "miscellaneous" if no specific categories apply. It's crucial that you include every mention without omission, as my requirements depend on a complete accounting of these details. My decision-making relies on this information being accurate and all-encompassing. Don't omit any names or mentions of importance.

-B: Also include the "start" time stamp you see for each item and include them in the JSON format shown below. It doesn't always have to be actionable advice, but all that is mentioned will go under that category in the JSON shown below.

-C: "Summary": Provide a concise summary of the key points discussed - needs to understand the context of the transcript and key points. It needs to make sense without having to research the idea further. Make this a paragraph long.

-D: Detail all actionable advice or mentions given, categorized by topic (or "miscellaneous" if no categories are appropriate). Include each piece of advice or mention of significance, under the corresponding category. Again, It's vital that all advice or mentions are captured.

-E: Analyze the overall sentiment of the transcript (the underlying emotion) in one word.

-F: Evaluate the reliability of the given advice in the transcript based on your knowledge, noting any misinformation or inaccuracies. Give it a score on a scale of 1 to 10, where 1 is the worst (not reliable at all) and 10 is very reliable.

-G: Describe the political leaning of the message, if applicable. If none, return null.

-X: Please format your response as follows (make sure the JSON returned has no syntax issues and the parameters are in the order they are shown below) - make sure each item has its own line and not grouped with other items in the same line. Each item is one element in the array returned. Even if they share the same explanation.

-Y: For "name", correct any misspelling from the transcript if you see fit. In your JSON don't mention the word transcript instead use "the speaker" or "video", whatever else makes sense. - there should be as many names in the JSON as the total mentioned. Considering point "D"

-Z: Category could be any specific area covered, such as those previously mentioned or "miscellaneous" for topics that don't fit neatly into one category. Whatever you see fit for the content.
-W: JSON structure/format - the parameter order needs to match exactly as below:

{{
  "summary": "Summary of the transcript (context is needed here)",
  "total mentioned": "Return an integer of the total number of topics, projects, concepts, advice mentioned in the video transcript. Should match the number of items you return",
  "all mentions": {{
    "<category 1>": [
      {{
        "name": "One of the items (item1) in the list of advice or projects in category 1",
        "description": "An understandable, full sentences (at least 2-3), contextual explanation mentioned in the transcript for item 1 - must have this",
        "start_time": 38.399
      }},
      ...
    ],
    ...
  }},

  "all actionable advices": {{
    "<category 1>": [
      ...
    ],
    ...
  }},
  "sentiment_analysis": "The overall sentiment is...",
  "reliability_score": "The reliability of the advice is...",
  "political_leaning": null or "Any evident bias or perspective is..."
}}

-L: Please always return JSON without any syntax errors.
-K: ***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS BEFORE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT LIKE an API would.***
"""

structured_crypto_prompt = f"""
***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS ABOVE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT.***

I: the video transcript is about a blockchain(s), NFT(s), coins(s), crypto, meme coins, or AI coins, etc. ensure all projects are captured and listed in the mentions section in json, (including total number mentioned). You must return a comprehensive (include ALL) and exhaustive list of ALL mentioned projects, coins, nfts, investments within each category (NFT, meme coins, AI coins, etc), emphasizing the importance of not missing any mentions. 

Some videos(transcripts) will have 100 + mentions. I am seeking detailed analysis similar to what a human expert would provide. Please ensure the analysis is exhaustive and considerate of the context provided, as this will inform significant decisions based on the transcript's content. For any name you mention, feel free to add more useful facts you know about the crypto or project. 

-E: The transcript given to you is in the following format, Analyze the following:

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
      }}, 
      .
      .
      .
      .
      ]
  }}

 and read all the text from all the arrays to get the transcript and generate a structured response in JSON format (format is shown below) covering the following points: 

-A: Ensure you provide a comprehensive and exhaustive list of all mentioned crypto projects, services, or products (i.e. coins in crypto, health products, books, tools, important people etc) within each category mentioned, categorized by their respective topics (e.g., meme coin, nft, gaming, gambling, AI, or "other" if no categories apply). It's crucial that you include every mention without omission, as my requirements depend on a complete accounting of these details. My decision-making relies on this information being accurate and all-encompassing. Don't omit any names or mentions of coins products or services. i.e. If 100 are mentioend, return all 100 of them, with a short description mentoend about them in the transcript (see json below).  

-B: also include the "start" time stamp you see for each item and include them in the json format shown below.
It doesnt always have to be actionable advice, but all that is mentioned will go under that category in the json shown below.

-C: "Summary": Provide a concise summary of the key points discussed - needs to understand the context of the transcript and key points. It needs to make sense without having to research the idea further. make this a paragraph long. 

-D: Detail all actionable advice or mentions given, categorized by topic (or "other" if no categories are appropriate). Include each piece of advice or mention of projects, services, etc., under the corresponding category. again, It's vital that all advice or mentions are captured. Dont include things vague ideas like "the internet" or "the world" or "the world's best" or "the world's worst" or "youtube" or obvious things people already know or large legacy categories like "culture" or "entertainment" or "politics" or "science" or "sports" or "technology" or "health" or "finance" or "education" or "religion" or "art, etc. If its crypto mentions, include all. 

-E: Analyze the overall sentiment of the transcript (the underlying emotion) in one word
-F: Evaluate the reliability of the given advice in the transcript based on your knowledge, noting any misinformation or inaccuracies. give it a score on a scale of 1 to 10, where 1 is the worst (not reliable at all) and 10 is very reliable.

-G: Describe the political leaning of the message, if applicable. if none, return null. 

-X: Please format your response as follows (make sure the json returned has no syntax issues and the parameters are in order they are shown below) - make sure each item has its own line and not grouped with other items in the same line. each item is one element in the array returned. even if they share the same explaination. 

-Y: For "name", correct misspelling from the transcript if you see fit. In your json dont mention the word transcript instead use "the speaker" or "video", whatever else makes sense. 
- "total mentioned": return an integer total items you are returning from the script. there should be as many names in the json as this total mentioned and considering point "D" which states: exclude vague broad categories. 
 -(note: all mentions should not include the items metioned in actionable advice section: remove dupicates especially if they have the same "name" and the same "time stampt". also remove any advice that is too vague and broad and not useful to listeners)

-Z: category could be meme, ai , game, etc. what every you see fit for crypto.
-W: Json structure/format - the parameter order needs to match exactly as below:

{{
  "summary": "summary of the transcript (context is needed here)",
  "total mentioned" : "return an integer of the total number of coins, nfts, project names mentioned in the video transcript. Should match the number of items you return"
  "all mentions": {{
    "<category 1>": [
      {{
        "name": " One of the items (item1) in the list of advice or projects in category 1,
        "description": "an understandable, Full sentences (atleast 2-3), contextual explanation mentioned in the transcript for item 1 - must have this""
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


-L: Please always return Json without any syntax errors.
-K: ***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS BEFORE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT LIKE an API would.***
  """

merge_prompt = f"""
 You are given a string that is a concatination of multiple jsons, of the same structure (json 1, json2, ...,n). Your task is to merge all the jsons into one json: json 1 + json 2 + ... + n = json final, where the last json has the same structure as the first json: 

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


 make sure you include all the unique values in all jsons, and exclude duplicate/similar values. if the same topic is mentioned at different "start_time", it is considered unique


 Lastly, make sure you always only return a json, no explaination or messages before or after it. similar to an APi JSON response 


"""

Topic = f"""
   Instructions: 
   - Firstly, scan the entire transcript to the end, and categorize the video transcript into the following categories based on the main domain it is in. If for example it is talking about crypto and blockchain, pick category "Crypto" :
   
   1. Crypto: anything related to blockchian, NFT, coins, crypto, meme coins, AI coins, gaming coins, etc. 
   2. Health: medical advice, health tips, diet, food, etc.
   3. Entertainment: anything related to movies, TV shows, music, etc.
   4. Gaming: anything related to gaming, video games, etc.
   5. Sports: anything related to sports, football, basketball, etc.
   6. Technology: anything related to technology, computers, tech, AI etc.
   7. Science: anything related to science, biology, chemistry, physics, etc.
   8. Politics: anything that sounds like news and debate and politics, etc.
   9. Business: For content focusing on business, including discussions on startups, ecommerce, buying and selling businesses, marketing, raising funds, stocks, and more
   10. History: anything related to history, including historical events, ancient civilizations, and ancient civilizations, history lessons, history greats
   11. Self-help: anything related to self-developement, including mental health, self-care, self-reflection, working out, motivational advice, quotes, etc.
   12. Other: anything that is not in the above categories, but still relevant to the video OR anything that has multiple of categories mentioned above.


you must return a json with the following format (example here is categry 1):


{{
  "category": "Crypto"
}}

- only return one of the following categories: [Crypto, Health, Entertainment, Gaming, Sports, Technology, Science, Politics, Business, History, Self-developement, Other]
- Please always return Json without any syntax errors as shown above.
- ***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS BEFORE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT LIKE an API would.***


"""

structured_prompt = f"""

***, Follow these Instructions:***

***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS ABOVE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT.***

- INTRO: 
Read the transcript, and make a list of all the names of projects, coins, NFTs, products, and other items mentioned in the transcript. Don't skip any of them. Then group them in categories if you see patterns, for those that don't fit, put them under "Other" category. Even if there are 100 mentions you will return all of them in this fashion. I have provided a json example in this instruction. This is the main point of this API call to you. The rest of the instructions are more details around it: 

To ensure all projects are captured and listed in the mentions section in json, you must return a comprehensive and exhaustive and inclusive list of all mentioned projects, services, or products (i.e. coins in crypto, health products, books, etc) within each category, emphasizing the importance of not missing any mentions. I am seeking detailed analysis similar to what a human expert would provide. Please ensure the analysis is exhaustive and considerate of the context provided, as this will inform significant decisions based on the transcript's content.

The video transcript is about a blockchain(s), NFT(s), coins(s), crypto, meme coins, or AI coins, etc. ensure all projects are captured and liste. You must return a comprehensive (include ALL) and exhaustive list of ALL mentioned projects, nfts, investments within each category (NFT, meme coins, AI coins, game coins, etc), emphasizing the importance of not missing any mentions in the transcript when you return. 


-E: The transcript given to you is in the following format, Analyze the following:

{{
  [
  {{"text": "[Music]", "start": 0.17}},
  {{"text": "okay listen you can laugh as much as you", "start": 0.76}},
  {{"text": "want about meme coins dog Worf hat the", "start": 2.36}},
      .
      .
      .
      .
      ]
  }}

 and read all the text from all the arrays to get the transcript and generate a structured response in JSON format (format is shown below) covering the following points: 


- Instruction details: 
-A: Ensure you provide a comprehensive and exhaustive list of all mentioned crypto projects, services, or products (i.e. coins in crypto, health products, books, tools, important people etc) within each category mentioned, categorized by their respective topics (e.g., meme coin, nft, gaming, gambling, AI, or "other" if no categories apply). It's crucial that you include every mention without omission, as my requirements depend on a complete accounting of these details. My decision-making relies on this information being accurate and all-encompassing. Don't omit any names or mentions of coins products or services. i.e. If 100 are mentioend, return all 100 of them, with a short description mentoend about them in the transcript (see json below). For crypto any investment advice mention them. 

-B: include the "start" time stamp you see for each item and include them in the json format shown below. For All mentions. 


-C: "Summary": Provide a concise summary of the key points discussed - needs to understand the context of the transcript and key points. It needs to make sense without having to research the idea further. make this a paragraph long. 

-D: Detail all actionable advice or mentions given, categorized by topic (or "other" if no categories are appropriate). Include each piece of advice or mention of projects, services, etc., under the corresponding category. again, It's vital that all advice or mentions are captured. Dont include things vague ideas like "the internet" or "the world" or "the world's best" or "the world's worst" or "youtube" or obvious things people already know or large legacy categories like "culture" or "entertainment" or "politics" or "science" or "sports" or "technology" or "health" or "finance" or "education" or "religion" or "art, etc. If its crypto mentions, include all. 

-E: Analyze the overall sentiment of the transcript (the underlying emotion) in one word

-F: Evaluate the reliability of the given advice in the transcript based on your knowledge, noting any misinformation or inaccuracies. give it a score on a scale of 1 to 10, where 1 is the worst (not reliable at all) and 10 is very reliable.

-X: Please format your response as follows (make sure the json returned has no syntax issues and the parameters are in order they are shown below) - make sure each item has its own line and not grouped with other items in the same line. each item is one element in the array returned. even if they share the same explaination. 

-Y: For "name", correct misspelling from the transcript if you see fit. In your json dont mention the word transcript instead use "the speaker" or "video", whatever else makes sense. 

 -all mentions should not include the items metioned in actionable advice section: remove dupicates especially if they have the same "name" and the same "time stampt". also remove any advice that is too vague and broad and not useful to listeners

-Z: category could be meme, ai , game, etc. what every you see fit for crypto. For reliability score always return as integer not string

-W: Json structure/format - the parameter order needs to match exactly as below:

{{
  "summary": "This video talks about (context is needed here)",
  "all mentions": {{
    "<category 1>": [
      {{
        "name": " One of the items (item1) in the list of advice or projects in category 1,
        "topic": make this a header of 2-5 words summerizing and titling the `description` and it must include the `name`
        "description": "an understandable, Full sentences (atleast 2-3), contextual explanation mentioned in the transcript for item 1 - must have this""
        "start_time": 38.399
      }},
      {{
        "name": " One of the items (item2) in the list of advice or projects in category 1,
           "topic": make this a header of 2-5 words summerizing and titling the `description` and it must include the `name`
        "description": "an understandable, Full sentences (atleast 2), contextual  explanation mentioned in the transcript for item 2 - must have this""
        "start_time": 40
      }}
      ...
    ],
    "<category 2>": [
      {{
        "name": " One of the items (item1) in the list of advice or projects in category 2,
           "topic": make this a header of 2-5 words summerizing and titling the `description` and it must include the `name`
        "description": " an understandable, Full sentences (atleast 2), contextual  explanation mentioned in the transcript for item 1 - must have this""
        "start_time": 67.5
      }},
      {{
        "name": " One of the items (item2) in the list of advice or projects in category 2,
           "topic": make this a header of 2-5 words summerizing and titling the `description` and it must include the `name`
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
           "topic": make this a header of 2-5 words summerizing and titling the `description` and it must include the `name`
        "description": "an understandable, Full sentences (atleast 2), contextual explanation mentioned in the transcript for item 1 - must have this""
        "start_time": 38.399
      }},
      {{
        "name": " One of the items (item2) in the list of advice or projects in category 1,
           "topic": make this a header of 2-5 words summerizing and titling the `description` and it must include the `name`
        "description": "an understandable, Full sentences (atleast 2), contextual  explanation mentioned in the transcript for item 2 - must have this""
        "start_time": 40
      }}
      ...
    ],
    "<category 2>": [
      {{
        "name": " One of the items (item1) in the list of advice or projects in category 2,
           "topic": make this a header of 2-5 words summerizing and titling the `description` and it must include the `name`
        "description": " an understandable, Full sentences (atleast 2), contextual  explanation mentioned in the transcript for item 1 - must have this""
        "start_time": 67.5
      }},
      {{
        "name": " One of the items (item2) in the list of advice or projects in category 2,
           "topic": make this a header of 2-5 words summerizing and titling the `description` and it must include the `name`
        "description": "an understandable, Full sentences (atleast 2), contextual explanation mentioned in the transcript for item 2 - must have this""
        "start_time": 105
      }}
      ...
    ]
    ...
  }},
  "sentiment_analysis": "The overall sentiment is...or null if none"",
  "reliability_score": "The reliability of the advice is...or null if none"",
}}


-L: Please always return Json without any syntax errors.
-O: return null, for parameters that are not applicable.
-K: ***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS BEFORE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT 
LIKE an API would.***
  """

structured_promptss = f"""

***Instructions for Processing Transcript Data***
***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS ABOVE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT.***
Analyze the transcript to identify mentions of crypto projects, services, or products, including coins, NFTs, investments, and related topics. Provide a detailed and comprehensive list categorized by type (e.g., meme coins, NFTs, AI coins). Ensure every mention is captured to inform significant decisions based on the content.

- **Content Format**: The transcript is provided in a JSON format with segments containing 'text', 'start', and 'duration'.
- **Analysis Goals**:
  1. **Comprehensive Listing**: Enumerate all mentioned projects and services, categorizing them appropriately. Include the start time for each mention.
  2. **Summary**: Offer a brief summary capturing key points discussed, focusing on context and actionable insights.
  3. **Sentiment and Reliability**: Assess the overall sentiment and reliability of the advice given, scoring reliability from 1 to 10.
  4. **Political Leaning**: Note any political leaning, or return null if not applicable.

- **Output Format**: Structure your response as follows, ensuring it's formatted correctly as JSON. Include categories such as meme coins, AI coins, etc., and provide details for each mentioned item, including a brief description and the start time.

Please adhere strictly to JSON output format guidelines, returning a comprehensive analysis that respects the instructions provided. the parameter order needs to match exactly as below:

{{
  "summary": "summary of the transcript (context is needed here)",
  "all mentions": {{
    "<category 1>": [
      {{
        "name": " One of the items (item1) in the list of advice or projects in category 1,
        "topic": make this a header of 2-5 words summerizing and titling the `description` and it must include the `name`
        "description": "an understandable, Full sentences (atleast 2-3), contextual explanation mentioned in the transcript for item 1 - must have this""
        "start_time": 38.399
      }},
      {{
        "name": " One of the items (item2) in the list of advice or projects in category 1,
           "topic": make this a header of 2-5 words summerizing and titling the `description` and it must include the `name`
        "description": "an understandable, Full sentences (atleast 2), contextual  explanation mentioned in the transcript for item 2 - must have this""
        "start_time": 40
      }}
      ...
    ],
    "<category 2>": [
      {{
        "name": " One of the items (item1) in the list of advice or projects in category 2,
           "topic": make this a header of 2-5 words summerizing and titling the `description` and it must include the `name`
        "description": " an understandable, Full sentences (atleast 2), contextual  explanation mentioned in the transcript for item 1 - must have this""
        "start_time": 67.5
      }},
      {{
        "name": " One of the items (item2) in the list of advice or projects in category 2,
           "topic": make this a header of 2-5 words summerizing and titling the `description` and it must include the `name`
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
           "topic": make this a header of 2-5 words summerizing and titling the `description` and it must include the `name`
        "description": "an understandable, Full sentences (atleast 2), contextual explanation mentioned in the transcript for item 1 - must have this""
        "start_time": 38.399
      }},
      {{
        "name": " One of the items (item2) in the list of advice or projects in category 1,
           "topic": make this a header of 2-5 words summerizing and titling the `description` and it must include the `name`
        "description": "an understandable, Full sentences (atleast 2), contextual  explanation mentioned in the transcript for item 2 - must have this""
        "start_time": 40
      }}
      ...
    ],
    "<category 2>": [
      {{
        "name": " One of the items (item1) in the list of advice or projects in category 2,
           "topic": make this a header of 2-5 words summerizing and titling the `description` and it must include the `name`
        "description": " an understandable, Full sentences (atleast 2), contextual  explanation mentioned in the transcript for item 1 - must have this""
        "start_time": 67.5
      }},
      {{
        "name": " One of the items (item2) in the list of advice or projects in category 2,
           "topic": make this a header of 2-5 words summerizing and titling the `description` and it must include the `name`
        "description": "an understandable, Full sentences (atleast 2), contextual explanation mentioned in the transcript for item 2 - must have this""
        "start_time": 105
      }}
      ...
    ]
    ...
  }},
  "sentiment_analysis": "One word emotion for the video",
  "reliability_score": "The reliability of the advice is...or null if none"",
}}


***Exclude empty topics and categories. Do not include any advice or mention of projects, services, or products that are not mentioned in the transcript.**
***Exclude duplicate topics from the entire json if they exist.***
***End of Instructions***
  """
