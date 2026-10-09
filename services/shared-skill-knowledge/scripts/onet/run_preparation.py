import os
import sys
import argparse
import csv
from typing import Dict, Any

from scripts.onet.prepare_roles import process_roles
from scripts.onet.prepare_skills import process_skills
from scripts.onet.prepare_software import process_software

def get_source_version(input_dir: str) -> str:
    # Attempt to read the date from knowledge.csv to infer version
    knowledge_file = os.path.join(input_dir, 'knowledge.csv')
    if os.path.exists(knowledge_file):
        with open(knowledge_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            try:
                row = next(reader)
                date = row.get('Date')
                if date:
                    return date
            except StopIteration:
                pass
    return "Unknown"

def main():
    parser = argparse.ArgumentParser(description="Prepare ONET data for review and import.")
    parser.add_argument("--input-dir", type=str, default="seed/onet",
                        help="Directory containing raw ONET CSV files.")
    parser.add_argument("--output-dir", type=str, default="seed/curated/onet",
                        help="Directory to save generated candidates and approved files.")
    parser.add_argument("--only-approved-roles", action="store_true",
                        help="Only process skills and software for APPROVED roles.")
    
    args = parser.parse_args()
    
    only_approved_roles = args.only_approved_roles

    # Resolve paths relative to the current working directory
    base_dir = os.getcwd()
    input_dir = os.path.join(base_dir, args.input_dir)
    output_dir = os.path.join(base_dir, args.output_dir)
    config_dir = os.path.join(base_dir, "scripts", "onet")

    if not os.path.exists(input_dir):
        print(f"Error: Input directory {input_dir} not found.")
        print("Please run this script from the services/shared-skill-knowledge directory.")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    report = {
        'source_occupations_read': 0,
        'candidate_roles_generated': 0,
        'roles_by_domain': {},
        
        'source_skills_knowledge_read': 0,
        'unique_skill_knowledge_selected': 0,
        'duplicate_concept_ids_detected': 0,
        'missing_descriptions': 0,
        
        'source_software_read': 0,
        'unique_software_selected': 0,
        
        'roles_approved': 0,
        'roles_excluded': 0,
        'roles_pending': 0,
        
        'skills_approved': 0,
        'skills_excluded': 0,
        'skills_pending': 0,
        
        'software_approved': 0,
        'software_excluded': 0,
        'software_pending': 0,
        
        'parsing_errors': []
    }

    source_version = get_source_version(input_dir)
    report['source_version'] = source_version

    print(f"Starting O*NET data preparation (Detected Version: {source_version})...")
    
    print("Processing roles...")
    try:
        process_roles(input_dir, output_dir, report, config_dir=config_dir, source_version=source_version)
    except Exception as e:
        report['parsing_errors'].append(f"Roles processing error: {str(e)}")
        print(f"Roles processing error: {e}")

    print("Processing skills and knowledge...")
    try:
        process_skills(input_dir, output_dir, report, only_approved_roles=only_approved_roles, source_version=source_version)
    except Exception as e:
        report['parsing_errors'].append(f"Skills processing error: {str(e)}")
        print(f"Skills processing error: {e}")

    print("Processing software...")
    try:
        process_software(input_dir, output_dir, report, only_approved_roles=only_approved_roles, source_version=source_version)
    except Exception as e:
        report['parsing_errors'].append(f"Software processing error: {str(e)}")
        print(f"Software processing error: {e}")

    report_path = os.path.join(output_dir, 'onet_preparation_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("O*NET Data Preparation Report\n")
        f.write("=============================\n\n")
        
        f.write(f"Source Data Date: {report.get('source_version', 'Unknown')}\n\n")
        
        f.write("Roles Summary:\n")
        f.write(f"- Source occupations read: {report['source_occupations_read']}\n")
        f.write(f"- Candidate roles generated: {report['candidate_roles_generated']}\n")
        f.write("- Roles by domain:\n")
        for domain, count in report['roles_by_domain'].items():
            f.write(f"  * {domain}: {count}\n")
        f.write(f"- Review status (Roles): Approved={report['roles_approved']}, Excluded={report['roles_excluded']}, Pending/Review={report['roles_pending']}\n\n")

        f.write("Skills & Knowledge Summary:\n")
        f.write(f"- Source skills/knowledge rows read: {report['source_skills_knowledge_read']}\n")
        f.write(f"- Unique skill/knowledge concepts selected: {report['unique_skill_knowledge_selected']}\n")
        f.write(f"- Duplicate concept IDs mapped across types: {report['duplicate_concept_ids_detected']}\n")
        f.write(f"- Missing descriptions: {report['missing_descriptions']}\n")
        f.write(f"- Review status (Skills/Knowledge): Approved={report['skills_approved']}, Excluded={report['skills_excluded']}, Pending/Review={report['skills_pending']}\n\n")

        f.write("Software & Technology Summary:\n")
        f.write(f"- Source software rows read: {report['source_software_read']}\n")
        f.write(f"- Unique software candidates selected: {report['unique_software_selected']}\n")
        f.write(f"- Review status (Software): Approved={report['software_approved']}, Excluded={report['software_excluded']}, Pending/Review={report['software_pending']}\n")
        f.write("- NOTE: Software candidates contain specific product examples that require review before canonical import.\n\n")
        
        if report['parsing_errors']:
            f.write("Errors/Warnings:\n")
            for err in report['parsing_errors']:
                f.write(f"- {err}\n")
        else:
            f.write("Errors/Warnings: None\n")

    print(f"Preparation complete. Report saved to {report_path}")

if __name__ == "__main__":
    main()
