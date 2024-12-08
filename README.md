## 仕様
# 機能要件仕様書

## 1. システム概要
- プログラムの全体的な目的と対象のユーザー:
  - このプログラムは、Google Search Console（GSC）からデータを取得し、BigQueryに格納することを目的としています。これにより、データ分析やレポート生成を支援します。対象ユーザーは、データエンジニアやデータアナリストで、GSCのデータを効率的に処理して活用したいと考えている人々です。

## 2. 主要機能要件
- 提供される各機能の説明:
  1. **Google Search Console データ取得**:
     - `GSCConnector`クラスを使用して、指定された日付範囲のデータをGoogle Search Consoleから取得します。
     - APIを通じて指定されたプロパティのデータをフェッチします。
  
  2. **データの集計と正規化**:
     - URLを正規化し、クエリパラメータやフラグメントを除去します。
     - 取得したデータをクリック数、インプレッション数、平均順位で集計します。
  
  3. **BigQueryへのデータ挿入**:
     - `insert_to_bigquery`メソッドを使用して、集計されたデータをBigQueryに挿入します。
     - リトライロジックを用いて、データ挿入の信頼性を向上させます。
  
  4. **設定と環境の管理**:
     - 環境変数と設定ファイル（`settings.ini`や`secrets.env`）を使用して、プログラムの動作を制御します。
     - 環境に応じた設定のロードと適用を行います。
  
  5. **ログ出力とエラーハンドリング**:
     - 詳細なログを出力し、エラーが発生した際のトラブルシューティングを支援します。
     - 各ステップでの進捗状況やエラーを記録します。

## 3. 非機能要件
- パフォーマンス:
  - データ取得と挿入は効率的に行われ、APIのレート制限を考慮して計画されています。
  - BigQueryへの挿入はバッチ処理で行い、リトライを通じて安定性を確保します。

- セキュリティ:
  - OAuth 2.0を使用してGoogle APIにアクセスします。認証情報は環境変数および設定ファイルで管理され、機密情報は.gitignoreで保護されます。

- 可用性:
  - 定期的なジョブの実行を前提として設計されており、エラー発生時には再試行を行います。

- ロギング:
  - ログファイルには詳細なデバッグ情報を含め、問題発生時の解析を容易にしています。

## 4. 技術要件
- 開発環境:
  - Python 3.8以上
  - Google Cloud SDKを使用したBigQueryアクセス
  - Google API Pythonクライアントライブラリ

- システム環境:
  - Google Cloud Platformの利用を想定（BigQueryおよびGoogle Search Consoleへのアクセス）

- 必要なライブラリ:
  - `google-cloud-bigquery`: BigQueryへのアクセス
  - `google-auth`: Google APIへのアクセス認証
  - `dotenv`: 環境変数の管理
  - `icecream`: デバッグ用のログ出力
  - `anytree`: ディレクトリ構造の可視化

以上がこのプログラムの機能要件仕様です。各機能は相互に連携し、GSCからのデータ取得から分析基盤への登録までのプロセスを自動化しています。 

---

## フォルダ構成
プロジェクトのフォルダ構成は以下の通りです。

```plaintext
```
bigquery_gsc
├── .gitignore
├── .req_hash
├── README.md
├── config
│   ├── boxwood-dynamo-384411-6dec80faabfc.json
│   ├── gcp4-441506-56861cb0311a.json
│   ├── gcp4-441506-affe38a981c3.json
│   ├── secrets.env
│   └── settings.ini
├── data
├── docs
│   ├── .gitkeep
│   ├── detail_spec.txt
│   ├── merge.txt
│   └── requirements_spec.txt
├── logs
│   ├── .gitkeep
│   └── app_20241207.log.2024-12-07
├── requirements.txt
├── run.bat
├── run_dev.bat
├── spec_tools
│   ├── generate_detailed_spec.py
│   ├── generate_spec.py
│   ├── logs
│   │   └── .gitkeep
│   ├── merge_files.py
│   ├── prompt
│   │   ├── README_tmp.md
│   │   ├── prompt_generate_detailed_spec.txt
│   │   └── prompt_requirements_spec.txt
│   └── utils.py
├── spec_tools_run.bat
├── src
│   ├── __init__.py
│   ├── main.py
│   ├── modules
│   │   ├── __init__.py
│   │   ├── date_initializer.py
│   │   ├── gsc_fetcher.py
│   │   └── gsc_handler.py
│   └── utils
│       ├── __init__.py
│       ├── date_utils.py
│       ├── environment.py
│       ├── helpers.py
│       ├── logging_config.py
│       ├── retry.py
│       └── url_utils.py
└── tests
    ├── __init__.py
    └── test_url_utils.py

# Merged Python Files


================================================================================
File: spec_tools\generate_detailed_spec.py
================================================================================

#generate_detailed_spec.py
import os
from utils import setup_logger  # setup_logger をインポート
from dotenv import load_dotenv
from icecream import ic
from utils import read_file_safely, write_file_content, OpenAIConfig

# 環境変数をロード
load_dotenv(dotenv_path="config/secrets.env")

# ロガーを設定
logger = setup_logger("generate_detailed_spec", log_file="\spec_tools\generate_detailed_spec.log")

class SpecificationGenerator:
    """仕様書生成を管理するクラス"""

    def __init__(self):
        """設定を読み込んで初期化"""
        try:
            # OpenAIConfigを使用してAI関連の設定を初期化
            self.ai_config = OpenAIConfig(
                model="gpt-4o",
                temperature=0.7
            )

            # ディレクトリ設定
            self.source_dir = os.path.abspath(".")
            self.document_dir = os.path.join(self.source_dir, 'docs')
            self.prompt_file = os.path.join(self.source_dir, 'spec_tools', 'prompt', 'prompt_generate_detailed_spec.txt')
            ic(self.source_dir, self.document_dir, self.prompt_file)  # デバッグ: パスを確認

            logger.debug("SpecificationGenerator initialized")
        except Exception as e:
            logger.error(f"SpecificationGeneratorの初期化に失敗しました: {e}")
            raise

    def generate(self) -> str:
        """仕様書を生成してファイルに保存"""
        try:
            # merge.txtの内容を読み込む
            code_content = self._read_merge_file()
            ic(code_content)  # デバッグ: merge.txtの内容を確認
            if not code_content:
                logger.error("コード内容が空です。")
                return ""

            # プロンプトファイルを読み込む
            prompt = self._read_prompt_file()
            ic(prompt)  # デバッグ: プロンプト内容を確認
            if not prompt:
                logger.error("プロンプトファイルの読み込みに失敗しました。")
                return ""

            # プロンプトの最終形を作成
            full_prompt = f"{prompt}\n\nコード:\n{code_content}"
            ic(full_prompt)  # デバッグ: 完成したプロンプトを確認

            # OpenAIConfigを使用してAI応答を取得
            specification = self.ai_config.get_response(full_prompt)
            ic(specification)  # デバッグ: 生成された仕様書を確認
            if not specification:
                return ""

            # 出力ファイルのパスを設定
            output_path = os.path.join(self.document_dir, 'detail_spec.txt')
            ic(output_path)  # デバッグ: 出力パスを確認
            if write_file_content(output_path, specification):
                logger.info(f"仕様書が正常に出力されました: {output_path}")
                return output_path
            return ""
        except Exception as e:
            logger.error(f"仕様書生成中にエラーが発生しました: {e}")
            return ""

    def _read_merge_file(self) -> str:
        """merge.txt ファイルの内容を読み込む"""
        merge_path = os.path.join(self.document_dir, 'merge.txt')
        ic(merge_path)  # デバッグ: merge.txtのパスを確認
        content = read_file_safely(merge_path)
        if content:
            logger.info("merge.txt の読み込みに成功しました。")
        else:
            logger.error("merge.txt の読み込みに失敗しました。")
        return content or ""

    def _read_prompt_file(self) -> str:
        """プロンプトファイルを読み込む"""
        ic(self.prompt_file)  # デバッグ: プロンプトファイルのパスを確認
        content = read_file_safely(self.prompt_file)
        if content:
            logger.info("prompt_generate_detailed_spec.txt の読み込みに成功しました。")
        else:
            logger.error(f"プロンプトファイルの読み込みに失敗しました: {self.prompt_file}")
        return content or ""

def generate_detailed_specification():
    """詳細仕様書を生成"""
    try:
        generator = SpecificationGenerator()
        output_file = generator.generate()
        if output_file:
            logger.info(f"Detailed specification generated successfully. Output saved to: {output_file}")
        else:
            logger.error("Detailed specification generation failed. Check logs for details.")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    generate_detailed_specification()


================================================================================
File: spec_tools\generate_spec.py
================================================================================

