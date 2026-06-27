import extract_msg
import pdfplumber
import glob
import os
import json

def extract_pdf_text_from_bytes(attachment_data):
    """Helper function to read PDF text straight from memory without saving it to disk first."""
    try:
        with pdfplumber.open(attachment_data) as pdf:
            pages_text = [page.extract_text() for page in pdf.pages if page.extract_text()]
            return "\n".join(pages_text)
    except Exception as e:
        print(f"Error parsing PDF attachment: {e}")
        return ""

# Automatically finds all .msg files in the current folder
msg_files = glob.glob("*.msg")

all_processed_offers = []

for f in msg_files:
    try:
        msg = extract_msg.openMsg(f)
        print(f"Processing: {msg.subject}")
        
        # Gather Email Context
        email_body = msg.body if msg.body else ""
        combined_text = f"EMAIL SUBJECT: {msg.subject}\nEMAIL SENDER: {msg.sender}\nEMAIL BODY:\n{email_body}\n"
        
        # Gather Attached PDF Context
        pdf_text = ""
        for attachment in msg.attachments:
            if attachment.longFilename and attachment.longFilename.lower().endswith('.pdf'):
                # Wrap the raw binary data in a bytes object for pdfplumber
                import io
                pdf_bytes = io.BytesIO(attachment.data)
                pdf_text += f"\n--- ATTACHMENT EXPOSÉ ({attachment.longFilename}) ---\n"
                pdf_text += extract_pdf_text_from_bytes(pdf_bytes)
        
        complete_payload = combined_text + pdf_text
        
        # Save a copy locally as a text file for debugging
        clean_filename = "".join([c for c in msg.subject if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        with open(f"{clean_filename}_raw_payload.txt", "w", encoding="utf-8") as out_f:
            out_f.write(complete_payload)
            
        all_processed_offers.append({
            "subject": msg.subject,
            "raw_text_payload": complete_payload
        })
        
    except Exception as e:
        print(f"Error compiling payload for {f}: {e}")

print(f"\nSuccessfully compiled {len(all_processed_offers)} full property data payloads!")