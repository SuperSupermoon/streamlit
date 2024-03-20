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
import io
import tempfile
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload, MediaIoBaseDownload


# 서비스 계정 키 JSON 파일 경로
SERVICE_ACCOUNT_FILE = {
  "type": "service_account",
  "project_id": "app-open-397403",
  "private_key_id": "b73248497df422c5e6497307d7cbdd0b191f5990",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCei28+sI0hMo7c\n75H47YBhdsx2QVexSeTRq0mS7s6Ka03AqcTDz4CWw7T2r9lvGXtrrqGpLer/qtN9\nFCH1MC+PwDrV9uzFQ4oakF42vXsc/DKEAGBU6FWf9K541O4KkFgr6NaUFOhCGpCR\nsdBG2+3bDThKHiYoVwCCMFjFD7hpsgDl0ZNhIDd11zlmN99Qjmkovou8Euw0Bv21\ndHsuIHalrIxGVOEK99xAYG5A9ZxcAxICQMGVHhCq2XybE5Mht1XMHp5MIYOraseI\nX1rwAl+di4sNHspLcBrEKaBbBwPx69iKl8YFR5QQiGNJA95kRnHlr55ja9/wMwew\n4I6DMKLFAgMBAAECggEAIWWrWygLLp9ND1bK58Y16TICe3WjwJWZhR5BGxnBedCF\nOiy45WuIQZn7vIxJ7/iM8l/Ar5fb3RvxvXMYfSL3nd8nNau0cBBcXuCi7AKJlM8+\nX+aJZFFluhJrj0oBU8nYvPUpAFwQGd6pLfuoLUkGR4K3JQvJS22aTpJbHLXFScQv\nwet92GCiNVz2BgStFLiL6yG68yShrGoXkmfQPMXIi6N6gqE1SIb0XXWE04loJSIO\nkRGMPvTYLjZliNr7LZB9n7twn6Ehe/5WCskkaf6BmFZs7IKEg6LN0FNbQwF4EIV0\nLLq/XmSDbBDHC3SJGy365yeM0C/QOuw5LKJgX6hhWQKBgQDKgGtzke/7blWmI0Wc\nirLv06YEW+qBkHCoNChmKujvb5mW0EMwxsVQLGk5N82BK7VxHuCVtQ9SUJ5y/r87\n+UQTEPcloCeFpNJ0jPi7Cndssc36Iv7lScYKc7b7gilXO3hBCetve40kqk9rxGsx\nyMTLiEG62lIpZpgeumlfgkranQKBgQDIbh59YhPuPRp+Oo5mvYBDqxk9wUUCeUZi\nGwRe/a5lfuKlKkSOMVMpsQcukCCISiUNHIGwGJ02SFgER4F60j8yIV7O8LaUTSXS\nKopENtb2X3UOM5Awn+7q1JicSFKwRMTrs473ueu6SCVH3QU37msRGF5tulTfnwwO\nmrqlNHG8SQKBgGRr0t15Hb1eNfMxwq+iyKHOH6JBwsWFz5haZT5lQSab/Vqg5PEn\nYWok2/mYBr1r44q5eT5Ej9iOSkVUt5kSQAQEgcuS5IaN+h/6WM7Infi1JCRLfoRO\nVXuRbsjC/6VWxIfcV3jtmEz6eHBE87O4kH8ujwoOgngtfHqgjujiQCSxAoGAfz7i\nHooQyzSByFfWpkVy1AMhMEKuVEa4N3qdiM0XVhp7O46dHYUVHifkvlwEO2KPKUbK\n0widbqP5NSZMfrRSKLpk3Y6W64obE9WsGGiUiq/Jue1kgmpXHUFBbh7AWGYget9x\nSbcAgDBjcr9QG9VCpgTJlnIwhhQMbI0xJ8cm2fkCgYA5K/b6/sLX6qUqcF38Rr15\nDcr8Gxqz/Zx4mMJNnAG4U6cuozmV3Z+wtF82QFnSaiibPH1cNo7+7W3MH7JN5ZyR\nWKl67J5kef/Pyo0GYH0PcWP5ZJ39LeApAesePz7t7seq+oKXGlPnXn6nLTY0++En\nk5b8RL/l6uo5p6EVb5csOA==\n-----END PRIVATE KEY-----\n",
  "client_email": "streamlit@app-open-397403.iam.gserviceaccount.com",
  "client_id": "114410097368575921127",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/streamlit%40app-open-397403.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

SCOPES = ['https://www.googleapis.com/auth/drive']

credentials = Credentials.from_service_account_info(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
drive_service = build('drive', 'v3', credentials=credentials)

# Drive 정보 가져오기
drive_info = drive_service.about().get(fields='storageQuota').execute()

# # 용량 정보 출력
total_space = int(drive_info['storageQuota']['limit'])
used_space = int(drive_info['storageQuota']['usage'])

print(f"Total Space: {total_space / 1e9} GB")
print(f"Used Space: {used_space / 1e9} GB")
print(f"Free Space: {(total_space - used_space) / 1e9} GB")

editable = True
# grid_height = "100%"
grid_width = "100%"


json_folder_path = './test2/'
json_files = [os.path.join(root, file) for root, _, files in os.walk(json_folder_path) for file in files if file.endswith('.json')]
st.set_page_config(layout="wide")
columns_to_drop = ['cat','subject_id', 'study_id', 'sequence', 'section', 'report']

# Google Drive에 파일 업로드
def upload_to_drive(filename, filedata, folder_id=None):
    file_metadata = {'name': filename}
    
    if folder_id:
        file_metadata['parents'] = [folder_id]
        
    # Convert DataFrame to CSV string and then to BytesIO object
    csv_buffer = io.BytesIO()
    filedata.to_csv(csv_buffer, index=False)
    csv_buffer.seek(0)
    
    media = MediaIoBaseUpload(csv_buffer, mimetype='text/csv', resumable=True)
        
    request = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, name, parents'
    )
    file = request.execute()

    # 파일의 ID와 부모 폴더 정보를 출력합니다.
    print(f"Uploaded file with name {file.get('name')}, ID {file.get('id')} to parent(s) {file.get('parents')}")


def create_folder(folder_name, parent_folder_id=None):
    query = f"name='{folder_name}'"
    if parent_folder_id:
        query += f" and '{parent_folder_id}' in parents"
        
    results = drive_service.files().list(
        q=query,
        pageSize=1,
        fields="files(id, name)"
    ).execute()

    # print("results", results)
    
    items = results.get('files', [])
    
    # print("items", items)
    
    # 폴더가 이미 존재하는 경우
    if len(items) > 0:
        return items[0]['id']
    
    # 새 폴더를 생성
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    # print("folder_name", folder_name)
    
    if parent_folder_id:
        folder_metadata['parents'] = [parent_folder_id]
        
    folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
    
    # print("folder['id']", folder['id'])
    
    return folder['id']


def recursive_defaultdict():
    return defaultdict(recursive_defaultdict)

def defaultdict_to_dict(d):
    if isinstance(d, defaultdict):
        d = {k: defaultdict_to_dict(v) for k, v in d.items()}
    return d

def remove_quotes_with_re(text):
    return re.sub(r'^["\']|["\']$|^["\'],|["\'],$','', text)

            
def extract_key_values(d, output_dict1=None, output_dict2=None, parent_key1='', parent_key2='', separator='.'):
    if output_dict1 is None:
        output_dict1, output_dict2  = {}, {}
    for key, value in d.items():
        new_key1 = f"{parent_key1}{separator}{key}" if parent_key1 else key
        new_key2 = f"{key}" if parent_key2 else key
        if isinstance(value, dict):
            extract_key_values(value, output_dict1, output_dict2, new_key1, new_key2, separator=separator)
        else:
            output_dict1[new_key1] = value
            output_dict2[new_key2] = value
    return output_dict1, output_dict2

def find_and_map_values_by_index(key_to_find, output_dict1, output_dict2):
    keys_output_dict2 = list(output_dict2.keys())
    keys_output_dict1 = list(output_dict1.keys())
    
    try:
        index_to_find = keys_output_dict2.index(key_to_find)
    except ValueError:
        return None  # 찾는 키가 output_dict2에 없다면 None을 반환
    
    # 동일한 인덱스를 output_dict1에 적용
    corresponding_key_in_output_dict1 = keys_output_dict1[index_to_find]
    return corresponding_key_in_output_dict1  # 해당하는 값이 없으면 None을 반환


def parse_input_to_dict(input_data):
    parsed_dict = {}
    
    if isinstance(input_data, str):
        # Remove unnecessary characters
        clean_str = re.sub(r"[}\]\n]", "", input_data)
        for match in re.finditer(r"(\w+):\s*([^,]*)(?:,|$)", clean_str, re.DOTALL):
            key, value = match.groups()
            parsed_dict[key.strip()] = value.strip()  # Remove whitespace
            
    elif isinstance(input_data, list):
        # Remove leading and trailing whitespace from each string in the list
        clean_list = [item.strip() for item in input_data]
        
        # Checking if there are exactly 2 items in the list
        if len(clean_list) == 2:
            key, value = clean_list
            parsed_dict[key] = value

    return parsed_dict


def adjust_key(k, reference_dict):
    # Attempt to find a matching key in reference_dict that starts with 'rel.'
    matching_key = next((key for key in reference_dict.keys() if key.endswith('.' + k)), None)
    
    if matching_key:
        # If a matching key is found, modify k to match the format of the key in reference_dict            
        return matching_key.replace('.', ': ').split(': ')
    return [k]


def save_feedback(jsonfile, input_feedback, current_section, section_texts, display_names, feedback_data=None):
    # 기존 데이터 불러오기
    top_folder_id = find_top_folder(drive_service)
    existing_feedback = load_feedback(jsonfile['subject'], display_names, drive_service, top_folder_id)

    # 기존 데이터에 새로운 피드백 추가
    if existing_feedback is not None:
        # 현재 섹션의 기존 피드백 찾기
        existing_section_feedback = existing_feedback[existing_feedback['section'] == current_section]

        # 기존 피드백이 있는 경우, 해당 피드백 삭제
        if not existing_section_feedback.empty:
            existing_feedback = existing_feedback[existing_feedback['section'] != current_section]

        input_feedback['subject_id'] = jsonfile['subject']
        input_feedback['study_id'] = jsonfile['study']
        input_feedback['sequence'] = jsonfile['sequence']
        input_feedback['section'] = current_section    
        input_feedback['report'] = section_texts

        # 새로운 피드백 추가
        feedback_data = pd.concat([existing_feedback, input_feedback], ignore_index=True)
    else:
        feedback_data = input_feedback.copy()
        feedback_data['subject_id'] = jsonfile['subject']
        feedback_data['study_id'] = jsonfile['study']
        feedback_data['sequence'] = jsonfile['sequence']
        feedback_data['section'] = current_section    
        feedback_data['report'] = section_texts

    # print("st.session_state.reviewer_name", st.session_state.reviewer_name)
    # 폴더 생성 및 데이터 저장
    
    reviewer_folder_id = create_folder(st.session_state.reviewer_name)
    patient_folder_id = create_folder(jsonfile['subject'], reviewer_folder_id)
    upload_to_drive(f"{display_names}.csv", feedback_data, patient_folder_id)
    # return patient_folder_id, feedback_data

def del_files(service, folder_id, indent=0):
    results = service.files().list(
        q=f"'{folder_id}' in parents",
        pageSize=100,
        fields="nextPageToken, files(id, name, mimeType)"
    ).execute()
    
    items = results.get('files', [])
    
    
    if not items:
        print('No files found.')
    else:
        for item in items:
            # Delete the folder
            print(f"Deleting folder: {item['name']} ({item['id']})")
            drive_service.files().delete(fileId=item['id']).execute()

# Start from root
# del_files(drive_service, 'root')
# exit()

# when local
# def load_feedback(patient_id, display_names):
#     if os.path.exists(f"./feedback/{st.session_state.reviewer_name}/{patient_id}/{display_names}.json"):
#         feedback_data = load_json(f"./feedback/{st.session_state.reviewer_name}/{patient_id}/{display_names}.json")
#         return feedback_data


def get_full_path(service, file_id, file_name):
    """Get the full path of a file or folder on Google Drive by recursively looking up its parents."""
    path = [file_name]

    while file_id:
        response = service.files().get(fileId=file_id, fields='parents').execute()
        if 'parents' in response:
            parent_id = response['parents'][0]
            parent_response = service.files().get(fileId=parent_id, fields='name').execute()
            parent_name = parent_response['name']
            path.insert(0, parent_name)
            file_id = parent_id
        else:
            file_id = None

    return "/".join(path)

# full_path = get_full_path(drive_service, '1tHqNkaqdwT9EqZu5ndvP9e1x-DXW2BN9', '2_s55504914.csv')
# print("full_path", full_path)

# when Gdrive.
def load_feedback(patient_id, display_names, service, folder_id):
    if folder_id is not None:
        results = service.files().list(
            q=f"'{folder_id}' in parents and name='{patient_id}' and mimeType='application/vnd.google-apps.folder'",
            pageSize=10,
            fields="files(id, name, mimeType)"
        ).execute()

        items = results.get('files', [])
        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                subfolder_id = item['id']
                subfolder_results = service.files().list(
                    q=f"'{subfolder_id}' in parents and name='{display_names}.csv'",
                    pageSize=10,
                    fields="files(id, name)"
                ).execute()
                
                subfolder_items = subfolder_results.get('files', [])
                if subfolder_items:
                    csv_file_id = subfolder_items[0]['id']
                    feedback_data = load_csv_from_drive(service, csv_file_id)
                    return feedback_data

    return None


def load_csv_from_drive(service, file_id):
    request = service.files().get_media(fileId=file_id)
    csv_buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(csv_buffer, request)
    done = False
    while done is False:
        _, done = downloader.next_chunk()
    
    csv_buffer.seek(0)
    df = pd.read_csv(csv_buffer)
    return df


def find_top_folder(service):
    results = service.files().list(
        q=f"name='{st.session_state.reviewer_name}' and mimeType='application/vnd.google-apps.folder'",
        pageSize=10,
        fields="files(id, name)"
    ).execute()
    items = results.get('files', [])
    
    # print("root folder path:", items)
    
    if items:
        return items[0]['id']
    else:
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
            if len(missing_sents_for_section) != 0 and missing_sents_for_section[0] != '':
                # print("missing_sents_for_section", missing_sents_for_section)
                missing_sents[sec] = missing_sents_for_section               
        else:                
            if len(section_sents) != 0 and section_sents[0] != '':
                # print("section_sents", section_sents)
                missing_sents[sec] = section_sents
                
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

# Function to create aggrid_grouped_options with multi-level headers
def generate_aggrid_grouped_options(df, row1, row2):
    existing_columns = df.columns.tolist()
    tuples = [(r1, r2) for r1, r2 in zip(row1, row2) if r2 in existing_columns]

    # Combine row1 with unique identifiers for duplicates
    row1_unique = []
    seen_row1 = {}
    for r1, _ in tuples:
        if r1 in seen_row1:
            seen_row1[r1] += 1
            row1_unique.append(f"{r1}_{seen_row1[r1]}")
        else:
            seen_row1[r1] = 1
            row1_unique.append(r1)

    # Create Ag-Grid Options
    aggrid_grouped_options = {"columnDefs": []}
    header_groups = {}
    for r1, r2 in tuples:
        if r1 not in header_groups:
            header_groups[r1] = {"headerName": r1, "children": []}
        header_groups[r1]["children"].append({"headerName": r2, "field": r2,  "width": 100})  # set width to 100
    
    aggrid_grouped_options["columnDefs"] = list(header_groups.values())

    return aggrid_grouped_options

# Define a mapping of column name variations to standard names
column_variations = {
    'emerge': ['emerg', 'emerge'],
    'no change': ['nchg', 'no change'],
    'distribution': ['dist', 'distribution', 'distribute'],
    'severity': ['sev', 'severity', 'seve'],
    'location': ['loc', 'location'],
    'morphology': ['mor', 'morp', 'morph'],
    'improved': ['impr', 'improve', 'improved', 'imp', 'improv', 'improvement'],
    'reposition': ['repl', 'replace'],
    'resolve': ['res', 'resolve', 'resolved', 'resolv'],
    'comparision': ['com', 'comp', 'comparision', 'compare'],
}

group_by_columns = ['sent', 'sent_idx', 'ent', 'status', 'cat', 'location']

# Determine columns to be aggregated
aggregate_columns = ['morphology', 'distribution', 'size', 'num', 'severity', 'comparision', 'emerge', 'no change', 'improved', 'worsened', 'reposition', 'resolve']

# Function to map variations to standard column names
def standardize_columns(df, variations_map):
    for standard_name, variations in variations_map.items():
        for variation in variations:
            if variation in df.columns:
                df.rename(columns={variation: standard_name}, inplace=True)
    return df

def clean_list(value_list):
    # Remove empty strings and strings consisting only of commas and/or spaces
    return [item for item in value_list if item.strip(',') and item.strip()]

def display_data(data):
    sections = {
        "HIST": data.get("History", ""),
        "FIND": data.get("Findings", ""),
        "IMPR": data.get("Impression", "")
    }
    
    annotations = data.get('annotations', [])

    # print("annotations", annotations)
    # annotations가 문자열 형태라면 JSON 객체로 변환
    if isinstance(annotations, str):
        try:
            annotations = json.loads(annotations)
            
        except json.JSONDecodeError:
            st.error(f"Failed to parse annotations in file: {selected_file}")
            annotations = []

    dfs = {}
    aggrid_grouped_options = {}
    row1 = ['sentence', 'sentence','entity', 'status', 'status', 'relation', 'attribute.appearance', 'attribute.appearance', 'attribute.appearance', 'attribute.level', 'attribute.level', 'attribute.level', 'attribute.temporal', 'attribute.temporal', 'attribute.temporal', 'attribute.temporal', 'attribute.temporal', 'attribute.temporal']
    row2 = ['sent', 'sent_idx','ent', 'status', 'cat', 'location', 'morphology', 'distribution', 'size', 'num', 'severity', 'comparision', 'emerge', 'no change', 'improved', 'worsened', 'reposition', 'resolve']


    for sec in sections.keys():
        filtered_annotations = [item for item in annotations if item['sec'] == sec]
        
        # Initialize empty DataFrame with all columns from row2
        df_sec = pd.DataFrame(columns=row2)

        if filtered_annotations:
            df_sec = pd.DataFrame(filtered_annotations)
            
            # print("df_sec", df_sec)

            # 모든 행의 'attr' 값이 빈 사전, None, 또는 빈 문자열인지 확인
            all_empty = df_sec['attr'].apply(lambda x: x == {} or x is None or x == '').all()

            # all_empty가 False인 경우에만 attr 관련 처리 수행
            if not all_empty:
                attr_data = []
                for _, row in df_sec.iterrows():
                    attr_dict = row.get('attr', {})
                    
                    if not attr_dict:
                        # attr_dict가 비어 있으면, 기존 row의 데이터를 유지
                        attr_data.append(row.to_dict())
                        continue  # 다음 행으로 넘어감

                    # attr_dict에 데이터가 있는 경우 처리
                    for key, compound_val in attr_dict.items():
                        # 콤마로 구분된 다중 값을 분리
                        compound_values_processed = False

                        if isinstance(compound_val, list):
                            compound_val = ', '.join(compound_val)

                        # print("compound_val", compound_val)
                        
                        for val in compound_val.split(', '):
                            # '|'로 키와 값을 분리
                            parts = val.split('|')
                            if len(parts) == 2:
                                # 분리된 값이 정확히 두 부분일 때, 새로운 키와 값으로 분리하여 사용
                                new_key, new_val = parts
                                attr_data.append({**row.to_dict(), new_key: new_val})
                                compound_values_processed = True
                            else:
                                # '|'가 없거나 두 개 이상 포함되어 있는 경우, 에러 처리나 다른 로직 적용
                                print(f"Unexpected format in 'attr' value: {val}")
                        
                        if not compound_values_processed:
                            # 콤마로 구분된 값이 처리되지 않았다면, 즉 '|'로 분리할 수 없는 경우
                            # 기존 row의 데이터를 그대로 유지
                            attr_data.append(row.to_dict())
                df_sec = pd.DataFrame(attr_data)
            
            # print("11 df_sec", df_sec.columns)
            df_sec = df_sec.drop(columns=['attr'], errors='ignore')
            

            # Standardize column names based on variations
            df_sec = standardize_columns(df_sec, column_variations)
            
        extra_columns = set(df_sec.columns) - set(row2)
        if extra_columns and not extra_columns.issubset({'sent_idx', 'sec', 'cat'}):
            raise ValueError(f"Extra columns found that are not defined in row2: {extra_columns}")

        df_sec = df_sec.reindex(columns=row2).fillna('')
        # print("22 df_sec", df_sec['sent_idx'])
        
        #######################################################################################################################################################################################
        # Ensure each aggregate column is a list (this simplifies combining them later)
        for column in aggregate_columns:
            df_sec[column] = df_sec[column].apply(lambda x: [x] if pd.notnull(x) else [])

        # Group by the specified columns and aggregate the rest
        df_sec = df_sec.groupby(group_by_columns, as_index=False).agg({col: 'sum' for col in aggregate_columns})

        # Optionally, remove duplicates from each aggregated list
        for column in aggregate_columns:
            df_sec[column] = df_sec[column].apply(clean_list)
            # df_sec[column] = df_sec[column].apply(lambda x: list(set(x)))

        # Your aggregated_df now contains combined information for 'morphology' to 'resolve'
        # based on unique combinations of 'sent', 'ent', 'status', 'cat', and 'location'
        df_sec = df_sec.sort_values(by='sent_idx', ascending=True)

        # print("aggregated_df", df_sec['size'])
        # print("33 df_sec", df_sec.columns)
        df_sec = df_sec.drop(columns=['sent_idx','cat'], errors='ignore')
        ########################################################################################################################################################################################
        
        dfs[sec] = df_sec
        aggrid_grouped_options[sec] = generate_aggrid_grouped_options(df_sec, row1, row2)

    return sections, dfs, annotations, aggrid_grouped_options




# if 'reviewer_name' not in st.session_state or not st.session_state.reviewer_name:
#     st.session_state.reviewer_name = st.text_input("Please enter your name for feedback:")

# Check if 'reviewer_name' is already in the session state
if 'reviewer_name' not in st.session_state:
    st.session_state.reviewer_name = ''

# If reviewer_name is empty, prompt the user to enter their name
# instruction_placeholder = st.empty()

if 'show_cof' not in st.session_state:
    st.session_state['show_cof'] = False
    
if 'show_sym' not in st.session_state:
    st.session_state['show_sym'] = False
    
if 'show_rel' not in st.session_state:
    st.session_state['show_rel'] = False
    
if 'show_attr' not in st.session_state:
    st.session_state['show_attr'] = False
    


if not st.session_state.reviewer_name:
    col1, col2, col3 = st.columns(3)
    
    st.session_state.reviewer_name = st.text_input("Please enter your name to start feedback!! :muscle:")
    with col1:
        with st.expander("한국어 안내", expanded=False):
            st.write("""
            ## 소개
            이 앱은 GPT-4를 통한 entity-relation-attribute 추출 결과에 대한 피드백을 위한 도구입니다. 
            
            리뷰어가 피드백을 제공할 총 데이터는 평균 10.07개의 study sequence를 갖는 293명의 환자로부터 얻어진 3,269개의 리포트입니다.
            
            최종 완료된 리뷰는 테스트 세트로 사용될 예정입니다.
            
            ## 시작하기 전에
            1. **입력은 영어로 작성 해주세요.**
            2. **리뷰어 이름 입력**: 앱 접속 후 리뷰어의 이름을 입력하세요.
            3. **데이터 탐색**: 왼쪽 사이드바에서 환자 ID와 study 파일(JSON 형식)을 선택할 수 있습니다.
            4. **리포트 및 GPT-4 결과 확인**: 선택한 study 파일을 클릭하면 원본 리포트의 'History', 'Findings', 'Impression' 섹션과 그에 대한 GPT-4 결과를 확인할 수 있습니다.

            ## 피드백 방법

            ### 기본 피드백
            - **GPT-4 결과**: Dataframe 형태와 추출에 사용된 문장, 그리고 해당 결과가 간략히 표시됩니다.
            - **저장**: 섹션별 리뷰를 수행한 후, 제출 버튼을 눌러야 해당 섹션의 리뷰 내용이 저장됩니다.
            - **피드백 형식**: 피드백을 남길 시 반드시 dictionary 형태로 'key-value' 쌍의 형식을 따라주세요.  
            *ex) exist: DP|worsening*
            - **피드백 시작**: 'Review {section}'을 클릭하여 피드백을 시작하세요.

            #### 피드백 종류:
            1. **Correct**: GPT-4의 결과가 정확하다면 ':thumbsup:'를 클릭하세요.
            2. **Include**: 추가해야 할 entity의 key와 value를 입력하세요.
            3. **Delete**: 삭제해야 할 entity의 key와 value를 입력하세요.
            4. **Modify**: 수정이 필요한 entity의 key는 유지하고 value만 변경하여 입력하세요.

            ### 추가적인 피드백
            - **Additional Annotation**: GPT-4가 누락한 문장이 있거나 새로운 annotation을 추가하고 싶다면, 각 섹션에 있는 'Add for section'을 클릭하여 추가나 삭제를 할 수 있습니다.

            ## 제출
            - **저장과 제출**: 각 섹션에서 피드백을 모두 완료한 뒤, '제출' 버튼을 클릭하여 피드백을 저장하세요. 이전에 제출한 피드백은 앱을 재접속하더라도 볼 수 있습니다.

            ### 중복 피드백
            - 중복으로 피드백을 입력하게 되면, 가장 최근의 피드백만 저장됩니다.
            """)
        
    with col2:
        with st.expander("English Guide", expanded=False):
            st.write("""

            ## Introduction
            This app serves as a tool for providing feedback on the entity-relation-attribute extraction results via GPT-4-turbo. 
            
            Reviewers will work with a total of 3,269 reports from 293 patients, each with an average of 10.07 study sequences.
            
            The finalized reviews are intended for use in test set.

            ## Before You Start
            1. **Please use English for feedback.**
            2. **Reviewer's Name Entry**: Upon accessing the app, please enter your name.
            3. **Data Exploration**: The left sidebar allows you to select the patient ID and study files (in JSON format).
            4. **Report and GPT-4 Results**: Clicking on the chosen study file will display the original report's 'History', 'Findings', and 'Impression' sections, along with the corresponding GPT-4 results.

            ## Feedback Method

            ### Basic Feedback
            - **GPT-4 Results**: Results are briefly displayed in a dataframe, along with the sentences used for extraction.
            - **Save**: After reviewing each section, click the 'Submit' button to save the review for that section.
            - **Feedback Format**: Please strictly follow a 'key-value' pair format in a dictionary when leaving feedback.  
            *e.g., exist: DP|worsening*
            - **Start Feedback**: Click 'Review {section}' to begin the feedback process.

            #### Types of Feedback:
            1. **Correct**: Click ':thumbsup:' if GPT-4's result is accurate.
            2. **Include**: Enter the key and value of the entity that should be added.
            3. **Delete**: Enter the key and value of the entity that should be removed.
            4. **Modify**: If an entity needs to be modified, keep the key the same and change only the value.

            ### Additional Feedback
            - **Additional Annotation**: If GPT-4 has missed any sentences or you wish to add new annotations, click 'Add for section' in each section to make additions or deletions.

            ## Submission
            - **Save and Submit**: After completing the feedback for all sections, click the 'Submit' button to save your feedback. You can view previously submitted feedback even after re-accessing the app.

            ### Duplicate Feedback
            - If duplicate feedback is entered, only the most recent feedback will be saved.

            """)
            
    with col3:
        with st.expander("Entity schema", expanded=False):
            st.markdown("Click button to see entity schema.")
            if st.button("6 Entity type", key='btn_cof'):
                st.session_state.show_cof = not st.session_state.show_cof

            if st.session_state.show_cof:
                st.markdown("""
                - COF (Clinical Objective Findings)
                
                    Evidence-based medical information obtained through lab tests, physical exams, and other diagnostic procedures not based on chest x-ray imaging.
                    
                    ex) 'hemoglobin levels', 'white blood cell count', 'liver function tests','heart rate', 'Systemic inflammatory response syndrom (SIRS)', 'temperature'
                
                - SYM (Symptom)
                    
                    Subjective indications of a disease or a change in condition as perceived by the patient, not directly measurable.
                    
                    ex) 'fatigue', 'cough', 'shortness of breath', 'vomiting'
                
                - ROF (Radiological objective findings)
                    
                    Identifiable radiological findings from a chest X-ray image alone, without external information such as the patient's history or other source results.
                    
                    ex) 'opacity', 'thickening', 'density', 'lung volume', 'collapse','consolidation', 'inﬁltration', 'atelectasis', 'pulmonary edema', 'pleural effusion', 'bronchiectasis', 'calciﬁcation', 'pneumothorax', 'hydropneumothorax', 'lesion', 'mass', 'nodule', 'fracture', 'hyperaeration', 'Cyst', 'Bullae', 'Scoliosis'
                
                - RSF (Radiological subjective findings)
                    
                    Diagnosis based on a physician's judgment or reasoning incorporating the chest x-ray image and external information like patient history or lab findings.       
                    
                    ex) 'pneumonia', 'heart failure', 'copd', 'granulomatous disease', 'interstitial lung disease', 'goiter', 'lung cancer', 'pericarditis', 'pulmonary hypertension', 'tumor'
                
                - OTH (Other object)
                    
                    Pertains to foreign objects (e.g., 'metal fragments', 'glass', 'bullets') or medical devices (e.g., 'chest tubes', 'endotracheal tubes') observed in chest X-ray images.""")

            if st.button("4 Existence", key='btn_sym'):
                st.session_state.show_sym = not st.session_state.show_sym

            if st.session_state.show_sym:
                st.markdown("""
            
            2. Status: Classify entity's status as 'Definitive' or 'Tentative' diagnosis, and categorize it as 'Positively mentioned'; present or abnormal, 'Negatively mentioned'; absent or normal. Answer as 'DP', 'DN' for Definitive, and 'TP', 'TN' for Tentative diagnoses.
            """)
        
            if st.button("2 Relation", key='btn_rel'):
                    st.session_state.show_rel = not st.session_state.show_rel

            if st.session_state.show_rel:
                st.markdown("""
            3. Location: The precise anatomical area or structure where the observation is noted, encompassing both broad regions (left, right, bileteral) and specific biological structures.
                """)
                
            if st.button("11 Attribution", key='btn_attr'):
                    st.session_state.show_attr = not st.session_state.show_attr

            if st.session_state.show_attr:
                st.markdown("""
            1. Appearance (appearance), which can be categorized as
                - Morphology (mor): Physical form, structure, shape, pattern or texture of an object or substance. (e.g., 'irregular', 'rounded', 'dense', 'ground-glass',  'patchy', 'linear', 'plate-like', 'nodular')
                - Distribution (dist): Arrangement, spread of objects or elements within a particular area or space (e.g., 'focal', 'multifocal/multi-focal', 'scattered', 'hazy', 'widespread')
                - Size (size): Physical dimensions or overall magnitude of an entity ('small', 'large', 'massive', 'subtle', 'minor', 'xx cm')

            2. Level (level), which can be categorized as
                - Numeric (num): Attributes are about counting or quantifying individual occurrences or components such as 'single', 'multiple', 'few', 'trace'.
                - Sevierity (sev): Attributes referring to the severity of an entity such as 'mild', 'moderate', 'severe', 'low-grade', 'benign', 'malignant'.

            3. Temporal (tmp) differential diagnosis, which can be categorized as
                - Emergence (emerg): Refers to the chronological progression or appearance of a medical finding or device. Unlike terms that highlight the comparative change in condition, this concept emphasizes the chronological state, either within a single study or in relation to a sequential study. (e.g., new, old, acute, subacute, chronic, remote, recurrent).
                - No Change (nchg): Refers to the consistent state or condition that remains unaltered from a prior study. (e.g., no changed, unchanged, similar, persistent)
                - Improvement (impr): Refers to a positive change or stabilization in a patient's clinical state when compared to a prior assessment. (e.g., improved, decreased, stable)
                - Worsened (worsened): Refers to the negative change in a patient's clinical state in comparison to a prior assessment. (e.g., worsened, increased)
                - Replacement of DEV (replace): Refers to the altered position of a medical device inside a patient compared to prior studies. (e.g., displaced, repositioned).
                - Resolve (resolve): Refers to the complete disappearance of a specific medical finding or device from imaging. (e.g., resolved, cleared).
                """)


def find_folder_id_by_name(service, folder_name):
    # 폴더 이름으로 폴더 검색
    results = service.files().list(
        q=f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}'",
        fields="files(id, name)"
    ).execute()
    folders = results.get('files', [])
    if not folders:
        print(f"No folder found with name: {folder_name}")
        return None
    # 첫 번째 검색 결과의 폴더 ID 반환
    folder_id = folders[0]['id']
    print(f"Folder ID for '{folder_name}': {folder_id}")
    return folder_id

