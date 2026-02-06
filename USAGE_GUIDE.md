# 📧 Email Extractor Tool - Usage Guide

## 🚀 Quick Start

### Step 1: Install Dependencies

Make sure you have Python 3.11 or higher installed. Then install the required packages:

```bash
pip install streamlit beautifulsoup4 pandas requests
```

Or if you have a `requirements.txt` file:
```bash
pip install -r requirements.txt
```

### Step 2: Run the Application

Navigate to the `Email_Extractor` folder and run:

```bash
streamlit run app.py
```

The app will automatically open in your default web browser at `http://localhost:8501`

---

## 📖 How to Use

### Method 1: Text Input Tab

1. **Enter URLs**: 
   - Type or paste website URLs in the text area
   - You can enter multiple URLs separated by:
     - Commas: `https://example.com, https://another-site.com`
     - New lines: One URL per line
     - Or a combination of both

2. **Extract Emails**:
   - Click the "Extract Emails" button
   - Watch the progress bar as it processes each website
   - Results will appear automatically when complete

3. **View Results**:
   - See a table with:
     - Website URLs
     - Extracted email addresses
     - Source pages where emails were found
     - Contact form detection status
     - Processing status

4. **Download Results**:
   - Click "📥 Download Results as CSV" to save the results

### Method 2: CSV Upload Tab

1. **Prepare Your CSV**:
   - Create a CSV file with website URLs
   - The CSV should have a column named: `url`, `website`, `link`, or `site`
   - Or the tool will use the first column automatically

2. **Upload CSV**:
   - Click "Choose a CSV file" and select your file
   - Preview will show the first few rows

3. **Extract Emails**:
   - Click "Extract Emails from CSV"
   - The tool processes all URLs from your CSV file
   - Results display in a table format

4. **Download Results**:
   - Download the results as a new CSV file

### Method 3: History Tab

1. **View History**:
   - Click on the "📜 History" tab
   - See all your past extractions (latest 15 only)

2. **Statistics Dashboard**:
   - View overall statistics:
     - Total extractions performed
     - Total URLs processed
     - Total emails found
     - Average processing time

3. **Search History**:
   - Use the search box to find specific URLs or email addresses
   - Search works across all past extractions

4. **Sort Results**:
   - Sort by:
     - Most Recent (default)
     - Oldest First
     - Most Emails
     - Longest Processing Time

5. **View Details**:
   - Click on any history entry to expand and see:
     - Full extraction details
     - All URLs processed
     - Complete results table
     - Download individual results

6. **Delete Entries**:
   - Click "🗑️ Delete" on any individual entry to remove it
   - Note: History automatically keeps only the latest 15 results

---

## 💡 Tips & Best Practices

### ✅ Best Practices

1. **URL Format**:
   - Include `http://` or `https://` in URLs
   - The tool will add `https://` automatically if missing

2. **Batch Processing**:
   - Process multiple URLs at once for efficiency
   - The tool handles up to 8 concurrent requests

3. **Large CSV Files**:
   - For very large CSV files, consider splitting them into smaller batches
   - This helps with performance and error handling

4. **History Management**:
   - History automatically maintains the latest 15 extractions
   - Older results are automatically removed when new ones are added

### ⚠️ Important Notes

1. **Rate Limiting**:
   - The tool respects website rate limits
   - There's a small delay between requests to be respectful

2. **Processing Time**:
   - Processing time depends on:
     - Number of URLs
     - Website response times
     - Number of pages crawled per site

3. **Email Detection**:
   - The tool finds emails in:
     - Page content
     - Contact pages
     - About pages
     - Mailto links
   - It also handles obfuscated emails (e.g., "email [at] domain [dot] com")

4. **Contact Forms**:
   - The tool detects contact forms but cannot extract emails from them
   - Contact forms require manual interaction

---

## 🔧 Troubleshooting

### App Won't Start
- Make sure all dependencies are installed: `pip install streamlit beautifulsoup4 pandas requests`
- Check Python version: `python --version` (needs 3.11+)

### No Emails Found
- Some websites may not have publicly visible email addresses
- Check if the website has a contact form instead
- Try accessing the website directly to verify it's accessible

### Slow Processing
- Large batches take longer to process
- Some websites may be slow to respond
- Check your internet connection

### CSV Upload Issues
- Ensure your CSV file has a URL column
- Check that URLs are properly formatted
- Make sure the CSV file is not corrupted

---

## 📝 Example Usage

### Example 1: Single Website
```
Input: https://example.com
Result: Extracts all emails found on example.com and its contact pages
```

### Example 2: Multiple Websites
```
Input:
https://company1.com
https://company2.com
https://company3.com

Result: Processes all three websites and shows combined results
```

### Example 3: CSV File
```
CSV Content:
url
https://business1.com
https://business2.com
https://business3.com

Result: Processes all URLs from CSV and generates results table
```

---

## 🎯 Features Summary

- ✅ Extract emails from multiple websites simultaneously
- ✅ Support for text input and CSV file uploads
- ✅ Automatic history tracking (latest 15 results)
- ✅ Search and filter history
- ✅ Download results as CSV
- ✅ Contact form detection
- ✅ Source page tracking
- ✅ Progress tracking
- ✅ Email de-obfuscation
- ✅ Rate limiting for respectful scraping

---

## 📞 Need Help?

If you encounter any issues:
1. Check the troubleshooting section above
2. Verify all dependencies are installed correctly
3. Make sure your URLs are accessible and properly formatted
4. Check the browser console for any error messages

Happy email extracting! 📧✨
