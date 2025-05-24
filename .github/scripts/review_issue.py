import os
import regex as re
from github import Github
import openai

if not os.getenv('GITHUB_ACTIONS'):
    from dotenv import load_dotenv
    load_dotenv()

GPT_MODEL = "gpt-4.1-nano"

class Config:
    def __init__(self):
        print("設定の初期化を開始します...")
        self.github_token = os.getenv("GITHUB_TOKEN")
        if self.github_token is None:
            print("GITHUB_TOKENが見つかりません ...")
        else:
            print("GITHUB_TOKENを正常に取得しました。")
        
        self.github_repo = os.getenv("GITHUB_REPOSITORY")
        if self.github_repo is None:
            print("GITHUB_REPOSITORYが見つかりません ...")
        else:
            print("GITHUB_REPOSITORYを正常に取得しました。")
        
        self.issue_number = os.getenv("GITHUB_EVENT_ISSUE_NUMBER")
        if self.issue_number is None:
            print("GITHUB_EVENT_ISSUE_NUMBERが見つかりません ...")
        else:
            self.issue_number = int(self.issue_number)
            print("GITHUB_EVENT_ISSUE_NUMBERを正常に取得しました。")

        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if self.openai_api_key is None:
            print("OPENAI_API_KEYが見つかりません ...")
        else:
            print("OPENAI_API_KEYを正常に取得しました。")

        print("設定の初期化が完了しました。")

class GithubHandler:
    def __init__(self, config: Config):
        self.github = Github(config.github_token)
        self.repo = self.github.get_repo(config.github_repo)
        self.issue = self.repo.get_issue(config.issue_number)

    def add_label(self, label: str):
        """Issueにラベルを追加する"""
        self.issue.add_to_labels(label)

class IssueProcessor:
    def __init__(self, github_handler: GithubHandler, openai_client: openai.Client):
        self.github_handler = github_handler
        self.openai_client = openai_client
        self.available_labels = [
            'Admin', 'Algorithm', 'API', 'bug', 'Client', 'dependencies', 'design', 
            'docker', 'documentation', 'e2e-test-required', 'enhancement', 
            'github_actions', 'good first issue', 'invalid', 'javascript', 'python'
        ]
        self.labels_for_content = {
            "documentation": "開発資料の提案",
            "design": "UIデザインの提案",
            "bug": "製品機能に不具合がある",
            "enhancement": "製品機能改善の提案",
            "good first issue": "軽微な修正",
            "Algorithm": "製品機能を変えないアルゴリズムの改善（速度改善など）",
            "e2e-test-required": "E2E testを実行します",
            "github_actions": "Github Actions関連の提案",
            "docker": "docker関連の提案",
            "Client": "レポート画面またはレポート一覧画面の提案",
            "Admin": "管理画面の提案",
            "API": "API処理の提案"
        }

    def process_issue(self, issue_content: str, issue_title: str = ""):
        """Issueを処理する"""
        if issue_title:
            self._check_and_add_title_labels(issue_title)
        
        self._analyze_and_add_content_labels(issue_content)
        
    def _check_and_add_title_labels(self, title: str):
        """タイトル内の[text]形式の文字列や絵文字を検出し、対応するラベルを付与する"""
        tag_matches = re.findall(r'\[([^\[\]]+)\]', title)
        if tag_matches:
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
                'enhancement': 'enhancement',
                'github': 'github_actions',
                'github actions': 'github_actions',
                'javascript': 'javascript',
                'js': 'javascript',
                'python': 'python',
                'py': 'python',
                'invalid': 'invalid'
            }
            
            for tag_match in tag_matches:
                tag = tag_match.strip().lower()
                if tag in tag_to_label:
                    self.github_handler.add_label(tag_to_label[tag])
        
        emoji_matches = re.findall(r'([^\w\s])', title)
        if emoji_matches:
            emoji_to_label = {
                '🐛': 'bug',
                '✨': 'enhancement',
                '📚': 'documentation',
                '📝': 'documentation',
                '🎨': 'design',
                '🤖': 'Algorithm'
            }
            
            for emoji in emoji_matches:
                if emoji in emoji_to_label:
                    self.github_handler.add_label(emoji_to_label[emoji])
                
    def _analyze_and_add_content_labels(self, issue_content: str):
        """OpenAIを使ってIssueの内容からラベルを判定する"""
        import json
        prompt = f"""以下はGitHubのIssueの内容です。この内容を分析して、解決すべき課題の分類として適切なラベルがもしあれば選んでください。明らかにそのラベルが適切であると判断できる場合以外はラベルを付与しないでください。画像は無視してください。

Issue内容:
{issue_content}

選択可能なラベルとその説明文:
{json.dumps(self.labels_for_content)}

このIssueに付与すべきラベルを3つまで選んでJSON形式で返してください。
例: {{"labels": ["documentation", "good first issue", "design"]}}

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

def setup():
    """セットアップを行い、必要なオブジェクトを返す"""
    config = Config()
    github_handler = GithubHandler(config)
    openai_client = openai.Client(api_key=config.openai_api_key) if config.openai_api_key else None
    return github_handler, openai_client

def main():
    github_handler, openai_client = setup()
    if not all([github_handler, openai_client]):
        print("セットアップに失敗しました。")
        return

    issue_processor = IssueProcessor(github_handler, openai_client)
    issue_title = github_handler.issue.title
    issue_content = f"{issue_title}\n{github_handler.issue.body}"
    issue_processor.process_issue(issue_content, issue_title)

if __name__ == "__main__":
    main()