def download_folder_by_name(service, folder_name, local_path):
    folder_id = find_folder_id_by_name(service, folder_name)
    if folder_id:
        download_folder(service, folder_id, local_path)
    else:
        print("Failed to find folder or download content.")

def list_to_string(value):
    # If the input value is None, return None immediately
    if value is None:
        return ''

    # If the input value is not a list, treat it as a single-element list
    if not isinstance(value, list):
        value = [value]

    # Clean the list: Remove duplicates, empty strings, and strip whitespace
    cleaned_list = list(set(
        str(item).strip() 
        for item in value 
        if item is not None 
        and str(item).strip() 
        and str(item).strip().lower() != 'nan' 
        and str(item).strip().lower() != 'none'  # Exclude 'None'
    ))
    
    # Convert to string and return None if the cleaned list is empty
    return ', '.join(cleaned_list) if cleaned_list else ''                         
            
def download_folder(service, folder_id, local_path):
    def download_file(file_id, file_name, local_file_path):
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        with open(local_file_path, 'wb') as f:
            fh.seek(0)
            f.write(fh.read())
        print(f"Downloaded {file_name} to {local_file_path}")

    def list_files_in_folder(folder_id, local_path):
        # 폴더가 없으면 생성
        if not os.path.exists(local_path):
            os.makedirs(local_path)

        results = service.files().list(
            q=f"'{folder_id}' in parents",
            orderBy='createdTime desc',
            fields="nextPageToken, files(id, name, mimeType, createdTime)"
        ).execute()
        
        items = results.get('files', [])
        latest_files = {}

        # 동일한 이름을 가진 파일 중 최신 파일만 선택
        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                # 하위 폴더에 대해 재귀적으로 처리
                new_local_path = os.path.join(local_path, item['name'])
                list_files_in_folder(item['id'], new_local_path)
            else:
                if item['name'] not in latest_files:
                    latest_files[item['name']] = item

        # 저장된 최신 파일들을 다운로드
        for file_info in latest_files.values():
            local_file_path = os.path.join(local_path, file_info['name'])
            download_file(file_info['id'], file_info['name'], local_file_path)

    # 최상위 폴더 이름 가져오기 (로컬 경로 생성에 사용)
    folder_name = service.files().get(fileId=folder_id, fields='name').execute().get('name')
    top_local_path = os.path.join(local_path, folder_name)
    list_files_in_folder(folder_id, top_local_path)

