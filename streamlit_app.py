import os
os.environ['TORCH_USE_CUDA_DSA'] = '0'
os.environ['PYTORCH_JIT'] = '0'  # Disable JIT to avoid class registration issues
os.environ['TORCH_DISABLE_GPU_DIAGNOSTICS'] = '1'

# Initialize pytorch first
import torch
torch.set_grad_enabled(False)

import streamlit as st
from PIL import Image
import io
from semantic_search import AnimeImageSearch
torch.classes.__path__= []
# Configure page settings at the very start
st.set_page_config(
    page_title="Anime Character Search Engine",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure image directories
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")
THUMBNAILS_DIR = os.path.join(os.path.dirname(__file__), "thumbnails")
os.makedirs(THUMBNAILS_DIR, exist_ok=True)

def create_thumbnail(image_path, thumbnail_path, size=(200, 200)):
    """Create a thumbnail for an image if it doesn't exist"""
    if not os.path.exists(thumbnail_path):
        with Image.open(image_path) as img:
            img.thumbnail(size)
            img.save(thumbnail_path, "JPEG")

# Initialize the search engine with proper error handling
@st.cache_resource(show_spinner=False)
def get_searcher():
    try:
        with st.spinner("Initializing search engine..."):
            searcher = AnimeImageSearch()
            return searcher
    except Exception as e:
        st.error(f"Failed to initialize search engine: {str(e)}")
        return None

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
                        display_name = result['jikan_data']['name'] if result.get('jikan_data') else result['character_name']
                        st.markdown(f'<div class="character-name">{display_name}</div>', unsafe_allow_html=True)
                        
                        # Image display from Jikan API
                        try:
                            if result.get('jikan_data') and result['jikan_data'].get('image_url'):
                                st.image(
                                    result['jikan_data']['image_url'],
                                    use_container_width=True,
                                    output_format="JPEG",
                                )
                            else:
                                st.warning("No image available")
                            
                            # Similarity score with color coding
                            score = result['similarity_score']
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
                                            <p><strong>Database Name:</strong> {result['character_name']}</p>
                                        </div>
                                    """, unsafe_allow_html=True)
                                    
                        except Exception as e:
                            st.error(f"Error loading image: {str(e)}")
                        
                        # Close card container
                        st.markdown('</div>', unsafe_allow_html=True)

def main():
    # Initialize the search engine
    searcher = get_searcher()
    if not searcher:
        st.error("Failed to initialize the search engine. Please try again.")
        return
    
    # Sidebar for app navigation and filters
    with st.sidebar:
        st.image("anime-style-mythical-dragon-creature.jpg", use_container_width=True)
        st.markdown("## 🎮 Search Options")
        search_type = st.radio(
            "Choose your search method:",
            ["Text Search 📝", "Image Search 🖼️"]
        )
        
        st.markdown("---")
        st.markdown("## ⚙️ Search Settings")
        top_k = st.slider("Number of results", min_value=1, max_value=20, value=6)
        threshold = st.slider("Similarity threshold", min_value=0.0, max_value=1.0, value=0.2, step=0.1)
    
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
                        results = searcher.search(query, top_k=top_k, threshold=threshold)
                        if results:
                            st.success("✨ Found some matches!")
                            display_results(results)
                        else:
                            st.warning("No matches found for your query.")
                    except Exception as e:
                        st.error(f"Error during search: {str(e)}")
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
                            # Convert uploaded file to bytes
                            image_bytes = uploaded_file.getvalue()
                            results = searcher.search_by_image(image_bytes, top_k=top_k, threshold=threshold)
                            if results:
                                st.success("✨ Found similar characters!")
                                display_results(results)
                            else:
                                st.warning("No similar characters found.")
                        except Exception as e:
                            st.error(f"Error during image search: {str(e)}")

    # Footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center; color: #666;'>
            <p>Made with ❤️ By ARYAN :) </p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()