from sync_status import Config, GithubHandler, STATUS_READY, STATUS_IN_PROGRESS
import os
import sys
import json
import re

def extract_issue_number():
    """
    イベントペイロードからIssue番号を抽出する
    
    Returns:
        str: 抽出されたIssue番号、見つからない場合は空文字列
    """
    event_name = os.getenv("GITHUB_EVENT_NAME")
    event_path = os.getenv("GITHUB_EVENT_PATH")
    
    if not event_name or not event_path:
        print("GITHUB_EVENT_NAME または GITHUB_EVENT_PATH が設定されていません。")
        return ""
    
    try:
        with open(event_path, 'r') as f:
            event_data = json.load(f)
    except Exception as e:
        print(f"イベントデータの読み込みエラー: {e}")
        return ""
    
    issue_number = ""
    
    if event_name == "issue_comment":
        if "issue" in event_data and "number" in event_data["issue"]:
            issue_number = str(event_data["issue"]["number"])
    elif event_name == "pull_request":
        if "pull_request" in event_data and "body" in event_data["pull_request"]:
            body = event_data["pull_request"]["body"] or ""
            matches = re.search(r'#(\d+)', body)
            if matches:
                issue_number = matches.group(1)
    
    if issue_number:
        print(f"抽出されたIssue番号: {issue_number}")
        os.environ["GITHUB_EVENT_ISSUE_NUMBER"] = issue_number
    else:
        print("Issue番号が見つかりませんでした。")
    
    return issue_number

def main():
    issue_number = extract_issue_number()
    if not issue_number:
        print("Issue番号が抽出できないため、処理を中止します。")
        return
    
    config = Config()
    
    if not all([config.github_token, config.github_repo, config.issue_number, 
               config.project_token, config.project_id, config.status_field_id]):
        print("必要な環境変数が設定されていません。処理を中止します。")
        return
    
    github_handler = GithubHandler(config)
    
    current_status = github_handler.get_issue_status()
    
    if current_status == STATUS_READY and github_handler.issue.assignees:
        print(f"進捗があり、ステータスが 'Ready' でアサインされているため、'In Progress' に更新します。")
        github_handler.update_issue_status(STATUS_IN_PROGRESS)
        print(f"Issueのステータスを '{STATUS_IN_PROGRESS}' に更新しました。")
    else:
        reason = "ステータスが 'Ready' ではない" if current_status != STATUS_READY else "アサインされていない"
        print(f"ステータスは更新されません。理由: {reason}")

if __name__ == "__main__":
    main()