#generate_spec.py
import os
import logging
from typing import Optional
from utils import read_file_safely, write_file_content, OpenAIConfig, setup_logger
from icecream import ic
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

# .envファイルを読み込む
load_dotenv(dotenv_path="config/secrets.env")


class SpecificationGenerator:
    """仕様書生成を管理するクラス"""

    def __init__(self, logger: logging.Logger):
        """設定を読み込んで初期化"""
        self.logger = logger
        try:
            # OpenAI設定の初期化
            # OpenAIConfigクラスで既にAPIキーのチェックが行われる
            self.ai_config = OpenAIConfig(
                model="gpt-4o",
                temperature=0.7
            )

            # ソースディレクトリの設定
            self.source_dir = os.path.abspath(".")
            self.document_dir = os.path.join(self.source_dir, 'docs')
            self.spec_tools_dir = os.path.join(self.source_dir, 'spec_tools/prompt')
            self.prompt_file = os.path.join(self.spec_tools_dir, 'prompt_requirements_spec.txt')
            ic(self.source_dir, self.document_dir, self.prompt_file)

            self.logger.debug("SpecificationGenerator initialized")
        except ValueError as ve:
            self.logger.error(str(ve))
            self._write_api_key_error()
            raise
        except Exception as e:
            self.logger.error(f"SpecificationGeneratorの初期化に失敗しました: {e}")
            raise

    def generate(self) -> str:
        """仕様書を生成してファイルに保存"""
        try:
            code_content = self._read_merge_file()
            ic(code_content)
            if not code_content:
                self.logger.error("コード内容が空です。")
                return ""

            prompt = self._read_prompt_file()
            ic(prompt)
            if not prompt:
                self.logger.error("プロンプトファイルの読み込みに失敗しました。")
                return ""

            full_prompt = f"{prompt}\n\nコード:\n{code_content}"
            ic(full_prompt)

            # OpenAIConfigを使用してAI応答を取得
            specification = self.ai_config.get_response(full_prompt)
            ic(specification)
            if not specification:
                return ""

            output_path = os.path.join(self.document_dir, 'requirements_spec.txt')
            ic(output_path)
            if write_file_content(output_path, specification):
                self.logger.info(f"仕様書が正常に出力されました: {output_path}")
                self.update_readme()
                return output_path
            return ""
        except Exception as e:
            self.logger.error(f"仕様書生成中にエラーが発生しました: {e}")
            return ""

    def _read_merge_file(self) -> str:
        """merge.txt ファイルの内容を読み込む"""
        merge_path = os.path.join(self.document_dir, 'merge.txt')
        ic(merge_path)  # デバッグ: merge.txtのパスを確認
        content = read_file_safely(merge_path)
        if content:
            self.logger.info("merge.txt の読み込みに成功しました。")
        else:
            self.logger.error("merge.txt の読み込みに失敗しました。")
        return content or ""

    def _read_prompt_file(self) -> str:
        """プロンプトファイル (prompt_requirements_spec.txt) を読み込む"""
        ic(self.prompt_file)  # デバッグ: プロンプトファイルのパスを確認
        try:
            with open(self.prompt_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.logger.info("prompt_requirements_spec.txt の読み込みに成功しました。")
                return content
        except FileNotFoundError:
            self.logger.error(f"プロンプトファイルが見つかりません: {self.prompt_file}")
        except UnicodeDecodeError as e:
            self.logger.error(f"エンコードエラー: {e}")
        except Exception as e:
            self.logger.error(f"プロンプトファイルの読み込み中にエラーが発生しました: {e}")
        return ""

    def _write_api_key_error(self) -> None:
        """APIキーが設定されていない場合のエラーメッセージをファイルに出力"""
        error_message = """
# OpenAI APIキー設定エラー

## エラー内容
OpenAI APIキーが設定されていないため、仕様書を生成できません。

## 解決方法
以下のいずれかの方法でAPIキーを設定してください：

1. 環境変数での設定:
   - OPENAI_API_KEY環境変数にAPIキーを設定

2. secrets.envファイルでの設定:
   - config/secrets.env ファイルを作成
   - 以下の形式でOpenAI APIキーを設定：
     ```
     OPENAI_API_KEY=sk-あなたのAPIキー
     ```

3. settings.iniファイルでの設定:
   - config/settings.ini ファイルのAPI セクションに設定：
     ```
     [API]
     openai_api_key=sk-あなたのAPIキー
     ```

## 補足
- APIキーはOpenAIのウェブサイトから取得できます
- APIキーは機密情報のため、GitHubなどに公開しないように注意してください
- .envファイルと設定ファイルは.gitignoreに追加することを推奨します
"""
        output_path = os.path.join(self.document_dir, 'requirements_spec.txt')
        write_file_content(output_path, error_message)
        self.logger.info(f"APIキー設定エラーメッセージを出力しました: {output_path}")

        # README.mdも更新
        self.update_readme(error_content=error_message)

    def update_readme(self, error_content: Optional[str] = None) -> None:
        """README.md を README_tmp.md のテンプレートを使用して更新する"""
        try:
            readme_tmp_path = os.path.join(self.spec_tools_dir, 'README_tmp.md')
            readme_path = os.path.join(self.source_dir, 'README.md')

            self.logger.info(f"README.md を更新するためにテンプレートを読み込みます: {readme_tmp_path}")

            # README_tmp.md の内容を読み込む
            template_content = read_file_safely(readme_tmp_path)
            if not template_content:
                self.logger.error(f"{readme_tmp_path} の読み込みに失敗しました。README.md は更新されませんでした。")
                return

            if error_content:
                # エラーの場合は、エラーメッセージで置換
                updated_content = template_content.replace("[spec]", error_content)
                updated_content = updated_content.replace("[tree]", "[APIキーが設定されていないため、フォルダ構成を取得できません。]")
            else:
                # 通常の更新処理
                # [spec] プレースホルダーを requirements_spec.txt の内容で置換
                spec_path = os.path.join(self.document_dir, 'requirements_spec.txt')
                spec_content = read_file_safely(spec_path)
                if not spec_content:
                    self.logger.error(f"{spec_path} の読み込みに失敗しました。README.md の [spec] プレースホルダーは置換されませんでした。")
                    spec_content = "[仕様書の内容が取得できませんでした。]"
                updated_content = template_content.replace("[spec]", spec_content)

                # [tree] プレースホルダーを merge.txt の内容で置換
                merge_path = os.path.join(self.document_dir, 'merge.txt')
                merge_content = read_file_safely(merge_path)
                if not merge_content:
                    self.logger.error(f"{merge_path} の読み込みに失敗しました。README.md の [tree] プレースホルダーは置換されませんでした。")
                    tree_content = "[フォルダ構成の取得に失敗しました。]"
                else:
                    tree_content = merge_content.strip()
                updated_content = updated_content.replace("[tree]", f"```\n{tree_content}\n```")

            # 現在の日付を挿入
            current_date = datetime.now().strftime("%Y-%m-%d")
            updated_content = updated_content.replace("2024-12-08", current_date)

            # README.md に書き込む
            if write_file_content(readme_path, updated_content):
                self.logger.info(f"README.md が正常に更新されました: {readme_path}")
            else:
                self.logger.error(f"README.md の更新に失敗しました: {readme_path}")

        except Exception as e:
            self.logger.error(f"README.md の更新中にエラーが発生しました: {e}")
            raise


def generate_specification():
    """仕様書を生成"""
    logger = setup_logger("generate_spec", log_dir="\spec_tools\logs")  # ロガーを設定
    try:
        generator = SpecificationGenerator(logger=logger)
        output_file = generator.generate()
        if output_file:
            logger.info(f"Specification generated successfully. Output saved to: {output_file}")
        else:
            logger.error("Specification generation failed. Check logs for details.")
    except ValueError as ve:
        logger.error(f"APIキーエラー: {ve}")
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    generate_specification()

================================================================================
File: spec_tools\merge_files.py
================================================================================

# merge_files.py

import os
import argparse
from typing import Optional, List, Tuple
import logging

from utils import (
    setup_logger,
    read_settings,
    get_python_files,
    read_file_safely,
    write_file_content,
    ensure_directories_exist,
    generate_tree_structure
)

class PythonFileMerger:
    """
    Pythonファイルをマージするクラス。
    指定されたディレクトリからPythonファイルを収集し、
    フォルダ構造とファイル内容を統合した出力ファイルを生成する。
    """

    def __init__(self, settings_path: str = 'config/settings.ini', logger: Optional[logging.Logger] = None):
        """
        INI設定を読み込んでマージャーを初期化。

        Args:
            settings_path (str): 設定ファイルのパス。
            logger (Optional[logging.Logger]): 使用するロガー。指定がなければ新規作成。
        """
        self.logger = logger or setup_logger("PythonFileMerger", log_file="merge_files.log")
        self.settings = read_settings(settings_path)

        self.project_dir = os.path.abspath(self.settings['source_directory'])
        self.output_dir = os.path.join(self.project_dir, 'docs')
        self.output_filename = self.settings['output_file']

        self.logger.debug(f"Project directory: {self.project_dir}")
        self.logger.debug(f"Output directory: {self.output_dir}")
        self.logger.debug(f"Output filename: {self.output_filename}")

        ensure_directories_exist([self.output_dir])

        # 除外ディレクトリとファイルパターン
        self.exclude_dirs: List[str] = self.settings.get('exclusions', '').split(',')
        self.exclude_files: List[str] = ['*.log']

        self.logger.debug(f"Excluded directories: {self.exclude_dirs}")
        self.logger.debug(f"Excluded file patterns: {self.exclude_files}")

        self.logger.info("PythonFileMergerの初期化に成功しました。")

    def _generate_tree_structure(self) -> str:
        """
        anytreeを使用してディレクトリ構造を生成する。
        """
        return generate_tree_structure(self.project_dir, self.exclude_dirs, self.exclude_files)

    def _collect_python_files(self) -> List[Tuple[str, str]]:
        """
        プロジェクトディレクトリからPythonファイルを収集する。
        """
        self.logger.info(f"{self.project_dir} からPythonファイルを収集中...")
        python_files = get_python_files(self.project_dir, self.exclude_dirs)
        self.logger.debug(f"収集したPythonファイル: {python_files}")
        return python_files

    def _merge_files_content(self, python_files: List[Tuple[str, str]]) -> str:
        """
        Pythonファイルの内容をマージする。
        """
        merged_content = ""

        if not python_files:
            self.logger.warning("マージするPythonファイルが見つかりません。")
            return merged_content

        tree_structure = self._generate_tree_structure()
        merged_content += f"{tree_structure}\n\n# Merged Python Files\n\n"

        for rel_path, filepath in sorted(python_files):
            content = read_file_safely(filepath)
            if content is not None:
                merged_content += f"\n{'='*80}\nFile: {rel_path}\n{'='*80}\n\n{content}\n"
                self.logger.debug(f"ファイルをマージしました: {rel_path}")
            else:
                self.logger.warning(f"読み込みエラーのためスキップしました: {filepath}")

        return merged_content

    def _write_output(self, content: str) -> Optional[str]:
        """
        マージされた内容を出力ファイルに書き込む。
        """
        if not content:
            self.logger.warning("出力する内容がありません。")
            return None

        output_path = os.path.join(self.output_dir, self.output_filename)
        success = write_file_content(output_path, content)

        if success:
            self.logger.info(f"マージされた内容を正常に書き込みました: {output_path}")
            return output_path
        else:
            self.logger.error(f"マージされた内容の書き込みに失敗しました: {output_path}")
            return None

    def process(self) -> Optional[str]:
        """
        ファイルマージ処理を実行する。
        """
        try:
            python_files = self._collect_python_files()

            if not python_files:
                self.logger.warning("マージ処理を中止します。Pythonファイルが見つかりません。")
                return None

            merged_content = self._merge_files_content(python_files)
            return self._write_output(merged_content)
        except Exception as e:
            self.logger.error(f"ファイルマージ処理中にエラーが発生しました: {e}")
            return None


def merge_py_files(settings_path: str = 'config/settings.ini', logger: Optional[logging.Logger] = None) -> Optional[str]:
    """
    マージ処理のエントリーポイント。
    """
    logger = logger or setup_logger("merge_py_files", log_file="merge_py_files.log")
    logger.info("Pythonファイルのマージ処理を開始します。")
    try:
        merger = PythonFileMerger(settings_path=settings_path, logger=logger)
        return merger.process()
    except Exception as e:
        logger.error(f"マージ処理中に予期せぬエラーが発生しました: {e}")
        return None


def parse_arguments() -> argparse.Namespace:
    """
    コマンドライン引数を解析する。
    """
    parser = argparse.ArgumentParser(description="Merge Python files into a single output.")
    parser.add_argument(
        "--settings",
        type=str,
        default="config/settings.ini",
        help="Path to the settings.ini file"
    )
    return parser.parse_args()


def main():
    """
    Main function to execute the Python file merging process.
    """
    args = parse_arguments()
    log_dir = os.path.join(os.getcwd(), "\spec_tools\logs")  # "spec_tools" を削除
    logger = setup_logger("merge_files", log_dir=log_dir, log_file="merge_files.log")

    try:
        output_file = merge_py_files(settings_path=args.settings, logger=logger)
        if output_file:
            logger.info(f"Python files successfully merged. Output saved to: {output_file}")
        else:
            logger.error("File merging failed. Check logs for more details.")
    except Exception as e:
        logger.error(f"Unexpected error occurred: {e}")


if __name__ == "__main__":
    main()


================================================================================
File: spec_tools\utils.py
================================================================================

# utils.py
import os
import logging
import fnmatch
import configparser
from typing import List, Tuple, Optional
from pathlib import Path
from datetime import datetime

from anytree import Node, RenderTree
from openai import OpenAI

logger = logging.getLogger(__name__)

def normalize_path(path: str) -> str:
    """パスを正規化"""
    return os.path.normpath(path).replace('\\', '/')

def read_settings(settings_path: str = 'config/settings.ini') -> dict:
    """設定ファイルを読み込む"""
    config = configparser.ConfigParser()
    default_settings = {
        'source_directory': '.',  # デフォルトのソースディレクトリ
        'output_file': 'merge.txt',  # デフォルトの出力ファイル名
        'exclusions': 'env,myenv,*__pycache__*,downloads,sample_file,*.log',  # 除外パターン
        'openai_api_key': '',  # デフォルトのOpenAI APIキー
        'openai_model': 'gpt-4o'  # デフォルトのOpenAIモデル
    }
    
    try:
        if os.path.exists(settings_path):
            config.read(settings_path, encoding='utf-8')
            settings = {
                'source_directory': config['DEFAULT'].get('SourceDirectory', default_settings['source_directory']),
                'output_file': config['DEFAULT'].get('OutputFile', default_settings['output_file']),
                'exclusions': config['DEFAULT'].get('Exclusions', default_settings['exclusions']).replace(' ', '')
            }
            
            # APIセクションの設定を追加
            if 'API' in config:
                settings['openai_api_key'] = config['API'].get('openai_api_key', default_settings['openai_api_key'])
                settings['openai_model'] = config['API'].get('openai_model', default_settings['openai_model'])
            else:
                logger.warning("API section not found in settings.ini")
                settings['openai_api_key'] = default_settings['openai_api_key']
                settings['openai_model'] = default_settings['openai_model']
        else:
            logger.warning(f"Settings file not found at {settings_path}. Using default settings.")
            settings = default_settings

        # APIキーが設定されていない場合の警告
        if not settings['openai_api_key']:
            logger.warning("OpenAI API key is not set. Some functionality may be limited.")
        
        return settings
    except Exception as e:
        logger.error(f"Error reading settings file {settings_path}: {e}")
        return default_settings

def read_file_safely(filepath: str) -> Optional[str]:
    """ファイルを安全に読み込む"""
    for encoding in ['utf-8', 'cp932']:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue  # 次のエンコーディングで試す
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {e}")
            return None
    logger.warning(f"Failed to read file {filepath} with supported encodings.")
    return None

def write_file_content(filepath: str, content: str) -> bool:
    """ファイルに内容を書き込む"""
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Error writing to file {filepath}: {e}")
        return False

def get_python_files(directory: str, exclude_patterns: List[str]) -> List[Tuple[str, str]]:
    """指定ディレクトリ配下のPythonファイルを取得"""
    python_files = []
    exclude_patterns = [pattern.strip() for pattern in exclude_patterns if pattern.strip()]  # パターンの正規化
    
    try:
        for root, dirs, files in os.walk(directory):
            # 除外パターンに一致するディレクトリをスキップ
            dirs[:] = [d for d in dirs if not any(fnmatch.fnmatch(d, pattern) for pattern in exclude_patterns)]
            
            for file in files:
                if file.endswith('.py') and not any(fnmatch.fnmatch(file, pattern) for pattern in exclude_patterns):
                    filepath = os.path.join(root, file)
                    rel_path = os.path.relpath(filepath, directory)
                    python_files.append((rel_path, filepath))
        
        return sorted(python_files)
    except Exception as e:
        logger.error(f"Error getting Python files from {directory}: {e}")
        return []

# 以下は共通化された関数

# utils.py の setup_logger 関数を更新
def setup_logger(name: str, log_dir: Optional[str] = None, log_file: str = "merge_files.log") -> logging.Logger:
    """
    ロガーをセットアップします。

    Args:
        name (str): ロガーの名前。
        log_dir (Optional[str]): ログファイルの保存ディレクトリ。
        log_file (str): ログファイル名。

    Returns:
        logging.Logger: セットアップ済みのロガー。
    """
    if log_dir is None:
        log_dir = os.path.join(os.getcwd(), "logs")  # デフォルトでカレントディレクトリ内の 'logs' フォルダを使用

    try:
        # ディレクトリが存在しない場合は作成
        os.makedirs(log_dir, exist_ok=True)
    except PermissionError as e:
        print(f"ログディレクトリの作成に失敗しました: {log_dir}. エラー: {e}")
        raise

    # ログファイルパスを構築
    log_path = os.path.join(log_dir, log_file)
    print(f"Logging to: {log_path}")  # デバッグ用の出力

    # ロガーを構築
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # 既存のハンドラーをクリア（重複ログを防ぐため）
    if logger.hasHandlers():
        logger.handlers.clear()

    try:
        # ログハンドラーを設定
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
    except PermissionError as e:
        print(f"ログファイルの作成に失敗しました: {log_path}. エラー: {e}")
        raise
    except Exception as e:
        print(f"ログファイルハンドラーの設定中にエラーが発生しました: {e}")
        raise

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # コンソールハンドラー（オプション）
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

class PromptLogger:
    """プロンプトとレスポンスをログに記録するクラス"""
    def __init__(self, logger: logging.Logger):
        self.logger = logger

    def log_prompt(self, prompt: str):
        """プロンプトをログに記録"""
        self.logger.debug("\n=== Prompt ===\n" + prompt + "\n")

    def log_response(self, response: str):
        """レスポンスをログに記録"""
        self.logger.debug("\n=== Response ===\n" + response + "\n")

def ensure_directories_exist(dirs: List[str]) -> None:
    """指定されたディレクトリが存在しない場合は作成する"""
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)

