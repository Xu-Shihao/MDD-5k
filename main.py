from doctor import Doctor
from patient import Patient
from diagtree import DiagTree
import json
import os
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from config import (
    get_model_name, get_patient_info_path, get_doctor_prompt_path,
    get_diagtree_path, get_output_dir, get_background_story_dir,
    SystemConfig
)

DOCTOR_PROMPT_PATH = get_doctor_prompt_path()
PATIENT_INFO_PATH = get_patient_info_path()
DIAGTREE_PATH = get_diagtree_path()
MODEL_NAME = get_model_name()
NUM = SystemConfig.NUM_CONVERSATIONS
OUTPUT_DATASYN_PATH = get_output_dir()
OUTPUT_PASTEXP_PATH = get_background_story_dir()

# 用于线程安全的成本累计
cost_lock = threading.Lock()
total_cost = 0

def process_single_patient(patient_template):
    """处理单个患者的对话生成"""
    global total_cost
    
    patient_total_cost = 0
    total_output_list = []
    
    for i in range(NUM):
        dialogue_history = []
        output_list = []
        output_dict = {}
        story_path = os.path.join(OUTPUT_PASTEXP_PATH, 'patient_{}'.format(patient_template['患者']), 'story_{}.txt'.format(i+1))

        doc = Doctor(patient_template, DOCTOR_PROMPT_PATH, DIAGTREE_PATH, MODEL_NAME, True)
        pat = Patient(patient_template, MODEL_NAME, True, story_path)

        doctor_response = doc.doctor_response_gen(None, None)
        output_dict['doctor'] = doctor_response
        dialogue_history.append('医生：' + doctor_response)
        print(f"患者{patient_template['患者']} 对话{i+1} - 医生：{doctor_response}")
        current_topic = '患者的精神状况'
        
        while True:
            patient_response, patient_cost = pat.patient_response_gen(current_topic, dialogue_history)
            output_dict['patient'] = patient_response
            dialogue_history.append('患者：' + patient_response)
            output_list.append(output_dict)
            output_dict = {}
            print(f"患者{patient_template['患者']} 对话{i+1} - 患者：{patient_response}")
            doctor_response, current_topic, doctor_cost = doc.doctor_response_gen(patient_response, dialogue_history)
            
            patient_total_cost += doctor_cost + patient_cost
            
            if '诊断结束，你的诊断结果' in doctor_response:
                output_dict = {'doctor': doctor_response}
                output_list.append(output_dict)
                print(f"患者{patient_template['患者']} 对话{i+1} - 医生：{doctor_response}")
                break
            else:
                dialogue_history.append('医生：' + doctor_response)
                output_dict['doctor'] = doctor_response
                print(f"患者{patient_template['患者']} 对话{i+1} - 医生：{doctor_response}")
        
        total_output_list.append({"conversation": output_list})

    # 保存单个患者的对话数据
    output_file_path = os.path.join(OUTPUT_DATASYN_PATH, 'patient_{}.json'.format(patient_template['患者']))
    with open(output_file_path, 'w') as f:
        json.dump(total_output_list, f, indent=2, ensure_ascii=False)
    
    # 线程安全地累计总成本
    with cost_lock:
        total_cost += patient_total_cost
    
    return patient_template['患者'], patient_total_cost

def main():
    global total_cost
    
    with open(PATIENT_INFO_PATH, 'r') as f:
        patient_info = json.load(f)
    
    # 设置并行处理的最大工作线程数，可以根据需要调整
    max_workers = min(len(patient_info), os.cpu_count() or 1)
    
    print(f"开始并行处理 {len(patient_info)} 个患者，使用 {max_workers} 个线程")
    
    # 使用ThreadPoolExecutor并行处理患者
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_patient = {executor.submit(process_single_patient, patient_template): patient_template 
                           for patient_template in patient_info}
        
        # 使用tqdm显示进度
        for future in tqdm(as_completed(future_to_patient), total=len(patient_info), desc="处理患者进度"):
            patient_template = future_to_patient[future]
            try:
                patient_id, patient_cost = future.result()
                print(f"患者 {patient_id} 处理完成，花费: {patient_cost}")
            except Exception as exc:
                print(f"患者 {patient_template['患者']} 处理时发生异常: {exc}")
    
    print("********总价格*********:", total_cost)

if __name__ == "__main__":
    main()