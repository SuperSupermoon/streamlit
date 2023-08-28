import streamlit as st
import os
import pandas as pd
import json
import copy
from collections import defaultdict
import nltk
nltk.download('punkt')
from nltk.tokenize import sent_tokenize
import re

json_folder_path = './test/'
json_files = [os.path.join(root, file) for root, _, files in os.walk(json_folder_path) for file in files if file.endswith('.json')]

st.set_page_config(layout="wide")

def recursive_defaultdict():
    return defaultdict(recursive_defaultdict)

def defaultdict_to_dict(d):
    if isinstance(d, defaultdict):
        d = {k: defaultdict_to_dict(v) for k, v in d.items()}
    return d

def remove_quotes_with_re(text):
    return re.sub(r'^["\']|["\']$|^["\'],|["\'],$','', text)

def save_feedback(patient_id, display_names, feedback_data, correct_rows, feedback_columns=['include', 'delete', 'modify', 'opinion']):
    original_name = display_names.split('_')[-1]
    original_json = load_json(f"./test/{patient_id}/{original_name}.json")
    new_json = copy.deepcopy(original_json)
    
    annotations_list = json.loads(original_json['annotations'])
    
    for sec, sec_data in feedback_data.items():
        for idx_str, feedback in sec_data.items():
            idx = int(idx_str)
            
            existing_annotation = next((annotation for annotation in annotations_list if annotation['sec'] == sec and annotation['sent_idx'] == idx+1), None)

            if existing_annotation:
                modified_annotation = copy.deepcopy(existing_annotation)

                # Single-key items (e.g., 'cat', 'norm_ent')
                single_keys = set(value.split(':')[0].strip(" '") for value in feedback.values() if len(value.split(':')) == 2)

                # Triple-key items (e.g., 'tmp: nchg: stable')
                triple_keys = set(value.split(':')[1].strip(" '") for value in feedback.values() if len(value.split(':')) == 3)

                # print("Single keys:", single_keys)
                # print("Triple keys:", triple_keys)
                # updated_first_value = False  # 플래그를 먼저 False로 설정

                # print("feedback", feedback)

                for key, value in feedback.items():
                    prefix = key.split('_')[0]
                    
                    if prefix in feedback_columns:
                        if prefix == 'opinion':
                            modified_annotation['opinion'] = value
                        else:
                            key_value_pair = value.split(": ")
                            if len(key_value_pair) == 1:
                                print(f"Invalid feedback. Expected key-value pair for prefix {prefix}, got {key_value_pair}")
                                st.error(f"Invalid feedback. Expected key-value pair for prefix {prefix}, got {key_value_pair}", icon="🚨")
                            
                            if len(key_value_pair) == 2:
                                k, v = key_value_pair
                                k = remove_quotes_with_re(k)
                                v = remove_quotes_with_re(v)

                                if prefix == 'include':
                                    if k in modified_annotation:
                                        if isinstance(modified_annotation[k], list):
                                            modified_annotation[k].append(v)
                                        else:
                                            modified_annotation[k] = [modified_annotation[k], v]
                                    else:
                                        modified_annotation[k] = v
                                elif prefix == 'modify':
                                    if k in modified_annotation:
                                        modified_annotation[k] = v
                                elif prefix == 'delete':
                                    if k in modified_annotation and modified_annotation[k] == v:
                                        del modified_annotation[k]
                                        
                            if len(key_value_pair) == 3:
                                k1, k2, v = key_value_pair
                                if k1 in modified_annotation:
                                    if isinstance(modified_annotation[k1], dict):
                                        modified_annotation[k1][k2] = v
                                    else:
                                        # 이 경우 modified_annotation[k1]가 dict가 아니라고 가정하고 새 dict를 생성합니다.
                                        modified_annotation[k1] = {k2: v}
                                else:
                                    modified_annotation[k1] = {k2: v}

                                    
                annotations_list.remove(existing_annotation)
                annotations_list.append(modified_annotation)
                
    new_json['annotations'] = annotations_list#json.dumps(annotations_list, indent=4)

    
    # print("new_json", new_json)

    # Create directories if they don't exist
    reviewer_name = st.session_state.reviewer_name
    os.makedirs(f"./feedback/{reviewer_name}/{patient_id}", exist_ok=True)
    
    # Save the new JSON
    with open(f"./feedback/{reviewer_name}/{patient_id}/{display_names}.json", "w") as f:
        json.dump(new_json, f, indent=4)