def initialize_openai_client(api_key: Optional[str] = None) -> OpenAI:
    """OpenAIクライアントを初期化する"""
    if not api_key:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OpenAI APIキーが設定されていません。環境変数または設定ファイルを確認してください。")
            raise ValueError("OpenAI APIキーが設定されていません。")
    client = OpenAI(api_key=api_key)
    return client

def generate_tree_structure(root_dir: str, exclude_dirs: List[str], exclude_files: List[str]) -> str:
    """ディレクトリ構造をツリー形式で生成"""
    def add_nodes(parent_node: Node, current_path: str):
        try:
            for item in sorted(os.listdir(current_path)):
                item_path = os.path.join(current_path, item)
                if os.path.isdir(item_path):
                    if item not in exclude_dirs:
                        dir_node = Node(item, parent=parent_node)
                        add_nodes(dir_node, item_path)
                elif not any(fnmatch.fnmatch(item, pattern) for pattern in exclude_files):
                    Node(item, parent=parent_node)
        except PermissionError:
            logger.warning(f"アクセス権限がないためスキップしました: {current_path}")

    root_node = Node(os.path.basename(root_dir))
    add_nodes(root_node, root_dir)
    return "\n".join([f"{pre}{node.name}" for pre, _, node in RenderTree(root_node)])

