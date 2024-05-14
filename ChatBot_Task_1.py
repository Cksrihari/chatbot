import re
from datetime import datetime
import spacy
from spacy.matcher import Matcher
import json
nlp = spacy.load('en_core_web_sm')
from dateutil.parser import parse
import logging

# Function to load a JSON knowledge base
def load_knowledge_base(filename="knowledge_base.json"):
    try:
        with open(filename, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print("Knowledge base file not found.")
        return {}


# Function to setup custom matchers for time and date patterns
def setup_matchers(nlp):
    matcher_time = Matcher(nlp.vocab)
    time_patterns = [
        [{"TEXT": {"REGEX": "^(\d{1,2}:\d{2})$"}}],  # e.g., "12:15", "03:00"
        [{"TEXT": {"REGEX": "^(\d{1,2})$"}}, {"LOWER": {"IN": ["am", "pm"]}}]  # e.g., "3 pm", "12 am"
    ]
    matcher_time.add("TIME", time_patterns)

    matcher_date = Matcher(nlp.vocab)
    date_patterns = [
        [{"LOWER": {"IN": ["january", "february", "march", "april", "may", "june", 
                           "july", "august", "september", "october", "november", "december"]}},
         {"IS_DIGIT": True, "OP": "?"}],  # Matches month names followed by optional day digits
        [{"LOWER": {"IN": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]}}],  # Days of the week
        [{"TEXT": {"REGEX": "^\d{1,2}(st|nd|rd|th)$"}}, {"LOWER": "of"}, {"LOWER": "january", "OP": "?"}],  # "3rd of July"
        [{"SHAPE": "dd/dd/dddd"}]  # Matches specific shapes like "01/01/2020"
    ]
    matcher_date.add("DATE", date_patterns)
    return matcher_time, matcher_date

# Function to extract entities from the text
def extract_entities(nlp, matcher_time, matcher_date, text):
    doc = nlp(text)
    entities = {'times': [], 'dates': [], 'departure': [], 'destination': [], 'return_trip': {}}

    # Apply the time and date matchers
    matches_time = matcher_time(doc)
    for _, start, end in matches_time:
        entities['times'].append(doc[start:end].text)

    matches_date = matcher_date(doc)
    for _, start, end in matches_date:
        date_text = doc[start:end].text
        try:
            formatted_date = parse(date_text, fuzzy=True).strftime("%Y-%m-%d")
            entities['dates'].append(formatted_date)
        except ValueError as e:
            logging.warning(f"Failed to parse date: {date_text} with error: {e}")

    # Initialize placeholders for trips
    initial_departure = None
    initial_destination = None
    return_date_identified = False

    # Extract locations and identify return details
    for ent in doc.ents:
        if ent.label_ == "GPE":
            # Use dependency parsing to better understand the sentence structure
            if ent.root.dep_ in ['pobj'] and ent.root.head.text in ['to', 'towards', 'for']:
                if not initial_destination:
                    initial_destination = ent.text
                entities['destination'].append(ent.text)
                
            elif ent.root.dep_ in ['pobj'] and ent.root.head.text in ['from', 'at']:
                if not initial_departure:
                    initial_departure = ent.text
                entities['departure'].append(ent.text)

    # Check for return indications and associated date
    for token in doc:
        if token.text.lower() == 'return':
            # Search for the nearest date entity following the 'return' keyword
            following_dates = [ent.text for ent in doc.ents if ent.start > token.i and ent.label_ == 'DATE']
            if following_dates:
                return_date = parse(following_dates[0], fuzzy=True).strftime("%Y-%m-%d")
                entities['return_trip'] = {'from': initial_destination, 'to': initial_departure, 'return_date': return_date}

                return_date_identified = True
                break

    if not return_date_identified and 'return_trip' in entities and initial_destination:
        # Assume last date in dates list is the return date if specific return date isn't captured
        if entities['dates']:
            entities['return_trip'] = {'from': initial_destination, 'to': initial_departure, 'return_date': entities['dates'][-1]}



    return entities

# Setup spaCy and Matchers
nlp = spacy.load('en_core_web_sm')
matcher_time = Matcher(nlp.vocab)
matcher_date = Matcher(nlp.vocab)

# Define patterns for time and date
time_patterns = [[{'IS_DIGIT': True}, {'LOWER': {'IN': ['am', 'pm']}}]]
date_patterns = [[{'SHAPE': 'dd'}, {'LOWER': 'of'}, {'IS_ALPHA': True}], [{'TEXT': {'REGEX': 'today|tomorrow|next'}}]]

matcher_time.add("TIME_PATTERN", time_patterns)
matcher_date.add("DATE_PATTERN", date_patterns)