def load_feedback(patient_id, display_names):
    if os.path.exists(f"./feedback/{st.session_state.reviewer_name}/{patient_id}/{display_names}.json"):
        feedback_data = load_json(f"./feedback/{st.session_state.reviewer_name}/{patient_id}/{display_names}.json")
        return feedback_data
    

def load_json(filepath):
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data

# Simplified sentence tokenizer
def custom_sent_tokenize(text):
    sentences = text.split('. ')
    sentences = [s + '.' if s != sentences[-1] else s for s in sentences]

    return sentences

# Helper function to tokenize sentences from annotations
def tokenize_annotations(annotations):
    tokenized_annotations = []
    for sent in annotations:
        tokenized_annotations.extend(sent_tokenize(sent))
    return tokenized_annotations


def get_statistics(data, dfs):
    present_sections = {key: True for key, value in data.items() if value and key in ["History", "Findings", "Impression"]}
    sent_stats, cat_stats, missing_sents = {}, {}, {}
    norm_ent_stats = defaultdict(recursive_defaultdict)  # Updated

    for sec, df in dfs.items():       
        if sec == 'HIST':
            section_texts = data.get('History', "")
        elif sec == 'FIND':
            section_texts = data.get('Findings', "")
        else:
            section_texts = data.get('Impression', "")
            
        section_sents = custom_sent_tokenize(section_texts)
        
        if 'sent' in df.columns:
            sent_counts = df['sent'].value_counts().to_dict()
            sent_stats[sec] = sent_counts
            
            sents_from_annos = list(set(df['sent']))
            sents_from_annos_tokenized = tokenize_annotations(sents_from_annos)
            
            missing_sents_for_section = [sent for sent in section_sents if sent not in sents_from_annos_tokenized]
            if missing_sents_for_section:
                missing_sents[sec] = missing_sents_for_section    
    
        if 'cat' in df.columns:
            cat_counts = df['cat'].value_counts().to_dict()
            cat_stats[sec] = cat_counts
            
            # if 'ROF-PATH' in cat_counts.keys():
            #     if 'norm_ent' in df.columns:
            #         norm_ent_counts = df[df['cat'] == 'ROF-PATH']['norm_ent'].value_counts().to_dict()
            if 'cat' in df.columns and 'norm_ent' in df.columns:
                for _, row in df.iterrows():
                    cat = row['cat']
                    norm_ent = row['norm_ent']
                    if not isinstance(norm_ent_stats[sec][cat][norm_ent], int):  # Check if the existing value is an int
                        norm_ent_stats[sec][cat][norm_ent] = 0  # If not, initialize it to 0
                    norm_ent_stats[sec][cat][norm_ent] += 1  # Increment
    
    return present_sections, sent_stats, cat_stats, dict(norm_ent_stats), missing_sents  # Assuming you want to return these


def display_data(data):
    sections = {
        "HIST": data.get("History", ""),
        "FIND": data.get("Findings", ""),
        "IMPR": data.get("Impression", "")
    }
    
    annotations = data.get('annotations', [])    
    annotations_list = json.loads(annotations.replace('\n', '').replace('    ', ''))
    
    desired_order = ['ent', 'cat', 'exist', 'rel', 'attr', 'sent']
    reordered_annotations = []

    for annotation in annotations_list:
        reordered_dict = {k: annotation[k] for k in desired_order if k in annotation}
        reordered_annotations.append(reordered_dict)

    # print("reordered_annotations", reordered_annotations)

    # annotations가 문자열 형태라면 JSON 객체로 변환
    if isinstance(annotations, str):
        try:
            annotations = json.loads(annotations)
        except json.JSONDecodeError:
            st.error(f"Failed to parse annotations in file: {selected_file}")
            annotations = []

    dfs = {}
    for sec in sections.keys():
        filtered_annotations = [item for item in annotations if item['sec'] == sec]
        
        if not filtered_annotations:
            dfs[sec] = pd.DataFrame()
            continue
        
        df_sec = pd.DataFrame(filtered_annotations)
        
        # 세부 구조화 부분
        df_sec[['ori_ent', 'norm_ent']] = df_sec['ent'].str.split('|', expand=True)
        attr_df = df_sec['attr'].apply(pd.Series)
        df_sec['loc'] = df_sec['rel'].apply(lambda x: x.get('loc') if isinstance(x, dict) else None)
        df_sec['asso'] = df_sec['rel'].apply(lambda x: x.get('asso') if isinstance(x, dict) else None)
        df_sec = df_sec.drop(columns=['ent', 'attr', 'rel']).join(attr_df)
        
        dfs[sec] = df_sec

    return sections, dfs, reordered_annotations


