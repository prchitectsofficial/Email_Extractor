import streamlit as st
import pandas as pd
import time
import io
import zipfile
import os
from pathlib import Path
from email_extractor import EmailExtractor

def main():
    st.set_page_config(
        page_title="Email Extractor Tool",
        page_icon="📧",
        layout="wide"
    )
    
    st.title("📧 Email Extractor Tool")
    st.markdown("Extract email addresses from websites with source tracking")
    
    # Initialize the email extractor
    extractor = EmailExtractor()
    
    # Create tabs for different input methods
    tab1, tab2 = st.tabs(["Text Input", "CSV Upload"])
    
    with tab1:
        st.header("Enter Website URLs")
        st.markdown("Enter multiple URLs separated by commas or new lines")
        
        # Text input for URLs
        urls_text = st.text_area(
            "Website URLs",
            placeholder="https://example.com, https://another-site.com\nhttps://third-site.com",
            height=150
        )
        
        # Process button for text input
        if st.button("Extract Emails", key="text_extract"):
            if urls_text.strip():
                # Parse URLs from text input
                urls = []
                for line in urls_text.split('\n'):
                    for url in line.split(','):
                        url = url.strip()
                        if url:
                            urls.append(url)
                
                if urls:
                    # Show progress
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    results_container = st.empty()
                    
                    # Start timing
                    start_time = time.time()
                    
                    # Extract emails with enhanced progress tracking
                    def progress_update(current, total):
                        progress = current / total
                        percentage = int(progress * 100)
                        progress_bar.progress(progress)
                        status_text.text(f'Processing: {current}/{total} websites completed ({percentage}%)')
                    
                    results = extractor.extract_emails_from_urls(
                        urls, 
                        progress_callback=progress_update
                    )
                    
                    # Calculate processing time
                    processing_time = time.time() - start_time
                    
                    # Display results
                    if results:
                        st.success(f"✅ Processing completed in {processing_time:.2f} seconds")
                        
                        # Create DataFrame for display
                        df_results = []
                        for result in results:
                            if result['emails']:
                                # Combine all emails for this website into a single cell
                                emails_str = ', '.join(sorted(result['emails']))
                                
                                # Get only the pages that actually found emails
                                source_pages = result.get('email_sources', [])
                                source_str = ', '.join(source_pages) if source_pages else result['url']
                                
                                df_results.append({
                                    'Website': result['url'],
                                    'Emails': emails_str,
                                    'Source Pages': source_str,
                                    'Contact Form Found': 'Yes' if result.get('has_contact_form', False) else 'No',
                                    'Status': result['status'],
                                    'Pages Crawled': result.get('successful_pages', 1)
                                })
                            else:
                                df_results.append({
                                    'Website': result['url'],
                                    'Emails': 'No emails found',
                                    'Source Pages': 'None',
                                    'Contact Form Found': 'Yes' if result.get('has_contact_form', False) else 'No',
                                    'Status': result['status'],
                                    'Pages Crawled': result.get('successful_pages', 0)
                                })
                        
                        if df_results:
                            df = pd.DataFrame(df_results)
                            st.dataframe(df, width='stretch')
                            
                            # Download button
                            csv_buffer = io.StringIO()
                            df.to_csv(csv_buffer, index=False)
                            csv_data = csv_buffer.getvalue()
                            
                            st.download_button(
                                label="📥 Download Results as CSV",
                                data=csv_data,
                                file_name=f"email_extraction_results_{int(time.time())}.csv",
                                mime="text/csv"
                            )
                        else:
                            st.warning("No emails were extracted from the provided URLs")
                    else:
                        st.error("Failed to process any URLs")
                else:
                    st.warning("Please enter at least one valid URL")
            else:
                st.warning("Please enter some URLs to process")
    
    with tab2:
        st.header("Upload CSV File")
        st.markdown("Upload a CSV file containing website URLs")
        
        # File uploader
        uploaded_file = st.file_uploader(
            "Choose a CSV file",
            type=['csv'],
            help="CSV file should contain URLs in the first column or a column named 'url' or 'website'"
        )
        
        if uploaded_file is not None:
            try:
                # Read the CSV file
                df_input = pd.read_csv(uploaded_file)
                st.write("**Preview of uploaded file:**")
                st.dataframe(df_input.head(), width='stretch')
                
                # Try to identify the URL column
                url_column = None
                possible_columns = ['url', 'website', 'link', 'site']
                
                for col in possible_columns:
                    if col.lower() in [c.lower() for c in df_input.columns]:
                        url_column = next(c for c in df_input.columns if c.lower() == col.lower())
                        break
                
                if url_column is None:
                    # Use the first column if no obvious URL column is found
                    url_column = df_input.columns[0]
                    st.info(f"Using '{url_column}' column as URL source")
                else:
                    st.info(f"Found URL column: '{url_column}'")
                
                # Process button for CSV
                if st.button("Extract Emails from CSV", key="csv_extract"):
                    # Get URLs from the identified column
                    urls = df_input[url_column].dropna().tolist()
                    
                    if urls:
                        # Show progress
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Start timing
                        start_time = time.time()
                        
                        # Extract emails with enhanced progress tracking
                        def progress_update(current, total):
                            progress = current / total
                            percentage = int(progress * 100)
                            progress_bar.progress(progress)
                            status_text.text(f'Processing: {current}/{total} websites completed ({percentage}%)')
                        
                        results = extractor.extract_emails_from_urls(
                            urls,
                            progress_callback=progress_update
                        )
                        
                        # Calculate processing time
                        processing_time = time.time() - start_time
                        
                        # Process results
                        if results:
                            st.success(f"✅ Processing completed in {processing_time:.2f} seconds")
                            
                            # Create DataFrame for results
                            df_results = []
                            for result in results:
                                if result['emails']:
                                    # Combine all emails for this website into a single cell
                                    emails_str = ', '.join(sorted(result['emails']))
                                    
                                    # Get only the pages that actually found emails
                                    source_pages = result.get('email_sources', [])
                                    source_str = ', '.join(source_pages) if source_pages else result['url']
                                    
                                    df_results.append({
                                        'Website': result['url'],
                                        'Emails': emails_str,
                                        'Source Pages': source_str,
                                        'Contact Form Found': 'Yes' if result.get('has_contact_form', False) else 'No',
                                        'Status': result['status'],
                                        'Pages Crawled': result.get('successful_pages', 1)
                                    })
                                else:
                                    df_results.append({
                                        'Website': result['url'],
                                        'Emails': 'No emails found',
                                        'Source Pages': 'None',
                                        'Contact Form Found': 'Yes' if result.get('has_contact_form', False) else 'No',
                                        'Status': result['status'],
                                        'Pages Crawled': result.get('successful_pages', 0)
                                    })
                            
                            if df_results:
                                df_final = pd.DataFrame(df_results)
                                st.dataframe(df_final, width='stretch')
                                
                                # Download button
                                csv_buffer = io.StringIO()
                                df_final.to_csv(csv_buffer, index=False)
                                csv_data = csv_buffer.getvalue()
                                
                                st.download_button(
                                    label="📥 Download Results as CSV",
                                    data=csv_data,
                                    file_name=f"csv_email_extraction_results_{int(time.time())}.csv",
                                    mime="text/csv"
                                )
                            else:
                                st.warning("No emails were extracted from the URLs in the CSV file")
                        else:
                            st.error("Failed to process URLs from the CSV file")
                    else:
                        st.warning("No valid URLs found in the selected column")
                        
            except Exception as e:
                st.error(f"Error reading CSV file: {str(e)}")
    
    # Add information section
    with st.expander("ℹ️ How to use this tool"):
        st.markdown("""
        **Text Input Method:**
        1. Enter website URLs in the text area (one per line or comma-separated)
        2. Click "Extract Emails" to process the URLs
        3. View results in real-time and download as CSV
        
        **CSV Upload Method:**
        1. Upload a CSV file containing website URLs
        2. The tool will automatically detect the URL column
        3. Click "Extract Emails from CSV" to process
        4. Download the results as a new CSV file
        
        **Features:**
        - Extracts email addresses from website content
        - Tracks the source website for each email
        - Shows processing time for performance monitoring
        - Handles multiple URLs concurrently for faster processing
        - Provides detailed status information for each URL
        """)

