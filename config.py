"""
配置文件 - MDD-5k项目
统一管理API配置、模型配置和文件路径常量
"""
import os

# ============= API配置 =============
class APIConfig:
    """API相关配置"""
    # OpenAI API配置
    OPENAI_API_KEY = ""  # GPT-4 API Key，需要用户填入
    OPENAI_BASE_URL = "https://api.openai.com/v1"  # OpenAI基础URL
    
    # 本地API配置 (Qwen等本地模型)
    LOCAL_API_KEY = "EMPTY"  # 本地API Key
    LOCAL_BASE_URL = "http://localhost:9012/v1/"  # 本地API基础URL

# ============= 模型配置 =============
class ModelConfig:
    """模型相关配置"""
    # 默认模型配置
    DEFAULT_MODEL_NAME = '/tcci_mnt/shihao/models/Qwen3-8B'
    GPT4_MODEL_NAME = 'gpt-4o'
    
    # 模型成本配置（每1000个token的成本）
    GPT4_INPUT_COST = 15 / 1000000   # GPT-4o输入成本
    GPT4_OUTPUT_COST = 5 / 1000000   # GPT-4o输出成本

# ============= 文件路径配置 =============
class PathConfig:
    """文件路径相关配置"""
    # 项目根目录
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    
    # 原始数据路径
    RAW_DATA_DIR = os.path.join(PROJECT_ROOT, 'raw_data')
    PATIENT_INFO_PATH = os.path.join(RAW_DATA_DIR, 'pat_smhc_train.json')
    PATIENT_CASES_ORIGIN_PATH = '/tcci_mnt/shihao/data/smhc_train.xlsx'
    PATIENT_CASES_JSON_PATH = os.path.join(RAW_DATA_DIR, 'pat_smhc_train.json')
    
    # 提示词路径
    PROMPTS_DIR = os.path.join(PROJECT_ROOT, 'prompts')
    DOCTOR_PROMPT_PATH = os.path.join(PROMPTS_DIR, 'doctor', 'doctor_persona.json')
    DIAGTREE_PATH = os.path.join(PROMPTS_DIR, 'diagtree')
    PATIENT_PROMPTS_DIR = os.path.join(PROMPTS_DIR, 'patient')
    
    # 背景故事路径
    BACKGROUND_STORY_DIR = os.path.join(PROMPTS_DIR, 'patient', 'background_story')
    
    # 输出路径
    OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'DataSyn')
    
    # 临时文件和缓存路径
    TEMP_DIR = os.path.join(PROJECT_ROOT, 'temp')
    CACHE_DIR = os.path.join(PROJECT_ROOT, 'cache')

# ============= 系统配置 =============
class SystemConfig:
    """系统相关配置"""
    # 生成配置
    NUM_CONVERSATIONS = 5  # 每个患者生成的对话数量
    
    # API调用配置
    DEFAULT_TOP_P = 0.9
    DEFAULT_TEMPERATURE = 0.8
    DEFAULT_FREQUENCY_PENALTY = 0.8
    
    # 对话配置
    MAX_DIALOGUE_HISTORY = 8  # 最大对话历史长度
    
    # 调试配置
    DEBUG = False

# ============= 便捷访问函数 =============
def get_model_name():
    """获取默认模型名称"""
    return ModelConfig.DEFAULT_MODEL_NAME

def get_patient_info_path():
    """获取患者信息文件路径"""
    return PathConfig.PATIENT_INFO_PATH

def get_doctor_prompt_path():
    """获取医生提示词路径"""
    return PathConfig.DOCTOR_PROMPT_PATH

def get_diagtree_path():
    """获取诊断树路径"""
    return PathConfig.DIAGTREE_PATH

def get_output_dir():
    """获取输出目录路径"""
    return PathConfig.OUTPUT_DIR

def get_background_story_dir():
    """获取背景故事目录路径"""
    return PathConfig.BACKGROUND_STORY_DIR

def ensure_dirs_exist():
    """确保必要的目录存在"""
    dirs_to_create = [
        PathConfig.OUTPUT_DIR,
        PathConfig.TEMP_DIR,
        PathConfig.CACHE_DIR,
        PathConfig.BACKGROUND_STORY_DIR
    ]
    
    for dir_path in dirs_to_create:
        os.makedirs(dir_path, exist_ok=True)

# 初始化时创建必要目录
ensure_dirs_exist() 