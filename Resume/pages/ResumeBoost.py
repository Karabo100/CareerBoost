import io
import streamlit as st
import openai
import os
from PyPDF2 import PdfReader
import re
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(filename='user_sessions.log', level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Ensure the API key is set
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Function to extract text from PDF
def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text
    return text

# Function to preprocess text
def preprocess_text(text):
    # Remove personal information
    text = re.sub(r'\b[\w\.-]+@[\w\.-]+\b', '', text)  # Remove emails
    text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '', text)  # Remove phone numbers
    text = re.sub(r'\b\d{5}\b', '', text)  # Remove ZIP codes
    return text

# Function to provide feedback using ChatGPT
def get_completion(prompt, model="gpt-4-turbo"):
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a talent career coach providing feedback on a resume. Please provide feedback on the resume as well as give recommendations on different career paths suited for that resume."},
                {"role": "user", "content": prompt},
            ]
        )
        return response.choices[0].message['content']
    except Exception as e:
        st.error(f"Error communicating with OpenAI: {e}")
        logging.error(f"Error communicating with OpenAI: {e}")
        return None

# Function to handle user consent
def get_user_consent():
    if 'consent_given' not in st.session_state:
        st.session_state.consent_given = False

    with st.expander("Consent Required"):
        st.write("We need your consent to process your resume information.")
        consent = st.checkbox("I consent to the use of my resume information for feedback purposes.")

        if consent:
            st.session_state.consent_given = True
            logging.info("User consent given.")

def resume_feedback():
    st.title("CareerBoost")
    st.write("Welcome! This feature serves as your resume job recommendation guide using AI. PLEASE BE CAUTIOUS: Remember to exclude sensitive and personal information on the PDF file you upload. Output may be inaccurate and does not guarantee interviews nor job offers.")

    # Ask for user consent
    get_user_consent()

    if st.session_state.consent_given:
        uploaded_file = st.file_uploader("Upload your resume in PDF format", type=["pdf"])

        if uploaded_file is not None:
            resume_text = extract_text_from_pdf(uploaded_file)
            st.write("Resume Content:")
            st.write(resume_text)
            logging.info("Resume uploaded and text extracted.")

            # Check for personal information in the resume
            if (re.search(r'\b[\w\.-]+@[\w\.-]+\.\w{2,4}\b', resume_text) or
                re.search(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', resume_text) or
                re.search(r'\b\d{5}\b', resume_text) or
                "@" in resume_text):
                st.warning("Personal information detected in the resume. Please remove any emails, phone numbers, ZIP codes, and @ symbols before uploading.")
                logging.warning("Personal information detected in the resume.")
            else:
                st.success("No personal information detected in the resume.")
                if st.button("Get Feedback"):
                    feedback = get_completion(resume_text)
                    if feedback:
                        st.write("Feedback:")
                        st.write(feedback)
                        logging.info("Feedback provided: " + feedback)
    else:
        st.warning("You need to give consent to upload your resume.")
        logging.warning("User did not give consent.")

if __name__ == "__main__":
    resume_feedback()