# if 'reviewer_name' not in st.session_state or not st.session_state.reviewer_name:
#     st.session_state.reviewer_name = st.text_input("Please enter your name for feedback:")

# Check if 'reviewer_name' is already in the session state
if 'reviewer_name' not in st.session_state:
    st.session_state.reviewer_name = ''

# If reviewer_name is empty, prompt the user to enter their name
if not st.session_state.reviewer_name:
    st.session_state.reviewer_name = st.text_input("Please enter your name for feedback:")

# If reviewer_name is set, display the rest of the app
if st.session_state.reviewer_name:
    st.title(f'GPT4 Results - Reviewer: {st.session_state.reviewer_name}')

    # Categorize files by patient ID
    file_structure = defaultdict(list)
    for file in json_files:
        patient_id = os.path.basename(os.path.dirname(file))
        file_structure[patient_id].append(file)

    selected_patient = st.sidebar.selectbox('Select a patient ID:', list(file_structure.keys()))

    # 파일 이름과 sequence 정보를 함께 보여주기 위한 변환
    sequence_filenames = []
    for f in file_structure[selected_patient]:
        data = load_json(f)
        sequence = data.get("sequence", "")
        filename = os.path.basename(f).replace('.json', '')
        display_name = f"{sequence}_{filename}"
        sequence_filenames.append((sequence, display_name))

    # sequence 값에 따라 정렬
    sequence_filenames.sort(key=lambda x: int(x[0]))

    # Display names만 선택하기 위해 분리
    display_names = [name[1] for name in sequence_filenames]

    selected_display_name = st.sidebar.selectbox('Select a JSON file:', display_names)

    selected_file = next(f for f in file_structure[selected_patient] if os.path.basename(f).replace('.json', '') in selected_display_name)

    # Initialize session_state if it doesn't exist
    if 'last_selected_file' not in st.session_state:
        st.session_state.last_selected_file = None

    if 'additional_feedback_count' not in st.session_state:
        st.session_state.additional_feedback_count = {}

    if 'checkbox_states' not in st.session_state:
        st.session_state.checkbox_states = {}

    # Check if selected_file has changed
    if st.session_state.last_selected_file != selected_file:
        # Reset the previous_feedback and additional_feedback_count
        
        previous_feedback = load_feedback(selected_patient, selected_display_name)
        st.session_state.additional_feedback_count = {}
        st.session_state.checkbox_states = {}
    else:
        # 이전에 저장한 피드백이 있다면 불러옴
        previous_feedback = load_feedback(selected_patient, selected_display_name)
        # print("previous_feedback", previous_feedback)

    # Update last_selected_file in session_state
    st.session_state.last_selected_file = selected_file

    # Load and display selected JSON data
    data = load_json(selected_file)
    sections, dfs, annotations_list = display_data(data)

    # Get statistics    
    present_sections, sent_stats, cat_stats, norm_ent_stats, missing_sents = get_statistics(data, dfs)

    # 파일 통계 섹션 시작
    with st.expander(f"**Show File Statistics: {len(missing_sents)} Missing Sents**"):
        #1. 'CAT'의 value 통계 출력
        st.write("CAT stats:")
        section_to_cat_and_norm_ent = defaultdict(list)
        
        for (section, cat_dict), (_, norm_ent_dict) in zip(cat_stats.items(), norm_ent_stats.items()):
            for cat, count in cat_dict.items():
                filtered_norm_ent = {k: v for k, v in norm_ent_dict.items() if k in norm_ent_dict}
                section_to_cat_and_norm_ent[section].append((cat, count, filtered_norm_ent))

        # Convert defaultdict to dict for better display
        norm_ent_stats = defaultdict_to_dict(norm_ent_stats)
        
        for section, cat_norm_ent_dict in norm_ent_stats.items():
            for cat, norm_ent_dict in cat_norm_ent_dict.items():
                st.write(f"  - {section} ({cat}): {dict(norm_ent_dict)}")
    
        # Display missing sentences
        st.write(f"{len(missing_sents)} Missing Sents")
        for sec, sents in missing_sents.items():
            st.write(f"  - {sec}: {', '.join(sents)}")
    

    feedback_data = {}
    correct_rows = {}
    # additional_feedback_count = {}  # Commented this out
    feedback_columns = ['include', 'delete', 'modify', 'opinion']

    for sec, content in sections.items():
        st.write(f"**{sec}:** {content}")

        current_df = dfs[sec]
        columns_to_drop = ["sec", "sent_idx"]
        columns_to_drop = [col for col in columns_to_drop if col in current_df.columns]
        if columns_to_drop:
            filtered_df = current_df.drop(columns=columns_to_drop)

            with st.expander(f"**{sec} DataFrame**"):
                st.write(filtered_df)

            feedback_data[sec] = {}
            correct_rows[sec] = {}
            # additional_feedback_count[sec] = {}  # Commented this out

            if previous_feedback:
                st.write("Previous Results:")
                annotations_list = previous_feedback.get('annotations', [])
                desired_order = ['ent', 'cat', 'exist', 'rel', 'attr', 'sent']
                reordered_annotations = []

                sec_list = [annotation for annotation in annotations_list if annotation['sec'] == sec]
                
                for annotation in sec_list:
                    reordered_dict = {k: annotation[k] for k in desired_order if k in annotation}
                    reordered_annotations.append(reordered_dict)
                
                for annotation in reordered_annotations:
                    st.write(f"  - {annotation}")

            with st.expander(f"**Review {sec}**"):
                for index, row in current_df.iterrows():
                    st.write(f"  - {sec} Row {index}: {annotations_list[index]}")
                    feedback_data[sec][index] = {}
                    correct_rows[sec][index] = {}

                    # Initialize session_state for the section and index
                    if sec not in st.session_state.additional_feedback_count:
                        st.session_state.additional_feedback_count[sec] = {}
                    st.session_state.additional_feedback_count[sec].setdefault(index, {col: 1 for col in feedback_columns})

                    col_list = st.columns(len(feedback_columns) + 1)
                    correct_key = f"{sec}_correct_{index}"
                    overall_correct = col_list[0].checkbox(f"Correct all", 
                                                            value=st.session_state.checkbox_states.get(correct_key, False),  # 상태 가져오기
                                                            key=correct_key
                                                        )
                    st.session_state.checkbox_states[correct_key] = overall_correct


                    if overall_correct:
                        correct_rows[sec][index]['overall'] = True
                    else:
                        correct_rows[sec][index]['overall'] = False

                        for col_num, col_name in enumerate(feedback_columns):
                            nested_col_list = col_list[col_num + 1].columns(2)
                            correct_key = f"{sec}_correct_{index}_{col_name}"
                            correct = nested_col_list[0].checkbox(f"{col_name}", key=correct_key)

                            if correct:
                                correct_rows[sec][index][col_name] = True
                            else:
                                if nested_col_list[1].button(f"Add", key=f"{sec}_add_more_{index}_{col_name}"):
                                    st.session_state.additional_feedback_count[sec][index][col_name] += 1

                                if nested_col_list[1].button(f"Remove", key=f"{sec}_remove_{index}_{col_name}"):
                                    if st.session_state.additional_feedback_count[sec][index][col_name] > 1:
                                        st.session_state.additional_feedback_count[sec][index][col_name] -= 1

                                # Dynamically generate additional feedback text boxes
                                for i in range(2, st.session_state.additional_feedback_count[sec][index][col_name] + 1):
                                    additional_feedback_key = f"{sec}_feedback_{index}_{col_name}_{i-1}"
                                    additional_feedback = col_list[col_num + 1].text_input(f"{col_name} {i-1}", key=additional_feedback_key)
                                    feedback_data[sec][index][f"{col_name}_{i-1}"] = additional_feedback

                # Added a unique key for the Submit Feedback button
                if st.button('Submit Feedback', key=f"unique_key_for_submit_button_{sec}"):
                    save_feedback(selected_patient, selected_display_name, feedback_data, correct_rows, feedback_columns)
                    # st.experimental_rerun()
                    now_feedback = load_feedback(selected_patient, selected_display_name)

                    st.write("Updated Results:")

                    # If now_feedback is already a Python dict, no need for json.loads
                    annotations_list = now_feedback.get('annotations', [])
                    desired_order = ['ent', 'cat', 'exist', 'rel', 'attr', 'sent']
                    reordered_annotations = []

                    sec_list = [annotation for annotation in annotations_list if annotation['sec'] == sec]
                    
                    for annotation in sec_list:
                        reordered_dict = {k: annotation[k] for k in desired_order if k in annotation}
                        reordered_annotations.append(reordered_dict)
                    
                    for annotation in reordered_annotations:
                        st.write(f"  - {annotation}")

                else:
                    st.write("No feedback found for this section.")

                