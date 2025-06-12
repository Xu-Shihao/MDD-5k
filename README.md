# MDD-5k: 基于神经符号LLM智能体的精神障碍诊断对话数据集

![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)

## 📄 论文信息

本项目是AAAI 2025论文《MDD-5k: A New Diagnostic Conversation Dataset for Mental Disorders Synthesized via Neuro-Symbolic LLM Agents》的官方实现。

## 🔥 最新更新

**注意：** MDD-5k数据集目前正在进行伦理审查，我们将在审查程序完成后发布完整数据集。所有最新信息将在此页面更新。

## 📖 项目简介

MDD-5k是一个专门用于精神障碍诊断的对话数据集，通过神经符号LLM智能体技术合成生成。该项目实现了一个完整的医患对话模拟系统，能够生成高质量的精神科诊断对话数据，为心理健康AI研究提供宝贵的数据资源。

### 🎯 主要特点

- **高质量对话生成**：基于真实患者病例，生成符合临床实际的诊断对话
- **多样化患者背景**：支持不同年龄、性别的患者模板和个人经历
- **专业医生角色扮演**：模拟具有不同专业特长和沟通风格的医生
- **动态诊断流程**：基于诊断树的动态话题选择和诊断决策
- **神经符号结合**：结合符号推理和神经网络生成的混合方法

## 🏗️ 项目架构

```
MDD-5k/
├── main.py                    # 主程序入口
├── doctor.py                  # 医生智能体实现
├── patient.py                 # 患者智能体实现
├── diagtree.py               # 诊断树和符号推理
├── patient_template_gen.py    # 患者模板生成工具
├── llm_tools_api.py          # LLM API工具
├── roleplay.py               # 角色扮演模块
├── raw_data/                 # 原始数据
│   └── pa20.json            # 真实患者案例
├── prompts/                  # 提示词模板
│   ├── doctor/              # 医生角色提示词
│   ├── patient/             # 患者角色提示词
│   └── diagtree/            # 诊断树配置
├── DataSyn/                  # 合成对话数据
├── evaluation/               # 评估工具和数据
└── requirements.txt          # 项目依赖
```

## 🛠️ 安装与配置

### 环境要求

- Python 3.8+
- OpenAI API密钥 或 本地部署的LLM服务

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-repo/MDD-5k.git
cd MDD-5k
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置LLM服务**

**选项1：使用OpenAI API**
- 在 `llm_tools_api.py` 的第37行输入您的OpenAI API密钥
- 推荐使用 `gpt-4o` 模型以获得最佳性能

**选项2：使用本地LLM服务**
- 使用vLLM等工具部署本地模型
- 在 `llm_tools_api.py` 的第44-45行配置服务器地址和密钥

## 🚀 使用方法

### 1. 数据预处理

首先运行患者模板生成脚本，获取MDD-5k数据集统计信息并生成虚构患者经历：

```bash
python patient_template_gen.py
```

此脚本将：
- 分析原始患者数据的统计特征
- 生成多样化的患者背景故事
- 创建患者模板用于后续对话生成

### 2. 生成诊断对话

运行主程序开始生成对话数据：

```bash
python main.py
```

程序将：
- 基于患者模板创建医生和患者智能体
- 进行多轮诊断对话模拟
- 保存生成的对话数据到 `DataSyn/` 目录

### 3. 配置参数

项目使用统一的配置文件 `config.py` 管理所有配置项：

```python
# API配置
class APIConfig:
    OPENAI_API_KEY = ""  # GPT-4 API Key，需要用户填入
    OPENAI_BASE_URL = "https://api.openai.com/v1"
    LOCAL_API_KEY = "EMPTY"  # 本地API Key
    LOCAL_BASE_URL = "http://localhost:9012/v1/"

# 模型配置
class ModelConfig:
    DEFAULT_MODEL_NAME = '/tcci_mnt/shihao/models/Qwen3-8B'
    GPT4_MODEL_NAME = 'gpt-4o'

# 文件路径配置
class PathConfig:
    PATIENT_INFO_PATH = './raw_data/pa20.json'
    DOCTOR_PROMPT_PATH = './prompts/doctor/doctor_persona.json'
    # ... 其他路径配置

# 系统配置
class SystemConfig:
    NUM_CONVERSATIONS = 5  # 每个患者生成的对话数量
    DEFAULT_TOP_P = 0.9
    DEFAULT_TEMPERATURE = 0.8
    DEFAULT_FREQUENCY_PENALTY = 0.8
```

您可以通过修改 `config.py` 文件来调整这些参数。

## 📊 数据结构

### 患者模板格式