def create_project_zip():
    """
    Create a zip file containing all project files
    """
    zip_buffer = io.BytesIO()
    
    # Define files to include in the zip
    project_files = [
        'app.py',
        'email_extractor.py',
        '.streamlit/config.toml',
        'replit.md'
    ]
    
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in project_files:
            if os.path.exists(file_path):
                zip_file.write(file_path, file_path)
                
        # Also add any additional files if they exist
        additional_files = ['requirements.txt', 'README.md', 'pyproject.toml']
        for file_path in additional_files:
            if os.path.exists(file_path):
                zip_file.write(file_path, file_path)
    
    zip_buffer.seek(0)
    return zip_buffer.getvalue()

if __name__ == "__main__":
    main()
    
    # Create the zip file
    zip_data = create_project_zip()
    
    # White file icon in bottom right corner
    st.download_button(
        label="⬇",
        data=zip_data,
        file_name="email_extractor_project.zip",
        mime="application/zip",
        help="Download complete project"
    )
    
    # CSS to position and style the download icon
    st.markdown("""
    <style>
    div[data-testid="stDownloadButton"] {
        position: fixed !important;
        bottom: 20px !important;
        right: 20px !important;
        z-index: 999 !important;
    }
    div[data-testid="stDownloadButton"] button {
        background-color: transparent !important;
        border: none !important;
        color: white !important;
        font-size: 24px !important;
        padding: 8px !important;
        border-radius: 50% !important;
        width: 50px !important;
        height: 50px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }
    div[data-testid="stDownloadButton"] button:hover {
        background-color: rgba(255,255,255,0.1) !important;
    }
    </style>
    """, unsafe_allow_html=True)
