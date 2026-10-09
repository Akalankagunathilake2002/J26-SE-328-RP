import os
import sys
import argparse
from typing import Dict, Any

from scripts.esco.prepare_roles import process_roles
from scripts.esco.prepare_skills import process_skills

def main():
    parser = argparse.ArgumentParser(description="Prepare ESCO data for review and import.")
    parser.add_argument("--input-dir", type=str, default="seed/esco",
                        help="Directory containing raw ESCO CSV files.")
    parser.add_argument("--output-dir", type=str, default="seed/curated/esco",
                        help="Directory to save generated candidates and approved files.")
    parser.add_argument("--only-approved-roles", action="store_true",
                        help="Only process skills for APPROVED roles.")
    
    args = parser.parse_args()
    
    only_approved_roles = args.only_approved_roles

    # Resolve paths relative to the current working directory
    base_dir = os.getcwd()
    input_dir = os.path.join(base_dir, args.input_dir)
    output_dir = os.path.join(base_dir, args.output_dir)

    if not os.path.exists(input_dir):
        print(f"Error: Input directory {input_dir} not found.")
        print("Please run this script from the services/shared-skill-knowledge directory.")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    report = {
        'source_occupations_read': 0,
        'candidate_roles_generated': 0,
        'roles_by_domain': {},
        'duplicate_role_uris_detected': 0,
        
        'source_skills_read': 0,
        'skills_associated_with_roles': 0,
        'unique_skill_uris_selected': 0,
        'missing_skill_references': 0,
        'missing_skill_types': 0,
        'duplicate_skill_uris_detected': 0,
        
        'roles_approved': 0,
        'roles_excluded': 0,
        'roles_pending': 0,
        
        'skills_approved': 0,
        'skills_excluded': 0,
        'skills_pending': 0,
        
        'parsing_errors': []
    }

    config_dir = os.path.join(base_dir, "scripts", "esco")

    print("Starting ESCO data preparation...")
    
    print("Processing roles...")
    try:
        process_roles(input_dir, output_dir, report, config_dir=config_dir)
    except Exception as e:
        report['parsing_errors'].append(f"Roles processing error: {str(e)}")
        print(f"Roles processing error: {e}")

    print("Processing skills...")
    try:
        process_skills(input_dir, output_dir, report, only_approved_roles=only_approved_roles)
    except Exception as e:
        report['parsing_errors'].append(f"Skills processing error: {str(e)}")
        print(f"Skills processing error: {e}")

    report_path = os.path.join(output_dir, 'esco_preparation_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("ESCO Data Preparation Report\n")
        f.write("============================\n\n")
        
        f.write("Roles Summary:\n")
        f.write(f"- Source occupations read: {report['source_occupations_read']}\n")
        f.write(f"- Candidate roles generated: {report['candidate_roles_generated']}\n")
        f.write(f"- Duplicate role URIs detected: {report['duplicate_role_uris_detected']}\n")
        f.write("- Roles by domain:\n")
        for domain, count in report['roles_by_domain'].items():
            f.write(f"  * {domain}: {count}\n")
        f.write(f"- Review status (Roles): Approved={report['roles_approved']}, Excluded={report['roles_excluded']}, Pending/Review={report['roles_pending']}\n\n")

        f.write("Skills Summary:\n")
        f.write(f"- Source skills read: {report['source_skills_read']}\n")
        f.write(f"- Skills associated with selected roles: {report['skills_associated_with_roles']}\n")
        f.write(f"- Unique skill URIs selected: {report['unique_skill_uris_selected']}\n")
        f.write(f"- Missing skill references: {report['missing_skill_references']}\n")
        f.write(f"- Missing skill types: {report['missing_skill_types']}\n")
        f.write(f"- Duplicate skill URIs detected: {report['duplicate_skill_uris_detected']}\n")
        f.write(f"- Associations (Essential): {report.get('essential_associations', 0)}\n")
        f.write(f"- Associations (Optional): {report.get('optional_associations', 0)}\n")
        f.write(f"- Review status (Skills): Approved={report['skills_approved']}, Excluded={report['skills_excluded']}, Pending/Review={report['skills_pending']}\n\n")
        
        if report['parsing_errors']:
            f.write("Errors/Warnings:\n")
            for err in report['parsing_errors']:
                f.write(f"- {err}\n")
        else:
            f.write("Errors/Warnings: None\n")

    print(f"Preparation complete. Report saved to {report_path}")

    if report['parsing_errors']:
        print("Pipeline completed with errors.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