def update_readme(template_path: str, readme_path: str, spec_path: str, merge_path: str) -> bool:
    """README.md をテンプレートから更新する"""
    try:
        template_content = read_file_safely(template_path)
        if not template_content:
            logger.error(f"{template_path} の読み込みに失敗しました。README.md は更新されませんでした。")
            return False

        # [spec] プレースホルダーを仕様書で置換
        spec_content = read_file_safely(spec_path)
        if not spec_content:
            logger.error(f"{spec_path} の読み込みに失敗しました。README.md の [spec] プレースホルダーは置換されませんでした。")
            spec_content = "[仕様書の内容が取得できませんでした。]"
        updated_content = template_content.replace("[spec]", spec_content)

        # [tree] プレースホルダーをディレクトリ構造で置換
        merge_content = read_file_safely(merge_path)
        if not merge_content:
            logger.error(f"{merge_path} の読み込みに失敗しました。README.md の [tree] プレースホルダーは置換されませんでした。")
            tree_content = "[フォルダ構成の取得に失敗しました。]"
        else:
            # " # Merged Python Files" までの内容を抽出
            split_marker = "# Merged Python Files"
            if split_marker in merge_content:
                tree_section = merge_content.split(split_marker)[0]
            else:
                tree_section = merge_content  # マーカーがなければ全体を使用
            tree_content = tree_section.strip()
        updated_content = updated_content.replace("[tree]", f"```\n{tree_content}\n```")

        # 現在の日付を挿入（オプション）
        current_date = datetime.now().strftime("%Y-%m-%d")
        updated_content = updated_content.replace("2024-12-08", current_date)

        # README.md に書き込む
        success = write_file_content(readme_path, updated_content)
        if success:
            logger.info(f"README.md が正常に更新されました: {readme_path}")
            return True
        else:
            logger.error(f"README.md の更新に失敗しました: {readme_path}")
            return False

    except Exception as e:
        logger.error(f"README.md の更新中にエラーが発生しました: {e}")
        return False

def initialize_openai_client(api_key: Optional[str] = None) -> OpenAI:
    """OpenAIクライアントを初期化する"""
    if not api_key:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OpenAI APIキーが設定されていません。環境変数または設定ファイルを確認してください。")
            raise ValueError("OpenAI APIキーが設定されていません。")
    client = OpenAI(api_key=api_key)
    return client

def get_ai_response(client: OpenAI, prompt: str, model: str = "o1-mini", temperature: float = 0.7, 
                   system_content: str = "あなたは仕様書を作成するAIです。") -> str:
    """OpenAI APIを使用してAI応答を生成"""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature
        )
        logger.info("AI応答の取得に成功しました。")
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"AI応答取得中にエラーが発生しました: {e}")
        return ""

class OpenAIConfig:
    """OpenAI設定を管理するクラス"""
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o", temperature: float = 0.7):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI APIキーが設定されていません。環境変数または設定ファイルを確認してください。")
        self.model = model
        self.temperature = temperature
        self.client = OpenAI(api_key=self.api_key)

    def get_response(self, prompt: str, system_content: str = "あなたは仕様書を作成するAIです。") -> str:
        """AI応答を取得"""
        return get_ai_response(
            self.client,
            prompt,
            self.model,
            self.temperature,
            system_content
        )

================================================================================
File: src\__init__.py
================================================================================

 


================================================================================
File: src\main.py
================================================================================

#main.py
from utils.environment import EnvironmentUtils as env
from utils.logging_config import get_logger
from modules.gsc_handler import process_gsc_data

# 名前付きロガーを取得
logger = get_logger(__name__)

def setup_configurations():
    """
    設定ファイルと機密情報をロードしてデータを取得します。
    """
    # 環境変数のロード
    env.load_env()

    # settings.ini の値を取得
    temp_value = env.get_config_value("demo", "temp", default="N/A")
    logger.info(f"取得した設定値: demo.temp = {temp_value}")

    # secrets.env の値を取得
    secrets_demo = env.get_env_var("secrets_demo", default="N/A")
    logger.info(f"取得した秘密情報: secrets_demo = {secrets_demo}")

    # 現在の環境
    environment = env.get_environment()
    logger.info(f"現在の環境: {environment}")

    return temp_value, secrets_demo, environment

def main() -> None:
    """メイン処理"""
    # 実行時のメッセージ
    print("Hello, newProject!!")
    logger.info("Hello, newProject!!")

    # 設定値と秘密情報のロード
    temp, secrets_demo, environment = setup_configurations()

    # 設定完了メッセージの表示
    print(f'設定ファイルの設定完了{{"demo": "{temp}"}}')
    print(f'機密情報ファイルの設定完了{{"demo": "{secrets_demo}"}}')
    print('ログ設定完了')

    # GSC データ取得処理を実行
    logger.info("process_gsc_data を呼び出します。")
    process_gsc_data()
    logger.info("process_gsc_data の呼び出しが完了しました。")

if __name__ == "__main__":
    main()


================================================================================
File: src\modules\__init__.py
================================================================================

 


================================================================================
File: src\modules\date_initializer.py
================================================================================

# date_initializer.py
from datetime import datetime, timedelta
from google.cloud import bigquery
from utils.date_utils import get_current_jst_datetime  # ユーティリティ関数のインポート

# src/modules/date_initializer.py

from datetime import datetime, timedelta
from google.cloud import bigquery
from utils.date_utils import get_current_jst_datetime
from utils.environment import config

