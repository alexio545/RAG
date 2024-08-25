import io
import logging
import requests
import docx
from pymongo import MongoClient

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def clean_line(line):
    """Cleans a line of text by stripping whitespace and removing special characters.

    Args:
        line (str): The line of text to clean.

    Returns:
        str: The cleaned line of text.
    """
    return line.strip().strip('\uFEFF')

def fetch_document(file_id):
    """Fetches a Google Doc file in DOCX format using the provided file ID.

    Args:
        file_id (str): The ID of the Google Doc file.

    Returns:
        bytes: The content of the DOCX file.
    """
    url = f'https://docs.google.com/document/d/{file_id}/export?format=docx'
    logging.info(f"Fetching document from {url}")
    response = requests.get(url)
    response.raise_for_status()
    logging.info("Document fetched successfully")
    return response.content

def parse_document(doc):
    """Parses a DOCX document to extract FAQ questions and their corresponding sections.

    Args:
        doc (docx.Document): The DOCX document object.

    Returns:
        list: A list of dictionaries containing the section title, question title, and answer text.
    """
    questions = []
    question_heading_style = 'heading 2'
    section_heading_style = 'heading 1'
    
    section_title = ''
    question_title = ''
    answer_text_so_far = ''
    
    logging.info("Parsing document content")
    for p in doc.paragraphs:
        style = p.style.name.lower()
        p_text = clean_line(p.text)
    
        if not p_text:
            continue
    
        if style == section_heading_style:
            section_title = p_text
            logging.debug(f"Found section heading: {section_title}")
        elif style == question_heading_style:
            if answer_text_so_far and section_title and question_title:
                questions.append({
                    'text': answer_text_so_far.strip(),
                    'section': section_title,
                    'question': question_title,
                })
                logging.debug(f"Added question: {question_title} under section: {section_title}")
            question_title = p_text
            answer_text_so_far = ''
        else:
            answer_text_so_far += '\n' + p_text
    
    if answer_text_so_far and section_title and question_title:
        questions.append({
            'text': answer_text_so_far.strip(),
            'section': section_title,
            'question': question_title,
        })
        logging.debug(f"Added final question: {question_title} under section: {section_title}")
    
    logging.info("Document parsing complete")
    return questions

def read_faq(file_id):
    """Reads and parses a Google Doc FAQ document by file ID.

    Args:
        file_id (str): The ID of the Google Doc file.

    Returns:
        list: A list of parsed FAQ questions and their corresponding sections.
    """
    logging.info(f"Reading FAQ document with ID: {file_id}")
    content = fetch_document(file_id)
    with io.BytesIO(content) as f_in:
        doc = docx.Document(f_in)
    return parse_document(doc)

def process_faq_documents(faq_documents):
    """Processes multiple FAQ documents and extracts their content.

    Args:
        faq_documents (dict): A dictionary mapping course names to Google Doc file IDs.

    Returns:
        list: A list of dictionaries containing course names and their corresponding documents.
    """
    documents = []
    for course, file_id in faq_documents.items():
        logging.info(f"Processing FAQ document for course: {course}")
        course_documents = read_faq(file_id)
        documents.append({'course': course, 'documents': course_documents})
    logging.info("All FAQ documents processed")
    return documents

def save_documents_to_mongodb(documents, mongo_uri='mongodb://root:root@localhost:27017/'):
    """Saves the extracted FAQ documents to a MongoDB collection.

    Args:
        documents (list): A list of dictionaries containing course names and their documents.
        mongo_uri (str, optional): The MongoDB connection URI. Defaults to 'mongodb://root:root@localhost:27017/'.
    """
    logging.info("Connecting to MongoDB")
    client = MongoClient(mongo_uri)
    db = client.faq_database
    collection = db.faq_collection
    
    logging.info("Clearing existing documents in MongoDB collection")
    collection.delete_many({})
    
    logging.info("Inserting new documents into MongoDB collection")
    for doc in documents:
        collection.insert_one(doc)
    
    logging.info(f"Saved {len(documents)} documents to MongoDB")

def main():
    """Main function to fetch, process, and save FAQ documents."""
    faq_documents = {
        'data-engineering-zoomcamp': '19bnYs80DwuUimHM65UV3sylsCn2j1vziPOwzBwQrebw',
        'machine-learning-zoomcamp': '1LpPanc33QJJ6BSsyxVg-pWNMplal84TdZtq10naIhD8',
        'mlops-zoomcamp': '12TlBfhIiKtyBv8RnsoJR6F72bkPDGEvPOItJIxaEzE0',
    }
    logging.info("Starting the FAQ document processing workflow")
    documents = process_faq_documents(faq_documents)
    save_documents_to_mongodb(documents)
    logging.info("FAQ document processing workflow completed")

if __name__ == "__main__":
    main()
