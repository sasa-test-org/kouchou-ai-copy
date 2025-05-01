import os
from typing import List, Dict, Any
import regex as re
from github import Github
from github.Issue import Issue
from github.Repository import Repository
# from qdrant_client import QdrantClient
# from qdrant_client.models import PointStruct
import openai

if not os.getenv('GITHUB_ACTIONS'):
    from dotenv import load_dotenv
    load_dotenv()

EMBEDDING_MODEL = "text-embedding-3-small"
COLLECTION_NAME = "issue_collection"
GPT_MODEL = "gpt-4o"
MAX_RESULTS = 3

class Config:
    def __init__(self):
        print("設定の初期化を開始します...")
        self.github_token = os.getenv("GITHUB_TOKEN")
        if self.github_token is None:
            print("GITHUB_TOKENが見つかりません ...")
        else:
            print("GITHUB_TOKENからトークンを正常に取得しました。")
        
        # self.qd_api_key = os.getenv("QD_API_KEY")
        # print("QD_API_KEYの状態:", "取得済み" if self.qd_api_key else "見つかりません")
        
        # self.qd_url = os.getenv("QD_URL")
        # print("QD_URLの状態:", "取得済み" if self.qd_url else "見つかりません")
        
        self.github_repo = os.getenv("GITHUB_REPOSITORY")
        print("GITHUB_REPOSITORYの状態:", "取得済み" if self.github_repo else "見つかりません")
        
        self.issue_number = os.getenv("GITHUB_EVENT_ISSUE_NUMBER")
        if self.issue_number:
            self.issue_number = int(self.issue_number)
            print(f"GITHUB_EVENT_ISSUE_NUMBER: {self.issue_number}")
        else:
            print("GITHUB_EVENT_ISSUE_NUMBERが見つかりません")
        print("設定の初期化が完了しました。")

class GithubHandler:
    def __init__(self, config: Config):
        self.github = Github(config.github_token)
        self.repo = self.github.get_repo(config.github_repo)
        self.issue = self.repo.get_issue(config.issue_number)

    def create_labels(self):
        """ラベルを作成する（既に存在する場合は無視）"""
        try:
            labels_to_create = [
                'Admin', 'Algorithm', 'API', 'bug', 'Client', 'dependencies', 'design', 
                'docker', 'documentation', # 'duplicate', 
                'e2e-test-required', 'enhancement', 
                'github_actions', 'good first issue', 'help wanted', 'high priority', 
                'invalid', 'javascript', 'python', 'question', 'wontfix' # , 'toxic'
            ]
            
            for label in labels_to_create:
                color = "708090"  # デフォルトのグレー
                
                if label == "Admin":
                    color = "0075ca"  # 青
                elif label == "github_actions":
                    color = "5319e7"  # 紫
                elif label == "docker":
                    color = "0db7ed"  # Docker青
                elif label == "dependencies":
                    color = "6b5b95"  # 薄紫
                
                elif label == "Algorithm":
                    color = "c5def5"  # 薄い青
                elif label == "API":
                    color = "1d76db"  # 濃い青
                elif label == "Client":
                    color = "fbca04"  # 黄色
                elif label == "javascript":
                    color = "f7df1e"  # JavaScript黄色
                elif label == "python":
                    color = "3572A5"  # Python青
                
                elif label == "documentation":
                    color = "0075ca"  # 青
                elif label == "e2e-test-required":
                    color = "bfdadc"  # 薄い青緑
                
                elif label == "bug":
                    color = "d73a4a"  # 赤系
                elif label == "enhancement":
                    color = "a2eeef"  # 水色系
                elif label == "design":
                    color = "cc33cc"  # ピンク
                elif label == "high priority":
                    color = "ff9900"  # オレンジ
                elif label == "invalid":
                    color = "e4e669"  # 黄緑
                elif label == "wontfix":
                    color = "ffffff"  # 白
                
                elif label == "good first issue":
                    color = "7057ff"  # 紫
                elif label == "help wanted":
                    color = "008672"  # 緑
                elif label == "question":
                    color = "d876e3"  # ピンク
                
                # elif label == "toxic":
                #     color = "ff0000"  # 赤
                # elif label == "duplicate":
                
                self.repo.create_label(name=label, color=color)
        except:
            pass

    def add_label(self, label: str):
        """Issueにラベルを追加する"""
        self.issue.add_to_labels(label)

    def close_issue(self):
        """Issueをクローズする"""
        self.issue.edit(state="closed")

    def add_comment(self, comment: str):
        """Issueにコメントを追加する"""
        self.issue.create_comment(comment)