from utils.logging_config import get_logger
logger = get_logger(__name__)

def initialize_date_range():
    """
    初回実行か毎日の実行かに応じて日付範囲を生成します。
    処理が古い日付から開始し、さらに過去に向かって進むように設定。
    """
    initial_run = config.gsc_settings['initial_run']
    if initial_run:
        days = config.gsc_settings['initial_fetch_days']
        logger.info(f"初回実行: 過去{days}日分のデータを取得します。")
    else:
        days = config.gsc_settings['daily_fetch_days']
        logger.info(f"毎日実行: 過去{days}日分のデータを取得します。")
    
    today = get_current_jst_datetime().date()
    end_date = today - timedelta(days=2)  # GSCの制限により2日前まで
    start_date = end_date - timedelta(days=days - 1)  # 過去n日間

    logger.debug(f"initialize_date_range: start_date={start_date}, end_date={end_date}")

    return start_date, end_date

def get_next_date_range(config):
    """
    BigQueryの進捗状況を元に、次のデータ範囲を決定する。
    """
    client = bigquery.Client()
    table_id = f"{config.config['BIGQUERY']['PROJECT_ID']}.{config.config['BIGQUERY']['DATASET_ID']}.T_progress_tracking"

    query = f"""
        SELECT data_date, record_position
        FROM `{table_id}`
        WHERE is_date_completed = FALSE
        ORDER BY data_date DESC
        LIMIT 1
    """
    query_job = client.query(query)
    result = list(query_job.result())

    if result:
        last_date = result[0]["data_date"]
        last_row = result[0]["record_position"] or 0
        return last_date, last_row
    else:
        # 進捗がない場合、最新の日付から開始
        today = get_current_jst_datetime().date()  # 現在の日本時間を使用
        return today, 0

def get_date_range_for_fetch(start_date_str=None, end_date_str=None):
    """
    開始日と終了日を指定された日付で設定。
    指定がない場合はデフォルトで2日前のデータを取得対象とする。
    """
    today = get_current_jst_datetime().date()  # 現在の日本時間を使用

    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    else:
        start_date = today - timedelta(days=2)

    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    else:
        end_date = start_date
    return start_date, end_date


================================================================================
File: src\modules\gsc_fetcher.py
================================================================================

# src/modules/gsc_fetcher.py

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.cloud import bigquery
from utils.date_utils import get_current_jst_datetime, format_datetime_jst
from utils.url_utils import aggregate_records
from datetime import datetime
from utils.retry import insert_rows_with_retry

from utils.logging_config import get_logger
logger = get_logger(__name__)

class GSCConnector:
    """Google Search Console データを取得するクラス"""

    def __init__(self, config):
        """
        コンストラクタ

        Args:
            config (Config): Config クラスのインスタンス
        """
        self.config = config
        self.logger = get_logger(__name__)  # ロガーを初期化

        # 認証情報ファイルのパスを Config から取得
        credentials_path = self.config.credentials_path

        if not credentials_path:
            raise ValueError("Credentials path not set in config.")

        # サービスアカウント認証を設定
        credentials = service_account.Credentials.from_service_account_file(
            str(credentials_path),
            scopes=["https://www.googleapis.com/auth/webmasters.readonly"]
        )

        # GSC API クライアントを構築
        self.service = build('searchconsole', 'v1', credentials=credentials)
        self.logger.info("Google Search Console API クライアントを初期化しました。")

    def fetch_records(self, date: str, start_record: int, limit: int):
        """
        指定された日付のGSCデータをフェッチします。

        Args:
            date (str): データ取得対象の日付（YYYY-MM-DD）
            start_record (int): 取得開始位置
            limit (int): 取得するレコード数

        Returns:
            tuple: (取得したレコードリスト, 次のレコード位置)
        """
        property_name = self.config.gsc_settings['url']  # 'site_url' を 'url' に変更

        request = {
            'startDate': date,
            'endDate': date,
            'dimensions': ['query', 'page'],  # 必要に応じて調整
            'rowLimit': limit,
            'startRow': start_record
        }

        try:
            response = self.service.searchanalytics().query(
                siteUrl=property_name,
                body=request
            ).execute()

            records = response.get('rows', [])
            next_record = start_record + len(records)

            self.logger.info(f"日付 {date} のレコードを {len(records)} 件取得しました。次の開始位置: {next_record}")

            return records, next_record

        except HttpError as e:
            self.logger.error(f"GSC API HTTP エラー: {e}", exc_info=True)
            raise
        except Exception as e:
            self.logger.error(f"GSC データの取得中にエラーが発生しました: {e}", exc_info=True)
            raise

    def insert_to_bigquery(self, records, date: str):
        """
        取得したGSCデータをBigQueryに挿入します。

        Args:
            records (list): GSCから取得したレコードのリスト
            date (str): データ取得対象の日付（YYYY-MM-DD）
        """
        # データの集計
        aggregated_records = aggregate_records(records)

        if not aggregated_records:
            self.logger.info("集計後のレコードがありません。")
            return

        # BigQuery クライアントを初期化
        client = bigquery.Client(
            credentials=self._get_bigquery_credentials(),
            project=self.config.get_config_value('BIGQUERY', 'PROJECT_ID')
        )

        # 挿入先のテーブルIDを取得
        table_id = f"{self.config.get_config_value('BIGQUERY', 'PROJECT_ID')}." \
                   f"{self.config.get_config_value('BIGQUERY', 'DATASET_ID')}." \
                   f"{self.config.get_config_value('BIGQUERY', 'TABLE_ID')}"

        # データの整形
        rows_to_insert = []
        for record in aggregated_records:
            row_data = {
                "data_date": date,
                "url": record['url'],
                "query": record['query'],
                "impressions": record['impressions'],
                "clicks": record['clicks'],
                "avg_position": record['avg_position'],  # フィールド名を統一
                "insert_time_japan": format_datetime_jst(get_current_jst_datetime())  # DATETIME 型
            }
            rows_to_insert.append(row_data)

        # リトライロジック付きで挿入
        try:
            insert_rows_with_retry(client, table_id, rows_to_insert, self.logger)
        except Exception as e:
            self.logger.error(f"BigQueryへの挿入が失敗しました: {e}", exc_info=True)
            raise

    def fetch_and_insert_gsc_data(self, start_date=None, end_date=None):
        """
        指定された期間のGSCデータを取得し、BigQueryに挿入します。

        Args:
            start_date (str, optional): 開始日付（YYYY-MM-DD）
            end_date (str, optional): 終了日付（YYYY-MM-DD）
        """
        start_date = start_date or self.config.gsc_settings['start_date']
        end_date = end_date or datetime.now().strftime('%Y-%m-%d')
        batch_size = self.config.gsc_settings['batch_size']

        try:
            records, _ = self.fetch_records(start_date, 0, batch_size)
            if records:
                self.insert_to_bigquery(records, start_date)
        except Exception as e:
            self._handle_error(e)

    def _handle_error(self, exception):
        """Unified error handling."""
        error_message = "GSC API error" if isinstance(exception, HttpError) else f"Unexpected error: {exception}"
        self.logger.error(error_message, exc_info=True)

    def _get_bigquery_credentials(self):
        """BigQuery 用の認証情報を取得します。"""
        credentials_path = self.config.credentials_path
        return service_account.Credentials.from_service_account_file(str(credentials_path))

    def _bq_schema(self):
        """Define and return the BigQuery table schema."""
        return [
            bigquery.SchemaField('data_date', 'DATE'),
            bigquery.SchemaField('url', 'STRING'),
            bigquery.SchemaField('query', 'STRING'),
            bigquery.SchemaField('impressions', 'INTEGER'),
            bigquery.SchemaField('clicks', 'INTEGER'),
            bigquery.SchemaField('avg_position', 'FLOAT'),  # フィールド名を統一
            bigquery.SchemaField('insert_time_japan', 'DATETIME')  # DATETIME 型
        ]

================================================================================
File: src\modules\gsc_handler.py
================================================================================

# src/modules/gsc_handler.py

from datetime import datetime, timedelta
from google.cloud import bigquery
from google.oauth2 import service_account

from modules.gsc_fetcher import GSCConnector
from modules.date_initializer import initialize_date_range
from utils.environment import config
from utils.date_utils import get_current_jst_datetime, format_datetime_jst
from utils.retry import insert_rows_with_retry

from utils.logging_config import get_logger
logger = get_logger(__name__)

