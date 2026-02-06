# Email Extractor Tool

## Overview

The Email Extractor Tool is a web-based application built with Streamlit that allows users to extract email addresses from websites. The tool provides two input methods: direct text input for URLs and CSV file uploads. It uses concurrent processing to efficiently scrape multiple websites simultaneously and tracks the source of each extracted email address. The application features a clean, user-friendly interface with progress tracking and real-time results display.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
The application uses Streamlit as the web framework, providing a simple yet effective user interface. The frontend is organized with:
- **Tab-based Interface**: Separates different input methods (text input vs CSV upload) for better user experience
- **Real-time Progress Tracking**: Shows extraction progress with progress bars and status updates
- **Responsive Layout**: Uses Streamlit's wide layout configuration for better screen utilization
- **Interactive Results Display**: Provides immediate feedback and results visualization

### Backend Architecture
The core functionality is split into two main components:
- **Main Application (app.py)**: Handles the Streamlit interface, user interactions, and orchestrates the email extraction process
- **Email Extractor Module (email_extractor.py)**: Contains the core business logic for web scraping and email extraction

### Data Processing Pipeline
The system implements a concurrent processing approach:
- **Multi-threading**: Uses ThreadPoolExecutor for parallel website processing to improve performance
- **Session Management**: Maintains persistent HTTP sessions for efficient connection reuse
- **URL Normalization**: Automatically adds protocol prefixes to URLs when missing
- **Regex-based Email Detection**: Uses compiled regular expressions for efficient email pattern matching

### Web Scraping Strategy
The email extraction process follows these architectural decisions:
- **BeautifulSoup Integration**: Uses BeautifulSoup for HTML parsing and content extraction
- **User Agent Spoofing**: Implements browser-like headers to avoid bot detection
- **Timeout Management**: Configurable request timeouts to prevent hanging operations
- **Error Handling**: Robust error handling for network failures and invalid URLs

### Data Structure Design
- **Source Tracking**: Each extracted email is linked to its source URL for traceability
- **Deduplication**: Implements mechanisms to handle duplicate emails across multiple sources
- **Flexible Input Processing**: Supports both comma-separated and newline-separated URL inputs

## External Dependencies

### Core Libraries
- **Streamlit**: Web application framework for creating the user interface
- **Pandas**: Data manipulation and analysis for handling CSV files and results
- **Requests**: HTTP library for making web requests to target websites
- **BeautifulSoup4**: HTML/XML parsing library for extracting content from web pages

### System Libraries
- **concurrent.futures**: Python's built-in threading support for parallel processing
- **urllib.parse**: URL parsing and manipulation utilities
- **logging**: Built-in logging system for debugging and monitoring
- **re**: Regular expression support for email pattern matching
- **time**: Time-related functions for progress tracking and delays
- **io**: Input/output operations for file handling