# class ContentModerator:
#     def __init__(self, openai_client: openai.Client):
#         self.openai_client = openai_client
# 
#     def is_inappropriate_image(self, text: str) -> bool:
#         """画像の内容が不適切かどうかを判断する"""
#         image_url = self._extract_image_url(text)
#         if not image_url:
#             return False
# 
#         prompt = "この画像が暴力的、もしくは性的な画像の場合trueと返してください。"
#         try:
#             response = self.openai_client.chat.completions.create(
#                 model=GPT_MODEL,
#                 messages=[
#                     {
#                         "role": "user",
#                         "content": [
#                             {"type": "text", "text": prompt},
#                             {"type": "image_url", "image_url": {"url": image_url}},
#                         ],
#                     }
#                 ],
#                 max_tokens=1200,
#             )
#             return "true" in response.choices[0].message.content.lower()
#         except:
#             return True
# 
#     def is_inappropriate_issue(self, text: str) -> bool:
#         """テキストと画像の内容が不適切かどうかを判断する"""
#         response = self.openai_client.moderations.create(input=text)
#         return response.results[0].flagged or self.is_inappropriate_image(text)
# 
#     @staticmethod
#     def _extract_image_url(text: str) -> str:
#         """テキストから画像URLを抽出する"""
#         match = re.search(r"!\[[^\s]+\]\((https://[^\s]+)\)", text)
#         return match.group(1) if match else ""

# class QdrantHandler:
#     def __init__(self, client: QdrantClient, openai_client: openai.Client):
#         self.client = client
#         self.openai_client = openai_client
# 
#     def add_issue(self, text: str, issue_number: int):
#         """新しい問題をQdrantに追加する"""
#         embedding = self._create_embedding(text)
#         point = PointStruct(id=issue_number, vector=embedding, payload={"text": text})
#         self.client.upsert(COLLECTION_NAME, [point])
# 
#     def search_similar_issues(self, text: str) -> List[Dict[str, Any]]:
#         """類似の問題を検索する"""
#         embedding = self._create_embedding(text)
#         results = self.client.search(collection_name=COLLECTION_NAME, query_vector=embedding)
#         return results[:MAX_RESULTS]
# 
#     def _create_embedding(self, text: str) -> List[float]:
#         """テキストのembeddingを作成する"""
#         result = self.openai_client.embeddings.create(input=[text], model=EMBEDDING_MODEL)
#         return result.data[0].embedding