def process_gsc_data():
    """GSC データを取得し、BigQuery に保存するメイン処理"""
    logger.info("process_gsc_data が呼び出されました。")

    # 取得する日付範囲を設定（古い日付から開始し、さらに過去に向かって進む）
    start_date, end_date = initialize_date_range()
    logger.info(f"Processing GSC data for date range: {start_date} to {end_date}")

    # GSCConnector に Config を渡す
    gsc_connector = GSCConnector(config)
    logger.info("GSCConnector を初期化しました。")

    # GSC APIの1日あたりのクォータを設定
    daily_api_limit = config.gsc_settings['daily_api_limit']
    processed_count = 0

    # 前回の処理位置を取得
    last_position = get_last_processed_position(config)
    if last_position:
        logger.info(f"Last position: date={last_position['date']}, record={last_position['record']}")
    else:
        logger.info("No previous processing position found.")

    # 処理開始日を設定
    current_date = last_position["date"] if last_position else end_date
    start_record = last_position["record"] if last_position else 0

    while current_date >= start_date and processed_count < daily_api_limit:
        try:
            remaining_quota = daily_api_limit - processed_count
            fetch_limit = config.gsc_settings['batch_size']  # 既に int として取得

            logger.debug(f"fetch_limit type: {type(fetch_limit)}, value: {fetch_limit}")

            logger.info(f"Fetching records from {current_date}, start_record={start_record}, limit={fetch_limit}")
            records, next_record = gsc_connector.fetch_records(
                date=str(current_date),
                start_record=start_record,
                limit=fetch_limit
            )
            logger.info(f"Fetched {len(records)} records.")

            if records:
                gsc_connector.insert_to_bigquery(records, str(current_date))
                logger.info(f"Inserted {len(records)} records into BigQuery.")
                processed_count += 1  # API呼び出し回数をカウント

                # 進捗保存（アップサート）
                save_processing_position(config, {
                    "date": current_date,
                    "record": next_record,
                    "is_date_completed": len(records) < fetch_limit
                })
                logger.info(f"Progress saved for date {current_date}.")

                if len(records) < fetch_limit:
                    # 日付完了、次の日付へ
                    current_date -= timedelta(days=1)
                    start_record = 0
                    logger.info(f"Moving to next date: {current_date}")
                else:
                    # 同じ日の続きから
                    start_record = next_record
                    logger.info(f"Continuing on the same date: {current_date}, new start_record={start_record}")
            else:
                # データなし、次の日付へ
                current_date -= timedelta(days=1)
                start_record = 0
                logger.info(f"No records fetched. Moving to next date: {current_date}")

        except Exception as e:
            logger.error(f"Error at date {current_date}, record {start_record}: {e}", exc_info=True)
            break

    logger.info(f"Processed {processed_count} API calls in total")

'''''
    # 初回実行後にフラグを更新
    initial_run = config.gsc_settings['initial_run']
    if initial_run and not last_position:
        # 初回実行が完了したらフラグをfalseに設定
        update_initial_run_flag(config, False)
        logger.info("初回実行が完了しました。INITIAL_RUNフラグをfalseに更新しました。")
'''''

def update_initial_run_flag(config, flag: bool):
    """
    settings.iniのINITIAL_RUNフラグを更新します。

    Args:
        config: Config クラスのインスタンス
        flag (bool): フラグの新しい値
    """
    import configparser

    settings_path = config.get_config_file('settings.ini')
    parser = configparser.ConfigParser()
    parser.read(settings_path, encoding='utf-8')

    if 'GSC_INITIAL' not in parser.sections():
        parser.add_section('GSC_INITIAL')

    parser.set('GSC_INITIAL', 'INITIAL_RUN', str(flag).lower())

    with open(settings_path, 'w', encoding='utf-8') as configfile:
        parser.write(configfile)

    logger.info(f"settings.ini の INITIAL_RUN を {flag} に更新しました。")

def save_processing_position(config, position):
    """処理位置を保存（アップサート操作）"""
    credentials_path = config.credentials_path
    credentials = service_account.Credentials.from_service_account_file(str(credentials_path))
    client = bigquery.Client(credentials=credentials, project=config.get_config_value('BIGQUERY', 'PROJECT_ID'))
    table_id = config.progress_table_id

    updated_at_jst = format_datetime_jst(get_current_jst_datetime())

    data_date = str(position["date"])
    record_position = position["record"]
    is_date_completed = position["is_date_completed"]

    # MERGE ステートメントを使用してアップサートを実行
    merge_query = f"""
        MERGE `{table_id}` T
        USING (SELECT @data_date AS data_date) S
        ON T.data_date = S.data_date
        WHEN MATCHED THEN
            UPDATE SET 
                record_position = @record_position,
                is_date_completed = @is_date_completed,
                updated_at = @updated_at
        WHEN NOT MATCHED THEN
            INSERT (data_date, record_position, is_date_completed, updated_at)
            VALUES (@data_date, @record_position, @is_date_completed, @updated_at)
    """

    job_config = bigquery.QueryJobConfig(
        query_parameters=[
            bigquery.ScalarQueryParameter("data_date", "DATE", data_date),
            bigquery.ScalarQueryParameter("record_position", "INT64", record_position),
            bigquery.ScalarQueryParameter("is_date_completed", "BOOL", is_date_completed),
            bigquery.ScalarQueryParameter("updated_at", "DATETIME", updated_at_jst)
        ]
    )

    try:
        query_job = client.query(merge_query, job_config=job_config)
        query_job.result()  # 完了まで待機
        logger.info(f"Progress updated for date {data_date}.")
    except Exception as e:
        logger.error(f"Failed to save processing position for {data_date}: {e}", exc_info=True)
        raise

def get_last_processed_position(config):
    """最後に処理したポジションを取得"""
    credentials_path = config.credentials_path
    credentials = service_account.Credentials.from_service_account_file(str(credentials_path))
    client = bigquery.Client(credentials=credentials, project=config.get_config_value('BIGQUERY', 'PROJECT_ID'))
    table_id = config.progress_table_id

    query = f"""
        SELECT data_date, record_position
        FROM `{table_id}`
        WHERE is_date_completed = FALSE
        ORDER BY updated_at DESC
        LIMIT 1
    """
    try:
        query_job = client.query(query)
        results = list(query_job.result())
        if results:
            return {
                "date": results[0].data_date,  # data_dateはすでにdatetime.date型
                "record": results[0].record_position
            }
        return None
    except Exception as e:
        logger.error(f"Error fetching last processed position: {e}", exc_info=True)
        return None


================================================================================
File: src\utils\__init__.py
================================================================================

 


================================================================================
File: src\utils\date_utils.py
================================================================================

# utils/date_utils.py
from datetime import datetime
import pytz

def get_current_jst_datetime():
    """
    現在の日本時間（JST）を取得します。
    
    Returns:
        datetime: 現在のJSTのdatetimeオブジェクト。
    """
    jst = pytz.timezone('Asia/Tokyo')
    return datetime.now(jst).replace(microsecond=0)

def format_datetime_jst(jst_datetime, fmt="%Y-%m-%d %H:%M:%S"):
    """
    JSTのdatetimeオブジェクトを指定されたフォーマットで文字列に変換します。
    
    Args:
        jst_datetime (datetime): JSTのdatetimeオブジェクト。
        fmt (str): 出力フォーマット。
    
    Returns:
        str: フォーマットされた日付文字列。
    """
    return jst_datetime.strftime(fmt)


================================================================================
File: src\utils\environment.py
================================================================================

# src/utils/environment.py

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Any
import configparser
import logging

