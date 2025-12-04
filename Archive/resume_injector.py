from docx import Document

def replace_section(doc_path, section_header, new_content, output_path):
    doc = Document(doc_path)
    in_target_section = False
    
    # 1. Iterate through the document to find the target section
    paragraphs_to_delete = []
    target_index = -1
    
    for i, p in enumerate(doc.paragraphs):
        # Detect the start of the section (e.g., "PROJECTS")
        if section_header.upper() in p.text.upper() and len(p.text) < 50:
            in_target_section = True
            target_index = i + 1 # Start inserting after header
            continue
            
        # Detect the START of the NEXT section (to stop deleting)
        if in_target_section and p.style.name.startswith('Heading'):
            in_target_section = False
            break
            
        # Mark paragraphs for deletion if we are inside the target section
        if in_target_section:
            paragraphs_to_delete.append(p)

    # 2. Delete old content
    for p in paragraphs_to_delete:
        p._element.getparent().remove(p._element)

    # 3. Insert NEW Tailored Content
    if target_index != -1:
        # Insert new bullets reversed so they appear in correct order
        for line in reversed(new_content.split('\n')):
            if line.strip():
                new_p = doc.paragraphs[target_index-1].insert_paragraph_before(line.strip())
                new_p.style = 'List Bullet' # Force bullet format

    doc.save(output_path)
    print(f"✅ Resume updated: {output_path}")

# Example Usage:
# new_project_text = "- Built a Lime IoT Pipeline using AWS Kinesis...\n- Optimized Latency by 40%..."
# replace_section("Master_Resume.docx", "PROJECTS", new_project_text, "Tailored_Resume.docx")