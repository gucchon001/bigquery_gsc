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
