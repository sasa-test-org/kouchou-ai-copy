import os
import json
import requests
from github import Github

if not os.getenv('GITHUB_ACTIONS'):
    from dotenv import load_dotenv
    load_dotenv()

STATUS_NO_STATUS = "No Status"
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
        
        self.issue_number = os.getenv("GITHUB_EVENT_ISSUE_NUMBER")
        if self.issue_number:
            self.issue_number = int(self.issue_number)
            print(f"GITHUB_EVENT_ISSUE_NUMBER: {self.issue_number}")
        else:
            print("GITHUB_EVENT_ISSUE_NUMBERが見つかりません")
        
        
        self.project_id = os.getenv("PROJECT_ID")
        if self.project_id is None:
            print("PROJECT_IDが見つかりません ...")
            return
        
        self.status_field_id = os.getenv("STATUS_FIELD")
        if self.status_field_id is None:
            print("STATUS_FIELDが見つかりません ...")
            return
        
        print("設定の初期化が完了しました。")

class GithubHandler:
    def __init__(self, config: Config):
        self.github = Github(config.github_token)
        self.repo = self.github.get_repo(config.github_repo)
        self.issue = self.repo.get_issue(config.issue_number)
        self.config = config
    
    def get_issue_status(self):
        """GraphQL APIを使用してIssueの現在のステータスを取得する"""
        headers = {
            "Authorization": f"Bearer {self.config.github_token}",
            "Content-Type": "application/json"
        }
        
        issue_node_id = self.issue.raw_data['node_id']
        
        query = """
        query($projectId: ID!, $nodeId: ID!) {
          node(id: $projectId) {
            ... on ProjectV2 {
              items(first: 1, filter: {idString: $nodeId}) {
                nodes {
                  id
                }
              }
            }
          }
        }
        """
        
        variables = {
            "projectId": self.config.project_id,
            "nodeId": issue_node_id
        }
        
        response = requests.post(
            "https://api.github.com/graphql",
            headers=headers,
            json={"query": query, "variables": variables}
        )
        
        if response.status_code != 200:
            print(f"GraphQL APIからのエラー: {response.text}")
            return None
        
        data = response.json()
        if not data.get("data", {}).get("node", {}).get("items", {}).get("nodes"):
            print("Projectにこのissueが見つかりません")
            return None
        
        item_id = data["data"]["node"]["items"]["nodes"][0]["id"]
        
        query = """
        query($projectId: ID!, $itemId: ID!, $fieldId: ID!) {
          node(id: $projectId) {
            ... on ProjectV2 {
              items(first: 1, filter: {idString: $itemId}) {
                nodes {
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
        """
        
        variables = {
            "projectId": self.config.project_id,
            "itemId": item_id,
            "fieldId": self.config.status_field_id
        }
        
        response = requests.post(
            "https://api.github.com/graphql",
            headers=headers,
            json={"query": query, "variables": variables}
        )
        
        if response.status_code != 200:
            print(f"GraphQL APIからのエラー: {response.text}")
            return None
        
        data = response.json()
        field_value = data.get("data", {}).get("node", {}).get("items", {}).get("nodes", [{}])[0].get("fieldValueByName")
        
        if field_value:
            return field_value.get("name")
        return None
    
    def update_issue_status(self, status: str):
        """GraphQL APIを使用してIssueのステータスを更新する"""
        headers = {
            "Authorization": f"Bearer {self.config.github_token}",
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
        
        issue_node_id = self.issue.raw_data['node_id']
        
        query = """
        query($projectId: ID!, $nodeId: ID!) {
          node(id: $projectId) {
            ... on ProjectV2 {
              items(first: 1, filter: {idString: $nodeId}) {
                nodes {
                  id
                }
              }
            }
          }
        }
        """
        
        variables = {
            "projectId": self.config.project_id,
            "nodeId": issue_node_id
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
        if not data.get("data", {}).get("node", {}).get("items", {}).get("nodes"):
            print("Projectにこのissueが見つかりません")
            return False
        
        item_id = data["data"]["node"]["items"]["nodes"][0]["id"]
        
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
