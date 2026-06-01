"""
Script to extract raw text from Cameroon legal PDFs, clean formatting/whitespace,
and save them as plain .txt files without modifying the actual text content.
(ASCII safe version to avoid UnicodeEncodeErrors on Windows. Skip-already-processed version.)
"""

import os
import re
import sys
from pypdf import PdfReader

# Add project root to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PDF_DIR = os.path.join("data", "pdfs")
OUTPUT_DIR = os.path.join("data", "extracted_texts")

def clean_extracted_text(text: str) -> str:
    """
    Cleans structural whitespace from the text without altering any words,
    spelling, punctuation, or numbers.
    """
    if not text:
        return ""
        
    # 1. Standardize line endings
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    
    # 2. Strip trailing whitespace from individual lines
    lines = [line.rstrip() for line in text.split("\n")]
    
    # 3. Re-assemble lines
    cleaned_text = "\n".join(lines)
    
    # 4. Collapse excessive consecutive blank lines (more than 2) into exactly one blank line
    cleaned_text = re.sub(r'\n{3,}', '\n\n', cleaned_text)
    
    # 5. Strip leading and trailing whitespace of the entire document
    return cleaned_text.strip()

def process_pdfs():
    """Loops through PDFs, extracts their text, and saves them as .txt files."""
    if not os.path.exists(PDF_DIR):
        print(f"Error: PDF directory '{PDF_DIR}' does not exist.")
        return
        
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    pdf_files = [f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")]
    
    if not pdf_files:
        print(f"No PDF files found in '{PDF_DIR}'.")
        return
        
    print(f"[*] Found {len(pdf_files)} PDF files in total.\n")
    
    success_count = 0
    
    for idx, filename in enumerate(pdf_files, 1):
        pdf_path = os.path.join(PDF_DIR, filename)
        txt_filename = os.path.splitext(filename)[0] + ".txt"
        txt_path = os.path.join(OUTPUT_DIR, txt_filename)
        
        if os.path.exists(txt_path):
            print(f"[{idx}/{len(pdf_files)}] SKIPPED: '{txt_filename}' already exists.")
            continue
            
        print(f"[{idx}/{len(pdf_files)}] Extracting: '{filename}'...")
        
        try:
            reader = PdfReader(pdf_path)
            raw_text = ""
            
            # Extract text page by page with explicit page number markers
            for page_num, page in enumerate(reader.pages, 1):
                page_text = page.extract_text()
                if page_text:
                    raw_text += f"\n[Page {page_num}]\n" + page_text + "\n"
            
            # Clean structural whitespace only
            cleaned_text = clean_extracted_text(raw_text)
            
            if not cleaned_text:
                print(f"  [!] Warning: No text could be extracted from '{filename}' (it may be scanned/image-only).")
                continue
                
            # Write to plain text file
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(cleaned_text)
                
            size_kb = os.path.getsize(txt_path) / 1024
            print(f"  [+] Success: Saved '{txt_filename}' ({size_kb:.1f} KB)")
            success_count += 1
            
        except Exception as e:
            print(f"  [-] Failed to process '{filename}': {e}")
            
    print(f"\n[Done] Processing Complete! Extracted {success_count} file(s) with page markers.")
    print(f"Folder containing extracted text files: '{OUTPUT_DIR}'")

if __name__ == "__main__":
    process_pdfs()
