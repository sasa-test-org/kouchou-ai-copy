from sync_status import Config, GithubHandler, STATUS_READY, STATUS_IN_PROGRESS
import os
import sys

def main():
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
