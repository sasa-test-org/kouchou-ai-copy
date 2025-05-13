import os
import json
import requests
from github import Github

if not os.getenv('GITHUB_ACTIONS'):
    from dotenv import load_dotenv
    load_dotenv()

STATUS_NO_STATUS = null
STATUS_COLD_LIST = "Cold List"
STATUS_NEED_REFINEMENT = "Need Refinement"
STATUS_READY = "Ready"
STATUS_IN_PROGRESS = "In Progress"

class Config:
    def __init__(self):
        print("設定の初期化を開始します...")
        self.github_token = os.getenv("GITHUB_TOKEN")
        if self.github_token is None:
            print("GITHUB_TOKENが見つかりません ...")
            return
        else:
            print("GITHUB_TOKENからトークンを正常に取得しました。")
        
        self.github_repo = os.getenv("GITHUB_REPOSITORY")
        print("GITHUB_REPOSITORYの状態:", "取得済み" if self.github_repo else "見つかりません")

        self.project_token = os.getenv("PROJECT_TOKEN")
        if self.project_token is None:
            print("PROJECT_TOKENが見つかりません...")
            return
        else:
            print("PROJECT_TOKENを正常に取得しました")
            
        self.issue_number = os.getenv("GITHUB_EVENT_ISSUE_NUMBER")
        if self.issue_number is None:
            print("GITHUB_EVENT_ISSUE_NUMBERが見つかりません...")
            return
        else:
            self.issue_number = int(self.issue_number)
            print("GITHUB_EVENT_ISSUE_NUMBERを正常に取得しました")
        
        self.status_field_id = os.getenv("STATUS_FIELD")
        if self.status_field_id is None:
            print("STATUS_FIELDが見つかりません...")
            return
        else:
            print("STATUS_FIELDを正常に取得しました。")
        
        print("設定の初期化が完了しました")

class GithubHandler:
    def __init__(self, config: Config):
        self.github = Github(config.github_token)
        self.repo = self.github.get_repo(config.github_repo)
        self.issue = self.repo.get_issue(config.issue_number)
        self.config = config
    
    def get_issue_status_and_id(self):
        """GraphQL APIを使用してIssueの現在のステータスを取得する"""
        
        issue_number = self.issue.number
        repo_parts = self.config.github_repo.split('/')
        repo_owner = repo_parts[0]
        repo_name = repo_parts[1]
        print(f"リポジトリ所有者: {repo_owner}")
        print(f"リポジトリ名: {repo_name}")
        print(f"Issue番号: {issue_number}")
        
        headers = {
            "Authorization": f"Bearer {self.config.project_token}",
            "Content-Type": "application/json"
        }
        query = """
        query($repoOwner: String!) {
          organization(login: $repoOwner) {
            projectV2(number: 1) {
              ... on ProjectV2 {
                items(first: 100) {
                  nodes {
                    id
                    content {
                      ... on Issue {
                        number
                        repository {
                          name
                        }
                      }
                    }
                    fieldValueByName(name: "Status") {
                      ... on ProjectV2ItemFieldSingleSelectValue {
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
        variables = {
            "repoOwner": repo_owner,
        }
        
        response = requests.post(
            "https://api.github.com/graphql",
            headers=headers,
            json={"query": query, "variables": variables}
        )
        if response.status_code != 200:
            print(f"GraphQL APIからのエラー: {response.text}")
            return None
        
        resjson = response.json()
        print("resjson: " + json.dumps(resjson))
        project_items = resjson.get("data", {}).get("organization", {}).get("projectV2", {}).get("items", {}).get("nodes", [])
        
        for item in project_items:
            content = item.get("content")
            if content and content.get("__typename") == "Issue":
                if (content.get("number") == issue_number and 
                    content.get("repository", {}).get("name") == repo_name):
                    field_value = item.get("fieldValueByName")
                    if field_value:
                        return field_value.get("name"), item["id"]
                    return None, None
        print("Projectにこのissueが見つかりません。アイテム数:", len(project_items))
        return None, None
    
    def update_issue_status(self, status: str, itemId: str):
        """GraphQL APIを使用してIssueのステータスを更新する"""
        
        # まずstatusに対応するIDを調べる
        headers = {
            "Authorization": f"Bearer {self.config.project_token}",
            "Content-Type": "application/json"
        }
        query = """
        query($fieldId: ID!) {
          node(id: $fieldId) {
            ... on ProjectV2SingleSelectField {
              options {
                id
                name
              }
            }
          }
        }
        """
        variables = {
            "fieldId": self.config.status_field_id
        }
        
        response = requests.post(
            "https://api.github.com/graphql",
            headers=headers,
            json={"query": query, "variables": variables}
        )
        if response.status_code != 200:
            print(f"GraphQL APIからのエラー: {response.text}")
            return False
        
        data = response.json()
        options = data.get("data", {}).get("node", {}).get("options", [])
        
        option_id = None
        for option in options:
            if option["name"] == status:
                option_id = option["id"]
                break
        
        if not option_id:
            print(f"ステータス '{status}' のオプションが見つかりません")
            return False

        # statusに対応するIDが見つかったので、次にIssueの
        
        repo_parts = self.config.github_repo.split('/')
        repo_owner = repo_parts[0]
        
        mutation = """
        mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $optionId: ID!) {
          updateProjectV2ItemFieldValue(input: {
            projectId: $projectId,
            itemId: $itemId,
            fieldId: $fieldId,
            value: {
              singleSelectOptionId: $optionId
            }
          }) {
            clientMutationId
          }
        }
        """
        variables = {
            "projectId": self.config.project_id,
            "itemId": item_id,
            "fieldId": self.config.status_field_id,
            "optionId": option_id
        }
        
        response = requests.post(
            "https://api.github.com/graphql",
            headers=headers,
            json={"query": mutation, "variables": variables}
        )
        if response.status_code != 200:
            print(f"GraphQL APIからのエラー: {response.text}")
            return False
        
        print(f"ステータスを '{status}' に正常に更新しました")
        return True
        
