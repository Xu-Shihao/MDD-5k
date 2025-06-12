"""
患者案例模板生成器
用于处理患者信息数据，生成患者背景故事模板
主要功能：
1. 从Excel文件读取患者信息并转换为JSON格式
2. 根据患者信息生成背景故事
3. 对患者案例进行统计分析
"""

import os
import pandas as pd
import json
import re
import llm_tools_api
import ast
from tqdm import tqdm
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 导入配置文件
from config import PathConfig, get_model_name, SystemConfig

# 并发处理配置类
class ConcurrencyConfig:
    """并发处理配置"""
    # API提取阶段的最大并发数
    MAX_API_EXTRACTION_WORKERS = 32
    # 背景故事生成阶段的最大并发数  
    MAX_STORY_GENERATION_WORKERS = 32
    # 单个患者API调用的最大并发数（个人史和精神检查并行）
    MAX_SINGLE_PATIENT_API_WORKERS = 5
    # 请求超时时间（秒）
    REQUEST_TIMEOUT = 60

# 取消设置代理相关的环境变量
proxy_vars = [
    'http_proxy',
    'https_proxy', 
    'HTTP_PROXY',
    'HTTPS_PROXY',
    'all_proxy'
]

for var in proxy_vars:
    # 使用pop方法安全地删除环境变量，如果不存在也不会报错
    removed_value = os.environ.pop(var, None)
    if removed_value is not None:
        print(f"已取消设置环境变量: {var} = {removed_value}")
    else:
        print(f"环境变量 {var} 不存在，跳过")
        
# 定义文件路径常量
PATIENT_CASES_ORIGIN_PATH = PathConfig.PATIENT_CASES_ORIGIN_PATH  # 原始患者信息Excel文件路径
PATIENT_CASES_JSON_PATH = PathConfig.PATIENT_CASES_JSON_PATH      # 转换后的JSON文件路径
PROMPT_PATH = PathConfig.PROMPTS_DIR                              # 提示词根目录路径
OUTPUT_PASTEXP_PATH = PathConfig.BACKGROUND_STORY_DIR             # 背景故事输出路径


