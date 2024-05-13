#test push
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
#def extract_entities(nlp, matcher_time, matcher_date, text):
    doc = nlp(text)
    entities = {'times': [], 'dates': [], 'departure': [], 'destination': []}

    # Apply the time and date matchers
    matches_time = matcher_time(doc)
    for _, start, end in matches_time:
        entities['times'].append(doc[start:end].text)

    matches_date = matcher_date(doc)
    for _, start, end in matches_date:
        entities['dates'].append(doc[start:end].text)

    # Extract pre-trained or pattern-based entities
    for ent in doc.ents:
        if ent.label_ == "GPE":
            entities['departure'].append(ent.text)
        elif ent.label_ == "DES":
            entities['destination'].append(ent.text)
    
    return entities
#def extract_entities(nlp, matcher_time, matcher_date, text):
    doc = nlp(text)
    entities = {'times': [], 'dates': [], 'departure': [], 'destination': []}

    # Apply the time and date matchers
    matches_time = matcher_time(doc)
    for _, start, end in matches_time:
        time_text = doc[start:end].text
        # Convert time to a uniform format, here we assume times are in 'HH:MM AM/PM' format
        try:
            formatted_time = datetime.strptime(time_text, "%I %p").strftime("%H:%M")
        except ValueError:
            formatted_time = time_text  # If the conversion fails, keep the original
        entities['times'].append(formatted_time)

    matches_date = matcher_date(doc)
    for _, start, end in matches_date:
        date_text = doc[start:end].text
        # Convert date to a sortable format, here we assume dates are in 'Day Month Year' format
        try:
            formatted_date = datetime.strptime(date_text, "%d %B %Y").date()
        except ValueError:
            formatted_date = date_text  # If the conversion fails, keep the original
        entities['dates'].append(formatted_date)

    # Sort times and dates
    entities['times'].sort()
    entities['dates'].sort()

    # Extract pre-trained or pattern-based entities
    for ent in doc.ents:
        if ent.label_ == "GPE":
            entities['departure'].append(ent.text)
        elif ent.label_ == "DES":
            entities['destination'].append(ent.text)

    return entities
#def extract_entities(nlp, matcher_time, matcher_date, text):
    doc = nlp(text)
    entities = {'times': [], 'dates': [], 'departure': [], 'destination': []}

    # Apply the time and date matchers
    matches_time = matcher_time(doc)
    for _, start, end in matches_time:
        time_text = doc[start:end].text
        # Normalize time to 24-hour format
        try:
            formatted_time = datetime.strptime(time_text, "%I %p").strftime("%H:%M")
        except ValueError:
            formatted_time = time_text
        entities['times'].append(formatted_time)

    matches_date = matcher_date(doc)
    for _, start, end in matches_date:
        date_text = doc[start:end].text
        # Normalize and parse date using more flexible handling
        formatted_date = parse_date(date_text)
        if formatted_date:
            entities['dates'].append(formatted_date)

    # Sort times and dates
    entities['times'].sort()
    entities['dates'].sort(key=lambda date: datetime.strptime(date, "%Y-%m-%d"))

    # Extract locations
    for ent in doc.ents:
        if ent.label_ == "GPE":
            entities['departure'].append(ent.text)
        elif ent.label_ == "DES":
            entities['destination'].append(ent.text)

    return entities
def extract_entities(nlp, matcher_time, matcher_date, text):
    doc = nlp(text)
    entities = {'times': [], 'dates': [], 'departure': [], 'destination': []}

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

    # Extracting using dependency parsing for better context understanding
    for ent in doc.ents:
        if ent.label_ == "GPE":
            # Check the dependency role in the sentence
            if ent.root.head.text in ['to', 'towards', 'for']:
                entities['destination'].append(ent.text)
            elif ent.root.head.text in ['from', 'at']:
                entities['departure'].append(ent.text)

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

    sample_text = "I need a train from Norwich to London tomorrow. on 13th of July at 5 AM."
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
    
    
    print("Extracted Entities:", entities)
    print("Detected Intent:", intent)

if __name__ == "__main__":
    main()
