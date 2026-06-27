import extract_msg
import glob
import os

# Automatically finds all .msg files in the current folder
files = glob.glob("*.msg")

if not files:
    print("No .msg files found in the current directory!")
    print("Current directory is:", os.getcwd())

for f in files:
    try:
        m = extract_msg.openMsg(f)
        print("=" * 60)
        print("SUBJECT:", m.subject)
        print("FROM:   ", m.sender)
        print("BODY (first 600 chars):")
        print(m.body[:600])
        print("ATTACHMENTS:")
        
        for a in m.attachments:
            # Check if the attachment has a valid filename and is a PDF
            if a.longFilename and a.longFilename.lower().endswith('.pdf'):
                print(f"  - Saving PDF: {a.longFilename}")
                
                # Save the binary data locally
                with open(a.longFilename, "wb") as pdf_file:
                    pdf_file.write(a.data)
            else:
                # Still list other attachments (like images or system files)
                filename = a.longFilename if a.longFilename else "Unnamed attachment"
                print(f"  - (Skipped non-PDF): {filename}")
        print()
    except Exception as e:
        print(f"Error reading {f}: {e}")