```json
{
  "患者": 1,
  "年龄": 20,
  "性别": "女",
  "ICD编码": "F32.901",
  "诊断结果": "抑郁状态",
  "主诉": "情绪低落，兴趣减退，睡眠差 1年，加重 2月",
  "现病史": "...",
  "个人史": {
    "工作、学习情况": "高一学生",
    "婚恋情况": "未婚，目前单身",
    "病前性格": "外向、急躁"
  },
  "精神检查": {
    "意识": "意识清晰",
    "情感": "情绪低落,焦虑,恐惧",
    "思维": "思维迟缓,无望感,消极观念"
  }
}
```

### 生成的对话格式

```json
[
  {
    "conversation": [
      {
        "doctor": "你好，请问你最近感觉怎么样？",
        "patient": "我最近情绪很低落，总是高兴不起来..."
      },
      {
        "doctor": "这种情况持续多长时间了？",
        "patient": "大概有一年了，最近两个月更严重..."
      }
    ]
  }
]
```

## 🎭 智能体设计

### 医生智能体

医生智能体具有以下特点：
- **多样化人格**：不同年龄、性别、专业特长的医生角色
- **问诊风格**：快速/缓慢、共情/理性等不同沟通风格
- **动态诊断**：基于诊断树进行话题选择和诊断决策
- **专业知识**：具备精神科专业知识和诊断能力

### 患者智能体

患者智能体特征：
- **个性化背景**：基于真实病例和虚构经历
- **情感表达**：符合诊断结果的情感状态和行为表现
- **记忆一致性**：保持对话过程中信息的一致性
- **自然回应**：口语化、真实的患者回应

## 🌳 诊断树系统

诊断树是本项目的核心创新，实现了符号推理与神经生成的结合：

### 特点

1. **分层诊断**：按照临床诊断流程组织话题
2. **动态选择**：根据患者回应动态调整诊断路径
3. **话题解析**：自动解析患者经历中的相关话题
4. **诊断决策**：基于收集信息进行诊断判断

### 配置

诊断树按患者类型分为：
- `male_teen.json`：男性青少年
- `male_adult.json`：男性成年人
- `female_teen.json`：女性青少年
- `female_adult.json`：女性成年人

## 📈 评估与验证

### 评估指标

项目提供多种评估工具：

1. **对话质量评估**：一致性、连贯性、专业性
2. **诊断准确性**：与真实诊断结果的对比
3. **数据统计分析**：年龄、性别、诊断类型分布

### 运行评估

```bash
cd evaluation/
python statistics.py
```

## 📁 示例数据

### 真实患者案例
- `./raw_data/pa20.json`：包含一个真实患者案例

### 虚构患者经历
- `./prompts/background_story/patient_1`：基于真实案例生成的五个虚构患者经历

### 合成对话
- `./DataSyn/patient1.json`：完整的诊断对话示例

## 🔧 自定义与扩展

### 添加新的患者模板

1. 在 `raw_data/` 中添加新的患者数据
2. 运行 `patient_template_gen.py` 重新生成模板
3. 更新诊断树配置以支持新的诊断类型

### 自定义医生角色

1. 编辑 `prompts/doctor/doctor_persona.json`
2. 添加新的医生特征和问诊风格
3. 更新医生智能体的初始化逻辑

### 扩展诊断树

1. 修改 `prompts/diagtree/` 中的配置文件
2. 添加新的诊断节点和决策逻辑
3. 更新 `diagtree.py` 中的相关代码

## 💰 成本控制

项目包含完整的API调用成本追踪功能：
- 自动计算token使用量
- 实时显示成本信息
- 支持不同模型的成本计算

## ⚠️ 注意事项

1. **伦理考虑**：本项目涉及心理健康数据，请严格遵守相关伦理规范
2. **数据隐私**：确保患者数据的隐私保护和安全处理
3. **专业指导**：生成的对话仅用于研究目的，不可用于实际临床诊断
4. **模型局限性**：AI生成的对话可能存在偏差，需要专业医生审核

## 📚 引用

如果您在研究中使用了本项目，请引用以下论文：

```bibtex
@inproceedings{yin2025mdd5k,
  title={MDD-5k: A New Diagnostic Conversation Dataset for Mental Disorders Synthesized via Neuro-Symbolic LLM Agents},
  author={Yin, Congchi and others},
  booktitle={AAAI Conference on Artificial Intelligence},
  year={2025}
}
```

## 📄 许可证

本项目采用MIT许可证，详情请参见 [LICENSE](LICENSE) 文件。

## 🤝 贡献

欢迎社区贡献！请通过以下方式参与：

1. 提交Issue报告bug或建议新功能
2. 提交Pull Request改进代码
3. 完善文档和示例

## 📞 联系我们

如有问题或建议，请通过以下方式联系：

- 邮箱：[项目维护者邮箱]
- GitHub Issues：[项目GitHub地址]

## 🔗 相关资源

- [论文预印本]()
- [数据集下载]()（伦理审查完成后开放）
- [在线演示]()

---

**免责声明**：本项目仅用于学术研究目的，生成的诊断对话不能替代专业医疗建议。如有心理健康问题，请咨询专业医疗机构。