class EnvironmentUtils:
    """プロジェクト全体で使用する環境関連のユーティリティクラス"""

    # プロジェクトルートのデフォルト値
    BASE_DIR = Path(__file__).resolve().parent.parent.parent

    @staticmethod
    def set_project_root(path: Path) -> None:
        """
        プロジェクトのルートディレクトリを設定します。

        Args:
            path (Path): 新しいプロジェクトルート
        """
        EnvironmentUtils.BASE_DIR = path

    @staticmethod
    def get_project_root() -> Path:
        """
        プロジェクトのルートディレクトリを取得します。

        Returns:
            Path: プロジェクトのルートディレクトリ
        """
        return EnvironmentUtils.BASE_DIR

    @staticmethod
    def load_env(env_file: Optional[Path] = None) -> None:
        """
        環境変数を .env ファイルからロードします。

        Args:
            env_file (Optional[Path]): .env ファイルのパス
        """
        env_file = env_file or (EnvironmentUtils.BASE_DIR / "config" / "secrets.env")

        if not env_file.exists():
            raise FileNotFoundError(f"{env_file} が見つかりません。正しいパスを指定してください。")

        load_dotenv(env_file)

    @staticmethod
    def get_env_var(key: str, default: Optional[Any] = None) -> Any:
        """
        環境変数を取得します。

        Args:
            key (str): 環境変数のキー
            default (Optional[Any]): デフォルト値

        Returns:
            Any: 環境変数の値またはデフォルト値
        """
        return os.getenv(key, default)

    @staticmethod
    def get_config_file(file_name: str = "settings.ini") -> Path:
        """
        設定ファイルのパスを取得します。

        Args:
            file_name (str): 設定ファイル名

        Returns:
            Path: 設定ファイルのパス

        Raises:
            FileNotFoundError: 指定された設定ファイルが見つからない場合
        """
        config_path = EnvironmentUtils.BASE_DIR / "config" / file_name
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        return config_path

    @staticmethod
    def get_config_value(section: str, key: str, default: Optional[Any] = None) -> Any:
        """
        設定ファイルから指定のセクションとキーの値を取得します。

        Args:
            section (str): セクション名
            key (str): キー名
            default (Optional[Any]): デフォルト値

        Returns:
            Any: 設定値
        """
        config_path = EnvironmentUtils.get_config_file()
        config = configparser.ConfigParser()

        # utf-8 エンコーディングで読み込む
        config.read(config_path, encoding='utf-8')

        if not config.has_section(section):
            return default
        if not config.has_option(section, key):
            return default

        value = config.get(section, key, fallback=default)

        # 型変換
        if isinstance(default, bool):
            return config.getboolean(section, key, fallback=default)
        if isinstance(default, int):
            try:
                return int(value)
            except ValueError:
                return default
        if isinstance(default, float):
            try:
                return float(value)
            except ValueError:
                return default
        return value

    @staticmethod
    def resolve_path(path: str) -> Path:
        """
        指定されたパスをプロジェクトルートに基づいて絶対パスに変換します。

        Args:
            path (str): 相対パスまたは絶対パス

        Returns:
            Path: 解決された絶対パス
        """
        resolved_path = Path(path)
        if not resolved_path.is_absolute():
            resolved_path = EnvironmentUtils.get_project_root() / resolved_path

        if not resolved_path.exists():
            raise FileNotFoundError(f"Resolved path does not exist: {resolved_path}")

        return resolved_path

    @staticmethod
    def get_service_account_file() -> Path:
        """
        サービスアカウントファイルのパスを取得します。

        Returns:
            Path: サービスアカウントファイルの絶対パス

        Raises:
            FileNotFoundError: ファイルが存在しない場合
        """
        service_account_file = EnvironmentUtils.get_env_var(
            "SERVICE_ACCOUNT_FILE",
            default=EnvironmentUtils.get_config_value("GOOGLE", "service_account_file", default="config/service_account.json")
        )

        return EnvironmentUtils.resolve_path(service_account_file)

    @staticmethod
    def get_environment() -> str:
        """
        環境変数 APP_ENV を取得します。
        デフォルト値は 'development' です。

        Returns:
            str: 現在の環境（例: 'development', 'production'）
        """
        return EnvironmentUtils.get_env_var("APP_ENV", "development")

    @staticmethod
    def get_openai_api_key():
        """
        Get the OpenAI API key from the environment variables.
        """
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY が設定されていません。環境変数を確認してください。")
        return api_key

    @staticmethod
    def get_openai_model():
        """
        OpenAI モデル名を settings.ini ファイルから取得します。
        設定がない場合はデフォルト値 'gpt-4o' を返します。
        """
        return EnvironmentUtils.get_config_value("OPENAI", "model", default="gpt-4o")

class Config:
    def __init__(self, env='development'):
        self.env = env
        self.logger = logging.getLogger(__name__)
        self.base_path = Path(__file__).parent.parent.parent
        self.config = self._load_config()
        self._load_secrets()
        self._setup_credentials()

        # GSC設定を初期化時にロード
        self._gsc_settings = self._load_gsc_settings()

    def _load_gsc_settings(self):
        """GSC関連の設定を初期化時に1度だけ読み込む"""
        try:
            settings = {
                'url': self.config['GSC']['SITE_URL'],
                'start_date': self.config['GSC'].get('START_DATE', '2024-11-01'),
                'batch_size': int(self.config['GSC']['BATCH_SIZE']),
                'metrics': self.config['GSC']['METRICS'].split(','),
                'dimensions': self.config['GSC']['DIMENSIONS'].split(','),
                'retry_count': int(self.config['GSC']['RETRY_COUNT']),
                'retry_delay': int(self.config['GSC']['RETRY_DELAY']),
                'daily_api_limit': int(self.config['GSC']['DAILY_API_LIMIT']),
                'initial_run': self.config['GSC_INITIAL'].getboolean('INITIAL_RUN', fallback=True),
                'initial_fetch_days': int(self.config['GSC_DAILY']['INITIAL_FETCH_DAYS']),
                'daily_fetch_days': int(self.config['GSC_DAILY']['DAILY_FETCH_DAYS']),
            }
            self.logger.info(f"GSC settings loaded: {settings}")  # 初回のみログ出力
            return settings
        except KeyError as e:
            self.logger.error(f"Missing key in GSC configuration: {e}")
            raise
        except ValueError as e:
            self.logger.error(f"Invalid value in GSC configuration: {e}")
            raise

    @property
    def gsc_settings(self):
        """初期化済みの GSC 設定を返す"""
        return self._gsc_settings

    def _load_config(self):
        """設定ファイルの読み込み"""
        config = configparser.ConfigParser()
        config_path = self.base_path / 'config' / 'settings.ini'

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8-sig') as f:
                config.read_file(f)
            self.logger.info(f"Loaded configuration from: {config_path}")
        except UnicodeDecodeError:
            try:
                with open(config_path, 'r', encoding='cp932') as f:
                    config.read_file(f)
                self.logger.warning(f"Loaded configuration using fallback encoding: {config_path}")
            except Exception as e:
                self.logger.error(f"Failed to load configuration file: {e}")
                raise

        return config

    def _load_secrets(self):
        """環境変数ファイルの読み込み"""
        env_path = self.base_path / 'config' / 'secrets.env'
        if not env_path.exists():
            raise FileNotFoundError(f"Secrets file not found: {env_path}")

        try:
            load_dotenv(env_path, encoding='utf-8')
            self.logger.info(f"Loaded environment variables from: {env_path}")
        except Exception as e:
            self.logger.error(f"Failed to load secrets file: {e}")
            raise

    def _setup_credentials(self):
        """認証情報ファイルのパスを設定"""
        credentials_file = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if not credentials_file:
            raise ValueError("GOOGLE_APPLICATION_CREDENTIALS not set in secrets.env")

        credentials_path = self.base_path / 'config' / credentials_file
        if not credentials_path.exists():
            raise FileNotFoundError(
                f"Credentials file not found: {credentials_path}\n"
                f"Expected file: {credentials_file}\n"
                f"Looking in: {self.base_path / 'config'}"
            )

        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(credentials_path.absolute())
        self.logger.info(f"Google credentials set: {credentials_path}")
        # 確認のために環境変数を追加で出力
        self.logger.debug(f"GOOGLE_APPLICATION_CREDENTIALS is set to: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS')}")

    @property
    def log_dir(self):
        """ログディレクトリのパスを取得"""
        log_dir = self.base_path / 'logs'
        if not log_dir.exists():
            log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir

    @property
    def credentials_path(self):
        return os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

    @property
    def debug_mode(self):
        """デバッグモードの有効化"""
        try:
            return self.config[self.env].getboolean('DEBUG')
        except KeyError:
            self.logger.warning("DEBUG setting not found; defaulting to False.")
            return False

    @property
    def log_level(self):
        """ログレベルの取得"""
        try:
            return self.config[self.env]['LOG_LEVEL']
        except KeyError:
            self.logger.warning("LOG_LEVEL setting not found; defaulting to INFO.")
            return 'INFO'

    @property
    def progress_table_id(self):
        """BigQuery進行状況トラッキングテーブルのIDを取得"""
        try:
            return (
                f"{self.config['BIGQUERY']['PROJECT_ID']}."
                f"{self.config['BIGQUERY']['DATASET_ID']}."
                f"{self.config['BIGQUERY']['PROGRESS_TABLE_ID']}"
            )
        except KeyError as e:
            self.logger.error(f"Missing BigQuery tracking table setting: {e}")
            raise

    def get_config_value(self, section, key, default=None):
        """指定されたセクションとキーの設定値を取得"""
        try:
            return self.config.get(section, key, fallback=default)
        except KeyError as e:
            self.logger.error(f"Missing configuration for {section}.{key}: {e}")
            raise

    def __str__(self):
        return f"Config(env={self.env}, base_path={self.base_path})"

# グローバルインスタンスの作成
config = Config()


================================================================================
File: src\utils\helpers.py
================================================================================

 


================================================================================
File: src\utils\logging_config.py
================================================================================

