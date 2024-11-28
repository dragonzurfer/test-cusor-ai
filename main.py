import csv
import random
import re

def parse_spintax(text):
    # Parse spintax format {word1|word2|word3}
    pattern = r'{([^{}]+)}'
    while '{' in text:
        text = re.sub(pattern, lambda m: random.choice(m.group(1).split('|')), text)
    return text

def replace_placeholders(text, row, mapping):
    # Replace <column_name> with values from CSV using mapping
    pattern = r'<([^>]+)>'
    return re.sub(pattern, lambda m: row.get(mapping.get(m.group(1), m.group(1)), f"<{m.group(1)}>"), text)

def get_template_placeholders(template):
    # Extract all placeholders from template
    pattern = r'<([^>]+)>'
    return set(re.findall(pattern, template))

def process_template(template_path, subject_template_path, csv_path, body_mapping, subject_mapping, email_column):
    with open(csv_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    with open(template_path, 'r', encoding='utf-8') as template_file:
        body_template = template_file.read()
        
    with open(subject_template_path, 'r', encoding='utf-8') as subject_file:
        subject_template = subject_file.read()

    results = []
    for row in rows:
        # Process subject with spintax
        subject = parse_spintax(subject_template)
        subject = replace_placeholders(subject, row, subject_mapping)
        
        # Process body with spintax
        body = parse_spintax(body_template)
        body = replace_placeholders(body, row, body_mapping)
        
        results.append({
            'recipient_email': row[email_column],
            'subject': subject,
            'body': body
        })

    return results

def main():
    # Ask for file paths
    template_path = input("Enter the path to template.txt: ")
    csv_path = input("Enter the path to data.csv: ")
    
    try:
        results = process_template(template_path, csv_path)
        
        # Print or save results
        for i, result in enumerate(results, 1):
            print(f"\n--- Output {i} ---")
            print(result)
            
    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()