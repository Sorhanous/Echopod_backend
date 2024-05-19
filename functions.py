def combine_jsons(json1, json2, json3):
  # Combine summaries with specified transitions
  #print(json1)
  #print(json2)
  #print(json3)
  
  summaries = []
  combined_summary = ''
  if 'summary' in json1:
      summaries.append(json1['summary'])
  if 'summary' in json2:
      summaries.append(json2['summary'])
  if 'summary' in json3:
      summaries.append(json3['summary'])
  
  # Function to remove the first sentence
  def remove_first_sentence(s):
      period_index = s.find('.')  # Find the first period
      if period_index != -1:  # If there is at least one period
          return s[period_index + 1:].strip()  # Return the string after the first period, stripped of leading whitespace
      else:
          return s  # Return the original string if no period found
  
  if len(summaries) >= 3:
      # Remove the first sentence from summaries[1] and summaries[2]
      summaries[1] = remove_first_sentence(summaries[1])
      summaries[2] = remove_first_sentence(summaries[2])
      combined_summary = summaries[0] + " Moreover, " + summaries[1] + " Finally, " + summaries[2]
  elif len(summaries) == 2:
      # Remove the first sentence from summaries[1] only
      summaries[1] = remove_first_sentence(summaries[1])
      combined_summary = summaries[0] + " Moreover, " + summaries[1]
  else:
      combined_summary = summaries[0]


  
  combined_json = {
      'summary': combined_summary,
      'reliability_score': max(json1.get('reliability_score', 0), json2.get('reliability_score', 0), json3.get('reliability_score', 0)),
      'sentiment_analysis': " & ".join(filter(None, [json1.get('sentiment_analysis', ''), json3.get('sentiment_analysis', '')])),
  }
  def normalize_key(key):
      # Convert to lowercase and replace underscores with spaces
      return key.lower().replace('_', ' ')
  
  def merge_categories(*categories):
      merged = {}
      original_key_names = {}  # To store the original casing of the category names
      for category in categories:
          for key, items in category.items():
              # Normalize the key using the normalize_key function
              key_normalized = normalize_key(key)
              if key_normalized not in merged:
                  merged[key_normalized] = items
                  original_key_names[key_normalized] = key  # Remember the original casing
              else:
                  # Use a normalized name for case-insensitive comparison
                  existing_items = {normalize_key(item['name']): item for item in merged[key_normalized]}
                  for item in items:
                      # Normalize the item name for comparison
                      item_name_normalized = normalize_key(item['name'])
                      if item_name_normalized not in existing_items:
                          merged[key_normalized].append(item)
      # Convert merged categories back to original casing
      return {original_key_names[k]: v for k, v in merged.items() if v}

  
  mentions1 = json1.get('all_mentions', {})
  mentions2 = json2.get('all_mentions', {})
  mentions3 = json3.get('all_mentions', {})
  advices1 = json1.get('all_actionable_advices', {}) or {}
  advices2 = json2.get('all_actionable_advices', {}) or {}
  advices3 = json3.get('all_actionable_advices', {}) or {}
  
  all_mentions = merge_categories(mentions1, mentions2, mentions3)
  if all_mentions:
      combined_json['all mentions'] = all_mentions
  
  all_advices = merge_categories(advices1, advices2, advices3)
  if all_advices:
      combined_json['all actionable advices'] = all_advices
  #print('combined_json')
  #print(combined_json)
  return combined_json



