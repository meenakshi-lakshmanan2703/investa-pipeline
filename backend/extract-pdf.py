import pdfplumber
import glob

# Find all the PDF files you just downloaded
pdf_files = glob.glob("*.pdf")

if not pdf_files:
    print("No PDF files found! Double check your folder.")

for pdf_path in pdf_files:
    print("=" * 60)
    print(f"EXTRACTING FROM: {pdf_path}")
    
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = []
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text:
                    full_text.append(text)
            
            # Combine all pages into one single block of text
            combined_pdf_text = "\n".join(full_text)
            
            # Print out the first 500 characters to make sure it worked
            print(f"Successfully extracted {len(pdf.pages)} page(s).")
            print("SAMPLE CONTENT:")
            print(combined_pdf_text[:500])
            print()
            
    except Exception as e:
        print(f"Failed to read {pdf_path}: {e}")