class IssueProcessor:
    def __init__(self, github_handler: GithubHandler, openai_client: openai.Client):
        self.github_handler = github_handler
        self.openai_client = openai_client
        self.available_labels = [
            'Admin', 'Algorithm', 'API', 'bug', 'Client', 'dependencies', 'design', 
            'docker', 'documentation', # 'duplicate', 
            'e2e-test-required', 'enhancement', 
            'github_actions', 'good first issue', 'help wanted', 'high priority', 
            'invalid', 'javascript', 'python', 'question', 'wontfix'
        ]

    def process_issue(self, issue_content: str, issue_title: str = ""):
        """Issueを処理する"""
        # if self.content_moderator.is_inappropriate_issue(issue_content):
        #     self._handle_violation()
        #     return

        if issue_title:
            self._check_and_add_title_labels(issue_title)
        
        self._analyze_and_add_content_labels(issue_content)

        # self.qdrant_handler.add_issue(issue_content, self.github_handler.issue.number)
        
    def _check_and_add_title_labels(self, title: str):
        """タイトルの先頭に[text]形式の文字列や絵文字があるか確認し、対応するラベルを付与する"""
        tag_match = re.match(r'^\s*\[([^\]]+)\]', title)
        if tag_match:
            tag = tag_match.group(1).strip().lower()
            
            tag_to_label = {
                'admin': 'Admin',
                'algorithm': 'Algorithm',
                'api': 'API',
                'bug': 'bug',
                'client': 'Client',
                'dependencies': 'dependencies',
                'design': 'design',
                'docker': 'docker',
                'documentation': 'documentation',
                'duplicate': 'duplicate',
                'enhancement': 'enhancement',
                'github': 'github_actions',
                'github actions': 'github_actions',
                'javascript': 'javascript',
                'js': 'javascript',
                'python': 'python',
                'py': 'python',
                'question': 'question',
                'help': 'help wanted',
                'priority': 'high priority',
                'high priority': 'high priority',
                'invalid': 'invalid',
                'wontfix': 'wontfix'
            }
            
            if tag in tag_to_label:
                self.github_handler.add_label(tag_to_label[tag])
        
        emoji_match = re.match(r'^\s*([^\w\s])', title)
        if emoji_match:
            emoji = emoji_match.group(1)
            
            emoji_to_label = {
                '🐛': 'bug',
                '✨': 'enhancement',
                '📚': 'documentation',
                '🎨': 'design',
                '❓': 'question',
                '🔥': 'high priority',
                '🐍': 'python',
                '🌐': 'javascript',
                '🐳': 'docker',
                '🤖': 'Algorithm',
                '🔧': 'enhancement'
            }
            
            if emoji in emoji_to_label:
                self.github_handler.add_label(emoji_to_label[emoji])
                
    def _analyze_and_add_content_labels(self, issue_content: str):
        """OpenAIを使ってIssueの内容からラベルを判定する"""
        prompt = f"""
        以下はGitHubのIssueの内容です。この内容を分析して、最も適切なラベルを選んでください。
        
        Issue内容:
        {issue_content}
        
        選択可能なラベル:
        {', '.join(self.available_labels)}
        
        このIssueに付与すべきラベルを3つまで選んでJSON形式で返してください。
        例: {{"labels": ["bug", "javascript", "high priority"]}}
        
        Issueの内容に合わないラベルは選ばないでください。適切なラベルが1つか2つしかない場合は、無理に3つ選ぶ必要はありません。
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model=GPT_MODEL,
                messages=[{"role": "system", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=1024
            )
            
            result = response.choices[0].message.content
            print(f"OpenAIからのレスポンス: {result}")
            
            import json
            try:
                labels_data = json.loads(result)
                if "labels" in labels_data and isinstance(labels_data["labels"], list):
                    for label in labels_data["labels"]:
                        if label in self.available_labels:
                            self.github_handler.add_label(label)
                            print(f"ラベルを追加しました: {label}")
            except json.JSONDecodeError as e:
                print(f"JSONのパースに失敗しました: {e}")
                
        except Exception as e:
            print(f"OpenAIによるラベル判定中にエラーが発生しました: {e}")

    def _handle_violation(self):
        """違反を処理する"""
        self.github_handler.add_label("toxic")
        self.github_handler.add_comment("不適切な投稿です。アカウントBANの危険性があります。")
        self.github_handler.close_issue()

    # 
    # 
    # 

def setup():
    """セットアップを行い、必要なオブジェクトを返す"""
    config = Config()
    github_handler = GithubHandler(config)
    github_handler.create_labels()

    openai_client = openai.Client()
    # content_moderator = ContentModerator(openai_client)

    # qdrant_client = QdrantClient(url=config.qd_url, api_key=config.qd_api_key)
    # qdrant_handler = QdrantHandler(qdrant_client, openai_client)

    return github_handler, openai_client

def main():
    github_handler, openai_client = setup()
    issue_processor = IssueProcessor(github_handler, openai_client)
    issue_title = github_handler.issue.title
    issue_content = f"{issue_title}\n{github_handler.issue.body}"
    issue_processor.process_issue(issue_content, issue_title)

if __name__ == "__main__":
    main()
