import streamlit as st
import os
import pandas as pd
import json
from collections import defaultdict
from nltk.tokenize import sent_tokenize


json_folder_path = './test/'
json_files = [os.path.join(root, file) for root, _, files in os.walk(json_folder_path) for file in files if file.endswith('.json')]

st.set_page_config(layout="wide")

def recursive_defaultdict():
    return defaultdict(recursive_defaultdict)

def defaultdict_to_dict(d):
    if isinstance(d, defaultdict):
        d = {k: defaultdict_to_dict(v) for k, v in d.items()}
    return d

def save_feedback(patient_id, display_names, feedback_data, correct_rows):
    # 피드백을 섹션과 행 인덱스로 정렬
    sorted_feedback_data = sorted(feedback_data, key=lambda x: (x[0], x[1]))
    sorted_correct_rows = sorted(correct_rows, key=lambda x: (x[0], x[1]))

    data_to_save = {
        'feedback': sorted_feedback_data,
        'correct_rows': sorted_correct_rows
    }
    
    os.makedirs(f"./feedback/{patient_id}", exist_ok=True)
    with open(f"./feedback/{patient_id}/{display_names}.json", "w") as f:
        json.dump(data_to_save, f)


def load_feedback(patient_id, display_names):
    try:
        with open(f"./feedback/{patient_id}/{display_names}.json", "r") as f:
            feedback_data = json.load(f)
            return feedback_data
    except FileNotFoundError:
        return None

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

    print("reordered_annotations", reordered_annotations)

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
    previous_feedback = load_feedback(selected_patient, selected_display_name)

    # Load and display selected JSON data
    data = load_json(selected_file)
    sections, dfs, annotations_list = display_data(data)

    # Get statistics    
    present_sections, sent_stats, cat_stats, norm_ent_stats, missing_sents = get_statistics(data, dfs)

    # 파일 통계 섹션 시작
    with st.expander("**Show File Statistics**"):
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

    for sec, content in sections.items():
        st.write(f"**{sec}:** {content}")
        
        current_df = dfs[sec]
        filtered_df = current_df.drop(columns=["sec", "sent_idx"])
        
        # 재정렬하려는 열의 순서를 리스트로 지정
        desired_column_order = ['ori_ent', 'norm_ent', 'cat', 'exist', 'loc', 'asso', 'appr', 'tmp', 'level', 'sent']

        # DataFrame에 실제로 존재하는 열만 필터링
        available_columns = [col for col in desired_column_order if col in current_df.columns]

        # 열을 새로운 순서로 재정렬
        filtered_df = filtered_df[available_columns]
        
        with st.expander("**Show DataFrame**"):
            st.write(filtered_df)

        feedback_data[sec] = {}
        correct_rows[sec] = {}

        for index, row in current_df.iterrows():
            
            st.write(f"  - {sec} Row {index}: {annotations_list[index]}")

            feedback_data[sec][index] = {}
            correct_rows[sec][index] = {}

            # Select columns for feedback (1st onwards)
            feedback_columns = filtered_df.columns.tolist()[:-1]

            col_list = st.columns(len(feedback_columns) + 1)  # Extra column for overall 'correct' checkbox

            # Overall 'correct' checkbox
            correct_key = f"{sec}_correct_{index}"
            overall_correct = col_list[0].checkbox(f"Correct all", key=correct_key)
            
            if overall_correct:
                correct_rows[sec][index]['overall'] = True
                continue  # Skip the rest of the loop for this row if 'Overall Correct' is checked
            else:
                correct_rows[sec][index]['overall'] = False

                for col_num, col_name in enumerate(feedback_columns):
                    # Create unique keys by including the section name, row index and column name
                    correct_key = f"{sec}_correct_{index}_{col_name}"
                    feedback_key = f"{sec}_feedback_{index}_{col_name}"

                    correct = col_list[col_num + 1].checkbox(f"{col_name}", key=correct_key)

                    if correct:
                        correct_rows[sec][index][col_name] = True
                    else:
                        correct_rows[sec][index][col_name] = False
                        feedback = col_list[col_num + 1].text_input(f"", key=feedback_key)
                        feedback_data[sec][index][col_name] = feedback


    if st.button('Submit Feedback'):
        save_feedback(selected_patient, selected_display_name, feedback_data, correct_rows)
        st.write("Feedback submitted!")
        st.experimental_rerun()

    # 이전 피드백을 보다 명확하게 표시
    if previous_feedback:
        st.write("Previous Feedback:")
        for sec, index, feedback in previous_feedback.get('feedback', []):
            st.write(f"  - Section {sec}, Row {index}: {feedback}")

        st.write("Previously Marked Correct Rows:")
        for sec, index in previous_feedback.get('correct_rows', []):
            st.write(f"  - Section {sec}, Row {index}")

    else:
        st.write("No feedback found for this selection.")






