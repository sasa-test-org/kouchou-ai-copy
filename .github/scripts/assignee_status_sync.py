from sync_status import Config, GithubHandler, STATUS_NO_STATUS, STATUS_COLD_LIST, STATUS_NEED_REFINEMENT, STATUS_READY
import os
import sys

def main():
    config = Config()
    
    if not all([config.github_token, config.github_repo, config.issue_number, 
               config.project_token, config.project_id, config.status_field_id]):
        print("必要な環境変数が設定されていません。処理を中止します。")
        return
    
    github_handler = GithubHandler(config)
    
    action = os.getenv("GITHUB_EVENT_ACTION")
    if not action:
        print("GITHUB_EVENT_ACTIONが見つかりません。処理を中止します。")
        return
    
    if action == "assigned":
        current_status = github_handler.get_issue_status()
        
        if current_status in [STATUS_NO_STATUS, STATUS_COLD_LIST, STATUS_NEED_REFINEMENT]:
            print(f"担当者が割り当てられ、ステータスが '{current_status}' のため、'Ready' に更新します。")
            github_handler.update_issue_status(STATUS_READY)
            print(f"Issueのステータスを '{STATUS_READY}' に更新しました。")
        else:
            print(f"ステータスは '{current_status}' です。更新は不要です。")

if __name__ == "__main__":
    main()
