import os
from pypdf import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI

from langchain.vectorstores import FAISS
import google.generativeai as genai
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
import streamlit as st

load_dotenv()

genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# Function to extract text from all PDF documents
def get_pdf_text(pdf_docs):
    text = ''
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text+=page.extract_text()
        
    return text

# Convert the text given by PDF into Chunks
def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size = 10000, chunk_overlap = 1000)
    chunks = text_splitter.split_text(text)
    return chunks


# Convert the chunks into vector
def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model='models/embedding-001')
    # Faiss takes all the text_chunks and embed according to the 
    # embedding that I have initialized
    vector_store = FAISS.from_texts(text_chunks, embedding = embeddings)
    # storing the vector_store in local device
    vector_store.save_local('faiss_index')


# Function that loads the Gemini Pro model, create template and returns chain
def get_conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure to provide
    all the details, if the answer is not in the provided context just say, "answer is not available in the context" 
    don't provide the wrong answer\n\n
    Context:\n{context}?\n
    Question: \n{question}\n

    Answer: 
    """

    model = ChatGoogleGenerativeAI(model='gemini-pro',temperature=.3)
    prompt = PromptTemplate(template=prompt_template, input_variables=['context', 'question'])
    chain = load_qa_chain(model,chain_type='stuff',prompt=prompt)
    return chain

def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model='models/embedding-001')
    new_db = FAISS.load_local('faiss_index', embeddings, allow_dangerous_deserialization=True)
    docs = new_db.similarity_search(user_question)

    chain = get_conversational_chain()

    response = chain(
        {'input_documents':docs, 'question': user_question}
        ,return_only_outputs=True
    )

    print(response)
    st.write('Reply: ', response['output_text'])


def main():
    st.set_page_config('Chat with Multiple PDF')
    st.header('Chat with PDF using GEMINI :)')

    user_question = st.text_input('Ask a Question from the PDF Files')

    if user_question:
        user_input(user_question)

    with st.sidebar:
        st.title('Menu: ')
        pdf_docs = st.file_uploader('Upload your PDF Files and Click on the Submit ',type=['pdf'], accept_multiple_files=True)
        if st.button('Submit & Process'):
            with st.spinner('Processing...'):
                raw_text = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunks(raw_text)
                get_vector_store(text_chunks)
                st.success('Done')


if __name__=='__main__':
    main()

