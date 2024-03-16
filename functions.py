def combine_jsons(json1, json2, json3):
  print('json1: ')
  print(json1)
  print('json2: ')
  print(json2)
  print('json3: ')
  print(json3)
  
  # Combine summaries with specified transitions
  combined_summary = json1['summary'] + " Moreover, " + json2['summary'] + " Also, " + json3['summary']
  
  # Initialize combined JSON with combined summary, max reliability score, and sentiment analysis
  combined_json = {
      'summary': combined_summary,
      'reliability_score': max(json1.get('reliability_score', 0), json2.get('reliability_score', 0), json3.get('reliability_score', 0)),
      'sentiment_analysis': " & ".join(filter(None, [json1.get('sentiment_analysis', ''), json2.get('sentiment_analysis', ''), json3.get('sentiment_analysis', '')])),
  }
  
  # Helper function to merge items under the same category across all JSONs, excluding empty categories
  def merge_categories(*categories):
      merged = {}
      for category in categories:
          for key, items in category.items():
              if not items:  # Skip empty lists
                  continue
              if key not in merged:
                  merged[key] = items
              else:
                  existing_items = {item['name']: item for item in merged[key]}
                  for item in items:
                      if item['name'] not in existing_items:
                          merged[key].append(item)
      return {k: v for k, v in merged.items() if v}  # Exclude empty categories
  
  # Prepare categories from each JSON, handling None as an empty dict
  mentions1 = json1.get('all mentions', {})
  mentions2 = json2.get('all mentions', {})
  mentions3 = json3.get('all mentions', {})
  advices1 = json1.get('all actionable advices', {}) or {}
  advices2 = json2.get('all actionable advices', {}) or {}
  advices3 = json3.get('all actionable advices', {}) or {}
  
  # Merge 'all mentions' and 'all actionable advices' from all three JSONs, excluding empty ones
  all_mentions = merge_categories(mentions1, mentions2, mentions3)
  if all_mentions:
      combined_json['all mentions'] = all_mentions
  
  all_advices = merge_categories(advices1, advices2, advices3)
  if all_advices:
      combined_json['all actionable advices'] = all_advices
  
  return combined_json