class PatientCases():
    """
    患者案例处理类
    用于处理患者信息，生成背景故事模板
    """
    
    def __init__(self, xlsx_path, json_path, prompt_path, use_api):
        """
        初始化患者案例处理器
        
        Args:
            xlsx_path (str): Excel文件路径
            json_path (str): JSON文件路径
            prompt_path (str): 提示词根目录路径
            use_api (bool): 是否使用API进行处理
        """
        self.xlsx_path = xlsx_path
        self.json_path = json_path
        self.use_api = use_api
        self.prompt_path = prompt_path    # 提示词根目录路径
        self.gender_mode = None           # 性别模式
        self.age_mode = None              # 年龄模式

    def patient_cases_json(self):
        """
        将Excel格式的患者案例数据转换为JSON格式
        包含数据清洗、格式化和过滤功能
        """
        # 定义输出字段：患者ID、年龄、性别、ICD编码、诊断结果、主诉、现病史、躯体疾病史、家族史、个人史、精神检查、处理意见
        output_list = []
        num = 0  # 患者编号计数器
        
        # 读取Excel文件
        file = pd.read_excel(self.xlsx_path, sheet_name='Sheet1').iloc[0:10,:]
        
        # 预处理数据，收集需要API处理的患者信息
        patients_for_api = []
        patients_basic_info = []
        
        # 逐行处理患者数据
        for index, row in file.iterrows():
            # 过滤掉关键字段为空的记录
            if (not pd.isna(row['Diagnosis'])) and (not pd.isna(row['ChiefComplaint'])) and (not pd.isna(row['PresentIllnessHistory'])) and (not pd.isna(row['TreatmentRecommendation'])):
                num += 1
                output_dict = {}
                
                # 基本信息提取
                output_dict['患者'] = num
                output_dict['年龄'] = int(row['Age'])
                output_dict['性别'] = row['Gender']
                
                # 清理ICD编码末尾的逗号
                output_dict['ICD编码'] = row['DiagnosisCode'] if str(row['DiagnosisCode'])[-1] != ',' else str(row['DiagnosisCode'])[:-1]
                # 清理诊断结果末尾的逗号
                output_dict['诊断结果'] = row['Diagnosis'] if str(row['Diagnosis'])[-1] != ',' else str(row['Diagnosis'])[:-1]
                
                # 使用正则表达式提取主诉信息
                output_dict['主诉'] = '无' if re.findall(r"主诉：(.+)", str(row['ChiefComplaint'])) == [" "] else re.findall(r"主诉：(.+)", str(row['ChiefComplaint']))[-1]
                # 使用正则表达式提取现病史信息
                output_dict['现病史'] = '无' if re.findall(r"现病史：(.+)", str(row['PresentIllnessHistory'])) == [" "] else re.findall(r"现病史：(.+)", str(row['PresentIllnessHistory']))[-1]
                
                # 处理躯体疾病史，如果为空则标记为"无"
                output_dict['重要或相关躯体疾病史'] = '无' if pd.isna(row['ImportantRelevantPhysicalIllnessHistory']) else row['ImportantRelevantPhysicalIllnessHistory']
                # 处理家族史，如果为空则标记为"无"
                output_dict['家族史'] = '无' if pd.isna(row['FamilyHistory']) else row['FamilyHistory']
                
                # 使用正则表达式提取个人史和精神检查信息
                output_dict['个人史'] = '无' if re.findall(r"个人史:(.+)", str(row['PersonalHistory'])) == [" "] else re.findall(r"个人史:(.+)", str(row['PersonalHistory']))[-1]
                output_dict['精神检查'] = '无' if re.findall(r"精神检查描述：(.+)", str(row['PsychiatricExamination'])) == [" "] else re.findall(r"精神检查描述：(.+)", str(row['PsychiatricExamination']))[-1]
                output_dict['处理意见'] = '无' if re.findall(r"处理意见：(.+)", str(row['TreatmentRecommendation'])) == [" "] else re.findall(r"处理意见：(.+)", str(row['TreatmentRecommendation']))[-1]

                # 进一步清理家族史数据
                output_dict['家族史'] = '无' if output_dict['家族史'] == '家族史：阴性。 ' or output_dict['家族史'] == '家族史：阴性 ' or "缺失" in output_dict['家族史'] else output_dict['家族史']
                output_dict['家族史'] = re.findall(r"家族史：(.+)", str(output_dict['家族史']))[-1] if output_dict['家族史'] != '无' else output_dict['家族史']
                
                # 进一步清理躯体疾病史数据
                if re.findall(r"重要或相关躯体疾病史：(.+)", str(output_dict['重要或相关躯体疾病史'])) == []:
                    output_dict['重要或相关躯体疾病史'] = '无'
                elif re.findall(r"重要或相关躯体疾病史：(.+)", str(output_dict['重要或相关躯体疾病史']))[-1][0] == '无':
                    output_dict['重要或相关躯体疾病史'] = '无'
                else:
                    output_dict['重要或相关躯体疾病史'] = re.findall(r"重要或相关躯体疾病史：(.+)", str(output_dict['重要或相关躯体疾病史']))[-1]

                # 数据质量过滤：确保关键字段不为"无"
                filter_flag = False
                for key in output_dict.keys():
                    if key in ['主诉', '处理意见', '精神检查', '个人史']:
                        if output_dict[key] == '无':
                            filter_flag = True
                            break
                            
                # 如果通过过滤，收集需要API处理的数据
                if not filter_flag:
                    patients_basic_info.append(output_dict.copy())
                    if self.use_api:
                        patients_for_api.append({
                            'index': len(patients_basic_info) - 1,
                            'personal_history': output_dict['个人史'],
                            'mental_exam': output_dict['精神检查']
                        })
        
        # 并行处理API调用
        if self.use_api and patients_for_api:
            print(f"开始并行处理 {len(patients_for_api)} 个患者的API请求...")
            
            def process_single_patient_api(patient_api_data):
                """处理单个患者的API请求"""
                try:
                    index = patient_api_data['index']
                    personal_history = patient_api_data['personal_history']
                    mental_exam = patient_api_data['mental_exam']
                    
                    # 并行调用API提取个人史和精神检查的详细信息
                    with ThreadPoolExecutor(max_workers=ConcurrencyConfig.MAX_SINGLE_PATIENT_API_WORKERS) as executor:
                        future_personal = executor.submit(llm_tools_api.api_load_for_extraction, get_model_name(), personal_history)
                        future_mental = executor.submit(llm_tools_api.api_load_for_extraction, get_model_name(), mental_exam)
                        
                        # 设置超时并获取结果
                        detail_personal = future_personal.result(timeout=ConcurrencyConfig.REQUEST_TIMEOUT)
                        detail_mental = future_mental.result(timeout=ConcurrencyConfig.REQUEST_TIMEOUT)
                    
                    detail_personal = ast.literal_eval(detail_personal)
                    detail_mental = ast.literal_eval(detail_mental)
                    
                    return {
                        'index': index,
                        'personal_history': detail_personal,
                        'mental_exam': detail_mental
                    }
                except Exception as e:
                    print(f"处理患者 {index} 时出错: {e}")
                    return {
                        'index': patient_api_data['index'],
                        'personal_history': patient_api_data['personal_history'],
                        'mental_exam': patient_api_data['mental_exam']
                    }
            
            # 使用线程池并行处理所有患者的API请求
            with ThreadPoolExecutor(max_workers=min(ConcurrencyConfig.MAX_API_EXTRACTION_WORKERS, len(patients_for_api))) as executor:
                future_to_patient = {executor.submit(process_single_patient_api, patient_data): patient_data for patient_data in patients_for_api}
                
                api_results = {}
                for future in tqdm(as_completed(future_to_patient), total=len(patients_for_api), desc="API处理进度"):
                    result = future.result()
                    api_results[result['index']] = result
            
            # 将API结果合并到基本信息中
            for i, basic_info in enumerate(patients_basic_info):
                if i in api_results:
                    basic_info['个人史'] = api_results[i]['personal_history']
                    basic_info['精神检查'] = api_results[i]['mental_exam']
                output_list.append(basic_info)
        else:
            # 不使用API时的处理
            for basic_info in patients_basic_info:
                if not self.use_api:
                    # TODO: 本地模型处理逻辑待实现
                    detail_mental = llm_tools_api.load_Qwen_for_extraction(basic_info['精神检查'])
                output_list.append(basic_info)
                    
        # 将处理后的数据保存为JSON文件
        with open(self.json_path, 'w') as f:
            json.dump(output_list, f, indent=2, ensure_ascii=False)


    def key_word_selelction1(self):
        """
        关键词选择方法1（多模式合并）
        合并不同年龄模式的关键词数据
        
        Returns:
            dict: 合并后的关键词字典
        """
        paths = []
        json_data = []
        
        # 读取不同年龄模式的数据文件
        for mode in self.age_mode:
            path = self.gender_mode + '_' + mode + '.json'
            paths.append(path)
            with open(os.path.join(self.prompt_path, 'patient', path)) as f:
                data = json.load(f)
                json_data.append(data)
                
        # 合并不同模式的关键词数据
        dict_for_gen = {}
        for key in json_data[0].keys():
            if isinstance(json_data[0][key], dict):
                # 处理嵌套字典类型的数据
                temp = {}
                for key1 in json_data[0][key].keys():                 
                    tmp = []
                    for data in json_data:
                        tmp.extend(data[key][key1])
                    temp[key1] = list(set(tmp))  # 去重
                dict_for_gen[key] = temp
            else:
                # 处理列表类型的数据
                tmp = []
                for data in json_data:
                    tmp.extend(data[key])
                tmp = list(set(tmp))  # 去重
                dict_for_gen[key] = tmp
        return dict_for_gen
        

    def key_word_selelction(self):
        """
        关键词选择方法（单模式）
        根据性别和年龄模式选择对应的关键词数据
        
        Returns:
            dict or None: 关键词数据字典，如果年龄模式未设置则返回None
        """
        if self.age_mode is not None:
            path = self.gender_mode + '_' + self.age_mode + '.json'
            with open(os.path.join(self.prompt_path, 'patient', path)) as f:
                data = json.load(f)
            return data
        else:
            return None

    def story_gen_for_background(self, patient):
        """
        为患者生成背景故事
        
        Args:
            patient (dict): 患者信息字典
            
        Returns:
            str: 生成的背景故事文本
        """
        dict_for_gen = self.key_word_selelction()
        if dict_for_gen is not None:
            first = False
            chosen_key = None
            
            # 随机选择关键词生成故事元素
            for key in dict_for_gen.keys():
                if isinstance(dict_for_gen[key], dict) and first == False:
                    # 根据权重随机选择子类别
                    chosen_key = random.choices([x for x in dict_for_gen[key].keys()], [len(dict_for_gen[key][x]) for x in dict_for_gen[key].keys()])[0]
                    value1 = random.choice(dict_for_gen[key][chosen_key])
                    dict_for_gen[key] = value1
                    first = True
                elif isinstance(dict_for_gen[key], list):
                    # 随机选择列表中的元素
                    dict_for_gen[key] = random.choice(dict_for_gen[key])
                else:
                    # 使用已选择的子类别
                    dict_for_gen[key] = random.choice(dict_for_gen[key][chosen_key])
                    
            print(dict_for_gen)
            
            # 读取背景故事模板
            with open(os.path.join(self.prompt_path, 'patient', 'patient_background.txt')) as f:
                text_prompt = f.readlines()[0]
                
            # 使用患者信息和生成的关键词填充模板
            text_prompt = text_prompt.format(age=patient['年龄'],gender=patient['性别'],diagnosis=patient['诊断结果'],illness=patient['现病史'],work=patient['个人史']['工作、学习情况'],
                                            time=dict_for_gen['time'],poeple=dict_for_gen['people'],experience=dict_for_gen['experience'])
            
            # 调用API生成背景故事
            response = llm_tools_api.api_load_for_background_gen(get_model_name(), text_prompt)
            return response
        else:
            return ''

    def save_background_story(self, patient, output_path):
        """
        保存患者背景故事到文件
        
        Args:
            patient (dict): 患者信息字典
            output_path (str): 输出文件路径
        """
        age = patient['年龄']
        gender = patient['性别']
        
        # 设置性别模式
        if gender == "男":
            self.gender_mode = 'male'
        else:
            self.gender_mode = 'female'
            
        # 设置年龄模式（50岁以下使用具体年龄，50岁以上不设置年龄模式）
        if int(age) <= 50:
            self.age_mode = str(age)
        else:
            self.age_mode = None
            
        # 生成背景故事
        story = self.story_gen_for_background(patient)
        story = story.replace("\n", "")  # 移除换行符
        
        # 保存故事到文件
        with open(output_path, 'w') as f:
            f.write(story)
    
    def generate_background_story_parallel(self, patient_template, story_index, output_dir):
        """
        为单个患者生成单个背景故事（用于并行处理）
        
        Args:
            patient_template (dict): 患者模板信息
            story_index (int): 故事编号
            output_dir (str): 输出目录
            
        Returns:
            str: 成功信息或错误信息
        """
        try:
            # 创建患者专属目录（如果不存在）
            patient_dir = os.path.join(output_dir, f'patient_{patient_template["患者"]}')
            if not os.path.exists(patient_dir):
                os.makedirs(patient_dir, exist_ok=True)
            
            # 定义输出文件路径
            output_path = os.path.join(patient_dir, f'story_{story_index}.txt')
            
            # 生成并保存背景故事
            self.save_background_story(patient_template, output_path)
            
            return f"成功生成患者 {patient_template['患者']} 的故事 {story_index}"
        except Exception as e:
            return f"生成患者 {patient_template['患者']} 的故事 {story_index} 时出错: {e}"

    def statistics(self):
        """
        对患者案例进行统计分析
        统计内容包括：总数、性别分布、年龄分布、ICD编码分布、家族史和个人史情况
        """
        # 读取患者数据
        with open(self.json_path, 'r') as f:
            patient_data = json.load(f)
            
        total_num = len(patient_data)
        gender = [0, 0]    # 性别统计：[男, 女]
        age = [0, 0, 0, 0, 0, 0, 0, 0]    # 年龄段统计：[10,20,30,40,50,60,70,80]
        icd_code = {}      # ICD编码统计
        family = [0, 0]    # 家族史统计：[无家族史, 有家族史]
        personal = [0, 0]  # 个人疾病史统计：[无疾病史, 有疾病史]
        
        # 遍历所有患者案例进行统计
        for case in patient_data:
            # 性别统计
            if case['性别'] == '男':
                gender[0] += 1
            else:
                gender[1] += 1
                
            # 年龄统计（按十年为单位）
            if case['年龄'] == 10:
                age[0] += 1
            elif case['年龄'] == 20:
                age[1] += 1
            elif case['年龄'] == 30:
                age[2] += 1
            elif case['年龄'] == 40:
                age[3] += 1
            elif case['年龄'] == 50:
                age[4] += 1
            elif case['年龄'] == 60:
                age[5] += 1
            elif case['年龄'] == 70:
                age[6] += 1
            elif case['年龄'] == 80:
                age[7] += 1
                
            # 家族史统计
            if case['家族史'] == '无':
                family[0] += 1
            else:
                family[1] += 1
                
            # 个人疾病史统计
            if case['重要或相关躯体疾病史'] == '无':
                personal[0] += 1
            else:
                personal[1] += 1
                
            # ICD编码统计
            icd = case['ICD编码']
            icd = icd.split(',')  # 分割多个ICD编码
            for i in icd:
                if i in icd_code.keys():
                    icd_code[i] += 1
                else:
                    icd_code[i] = 1
                    
        # 数据一致性检查
        assert gender[0]+gender[1] == total_num == family[0]+family[1] == personal[0]+personal[1] == sum(age)
        print(age, gender, icd_code, family, personal)            

