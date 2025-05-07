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
    /* Grid layout improvements */
    .grid-container {
        display: grid;
        gap: 2rem;
        padding: 1rem;
    }
    .result-card {
        background: white;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        overflow: hidden;
        transition: transform 0.2s;
        height: 100%;
    }
    .result-card:hover {
        transform: translateY(-5px);
    }
    .result-image {
        width: 100%;
        height: 300px;
        object-fit: cover;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .result-content {
        padding: 1rem;
    }
    .character-name {
        font-size: 1.2rem;
        font-weight: bold;
        color: #FF4B4B;
        margin-bottom: 0.5rem;
        text-align: center;
    }
    .similarity-score {
        padding: 0.5rem;
        border-radius: 5px;
        text-align: center;
        font-weight: bold;
        margin: 0.5rem 0;
    }
    .details-section {
        margin-top: 1rem;
        padding: 1rem;
        background: #f8f9fa;
        border-radius: 10px;
    }
    /* Make columns equal width */
    div[data-testid="column"] {
        width: calc(33.33% - 1.33rem) !important;
        padding: 0.5rem !important;
    }
    /* Responsive grid adjustments */
    @media (max-width: 768px) {
        div[data-testid="column"] {
            width: calc(50% - 1rem) !important;
        }
    }
    @media (max-width: 480px) {
        div[data-testid="column"] {
            width: 100% !important;
        }
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
    
    # Calculate number of rows needed for 3 columns
    num_results = len(results)
    num_rows = (num_results + 2) // 3  # Round up division
    
    for row in range(num_rows):
        # Create a row with 3 columns
        cols = st.columns(3)
        
        for col_idx in range(3):
            result_idx = row * 3 + col_idx
            if result_idx < num_results:
                result = results[result_idx]
                with cols[col_idx]:
                    with st.container():
                        # Card container
                        st.markdown('<div class="result-card">', unsafe_allow_html=True)
                        
                        # Character name header
                        display_name = result['jikan_data']['name'] if result.get('jikan_data') else result['name']
                        st.markdown(f'<div class="character-name">{display_name}</div>', unsafe_allow_html=True)
                        
                        # Image display
                        image_url = f"{FLASK_API}/thumbnails/{result['id']}"
                        try:
                            st.image(
                                image_url,
                                use_container_width=True,
                                output_format="JPEG",
                                clamp=True  # Ensures consistent color range
                            )
                            
                            # Similarity score with color coding
                            score = result['score']
                            color = '#28a745' if score > 0.7 else '#ffc107' if score > 0.5 else '#dc3545'
                            st.markdown(f"""
                                <div class="similarity-score" style="background-color: {color}; color: white;">
                                    Similarity: {score:.1%}
                                </div>
                            """, unsafe_allow_html=True)
                            
                            # MAL link if available
                            if result.get('jikan_data'):
                                mal_url = result['jikan_data']['url']
                                st.markdown(f"""
                                    <div style="text-align: center;">
                                        <a href="{mal_url}" target="_blank" 
                                           style="text-decoration: none; color: #FF4B4B;">
                                            View on MAL 🔗
                                        </a>
                                    </div>
                                """, unsafe_allow_html=True)
                                
                                # Expandable details section
                                with st.expander("Details 📝"):
                                    st.markdown(f"""
                                        <div class="details-section">
                                            <p><strong>MAL ID:</strong> {result['jikan_data']['mal_id']}</p>
                                            <p><strong>Official Name:</strong> {result['jikan_data']['name']}</p>
                                            <p><strong>Database Name:</strong> {result['name']}</p>
                                        </div>
                                    """, unsafe_allow_html=True)
                                    
                        except Exception as e:
                            st.error(f"Error loading image: {str(e)}")
                        
                        # Close card container
                        st.markdown('</div>', unsafe_allow_html=True)

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