updated_df = None

# If reviewer_name is set, display the rest of the app
if st.session_state.reviewer_name:    
    st.title(f'GPT4 Results - Reviewer: {st.session_state.reviewer_name}')
    # st.write(f"**Folder path:** {count_json_files_in_subfolders(drive_service, find_top_folder(drive_service))}")  # 과거 얼마나 했고 몇퍼센트 남았는지 진행상태를 알려줌
    
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

    if 'last_selected_file' not in st.session_state:
        st.session_state.last_selected_file = None

    if 'additional_feedback_count' not in st.session_state:
        st.session_state.additional_feedback_count = {}

    if 'checkbox_states' not in st.session_state:
        st.session_state.checkbox_states = {}

    if 'row_count_state' not in st.session_state:
        st.session_state.row_count_state = {}
        st.session_state.row_feedback_data = {}

    # Check if selected_file has changed
    if st.session_state.last_selected_file != selected_file:
        # Reset the previous_feedback and additional_feedback_count
        
        previous_feedback = load_feedback(selected_patient, selected_display_name, drive_service, find_top_folder(drive_service))
        st.session_state.additional_feedback_count = {}
        st.session_state.checkbox_states = {}
        st.session_state.row_count_state = {}
        st.session_state.my_dfs = {}
    else:
        # 이전에 저장한 피드백이 있다면 불러옴
        previous_feedback = {}#load_feedback(selected_patient, selected_display_name, drive_service, find_top_folder(drive_service))
    st.session_state.last_selected_file = selected_file

    # Load and display selected JSON data
    jsonfile = load_json(selected_file)
    
    sections, dfs, annotations, aggrid_grouped_options = display_data(jsonfile)
    
    # Get statistics    
    present_sections, sent_stats, cat_stats, norm_ent_stats, missing_sents = get_statistics(jsonfile, dfs)
    total_missing = sum(len(value) for value in missing_sents.values())

    with st.expander(f"**Show File Statistics: {total_missing} Missing Sents**"):
        #1. 'CAT'의 value 통계 출력
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
        count_per_key = {key: len(value) for key, value in missing_sents.items()}
        st.write(f"{total_missing} Missing Sents")
        for sec, sents in missing_sents.items():
            st.write(f"  - {sec} ({count_per_key[sec]}): {', '.join(sents)}")
    
    feedback_data = {}
    for current_section, content in sections.items():
        feedback_data[current_section] = {}
        st.write("")
        st.markdown(f" <span style='font-size: 2em;'> :clipboard: {current_section}: </span> <span style='font-size: 1.2em;'> {content}</span>", unsafe_allow_html=True)

        current_df = dfs[current_section]
        if isinstance(previous_feedback, pd.DataFrame):    
            filtered_df = previous_feedback[previous_feedback['section'] == current_section]

            if filtered_df.empty:
                if len(content) != 0 and content != '':
                    error_message = f"Did you forget to annotate this section?"
                    st.error(error_message, icon="🚨")
        ################################################################################################
        with st.expander(f"**{current_section} DataFrame**"):
            
            # # Check for previous feedback for the current section and use it if available
            initial_df = current_df.copy()            
            initial_df.drop(columns=[col for col in columns_to_drop if col in initial_df.columns], inplace=True)
            initial_df.columns = initial_df.columns.astype(str)            
            
            if isinstance(previous_feedback, pd.DataFrame):
                if current_section not in st.session_state.my_dfs:
                    st.write(":male-doctor: Previous Review:")                        
                    load_df = filtered_df.copy()
                    load_df.columns = load_df.columns.astype(str)
                    st.session_state.my_dfs[current_section] = load_df                    
            else:
                if current_section not in st.session_state.my_dfs:
                    st.session_state.my_dfs[current_section] = initial_df

            col1, col2, _,_,_,_,_,_ = st.columns(8)

            with col1:
                if st.button('Add Row', key=f'add_row_button_{current_section}'):
                    columns = st.session_state.my_dfs[current_section].columns.tolist()
                    new_row = pd.DataFrame([pd.Series({col: '' for col in columns})])
                    st.session_state.my_dfs[current_section] = pd.concat([st.session_state.my_dfs[current_section], new_row], ignore_index=True)

            with col2:
                if st.button('Remove Last Row', key=f'remove_last_row_button_{current_section}'):
                    if len(st.session_state.my_dfs[current_section]) > 0:  # 데이터프레임이 비어 있지 않은 경우
                        st.session_state.my_dfs[current_section].drop(st.session_state.my_dfs[current_section].index[-1], inplace=True)
                        st.session_state.my_dfs[current_section].reset_index(drop=True, inplace=True)

            gb = GridOptionsBuilder.from_dataframe(st.session_state.my_dfs[current_section])
            gb.configure_default_column(groupable=True, value=True, enableRowGroup=True, editable=True)
            gb.configure_grid_options(enableCellTextSelection=True)
            
            # Merge the custom columnDefs into the gridOptions
            original_grid_options = gb.build()
            if current_section in aggrid_grouped_options:
                original_grid_options['columnDefs'] = aggrid_grouped_options[current_section]['columnDefs']
            else:
                # Handle the case where the section does not exist in aggrid_grouped_options
                original_grid_options['columnDefs'] = []
            
            ag_grid_key = f"{current_section}_dataframe_{hash(str(st.session_state.my_dfs[current_section]))}"
            response = AgGrid(
                data=st.session_state.my_dfs[current_section],
                gridOptions=original_grid_options,
                width='100%',
                data_return_mode='AS_INPUT',
                update_mode=GridUpdateMode.VALUE_CHANGED,
                key=ag_grid_key  # updated key
            )
            
            st.write(":robot_face: GPT4 Results:")
            st.write(initial_df.drop(['sent'], axis=1))
            updated_df = pd.DataFrame(response['data'])
            updated_df = updated_df.drop(columns=[col for col in columns_to_drop if col in updated_df.columns])            

            for column in updated_df.columns.tolist():
                updated_df[column] = updated_df[column].apply(list_to_string)
            st.session_state.my_dfs[current_section] = updated_df

            # download_folder_by_name(drive_service, 'jh', '/Users/super_moon/Desktop/streamlit/feedback_result')

            # # 'Submit Feedback' 버튼
            if st.button('Submit Feedback', key=f"unique_key_for_submit_button_{current_section}"):
                save_feedback(jsonfile, st.session_state.my_dfs[current_section], current_section, content, selected_display_name, feedback_data)
                
                # st.experimental_rerun()
                now_feedback = load_feedback(selected_patient, selected_display_name, drive_service, find_top_folder(drive_service))
                filtered_df = now_feedback[now_feedback['section'] == current_section]

                st.write(":point_right: Updated Results:")
                st.write(filtered_df.drop(['sent', 'subject_id', 'study_id', 'sequence', 'section', 'report'], axis=1))
            else:
                st.write("No feedback found for this section.")
                
                
                