def parse_date(date_str):
    # Attempt to parse dates from various formats
    for fmt in ("%d %B", "%B %d, %Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    # Handle specific cases like '13th of July'
    if 'of' in date_str:
        date_str = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_str)  # Remove 'st', 'nd', etc.
        try:
            return datetime.strptime(date_str, "%d of %B").strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None

# Define your patterns here
# Assuming basic patterns are added to matchers
#matcher_time.add("TIME_PATTERN", [[{'IS_DIGIT': True}, {'LOWER': 'am'}], [{'IS_DIGIT': True}, {'LOWER': 'pm'}]])
#matcher_date.add("DATE_PATTERN", [[{'SHAPE': 'dd'}, {'SHAPE': 'dd'}, {'SHAPE': 'dddd'}]])

matcher_time.add("TIME_PATTERN", [[{'IS_DIGIT': True}, {'LOWER': 'am'}], [{'IS_DIGIT': True}, {'LOWER': 'pm'}]])
matcher_date.add("DATE_PATTERN", [[{'SHAPE': 'dd'}, {'LOWER': 'of'}, {'IS_ALPHA': True}]])  # Example for '13th of July'

def handle_missing_values(entities):
    # Required keys with expected structure
    required_keys = {
        'times': list,
        'dates': list,
        'departure': list,
        'destination': list,
        'return_trip': dict
    }
    
    # Initialize default missing value for times and dates
    default_time = "00:00"  # Default time if none found
    default_date = "0000-00-00"  # Default date if none found

    # Check for missing keys or empty values and set defaults or corrections
    for key, expected_type in required_keys.items():
        if key not in entities or not isinstance(entities[key], expected_type):
            if expected_type is list:
                entities[key] = []
            elif expected_type is dict:
                entities[key] = {}
        elif not entities[key]:  # Checks for empty list or dict
            if key == 'times':
                entities[key].append(default_time)
                logging.warning("No times found, setting default time.")
            elif key == 'dates':
                entities[key].append(default_date)
                logging.warning("No dates found, setting default date.")
            else:
                print(f"Warning: No {key} information found.")

    # Ensure valid date format for all entries in dates
    for i, date in enumerate(entities['dates']):
        try:
            # Validate and reformat date if necessary
            entities['dates'][i] = parse(date, fuzzy=True).strftime("%Y-%m-%d")
        except ValueError as e:
            entities['dates'][i] = default_date
            logging.warning(f"Invalid date format found: {date}. Setting default date. Error: {e}")

    # Handling specifics for return trip details
    if entities['return_trip']:
        if 'from' not in entities['return_trip'] or not entities['return_trip']['from']:
            entities['return_trip']['from'] = entities['destination'][0] if entities['destination'] else "Unknown"
        if 'to' not in entities['return_trip'] or not entities['return_trip']['to']:
            entities['return_trip']['to'] = entities['departure'][0] if entities['departure'] else "Unknown"
        if 'return_date' not in entities['return_trip'] or not entities['return_trip']['return_date']:
            if entities['dates']:
                entities['return_trip']['return_date'] = entities['dates'][-1]
            else:
                entities['return_trip']['return_date'] = default_date
                logging.warning("Return date is missing and no other dates to infer from. Setting default date.")

    return entities

# Function to determine the intent of the text
def get_intent(text, knowledge_base, nlp):
    doc = nlp(text)
    best_intent = None
    highest_sim = 0.0
    for interaction_type, data in knowledge_base.items():
        for example in data["patterns"]:
            example_doc = nlp(example)
            sim = doc.similarity(example_doc)
            if sim > highest_sim:
                highest_sim = sim
                best_intent = interaction_type
    return best_intent

# Main function to run the application
def main():
    nlp = spacy.load("en_core_web_md")  # Load spaCy model

    matcher_time, matcher_date = setup_matchers(nlp)  # Setup custom matchers
    knowledge_base = load_knowledge_base()  # Load the knowledge base

    sample_text = "train tickits from New York  and arrive to London. We return ."

    #entities = extract_entities(nlp, matcher_time, matcher_date, sample_text)
    #entities = extract_entities(nlp, matcher_time, matcher_date, sample_text)
    entities = extract_entities(nlp, matcher_time, matcher_date, sample_text)


    #for entity_type, values in entities.items():
    #    print(f"{entity_type.capitalize()}:")
    #    for value in values:
    #        print(f"  - {value}")


    #print(list(entities.values()))
    #print(list(entities.keys())) 
    print("Times:", entities['times'])
    print("Dates:", entities['dates'])
    
   

    intent = get_intent(sample_text, knowledge_base, nlp)
    
    
    
    #print("Extracted Entities:", entities)
    #print("Detected Intent:", intent)

    miss_value = handle_missing_values(entities)
    print("Extracted Missing Value:", miss_value)

if __name__ == "__main__":
    main()
