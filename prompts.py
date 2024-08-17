structured_prompt = f"""

*** Follow these Instructions: ***

****>>>> "key_conclusions": Provide a list of items each start with "-". end with a period '. ' and It needs to be all the key take aways and conclusions of the transcript. Use your own judgment to come up with top 3-4 key points/conclusions. They cant be vague.  ****
this key_conclusions  needs to always be in this format mentioend ^ above. there needs to be a space after the period.

***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS ABOVE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT.***

- INTRO:
Read the transcript, and make a list of all the names of projects, coins, NFTs, products, and other items mentioned in the transcript. Don't skip any of them. Then group them in categories if you see patterns; if a name doesn't have a category, put them under the "Other" category. Even if there are 100 mentions, you will return all of them without exceptions. Don't skip them. I have provided a json example in this instruction at the end. This is the main point of this instruction, followed by the details below:

To ensure all projects, coins, products are captured and listed in the 'all mentions' or 'actionable advices' parameters in json below, you must return a comprehensive and exhaustive list of all mentioned projects, services, crypto coins, or products (i.e. coins in crypto, or health products, or books, or etc) within each category (refer to json), emphasizing the importance of not missing any mentions in the transcript. I am seeking detailed analysis similar to what a human expert would provide. Please ensure the analysis is exhaustive and considerate of the context provided in the transcript, as this will inform significant decisions based on the transcript's content.

If the video transcript is about crypto space: a blockchain(s), NFT(s), coins(s), crypto, meme coins, or AI coins, etc. ensure all projects, coins, chains are captured separately and listed separately. You must return a comprehensive (include ALL) and exhaustive list of ALL mentioned projects, coins, nfts, investments within each category (NFT, meme coins, AI coins, game coins, , and more , etc), emphasizing the importance of not missing any mentions, coins, in the transcript when you return.

Once you read all the text from all the arrays to get the transcript to analyze, generate a structured response in JSON format (format is shown below) covering the following points:

- More Instruction details:

-A: (dont skip any coins mentioned) include the "start" time stamp you see for each item and include them in the json format shown below. For All mentions.

-B: (dont skip any coins mentioned) "key_conclusions": Provide a list of items each start with "-". It needs to be all the main key take aways and conclusions of the transcript.

"description": this parameter needs to be understandable, Full sentences (at least 3-4 sentences nothing less), contextual explanation mentioned in the transcript for the item. must have this - read the texts after the name is mentioned in the transcript to understand the message about it better.

-C: (dont skip any coins mentioned) Detail all actionable advice or mentions given, categorized by topic (or "other" if no categories are appropriate). Include each piece of advice or mention of projects, coins, services, etc., under the corresponding category. again, It's vital that all advice or mentions are captured. Dont include vague ideas like "the internet" or "the world" or "the world's best" or "the world's worst" or "youtube" or things people already know or large legacy categories like "culture" or "entertainment" or "politics" or "science" or "sports" or "health" or "finance" or "education" or "religion" or "art, etc. If its crypto mentions, include all.

-D: (dont skip any coins mentioned) The transcript given to you is in the following format, Analyze the following:

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

You have to combine the "texts" before analyzing. For example the above json will be: "...okay listen you can laugh as much as you want about meme coins dog Worf hat the...". Then make a list of all the names of projects, coins, NFTs, products, and other items mentioned in the transcript. ALL OF THEM. Don't skip any of them.

-E: (dont skip any coins mentioned) Evaluate the reliability of the given advice in the transcript based on your knowledge, noting any misinformation or inaccuracies. give it a score on a scale of 1 to 10, where 1 is the worst (not reliable at all) and 10 is very reliable.

-F: (dont skip any coins mentioned) Please format your response as follows (make sure the json returned has no syntax issues and the parameters are in order they are shown below) - make sure each item has its own line and not grouped with other items in the same line. each item is one element in the array returned. even if they share the same explanation.

-G: (dont skip any coins mentioned) For "name", In your json dont mention the word transcript instead use "the speaker" or "video", whatever else makes sense. for example dont return salana when you know its solana.

-H: dont return duplicate items with the same names or similar names (solana/salana), only one of the items. If duplicate names exist in actionable items and in mentions, return one of them with the first start time.

-I: (dont skip any coins mentioned) category could be meme, ai, game, etc. whatever you see fit for crypto or for other domains.

-J: (dont skip any coins mentioned) For reliability score always return as integer not string.

-K: Please adhere strictly to JSON output format guidelines, returning a comprehensive analysis that respects the instructions provided. the parameter order needs to match exactly as below.

-V: Identify any product mentions in the following video script that can be bought on Amazon or google. For each identified product, provide the product name, a descriptive topic, a full-sentence contextual explanation, and the start time in the script where the product is mentioned. Also, generate accurate search queries for both Google and Amazon. For Amazon, include terms like "top rated" or "top reviewed" along with potential product specifications.

Example video script regarding searchable/ buyable product mentions (  shown in "products_one_can_order_on_amazon": section in the json below):
"Here we have an excellent example of the Echo Dot, a smart speaker from Amazon. Next, let's talk about the Fitbit Charge 4, a fitness tracker with GPS. Another great product is the Instant Pot, a versatile electric pressure cooker."

Expected JSON output:

Each item under categories must always have "name", "topic", "description", and "start_time" as shown below.

***always return the following format or our app will break if any of the parameters are missing***

{{
  "key_conclusions": "-item1 -item2 -item3 -item4 -item5 ....",
  "all_mentions": {{
    "<category 1>": [
      {{
        "name": " One of the items (item1) in the list of advice or projects in category 1,
        "topic": make this a header of 2-5 words summarizing and titling the `description` and it must include the `name`
        "description": "an understandable, Full sentences (at least 3-4), contextual explanation ",
        "start_time": 38.399
      }},
      {{
        "name": " One of the items (item2) in the list of advice or projects in category 1,
           "topic": make this a header of 2-5 words summarizing and titling the `description` and it must include the `name`
        "description": "an understandable, Full sentences (at least 3-4), contextual explanation ",
        "start_time": 40
      }}
      ...
    ],
    "<category 2>": [
      {{
        "name": " One of the items (item1) in the list of advice or projects in category 2,
           "topic": make this a header of 2-5 words summarizing and titling the `description` and it must include the `name`
        "description": "an understandable, Full sentences (at least 3-4), contextual explanation "
        "start_time": 67.5
      }},
      {{
        "name": " One of the items (item2) in the list of advice or projects in category 2,
           "topic": make this a header of 2-5 words summarizing and titling the `description` and it must include the `name`
        "description": "an understandable, Full sentences (at least 3-4), contextual explanation"
        "start_time": 105
      }}
      ...
    ]
    ...
  }},
  
  "all_actionable_advices": {{ 
    "<category 1>": [
      {{
        "name": " One of the items (item1) in the list of advice or projects in category 1,
           "topic": make this a header of 2-5 words summarizing and titling the `description` and it must include the `name`
        "description": "an understandable, Full sentences (at least 3-4), contextual explanation ",
        "start_time": 38.399
      }},
      {{
        "name": " One of the items (item2) in the list of advice or projects in category 1,
           "topic": make this a header of 2-5 words summarizing and titling the `description` and it must include the `name`
        "description": "an understandable, Full sentences (at least 3-4), contextual explanation ",
        "start_time": 40
      }}
      ...
    ],
    "<category 2>": [
      {{
        "name": " One of the items (item1) in the list of advice or projects in category 2,
           "topic": make this a header of 2-5 words summarizing and titling the `description` and it must include the `name`
        "description": "an understandable, Full sentences (must have at least 2-4 sentences)",
        "start_time": 67.5
      }},
      {{
        "name": " One of the items (item2) in the list of advice or projects in category 2,
           "topic": make this a header of 2-5 words summarizing and titling the `description` and it must include the `name`
        "description": "an understandable, Full sentences (at least 2-4), contextual explanation ",
        "start_time": 105
      }}
      ...
    ]
    ...
  }},
  "products_one_can_order_on_amazon": {{ 
    "Products": [
      {{
        "product_name": "Echo Dot",
        "topic": "Smart Speaker Echo Dot",
        "description": "The Echo Dot is a smart speaker from Amazon. It can play music, control smart home devices, provide weather updates, and more. It's a versatile and compact device ideal for any home.",
        "start_time": 38.399,
        "search_queries": {{
          "Google": "\\"buy Echo Dot\\" OR \\"purchase Echo Dot\\" OR \\"order Echo Dot\\"",
          "Amazon": "Echo Dot 4th Generation top rated"
        }}
      }},
      {{
        "product_name": "Fitbit Charge 4",
        "topic": "Fitness Tracker Fitbit Charge 4",
        "description": "The Fitbit Charge 4 is a fitness tracker with built-in GPS. It helps track your daily activity, monitor your heart rate, and analyze your sleep patterns. It's a great tool for maintaining a healthy lifestyle.",
        "start_time": 40,
        "search_queries": {{
          "Google": "\\"buy Fitbit Charge 4\\" OR \\"purchase Fitbit Charge 4\\" OR \\"order Fitbit Charge 4\\"",
          "Amazon": "Fitbit Charge 4 top reviewed"
        }}
      }},
      {{
        "product_name": "Instant Pot",
        "topic": "Versatile Cooker Instant Pot",
        "description": "The Instant Pot is a versatile electric pressure cooker. It can be used for cooking a variety of dishes quickly and efficiently. It's perfect for busy individuals who want to prepare home-cooked meals.",
        "start_time": 45,
        "search_queries": {{
          "Google": "\\"buy Instant Pot\\" OR \\"purchase Instant Pot\\" OR \\"order Instant Pot\\"",
          "Amazon": "Instant Pot 6 Quart top rated"
        }}
      }}
      ...
    ]
  }},
  "sentiment_analysis": "The overall sentiment is...or null if none"",
  "reliability_score": "The reliability of the advice is...or null if none"",
}}

Each item under categories must always have "name", "topic", "description", and "start_time" as shown above.

***Exclude empty topics and categories. Do not include any advice or mention of projects, services, or products that are not mentioned in the transcript.**
***Exclude duplicate topics from the entire json if they exist.***
***End of Instructions***

-L: (Analyze the overall sentiment of the transcript (the underlying emotion) in one word
-M: (dont skip any coins mentioned) Please always return Json without any syntax errors.
-N: (dont skip any coins mentioned) return null, for parameters that are not applicable.
-O: ***IMPORTANT: NEVER RETURN ANY MESSAGE STRINGS BEFORE OR AFTER THE JSON OBJECT. ALWAYS ONLY RETURN JSON OBJECT 
LIKE an API would.***
-P: if there are duplicates (categories or items) in the final json, remove one of them, unless they are in different times. again, dont return duplicate names or categories, merge them all if you see duplicates.
"""




