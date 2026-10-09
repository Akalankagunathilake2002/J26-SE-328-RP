import os
import sys
import argparse

from .utils import load_csv, safe_write_csv, load_existing_reviews
from .compare_roles import compare_roles
from .compare_skills import compare_skills
from .compare_software import compare_software

def main():
    parser = argparse.ArgumentParser(description="Compare ESCO and O*NET data.")
    parser.add_argument("--esco-dir", type=str, default="seed/curated/esco",
                        help="Directory containing ESCO curated data.")
    parser.add_argument("--onet-dir", type=str, default="seed/curated/onet",
                        help="Directory containing O*NET curated data.")
    parser.add_argument("--output-dir", type=str, default="seed/curated/comparison",
                        help="Directory to save comparison outputs.")
    
    args = parser.parse_args()

    base_dir = os.getcwd()
    esco_dir = os.path.join(base_dir, args.esco_dir)
    onet_dir = os.path.join(base_dir, args.onet_dir)
    output_dir = os.path.join(base_dir, args.output_dir)

    os.makedirs(output_dir, exist_ok=True)

    print("Loading prepared data...")
    esco_roles = load_csv(os.path.join(esco_dir, "esco_roles_candidates.csv"))
    esco_skills = load_csv(os.path.join(esco_dir, "esco_skills_candidates.csv"))
    onet_roles = load_csv(os.path.join(onet_dir, "onet_roles_candidates.csv"))
    onet_skills = load_csv(os.path.join(onet_dir, "onet_skills_candidates.csv"))
    
    software_file = os.path.join(onet_dir, "onet_software_candidates.csv")
    onet_software = load_csv(software_file) if os.path.exists(software_file) else []

    if not esco_roles or not onet_roles:
        print("Missing required candidate files. Run preparation pipelines first.")
        sys.exit(1)

    print("Comparing Roles...")
    roles_out = os.path.join(output_dir, "role_matches.csv")
    r_matches, r_un_esco, r_un_onet, r_report = compare_roles(
        esco_roles, onet_roles, 
        existing_reviews=load_existing_reviews(roles_out)
    )
    safe_write_csv(r_matches, roles_out, ['match_id', 'esco_uri', 'esco_name', 'onet_source_id', 'onet_name', 'match_method', 'match_score', 'review_status', 'review_notes'])

    print("Comparing Skills...")
    skills_out = os.path.join(output_dir, "skill_matches.csv")
    s_matches, s_un_esco, s_un_onet, s_report = compare_skills(
        esco_skills, onet_skills,
        existing_reviews=load_existing_reviews(skills_out)
    )
    safe_write_csv(s_matches, skills_out, ['match_id', 'esco_uri', 'esco_name', 'esco_skill_type', 'esco_domain', 'onet_source_id', 'onet_name', 'onet_skill_type', 'onet_domain', 'match_method', 'match_score', 'domain_conflict', 'review_status', 'review_notes'])
    
    safe_write_csv(s_un_esco, os.path.join(output_dir, "unmatched_esco_skills.csv"), list(esco_skills[0].keys()) if esco_skills else [])
    safe_write_csv(s_un_onet, os.path.join(output_dir, "unmatched_onet_skills.csv"), list(onet_skills[0].keys()) if onet_skills else [])

    sw_report = None
    if onet_software:
        print("Comparing Software Technologies...")
        sw_out = os.path.join(output_dir, "technology_matches.csv")
        sw_matches, sw_report = compare_software(
            esco_skills, onet_software,
            existing_reviews=load_existing_reviews(sw_out)
        )
        safe_write_csv(sw_matches, sw_out, ['match_id', 'esco_uri', 'esco_name', 'esco_skill_type', 'onet_element_id', 'onet_software_category', 'onet_technology_example', 'match_method', 'match_score', 'review_status', 'review_notes'])

    # Write Report
    report_path = os.path.join(output_dir, "comparison_report.txt")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("ESCO-O*NET Comparison Report\n")
        f.write("============================\n\n")
        
        f.write("Role Comparison Summary:\n")
        f.write(f"- Exact matches: {r_report['exact_matches']}\n")
        f.write(f"- Alternative matches: {r_report['alternative_matches']}\n")
        f.write(f"- Fuzzy matches: {r_report['fuzzy_matches']}\n")
        f.write(f"- Unmatched ESCO roles: {r_report['unmatched_esco']}\n")
        f.write(f"- Unmatched O*NET roles: {r_report['unmatched_onet']}\n\n")
        
        f.write("Skill/Knowledge Comparison Summary:\n")
        f.write(f"- Exact matches: {s_report['exact_matches']}\n")
        f.write(f"- Alternative matches: {s_report['alternative_matches']}\n")
        f.write(f"- Fuzzy matches: {s_report['fuzzy_matches']}\n")
        f.write(f"- Unmatched ESCO skills: {s_report['unmatched_esco']}\n")
        f.write(f"- Unmatched O*NET skills: {s_report['unmatched_onet']}\n")
        f.write(f"- Missing ESCO types: {s_report['missing_esco_types']}\n")
        f.write(f"- Conflicting Domains: {s_report['conflicting_domains']}\n\n")
        
        if sw_report:
            f.write("Technology/Software Comparison Summary:\n")
            f.write(f"- Exact matches: {sw_report['exact_matches']}\n")
            f.write(f"- Alternative matches: {sw_report['alternative_matches']}\n")
            f.write(f"- Fuzzy matches: {sw_report['fuzzy_matches']}\n")
            f.write(f"- Unmatched O*NET technologies: {sw_report['unmatched_software']}\n")

    print(f"Comparison complete. Report saved to {report_path}")

if __name__ == "__main__":
    main()
