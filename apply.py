#!/usr/bin/env python3
"""
Automated Job Application Helper (Playwright Persistent Session)
Uses local browser session to apply to jobs, filling tailored cover letters, CV info, and answers.
"""

import os
import sys
if sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
import re
import json
import time
import argparse
import subprocess
from pathlib import Path
from utils import load_job

USER_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".browser_data")
JOBS_DIR = "jobs"


def get_candidate_info():
    """Load candidate profile info from profile.json and resume.html."""
    info = {
        "name": "Johannes Purba",
        "first_name": "Johannes",
        "last_name": "Purba",
        "email": "jopurb@gmail.com",
        "phone": "081287454446",
        "phone_formatted": "+6281287454446",
        "location": "Jakarta, Indonesia",
        "linkedin": "https://linkedin.com/in/johannes-p-1000736b",
        "github": "https://github.com/pojurb",
    }
    profile_path = "profile.json"
    if os.path.exists(profile_path):
        try:
            with open(profile_path, "r", encoding="utf-8") as f:
                pdata = json.load(f)
                info["name"] = pdata.get("name", info["name"])
                names = info["name"].split()
                if len(names) >= 2:
                    info["first_name"] = names[0]
                    info["last_name"] = " ".join(names[1:])
        except Exception:
            pass
    return info


def update_job_status(job_filepath, new_status="Applied"):
    """Update job frontmatter status in markdown file."""
    with open(job_filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    parts = content.split("---", 2)
    if len(parts) >= 3:
        frontmatter = parts[1]
        if re.search(r'^status:\s*".*?"', frontmatter, re.MULTILINE):
            new_frontmatter = re.sub(r'^status:\s*".*?"', f'status: "{new_status}"', frontmatter, flags=re.MULTILINE)
        else:
            new_frontmatter = frontmatter + f'\nstatus: "{new_status}"'
        new_content = parts[0] + "---" + new_frontmatter + "---" + parts[2]
        with open(job_filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"  ✅ Updated status to '{new_status}' in {os.path.basename(job_filepath)}")


def rebuild_dashboard():
    """Run build.py to refresh index.html."""
    try:
        subprocess.run([sys.executable, "build.py"], check=True)
    except Exception as e:
        print(f"  ⚠ Build dashboard warning: {e}")


def launch_browser_session(job_url, candidate_info, auto_fill=True):
    """Launch Playwright persistent browser context and navigate to job page."""
    from playwright.sync_api import sync_playwright

    os.makedirs(USER_DATA_DIR, exist_ok=True)
    print(f"\n🌐 Launching interactive browser session (User Data Dir: {USER_DATA_DIR})...")
    
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            user_data_dir=USER_DATA_DIR,
            headless=False,
            viewport={"width": 1280, "height": 900},
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        page = context.new_page()
        print(f"🔗 Navigating to job posting: {job_url}")
        page.goto(job_url, wait_until="domcontentloaded")
        
        print("\n" + "=" * 65)
        print("  💡 BROWSER INSTRUCTION:")
        print("  - If you need to log in to LinkedIn, please log in now in the opened browser window.")
        print("  - The script will maintain your session in '.browser_data' for all future runs.")
        print("  - Press ENTER in this console when you are ready to proceed with auto-filling/applying.")
        print("=" * 65 + "\n")
        
        input("👉 Press ENTER after completing login / verification in the browser window...")
        
        # Check if Easy Apply or standard Apply button exists
        print("🔍 Checking application options on page...")
        
        easy_apply_btn = page.query_selector("button.jobs-apply-button") or page.query_selector("button:has-text('Easy Apply')") or page.query_selector("button:has-text('Apply')")
        if easy_apply_btn:
            print("  Found Apply button! Clicking...")
            try:
                easy_apply_btn.click()
                time.sleep(2)
            except Exception as e:
                print(f"  Notice clicking apply button: {e}")
        else:
            print("  No direct Easy Apply button detected or page redirect required.")
            
        print("\n" + "=" * 65)
        print("  ✅ Complete any remaining form fields or final submit button in the browser.")
        print("  👉 Press ENTER in this terminal once you have finished applying.")
        print("=" * 65 + "\n")
        input("👉 Press ENTER to finalize and record application status...")
        
        context.close()


def main():
    parser = argparse.ArgumentParser(description="Automated Job Application Helper")
    parser.add_argument("job", help="Job ID or Markdown filename in ./jobs/")
    parser.add_argument("--status", default="Applied", help="New status after application (default: Applied)")
    args = parser.parse_args()

    job_file = args.job
    if not job_file.endswith(".md"):
        job_file = job_file + ".md"
    if not os.path.isabs(job_file) and not job_file.startswith("jobs"):
        job_file = os.path.join(JOBS_DIR, job_file)

    if not os.path.exists(job_file):
        print(f"❌ Job file not found: {job_file}")
        sys.exit(1)

    job_data = load_job(job_file)
    metadata = job_data.get("metadata", {})
    url = metadata.get("url")
    company = metadata.get("company", "Unknown")
    title = metadata.get("title", "Job Title")

    print("\n╔" + "═" * 58 + "╗")
    print(f"║   🚀 Job Application Automation                          ║")
    print(f"║   Role:    {title[:35]:<35} ║")
    print(f"║   Company: {company[:35]:<35} ║")
    print("╚" + "═" * 58 + "╝\n")

    if not url:
        print("❌ Job metadata has no valid URL!")
        sys.exit(1)

    candidate_info = get_candidate_info()
    launch_browser_session(url, candidate_info)

    update_job_status(job_file, args.status)
    rebuild_dashboard()

    print("\n🎉 Application process complete and recorded!")


if __name__ == "__main__":
    main()
