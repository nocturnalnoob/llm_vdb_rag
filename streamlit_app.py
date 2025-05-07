import streamlit as st
import requests
from PIL import Image
import io

# Configure page with custom theme and layout
st.set_page_config(
    page_title="Anime Character Search Engine",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to improve the design
st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        margin-top: 1rem;
        background-color: #FF4B4B;
        color: white;
    }
    /* Styling for text input and placeholder */
    .stTextInput>div>div>input {
        background-color: #f0f2f6;
        color: #31333F !important;
    }
    .stTextInput>div>div>input::placeholder {
        color: #666666 !important;
        opacity: 0.8;
    }
    /* Ensure input text is clearly visible when typing */
    .stTextInput>div>div>input:focus {
        background-color: #ffffff;
        box-shadow: 0 0 0 2px #FF4B4B;
    }
    div.css-1kyxreq.e115fcil2 {
        justify-content: center;
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    .result-card {
        padding: 1rem;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin-bottom: 1rem;
    }
    .search-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #FF4B4B 0%, #FF9B9B 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    /* Style for help text */
    .stTextInput>div>div>div>small {
        color: #666666 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# API endpoints
FLASK_API = "http://localhost:5000"
TEXT_SEARCH_URL = f"{FLASK_API}/search/text"
IMAGE_SEARCH_URL = f"{FLASK_API}/search/image"

def display_results(results):
    """Display search results in a grid with improved styling"""
    if not results:
        st.warning("No results found 😕")
        return
    
    # Create a 3-column grid
    cols = st.columns(3)
    
    # Display results in grid with cards
    for idx, result in enumerate(results):
        col = cols[idx % 3]
        with col:
            with st.container():
                st.markdown(f"""
                    <div class="result-card">
                        <h3 style='text-align: center; color: #FF4B4B;'>{result['name']}</h3>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Display image with enhanced styling
                image_url = f"{FLASK_API}/thumbnails/{result['id']}"
                try:
                    st.image(
                        image_url, 
                        caption=f"Similarity: {result['score']:.2%}",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Error loading image: {str(e)}")

def main():
    # Sidebar for app navigation and filters
    with st.sidebar:
        st.image(r"D:\llm\anime-style-mythical-dragon-creature.jpg", use_container_width=True)
        st.markdown("## 🎮 Search Options")
        search_type = st.radio(
            "Choose your search method:",
            ["Text Search 📝", "Image Search 🖼️"]
        )
        
        st.markdown("---")
        st.markdown("## ⚙️ Search Settings")
        top_k = st.slider("Number of results", min_value=1, max_value=20, value=5)
        threshold = st.slider("Similarity threshold", min_value=0.0, max_value=1.0, value=0.3, step=0.1)
    
    # Main content area
    st.markdown("""
        <div class='search-header'>
            <h1>🎯 Anime Character Search Engine</h1>
            <p>Find anime characters by description or image similarity!</p>
        </div>
    """, unsafe_allow_html=True)

    if search_type == "Text Search 📝":
        st.markdown("### 🔍 Search by Description")
        with st.form("text_search_form"):
            query = st.text_input(
                "Describe the character:", 
                placeholder="e.g., girl with long blue hair and red eyes",
                help="Try to be specific about appearance, clothing, or distinctive features"
            )
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                search_button = st.form_submit_button("🔍 Search", use_container_width=True)
            
            if search_button and query:
                with st.spinner("🎯 Searching for matching characters..."):
                    try:
                        response = requests.post(
                            TEXT_SEARCH_URL,
                            json={
                                "query": query,
                                "top_k": top_k,
                                "threshold": threshold
                            }
                        )
                        if response.status_code == 200:
                            st.success("✨ Found some matches!")
                            display_results(response.json()['results'])
                        else:
                            st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                    except Exception as e:
                        st.error(f"Error connecting to server: {str(e)}")
    else:
        st.markdown("### 📸 Search by Image")
        uploaded_file = st.file_uploader(
            "Upload a character image:", 
            type=['png', 'jpg', 'jpeg'],
            help="Upload an image to find similar-looking characters"
        )
        
        if uploaded_file:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(uploaded_file, caption="Uploaded Image", use_container_width=True)
                
                if st.button("🔍 Search Similar Characters", use_container_width=True):
                    with st.spinner("🎯 Finding similar characters..."):
                        try:
                            files = {'file': ('image.jpg', uploaded_file, 'image/jpeg')}
                            response = requests.post(
                                IMAGE_SEARCH_URL,
                                files=files,
                                data={
                                    'top_k': top_k,
                                    'threshold': threshold
                                }
                            )
                            
                            if response.status_code == 200:
                                st.success("✨ Found similar characters!")
                                display_results(response.json()['results'])
                            else:
                                st.error(f"Error: {response.json().get('error', 'Unknown error')}")
                        except Exception as e:
                            st.error(f"Error connecting to server: {str(e)}")

    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #666;'>
            <p>Made with ❤️ By ARYAN :) </p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()