# logging_config.py
import logging
import logging.handlers
from datetime import datetime
from pathlib import Path
from typing import Optional

class LoggingConfig:
    _initialized = False

    def __init__(self):
        """
        ログ設定を初期化します。
        """
        if LoggingConfig._initialized:
            return  # 再初期化を防止

        self.log_dir = Path("logs")
        self.log_level = logging.INFO
        self.log_format = "%(asctime)s - %(name)s - [%(levelname)s] - %(message)s"

        self.setup_logging()

        LoggingConfig._initialized = True  # 初期化済みフラグを設定

    def setup_logging(self) -> None:
        """
        ロギング設定をセットアップします。
        """
        if not self.log_dir.exists():
            self.log_dir.mkdir(parents=True, exist_ok=True)

        log_file = self.log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"

        handlers = [
            logging.handlers.TimedRotatingFileHandler(
                log_file, when="midnight", interval=1, backupCount=30, encoding="utf-8"
            ),
            logging.StreamHandler(),
        ]

        logging.basicConfig(
            level=self.log_level,
            format=self.log_format,
            handlers=handlers,
        )

        logging.getLogger().info("Logging setup complete.")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    名前付きロガーを取得します。

    Args:
        name (Optional[str]): ロガー名

    Returns:
        logging.Logger: 名前付きロガー
    """
    LoggingConfig()
    return logging.getLogger(name)

================================================================================
File: src\utils\retry.py
================================================================================

# src/utils.py

import time
from google.auth.exceptions import RefreshError
from google.cloud import bigquery
import logging

def insert_rows_with_retry(client: bigquery.Client, table_id: str, rows_to_insert: list, logger: logging.Logger,
                           max_retries: int = 5, retry_delay: int = 10) -> None:
    """
    BigQueryへのデータ挿入をリトライロジック付きで実行します。

    Args:
        client (bigquery.Client): BigQuery クライアント
        table_id (str): 挿入先のテーブルID
        rows_to_insert (list): 挿入する行データのリスト
        logger (logging.Logger): ロガー
        max_retries (int): 最大リトライ回数
        retry_delay (int): リトライ間の待機時間（秒）

    Raises:
        Exception: 最大リトライ回数に達した場合
    """
    for attempt in range(1, max_retries + 1):
        try:
            errors = client.insert_rows_json(table_id, rows_to_insert)
            if not errors:
                logger.info(f"Successfully inserted {len(rows_to_insert)} rows into {table_id}.")
                return
            else:
                logger.error(f"BigQuery insertion errors (Attempt {attempt}): {errors}")
                if attempt < max_retries:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
        except RefreshError as e:
            logger.error(f"Authentication error occurred (Attempt {attempt}): {e}")
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
        except Exception as e:
            logger.error(f"Unexpected error during BigQuery insertion (Attempt {attempt}): {e}")
            if attempt < max_retries:
                logger.info(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
    else:
        logger.critical(f"Failed to insert rows into {table_id} after {max_retries} attempts.")
        raise Exception("BigQuery insertion failed after maximum retries.")


================================================================================
File: src\utils\url_utils.py
================================================================================

# src/utils/url_utils.py
from urllib.parse import urlparse, urlunparse
from collections import defaultdict

from urllib.parse import urlparse, urlunparse
from collections import defaultdict

def normalize_url(url):
    """
    URLからクエリパラメータとフラグメント識別子を除去します。

    Args:
        url (str): 正規化前のURL

    Returns:
        str: クエリパラメータとフラグメント識別子を除去したURL
    """
    parsed_url = urlparse(url)
    # クエリとフラグメントを除去
    normalized_url = urlunparse(parsed_url._replace(query="", fragment=""))
    return normalized_url

def aggregate_records(records):
    """
    レコードをURLでグルーピングし、クリック数、インプレッション数、平均順位を集計します。

    Args:
        records (list): GSCから取得したレコードのリスト

    Returns:
        list: 集計後のレコードリスト
    """
    aggregated_data = defaultdict(lambda: {"clicks": 0, "impressions": 0, "positions": []})

    for record in records:
        query = record['keys'][0]
        url = record['keys'][1]
        clicks = record.get('clicks', 0)
        impressions = record.get('impressions', 0)
        position = record.get('position', 0.0)

        normalized_url = normalize_url(url)

        key = (query, normalized_url)
        aggregated_data[key]["clicks"] += clicks
        aggregated_data[key]["impressions"] += impressions
        aggregated_data[key]["positions"].append(position)

    # 平均順位を計算
    final_records = []
    for (query, url), data in aggregated_data.items():
        avg_position = sum(data["positions"]) / len(data["positions"]) if data["positions"] else 0.0
        final_records.append({
            "query": query,
            "url": url,
            "clicks": data["clicks"],
            "impressions": data["impressions"],
            "avg_position": avg_position  # フィールド名を統一
        })

    return final_records


================================================================================
File: tests\__init__.py
================================================================================

 


================================================================================
File: tests\test_url_utils.py
================================================================================

# tests/test_url_utils.py
import unittest
from src.utils.url_utils import normalize_url, aggregate_records

class TestURLUtils(unittest.TestCase):

    def test_normalize_url(self):
        url_with_query = "https://www.juku.st/info/entry/843?param=value"
        expected = "https://www.juku.st/info/entry/843"
        self.assertEqual(normalize_url(url_with_query), expected)

        url_without_query = "https://www.juku.st/info/entry/843"
        self.assertEqual(normalize_url(url_without_query), url_without_query)

    def test_aggregate_records(self):
        records = [
            {
                'keys': ['query1', 'https://www.juku.st/info/entry/843?param=value1'],
                'clicks': 10,
                'impressions': 100,
                'position': 1.5
            },
            {
                'keys': ['query1', 'https://www.juku.st/info/entry/843?param=value2'],
                'clicks': 20,
                'impressions': 200,
                'position': 2.0
            },
            {
                'keys': ['query2', 'https://www.juku.st/info/entry/844'],
                'clicks': 5,
                'impressions': 50,
                'position': 3.0
            }
        ]

        expected = [
            {
                "query": "query1",
                "url": "https://www.juku.st/info/entry/843",
                "clicks": 30,
                "impressions": 300,
                "avg_position": 1.75
            },
            {
                "query": "query2",
                "url": "https://www.juku.st/info/entry/844",
                "clicks": 5,
                "impressions": 50,
                "avg_position": 3.0
            }
        ]

        result = aggregate_records(records)
        # ソートして比較
        self.assertEqual(sorted(result, key=lambda x: (x['query'], x['url'])),
                         sorted(expected, key=lambda x: (x['query'], x['url'])))

if __name__ == '__main__':
    unittest.main()
```
```

---

## 実行方法

### 1. 仮想環境の作成と有効化
初回実行時には仮想環境を作成します。以下のコマンドを使用してください。

```bash
.\run_dev.bat
```

- 仮想環境が存在しない場合、自動的に作成されます。
- 必要なパッケージは `requirements.txt` から自動インストールされます。

仮想環境を手動で有効化する場合：
```bash
.\env\Scripts Activate
```

---

### 2. メインスクリプトの実行
デフォルトでは `src\main.py` が実行されます。他のスクリプトを指定する場合は、引数にスクリプトパスを渡します。

```bash
.\run_dev.bat src\your_script.py
```

環境を指定する場合、`--env` オプションを使用します（例: `development`, `production`）。

```bash
.\run_dev.bat --env production
```

---

### 3. 仕様書生成ツールの使用
仕様書生成スクリプトは `spec_tools_run.bat` を使用して実行できます。

- **merge_files.py の実行**:
  ```bash
  .\spec_tools_run.bat --merge
  ```

- **仕様書生成**:
  ```bash
  .\spec_tools_run.bat --spec
  ```

- **詳細仕様書生成**:
  ```bash
  .\spec_tools_run.bat --detailed-spec
  ```

- **すべてを一括実行**:
  ```bash
  .\spec_tools_run.bat --all
  ```

---

### 4. 本番環境の実行
タスクスケジューラ等で設定をする際には、'run.bat'を利用してください。（パラメータ無しでproduction環境の実行をします）

```bash
.\run.bat
```


## 注意事項

1. **仮想環境の存在確認**:
   `run.bat` / `run_dev.bat` または `spec_tools_run.bat` を初回実行時に仮想環境が作成されます。既存の仮想環境を削除する場合、手動で `.\env` を削除してください。

2. **環境変数の設定**:
   APIキーなどの秘密情報は `config\secrets.env` に格納し、共有しないよう注意してください。

3. **パッケージのアップデート**:
   必要に応じて、`requirements.txt` を更新してください。更新後、`run_dev.bat` を実行すると自動的にインストールされます。

---