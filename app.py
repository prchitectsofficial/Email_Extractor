import streamlit as st
import pandas as pd
import time
import io
from email_extractor import EmailExtractor
from history_manager import HistoryManager

def main():
    st.set_page_config(
        page_title="Email Extractor Tool",
        page_icon="📧",
        layout="wide",
        menu_items={
            'Get Help': None,
            'Report a bug': None,
            'About': None
        }
    )
    
    # Custom CSS for better styling
    st.markdown("""
    <style>
    /* Hide deploy button and menu */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stDeployButton {display:none;}
    
    /* Center align heading */
    .main .block-container {
        padding-top: 2rem;
    }
    
    h1 {
        text-align: center;
        font-size: 3.5rem !important;
        font-weight: 700 !important;
        color: #1f77b4 !important;
        margin-bottom: 0.5rem !important;
        letter-spacing: -0.02em !important;
    }
    
    /* Subtitle styling */
    .subtitle {
        text-align: center;
        font-size: 1.2rem;
        color: #666;
        margin-bottom: 3rem;
        font-weight: 300;
    }
    
    /* Section headers */
    h2 {
        font-size: 1.8rem !important;
        font-weight: 600 !important;
        color: #2c3e50 !important;
        margin-top: 2rem !important;
        margin-bottom: 1rem !important;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #e0e0e0;
    }
    
    h3 {
        font-size: 1.4rem !important;
        font-weight: 500 !important;
        color: #34495e !important;
        margin-top: 1.5rem !important;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        margin-bottom: 2rem;
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 14px 28px;
        font-size: 1.1rem;
        font-weight: 600;
        border-radius: 12px 12px 0 0;
        background: #f8f9fa;
        color: #495057;
        transition: all 0.3s ease;
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: #e9ecef;
        transform: translateY(-2px);
    }
    
    .stTabs [aria-selected="true"]:hover {
        background: linear-gradient(135deg, #5568d3 0%, #6a3f8f 100%);
    }
    
    /* Button styling */
    .stButton > button {
        width: 100%;
        background-color: #1f77b4;
        color: white;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        border: none;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        background-color: #1565a0;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(31, 119, 180, 0.3);
    }
    
    /* Input area styling */
    .stTextArea textarea {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        padding: 12px;
    }
    
    .stTextArea textarea:focus {
        border-color: #1f77b4;
        box-shadow: 0 0 0 3px rgba(31, 119, 180, 0.1);
    }
    
    /* Success/Info messages */
    .stSuccess {
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Dataframe styling */
    .dataframe {
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Metrics styling */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 700 !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        font-weight: 500 !important;
    }
    
    /* Divider styling */
    hr {
        margin: 2rem 0;
        border: none;
        border-top: 1px solid #e0e0e0;
    }
    
    /* Download button styling - icon only, no background */
    .stDownloadButton > button {
        background-color: transparent !important;
        color: #28a745 !important;
        font-size: 1.5rem !important;
        padding: 0.2rem 0.4rem !important;
        border: none !important;
        border-radius: 0 !important;
        font-weight: normal !important;
        min-width: auto !important;
        width: auto !important;
        box-shadow: none !important;
    }
    
    .stDownloadButton > button:hover {
        background-color: transparent !important;
        color: #218838 !important;
        box-shadow: none !important;
        transform: scale(1.1);
    }
    
    .stDownloadButton > button:focus {
        box-shadow: none !important;
    }
    
    /* History table styling */
    .history-row {
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
    }
    
    /* Section backgrounds for differentiation */
    section[data-testid="stTabs"] > div:first-child {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 2rem;
    }
    
    /* Tab content styling */
    .stTabs [data-baseweb="tab-panel"] {
        padding: 2rem 0;
    }
    
    /* Text input section styling */
    .element-container:has(textarea) {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
    }
    
    /* Fix textarea overflow */
    .stTextArea textarea {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        padding: 12px;
        width: 100% !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
        resize: vertical !important;
        overflow-x: hidden !important;
        word-wrap: break-word !important;
    }
    
    .stTextArea > div > div {
        width: 100% !important;
        max-width: 100% !important;
    }
    
    /* Fix input container */
    .stTextArea {
        width: 100% !important;
        max-width: 100% !important;
    }
    
    /* Ensure proper container width */
    .main .block-container {
        max-width: 100% !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    
    /* File uploader styling */
    .uploadedFile {
        background: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* Results section styling */
    .element-container:has([data-testid="stDataFrame"]) {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin: 1.5rem 0;
    }
    
    /* Statistics cards */
    [data-testid="stMetricContainer"] {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        color: white;
    }
    
    [data-testid="stMetricContainer"] [data-testid="stMetricValue"],
    [data-testid="stMetricContainer"] [data-testid="stMetricLabel"] {
        color: white !important;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Success message styling */
    .stSuccess {
        background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
        border-left: 4px solid #28a745;
    }
    
    /* Warning message styling */
    .stWarning {
        background: linear-gradient(135deg, #ffeaa7 0%, #fdcb6e 100%);
        border-left: 4px solid #ffc107;
    }
    
    /* Error message styling */
    .stError {
        background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
        border-left: 4px solid #dc3545;
    }
    
    /* Info message styling */
    .stInfo {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        border-left: 4px solid #17a2b8;
    }
    
    /* History table row styling */
    .history-table-row {
        background: #ffffff;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        transition: all 0.3s ease;
    }
    
    .history-table-row:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    
    /* Divider styling */
    hr {
        background: linear-gradient(90deg, transparent, #667eea, transparent);
        height: 2px;
        border: none;
        margin: 2rem 0;
    }
    
    /* Search input styling */
    .stTextInput > div > div > input {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
        padding: 0.75rem;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Selectbox styling */
    .stSelectbox > div > div {
        border-radius: 8px;
        border: 2px solid #e0e0e0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Centered heading
    st.markdown("<h1>📧 Email Extractor Tool</h1>", unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Extract email addresses from websites with source tracking</p>', unsafe_allow_html=True)
    
    # Initialize the email extractor and history manager
    extractor = EmailExtractor()
    history_manager = HistoryManager(
        host='localhost',
        database='email_extractor',
        user='root',
        password='admin',
        port=3306
    )
    
    # Create tabs for different input methods
    tab1, tab2, tab3 = st.tabs(["Text Input", "CSV Upload", "📜 History"])
    
    with tab1:
        st.markdown("### 📝 Enter Website URLs")
        st.markdown("Enter multiple URLs separated by commas or new lines")
        st.markdown("---")
        
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
                    
                    # Generate extraction name for text input
                    history = history_manager.load_history()
                    extraction_num = len(history) + 1
                    extraction_name = f"Extraction {extraction_num}"
                    
                    # Save to history
                    history_manager.save_extraction(urls, results, processing_time, "text", extraction_name)
                    
                    # Display results
                    if results:
                        st.success(f"✅ Processing completed in {processing_time:.2f} seconds")
                        
                        # Create DataFrame for display with separate columns for each email
                        df_results = []
                        for result in results:
                            # Get emails (already limited to 5)
                            emails = result.get('emails', [])[:5] if result.get('emails') else []
                            
                            # Get only the pages that actually found emails
                            source_pages = result.get('email_sources', [])
                            source_str = ', '.join(source_pages[:3]) if source_pages else result['url']
                            if len(source_pages) > 3:
                                source_str += f" ... (+{len(source_pages) - 3} more)"
                            
                            # Create row with separate columns for each email (max 5)
                            row = {
                                'Website': result['url'],
                                'Email 1': emails[0] if len(emails) > 0 else '',
                                'Email 2': emails[1] if len(emails) > 1 else '',
                                'Email 3': emails[2] if len(emails) > 2 else '',
                                'Email 4': emails[3] if len(emails) > 3 else '',
                                'Email 5': emails[4] if len(emails) > 4 else '',
                                'Source Pages': source_str,
                                'Contact Form Found': 'Yes' if result.get('has_contact_form', False) else 'No',
                                'Status': result['status'],
                                'Pages Crawled': result.get('successful_pages', 0)
                            }
                            df_results.append(row)
                        
                        if df_results:
                            df = pd.DataFrame(df_results)
                            st.dataframe(df, use_container_width=True)
                            
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
        st.markdown("### 📤 Upload CSV File")
        st.markdown("Upload a CSV file containing website URLs")
        st.markdown("---")
        
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
                st.dataframe(df_input.head(), use_container_width=True)
                
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
                        
                        # Get CSV filename for name
                        csv_filename = uploaded_file.name
                        # Remove extension
                        if csv_filename.endswith('.csv'):
                            csv_name = csv_filename[:-4]
                        else:
                            csv_name = csv_filename
                        
                        # Save to history
                        history_manager.save_extraction(urls, results, processing_time, "csv", csv_name)
                        
                        # Process results
                        if results:
                            st.success(f"✅ Processing completed in {processing_time:.2f} seconds")
                            
                            # Create DataFrame for results with separate columns for each email
                            df_results = []
                            for result in results:
                                # Get emails (already limited to 5)
                                emails = result.get('emails', [])[:5] if result.get('emails') else []
                                
                                # Get only the pages that actually found emails
                                source_pages = result.get('email_sources', [])
                                source_str = ', '.join(source_pages[:3]) if source_pages else result['url']
                                if len(source_pages) > 3:
                                    source_str += f" ... (+{len(source_pages) - 3} more)"
                                
                                # Create row with separate columns for each email (max 5)
                                row = {
                                    'Website': result['url'],
                                    'Email 1': emails[0] if len(emails) > 0 else '',
                                    'Email 2': emails[1] if len(emails) > 1 else '',
                                    'Email 3': emails[2] if len(emails) > 2 else '',
                                    'Email 4': emails[3] if len(emails) > 3 else '',
                                    'Email 5': emails[4] if len(emails) > 4 else '',
                                    'Source Pages': source_str,
                                    'Contact Form Found': 'Yes' if result.get('has_contact_form', False) else 'No',
                                    'Status': result['status'],
                                    'Pages Crawled': result.get('successful_pages', 0)
                                }
                                df_results.append(row)
                            
                            if df_results:
                                df_final = pd.DataFrame(df_results)
                                st.dataframe(df_final, use_container_width=True)
                                
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
    
    with tab3:
        st.markdown("### 📜 Extraction History")
        st.markdown("View and manage your past email extraction results")
        st.markdown("---")
        
        # Load history
        history = history_manager.load_history()
        
        if not history:
            st.info("📭 No extraction history found. Start extracting emails to see your history here!")
        else:
            # Statistics section
            stats = history_manager.get_statistics()
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Extractions", stats['total_extractions'])
            with col2:
                st.metric("Total URLs Processed", stats['total_urls_processed'])
            with col3:
                st.metric("Total Emails Found", stats['total_emails_found'])
            with col4:
                st.metric("Avg Processing Time", f"{stats['average_processing_time']}s")
            
            st.divider()
            
            # Search and filter section
            col1, col2 = st.columns([2, 1])
            with col1:
                search_query = st.text_input("🔍 Search History", placeholder="Search by URL or email address...")
            with col2:
                sort_option = st.selectbox("Sort By", ["Most Recent", "Oldest First", "Most Emails", "Longest Time"])
            
            # Filter history based on search
            filtered_history = history
            if search_query:
                filtered_history = history_manager.search_history(search_query)
                if not filtered_history:
                    st.info(f"No results found for '{search_query}'")
            
            # Sort history
            if sort_option == "Most Recent":
                filtered_history = sorted(filtered_history, key=lambda x: x.get('timestamp', ''), reverse=True)
            elif sort_option == "Oldest First":
                filtered_history = sorted(filtered_history, key=lambda x: x.get('timestamp', ''))
            elif sort_option == "Most Emails":
                filtered_history = sorted(filtered_history, key=lambda x: x.get('total_emails_found', 0), reverse=True)
            elif sort_option == "Longest Time":
                filtered_history = sorted(filtered_history, key=lambda x: x.get('processing_time', 0), reverse=True)
            
            # Display history entries in table format
            if filtered_history:
                st.write(f"**Showing {len(filtered_history)} extraction(s)**")
                
                # Create table data with only requested columns
                table_data = []
                for idx, entry in enumerate(filtered_history):
                    # Get name from entry (CSV filename or "Extraction X")
                    # If no name exists (old entries), generate one
                    name = entry.get('name')
                    if not name:
                        # Generate name for old entries without name field
                        extraction_num = len(filtered_history) - idx
                        name = f"Extraction {extraction_num}"
                    
                    # Format timestamp as date and time
                    timestamp = entry.get('timestamp', 'Unknown')
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        date_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                    except:
                        date_time = timestamp[:19] if len(timestamp) > 19 else timestamp
                    
                    # Prepare full CSV data with all details
                    results = entry.get('results', [])
                    csv_rows = []
                    for result in results:
                        emails = result.get('emails', [])[:5] if result.get('emails') else []
                        source_pages = result.get('email_sources', [])
                        source_str = ', '.join(source_pages) if source_pages else result.get('url', 'N/A')
                        
                        row = {
                            'Website': result.get('url', 'N/A'),
                            'Email 1': emails[0] if len(emails) > 0 else '',
                            'Email 2': emails[1] if len(emails) > 1 else '',
                            'Email 3': emails[2] if len(emails) > 2 else '',
                            'Email 4': emails[3] if len(emails) > 3 else '',
                            'Email 5': emails[4] if len(emails) > 4 else '',
                            'Source Pages': source_str,
                            'Contact Form Found': 'Yes' if result.get('has_contact_form', False) else 'No',
                            'Status': result.get('status', 'N/A'),
                            'Pages Crawled': result.get('successful_pages', 0)
                        }
                        csv_rows.append(row)
                    
                    # Create CSV data
                    csv_buffer = io.StringIO()
                    if csv_rows:
                        df_csv = pd.DataFrame(csv_rows)
                        df_csv.to_csv(csv_buffer, index=False)
                        csv_data = csv_buffer.getvalue()
                    else:
                        csv_data = "Website,Email 1,Email 2,Email 3,Email 4,Email 5,Source Pages,Contact Form Found,Status,Pages Crawled\n"
                    
                    table_data.append({
                        'Name': name,
                        'Date_Time': date_time,
                        'Processing Time': f"{entry.get('processing_time', 0)}s",
                        'Total Input URLs': entry.get('total_urls', 0),
                        'Email Found': entry.get('total_emails_found', 0),
                        'Download': entry.get('id', ''),
                        '_csv_data': csv_data,  # Store CSV data for download
                        '_entry_id': entry.get('id', '')  # Store entry ID for delete
                    })
                
                # Display table with download buttons in rows
                if table_data:
                    # Create table header
                    header_cols = st.columns([2.5, 2, 1.5, 1, 1, 1.2])
                    with header_cols[0]:
                        st.markdown("**Name**")
                    with header_cols[1]:
                        st.markdown("**Date and Time**")
                    with header_cols[2]:
                        st.markdown("**Processing Time**")
                    with header_cols[3]:
                        st.markdown("**Total Input URLs**")
                    with header_cols[4]:
                        st.markdown("**Email Found**")
                    with header_cols[5]:
                        st.markdown("**Download**")
                    st.divider()
                    
                    # Create table rows with download buttons
                    for idx, row_data in enumerate(table_data):
                        row_cols = st.columns([2.5, 2, 1.5, 1, 1, 1.2])
                        with row_cols[0]:
                            st.write(row_data['Name'])
                        with row_cols[1]:
                            st.write(row_data['Date_Time'])
                        with row_cols[2]:
                            st.write(row_data['Processing Time'])
                        with row_cols[3]:
                            st.write(row_data['Total Input URLs'])
                        with row_cols[4]:
                            st.write(row_data['Email Found'])
                        with row_cols[5]:
                            # Use the name for download filename
                            download_filename = f"{row_data['Name']}.csv"
                            st.download_button(
                                label="📥",
                                data=row_data['_csv_data'],
                                file_name=download_filename,
                                mime="text/csv",
                                key=f"download_{row_data['_entry_id']}",
                                type="primary",
                                use_container_width=True
                            )
                        if idx < len(table_data) - 1:
                            st.divider()
    


if __name__ == "__main__":
    main()
