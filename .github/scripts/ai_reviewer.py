import os
import sys
import google.generativeai as genai
from github import Github

def main():
    # 1. Setup API Keys (Getting them from GitHub Secrets)
    genai.configure(api_key=os.getenv("LLM_API_KEY"))
    gh = Github(os.getenv("GITHUB_TOKEN"))
    
    # 2. Load the diff file
    diff_file = sys.argv[1]
    with open(diff_file, 'r') as f:
        diff_text = f.read()

    if not diff_text.strip():
        print("No changes to review.")
        return

    # 3. Ask Gemini to review
    model = genai.GenerativeModel('gemini-1.5-flash-latest')
    prompt = f"""
    You are a Senior Staff Engineer. Review this Git diff for logic errors and security bugs.
    Be concise. Provide feedback as a bulleted list.
    
    DIFF:
    {diff_text}
    """
    
    response = model.generate_content(prompt)
    review_text = response.text

    # 4. Post the comment to GitHub
    repo_name = os.getenv("GITHUB_REPOSITORY")
    pr_number = int(os.getenv("GITHUB_REF").split('/')[-2])
    repo = gh.get_repo(repo_name)
    pr = repo.get_pull(pr_number)
    
    pr.create_issue_comment(f"### 🤖 AI Code Review\n\n{review_text}")

if __name__ == "__main__":
    main()
