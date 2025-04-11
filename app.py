import streamlit as st
import requests
from bs4 import BeautifulSoup
import groq
import os
from dotenv import load_dotenv
from duckduckgo_search import DDGS
from urllib.parse import urlparse

# Load environment variables from a .env file
load_dotenv()

# Initialize the Groq API client with the API key
groq_api_key = st.secrets["GROQ_API_KEY"] # Ensure your .env file contains the GROQ_API_KEY
groq_client = groq.Groq(api_key=groq_api_key)

# Function to perform web search using DuckDuckGo
def search_web(query):
    with DDGS() as ddgs:
        text_results = list(ddgs.text(query, max_results=3))
        image_results = list(ddgs.images(query, max_results=3))
    return text_results, image_results

# Function to scrape content from a website with a maximum character limit
def scrape_website(url, max_chars=2000):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')
        content = ''
        for p in paragraphs:
            if len(content) + len(p.get_text()) <= max_chars:
                content += p.get_text() + ' '
            else:
                break
        return content.strip()
    except:
        return ""

# Function to summarize content using Groq LLM
def summarize_with_groq(content):
    response = groq_client.chat.completions.create(
        model="llama3-8b-8192",  # Replace with your model name if different
        messages=[{"role": "user", "content": f"Summarize the following content:\n\n{content}"}]
    )
    return response.choices[0].message.content

# Function to handle the search, scraping, and summarization
def search_and_summarize(query):
    text_results, image_results = search_web(query)
    
    contents = []
    max_chars_per_site = 2000
    for result in text_results[:3]:
        content = scrape_website(result['href'], max_chars=max_chars_per_site)
        contents.append(content)
    
    all_content = " ".join(contents)
    
    summary = summarize_with_groq(all_content)
    
    sources = [result['href'] for result in text_results[:3]]
    
    return summary, sources, image_results

# Custom CSS for modern, clean, and gradient look
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    @import url('https://fonts.googleapis.com/icon?family=Material+Icons');

    body {
        font-family: 'Roboto', sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #ffffff;
    }
    .stApp {
        background: black;
    }
    .stTextInput > div > div > input {
        background-color: rgba(255, 255, 255, 0.1);
        color: #ffffff;
        border: none;
        border-radius: 25px;
        padding: 10px 20px;
    }
    .search-icon {
        color: #ffffff;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .search-icon:hover {
        transform: translateY(-2px);
    }
    h1, h2, h3 {
        font-weight: 700;
        color: #ffffff;
    }
    .stAlert {
        background-color: rgba(255, 255, 255, 0.1);
        color: #ffffff;
        border: none;
        border-radius: 10px;
    }
    .source-link {
        display: inline-flex;
        align-items: center;
        background-color: rgba(255, 255, 255, 0.1);
        color: #ffffff;
        border: none;
        border-radius: 20px;
        padding: 5px 15px;
        margin: 5px;
        text-decoration: none;
        font-size: 14px;
        transition: all 0.3s ease;
    }
    .source-link:hover {
        background-color: rgba(255, 255, 255, 0.2);
        transform: translateY(-2px);
    }
    .source-link .material-icons {
        font-size: 18px;
        margin-right: 5px;
    }
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    .fade-in {
        animation: fadeIn 1s ease-in;
    }
    .image-grid {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-around;
    }
    .image-item {
        margin: 10px;
        text-align: center;
    }
    .image-item img {
        max-width: 200px;
        max-height: 200px;
        object-fit: cover;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)

# Remove the header and footer
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# Streamlit UI
st.markdown("<h1 style='text-align: center;'>LangSearch</h1>", unsafe_allow_html=True)

# Input box for search query and search icon
col1, col2 = st.columns([4, 1])
with col1:
    query = st.text_input("", placeholder="Enter your search query...")
with col2:
    st.markdown("""
    <span class="material-icons search-icon" onclick="document.querySelector('.stTextInput input').dispatchEvent(new KeyboardEvent('keydown', {'key': 'Enter'}));">
        search
    </span>
    """, unsafe_allow_html=True)

if query:
    with st.spinner("Searching and summarizing..."):
        summary, sources, image_results = search_and_summarize(query)
    
    # Display results
    st.markdown("<h2>Summary</h2>", unsafe_allow_html=True)
    st.markdown(f'<div class="fade-in">{summary}</div>', unsafe_allow_html=True)
    
    st.markdown("<h2>Sources</h2>", unsafe_allow_html=True)
    for link in sources:
        domain = urlparse(link).netloc
        domain = domain.replace("www.", "")
        st.markdown(f'<a href="{link}" target="_blank" class="source-link"><span class="material-icons">link</span>{domain}</a>', unsafe_allow_html=True)
    
    st.markdown("<h2>Images</h2>", unsafe_allow_html=True)
    st.markdown('<div class="image-grid">', unsafe_allow_html=True)
    for image in image_results:
        st.markdown(f'''
        <div class="image-item">
            <img src="{image['image']}" alt="{image['title']}">
            <p>{image['title']}</p>
        </div>
        ''', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