# 主程序执行部分
# 创建患者案例处理器实例
patient = PatientCases(PATIENT_CASES_ORIGIN_PATH, PATIENT_CASES_JSON_PATH, PROMPT_PATH, use_api=True)

# 生成患者案例JSON文件
if not os.path.exists(PATIENT_CASES_JSON_PATH):
    patient.patient_cases_json()

# 输出患者案例的统计信息
patient.statistics()

# 设置每个患者案例生成的对话数量
NUM = SystemConfig.NUM_CONVERSATIONS    # 1个患者案例将用于生成5个对话

# 读取患者信息JSON文件
with open(PATIENT_CASES_JSON_PATH, 'r') as f:
    patient_info = json.load(f)

# 为每个患者模板生成背景经历故事（并行处理）
print(f"开始并行生成 {len(patient_info)} 个患者的背景故事，每个患者生成 {NUM} 个故事...")

# 创建所有需要处理的任务列表
tasks = []
for patient_template in patient_info:
    for i in range(NUM):
        tasks.append({
            'patient_template': patient_template,
            'story_index': i + 1,
            'output_dir': OUTPUT_PASTEXP_PATH
        })

print(f"总共需要生成 {len(tasks)} 个背景故事")

# 使用线程池并行生成背景故事
max_workers = min(ConcurrencyConfig.MAX_STORY_GENERATION_WORKERS, len(tasks))  # 限制最大并发数，避免过度并发
print(f"使用 {max_workers} 个并发线程进行处理...")

def process_story_task(task):
    """处理单个故事生成任务"""
    return patient.generate_background_story_parallel(
        task['patient_template'], 
        task['story_index'], 
        task['output_dir']
    )

with ThreadPoolExecutor(max_workers=max_workers) as executor:
    # 提交所有任务
    future_to_task = {executor.submit(process_story_task, task): task for task in tasks}
    
    # 收集结果并显示进度
    success_count = 0
    error_count = 0
    
    for future in tqdm(as_completed(future_to_task), total=len(tasks), desc="背景故事生成进度"):
        result = future.result()
        if "成功生成" in result:
            success_count += 1
        else:
            error_count += 1
            print(f"错误: {result}")

print(f"\n背景故事生成完成!")
print(f"成功生成: {success_count} 个故事")
print(f"生成失败: {error_count} 个故事")
