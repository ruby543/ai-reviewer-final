import os
import sys
import json
from google import genai  # Modern v2 SDK import
from github import Github, Auth

def main():
    # 1. Parse command-line arguments to find the diff file path
    if len(sys.argv) < 2:
        print("Error: Missing diff file argument.")
        sys.exit(1)
        
    diff_file_path = sys.argv[1]
    
    if not os.path.exists(diff_file_path):
        print(f"Error: Diff file not found at path: {diff_file_path}")
        sys.exit(1)

    # 2. Extract environment variables passed from your YAML workflow
    api_key = os.getenv("LLM_API_KEY")
    github_token = os.getenv("GITHUB_TOKEN")
    event_path = os.getenv("GITHUB_EVENT_PATH")

    if not api_key or not github_token or not event_path:
        print("Error: Required environment variables are missing.")
        sys.exit(1)

    # 3. Read the contents of the generated git diff file
    with open(diff_file_path, "r", encoding="utf-8") as f:
        diff_content = f.read().strip()

    if not diff_content:
        print("No code changes detected in the diff file. Skipping review.")
        sys.exit(0)

    # 4. Parse the GitHub Actions Event JSON to find the PR number and Repo name safely
    with open(event_path, "r", encoding="utf-8") as f:
        event_data = json.load(f)

    pr_number = event_data.get("pull_request", {}).get("number")
    repo_fullname = event_data.get("repository", {}).get("full_name")

    if not pr_number or not repo_fullname:
        print("Error: Script must be triggered by a pull_request event context.")
        sys.exit(1)

    print(f"Initializing AI Review for Pull Request #{pr_number} in {repo_fullname}...")

    # 5. Initialize the modern Google GenAI Client
    client = genai.Client(api_key=api_key)

    # 6. Initialize the PyGithub client using modern Token Auth authentication
    auth = Auth.Token(github_token)
    gh = Github(auth=auth)
    repo = gh.get_repo(repo_fullname)
    pull_request = repo.get_pull(pr_number)

    # 7. Build the explicit instructions prompt for Gemini
    prompt = f"""
    You are a Senior Staff Engineer. Review this Git diff for logic errors and security bugs.
    Be concise. Provide feedback as a bulleted list.
    
    DIFF:
    {diff_content}
    """

    # 8. Request the review text via the correct modern Gemini v2 model endpoint
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",  # Modern clean string mapping
            contents=prompt,
        )
        review_feedback = response.text
    except Exception as e:
        print(f"Failed to communicate or parse response from Gemini API: {e}")
        sys.exit(1)

    # 9. Post the generated AI response text back onto the Pull Request timeline
    if review_feedback:
        header = "### 🤖 AI Automated Code Review Feedback\n\n"
        pull_request.create_issue_comment(header + review_feedback)
        print("AI Review Comment successfully posted to the Pull Request!")
    else:
        print("Error: Received completely empty text content back from the AI model.")
        sys.exit(1)

if __name__ == "__main__":
    main()
