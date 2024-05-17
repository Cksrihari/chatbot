import re
import json
import logging
from datetime import datetime
from dateutil.parser import parse
import spacy
from spacy.matcher import Matcher

# Load spaCy model
nlp = spacy.load('en_core_web_sm')

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
        [{"TEXT": {"REGEX": "^\d{1,2}(st|nd|rd|th)$"}}, {"LOWER": "of"}, {"LOWER": {"IN": ["january", "february", "march", "april", "may", "june", 
                           "july", "august", "september", "october", "november", "december"]}}],  # "3rd of July"
        [{"SHAPE": "dd/dd/dddd"}]  # Matches specific shapes like "01/01/2020"
    ]
    matcher_date.add("DATE", date_patterns)
    return matcher_time, matcher_date

# Function to extract entities from the text
def extract_entities(nlp, matcher_time, matcher_date, text):
    doc = nlp(text)
    entities = {'times': [], 'dates': [], 'departure': [], 'destination': [], 'return_trip': {}}
    parse_and_add_entities(doc, entities, matcher_time, matcher_date)
    determine_trip_details(doc, entities)
    return entities

# Function to parse and add entities from the document
def parse_and_add_entities(doc, entities, matcher_time, matcher_date):
    for _, start, end in matcher_time(doc):
        entities['times'].append(doc[start:end].text)

    for _, start, end in matcher_date(doc):
        date_text = doc[start:end].text
        try:
            formatted_date = parse(date_text, fuzzy=True).strftime("%Y-%m-%d")
            entities['dates'].append(formatted_date)
        except ValueError as e:
            logging.warning(f"Failed to parse date: {date_text} with error: {e}")

# Function to determine trip details from the document
def determine_trip_details(doc, entities):
    initial_departure, initial_destination = None, None
    for ent in doc.ents:
        if ent.label_ == "GPE":
            check_entity_dependency(ent, entities, initial_departure, initial_destination)

    handle_return_trip(doc, entities, initial_destination, initial_departure)

def check_entity_dependency(ent, entities, initial_departure, initial_destination):
    if ent.root.dep_ in ['pobj'] and ent.root.head.text in ['to', 'towards', 'for']:
        if not initial_destination:
            initial_destination = ent.text
        entities['destination'].append(ent.text)
    elif ent.root.dep_ in ['pobj'] and ent.root.head.text in ['from', 'at']:
        if not initial_departure:
            initial_departure = ent.text
        entities['departure'].append(ent.text)

def handle_return_trip(doc, entities, initial_destination, initial_departure):
    return_date_identified = False
    for token in doc:
        if token.lower_ == 'return':
            for ent in doc.ents:
                if ent.start > token.i and ent.label_ == 'DATE':
                    return_date = parse(ent.text, fuzzy=True).strftime("%Y-%m-%d")
                    entities['return_trip'] = {
                        'from': initial_destination, 
                        'to': initial_departure, 
                        'return_date': return_date
                    }
                    return_date_identified = True
                    break

    if not return_date_identified and initial_destination and entities['dates']:
        entities['return_trip'] = {
            'from': initial_destination, 
            'to': initial_departure, 
            'return_date': entities['dates'][-1]
        }

# Function to determine the intent based on entities and knowledge base
def determine_intent(entities, knowledge_base):
    if entities['departure'] and entities['destination']:
        return 'book_train_tickets'
    return 'unknown_intent'

# Function to generate response based on intent and entities
def generate_response(intent, entities):
    if intent == 'book_train_tickets':
        if entities['departure'] and entities['destination']:
            return f"Booking your train from {entities['departure'][0]} to {entities['destination'][0]}."
        else:
            return "Please provide both departure and destination locations."
    return "I'm sorry, I don't understand."

# Function to handle missing values in the entities
#def handle_missing_values(entities):
    required_keys = {
        'times': list,
        'dates': list,
        'departure': list,
        'destination': list,
        'return_trip': dict
    }

    default_time = "00:00"
    default_date = "0000-00-00"

    for key, expected_type in required_keys.items():
        if key not in entities or not isinstance(entities[key], expected_type):
            if expected_type is list:
                entities[key] = []
            elif expected_type is dict:
                entities[key] = {}
        elif not entities[key]:
            if key == 'times':
                entities[key].append(default_time)
                logging.warning("No times found, setting default time.")
            elif key == 'dates':
                entities[key].append(default_date)
                logging.warning("No dates found, setting default date.")
            else:
                print(f"Warning: No {key} information found.")

    for i, date in enumerate(entities['dates']):
        try:

            entities['dates'][i] = parse(date, fuzzy=True).strftime("%Y-%m-%d")
        except ValueError as e:
            entities['dates'][i] = default_date
            logging.warning(f"Invalid date format found: {date}. Setting default date. Error: {e}")

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

def handle_missing_values(entities):
    required_keys = {
        'times': list,
        'dates': list,
        'departure': list,
        'destination': list,
        'return_trip': dict
    }

    default_time = "00:00"
    default_date = "0000-00-00"

    # Initialize missing keys with default types and values
    for key, expected_type in required_keys.items():
        if key not in entities or not isinstance(entities[key], expected_type):
            entities[key] = [] if expected_type is list else {}
        elif not entities[key]:
            if key == 'times':
                entities[key].append(default_time)
                logging.warning("No times found, setting default time.")
            elif key == 'dates':
                entities[key].append(default_date)
                logging.warning("No dates found, setting default date.")
            else:
                logging.warning(f"No {key} information found.")

    # Parse dates and set default if parsing fails
    for i, date in enumerate(entities['dates']):
        try:
            entities['dates'][i] = parse(date, fuzzy=True).strftime("%Y-%m-%d")
        except ValueError as e:
            entities['dates'][i] = default_date
            logging.warning(f"Invalid date format found: {date}. Setting default date. Error: {e}")

    # Handle missing return trip information
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
        if 'return_trip_time' not in entities['return_trip'] or not entities['return_trip']['return_trip_time']:
            entities['return_trip']['return_trip_time'] = default_time
            logging.warning("Return trip time is missing. Setting default time.")

    return entities

# Function to process input and return a response
def process_input(text, nlp, matcher_time, matcher_date):
    knowledge_base = load_knowledge_base()
    matcher_time, matcher_date = setup_matchers(nlp)
    entities = extract_entities(nlp, matcher_time, matcher_date, text)
    entities = handle_missing_values(entities)
    intent = determine_intent(entities, knowledge_base)
    response = generate_response(intent, entities)
    
    
    
    print("Extracted Entities:", entities)
    print("Detected Intent:", intent)

    miss_value = handle_missing_values(entities)
    print("Extracted Missing Value:", miss_value)
    return response

# Main function to run the chatbot
def chatbot():
    nlp = spacy.load("en_core_web_sm")
    matcher_time, matcher_date = setup_matchers(nlp)
    print("Chatbot initialized. Type 'quit' to exit.")
    knowledge_base = load_knowledge_base()

    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            print("Chatbot: Goodbye!")
            break
        response = process_input(user_input, nlp, matcher_time, matcher_date)
        print("Chatbot:", response)


if __name__ == "__main__":
    chatbot()
