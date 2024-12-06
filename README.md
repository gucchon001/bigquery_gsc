## 仕様
# 機能要件仕様書

### 1. システム概要
- プログラムの全体的な目的と対象のユーザー
  - このプログラムは、Pythonプロジェクト内のソースコードファイルを収集し、その内容をマージして仕様書を生成するためのツールです。仕様書はOpenAIのモデルを使用して生成されます。このツールは、コードの仕様を文書化したい開発者やプロジェクトマネージャー向けに設計されています。プログラムは特にAIを使用した自動化されたドキュメント生成に重点を置いています。

### 2. 主要機能要件
- 提供される各機能の説明
  - **SpecificationGeneratorクラス**:
    - 仕様書を生成するための主要なクラス。OpenAIのAPIを使用して、コード内容をもとに仕様書を生成します。
    - `generate()`メソッド: プロンプトとコードを結合してAIに送り、生成された仕様書をファイルに保存します。
    - `_read_merge_file()`メソッド: マージされたコードファイルを読み込みます。
    - `_read_prompt_file()`メソッド: 仕様書生成に使用するプロンプトを読み込みます。
  
  - **PythonFileMergerクラス**:
    - Pythonファイルをマージする機能を提供。指定されたディレクトリからPythonファイルを収集し、フォルダ構造とファイル内容を統合したファイルを生成します。
    - `_collect_python_files()`メソッド: 指定されたディレクトリからPythonファイルを収集します。
    - `_merge_files_content()`メソッド: 収集したファイルの内容をマージします。
  
  - **環境設定とログ管理**:
    - 環境変数や設定ファイルからの情報取得をサポートするユーティリティクラスが用意されています。
    - ログ設定が包括的に管理されており、アプリケーションの動作を記録します。

### 3. 非機能要件
- パフォーマンス
  - 仕様書生成はAIモデルを使用するため、ネットワークの速度やAPIの応答時間に依存します。
  
- セキュリティ
  - OpenAI APIキーのセキュリティが重要。環境変数や設定ファイルで管理されており、公開されないように注意が必要です。
  
- 可用性
  - エラーログが詳細に記録されており、問題発生時のトラブルシューティングがしやすい構造になっています。

### 4. 技術要件
- 開発環境
  - Python 3.x（3.6以上推奨）
  - 利用ライブラリ: dotenv, icecream, anytree, openaiなど
  
- システム環境
  - OS: クロスプラットフォーム（Windows, macOS, Linuxで動作可能）
  
- 必要なライブラリ
  - `requirements.txt`で指定されたPythonパッケージが必要です。特に、OpenAI APIを使用するために`openai`ライブラリが必要です。 

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
│   ├── secrets.env
│   └── settings.ini
├── data
├── docs
│   ├── .gitkeep
│   └── merge.txt
├── logs
│   └── .gitkeep
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
│   │   └── module1.py
│   └── utils
│       ├── __init__.py
│       ├── environment.py
│       ├── helpers.py
│       └── logging_config.py
└── tests
    └── __init__.py

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
            updated_content = updated_content.replace("2024-12-06", current_date)

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
        updated_content = updated_content.replace("2024-12-06", current_date)

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

from utils.environment import EnvironmentUtils as env
from utils.logging_config import get_logger

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

if __name__ == "__main__":
    main()


================================================================================
File: src\modules\__init__.py
================================================================================

 


================================================================================
File: src\modules\module1.py
================================================================================

 


================================================================================
File: src\utils\__init__.py
================================================================================

 


================================================================================
File: src\utils\environment.py
================================================================================

import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Optional, Any
import configparser

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
        if value.isdigit():
            return int(value)
        if value.replace('.', '', 1).isdigit():
            return float(value)
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'
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
File: tests\__init__.py
================================================================================
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