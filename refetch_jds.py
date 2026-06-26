import os
import re
from scrape import fetch_full_jd

def main():
    jobs_dir = "jobs"
    count = 0
    for fname in os.listdir(jobs_dir):
        if not fname.endswith(".md"): continue
        filepath = os.path.join(jobs_dir, fname)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        if "Visit the link for full job details" in content and "LinkedIn" in content:
            # Extract URL
            m = re.search(r'^url:\s*"(.+?)"', content, re.MULTILINE)
            if not m: continue
            url = m.group(1)
            
            jd = fetch_full_jd(url, "LinkedIn")
            if jd:
                content = content.replace("- Visit the link for full job details.", f"- Visit the link for full job details.\n\n### Full Job Description\n{jd}")
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Updated {fname}")
                count += 1
                if count >= 20: # Just do 20 for testing
                    break
    print(f"Finished updating {count} jobs.")

if __name__ == "__main__":
    main()
