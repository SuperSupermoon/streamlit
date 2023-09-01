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
# total_space = int(drive_info['storageQuota']['limit'])
# used_space = int(drive_info['storageQuota']['usage'])

# print(f"Total Space: {total_space / 1e9} GB")
# print(f"Used Space: {used_space / 1e9} GB")
# print(f"Free Space: {(total_space - used_space) / 1e9} GB")


json_folder_path = './test/'
json_files = [os.path.join(root, file) for root, _, files in os.walk(json_folder_path) for file in files if file.endswith('.json')]
st.set_page_config(layout="wide")


# Google Drive에 파일 업로드
# upload_to_drive(f"{display_names}.json", temp_name, 'application/json', patient_folder_id)
def upload_to_drive(filename, filedata, mimetype, folder_id=None):
    file_metadata = {'name': filename}
    
    if folder_id:
        file_metadata['parents'] = [folder_id]
        
    media = MediaFileUpload(filedata, mimetype=mimetype)
        
    request = drive_service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    )
    file = request.execute()
    print(f"Uploaded file with ID {file.get('id')}")


def create_folder(folder_name, parent_folder_id=None):
    query = f"name='{folder_name}'"
    if parent_folder_id:
        query += f" and '{parent_folder_id}' in parents"
        
    results = drive_service.files().list(
        q=query,
        pageSize=1,
        fields="files(id, name)"
    ).execute()

    items = results.get('files', [])
    
    # 폴더가 이미 존재하는 경우
    if len(items) > 0:
        return items[0]['id']
    
    # 새 폴더를 생성
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    if parent_folder_id:
        folder_metadata['parents'] = [parent_folder_id]
        
    folder = drive_service.files().create(body=folder_metadata, fields='id').execute()
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



def save_feedback(patient_id, display_names, feedback_data, feedback_columns=['include', 'delete', 'modify', 'opinion'], valid_keys = ['ent', 'sec', 'exist', 'cat', 'sent', 'sent_idx', 'rel', 'loc', 'asso', 'attr', 'appr', 'level', 'tmp', 'opinion', 'norm_ent', 'ori_ent']):
   
    original_name = display_names.split('_')[-1]
    original_json = load_json(f"./test/{patient_id}/{original_name}.json")
    new_json = copy.deepcopy(original_json)    
    annotations_list = json.loads(original_json['annotations'])
    new_annotate_list = []
    
    for sec, sec_data in feedback_data.items():
        annot = [item for item in annotations_list if item['sec'] == sec]
        empty_indices = [index for index, value in sec_data.items() if not value]
        if empty_indices:
            indices_str = ', '.join(map(str, empty_indices))
            error_message = f"Please fill in {sec} section data for the following indices: {indices_str}."
            st.error(error_message, icon="🚨")
            
        for idx_str, feedback in sec_data.items():           
            if isinstance(idx_str, str):
                feedback = parse_input_to_dict(feedback)
                feedback['sec'] = sec
                
                if not any(key in valid_keys for key in feedback.keys()):
                    st.error(f"Invalid key. Please use a key from the list: {valid_keys}", icon="🚨")
                    break
                idx = int(idx_str)
                modified_annotation = feedback
                
            else:
                idx = int(idx_str)
                modified_annotation = annot[idx]
            
            if feedback != 'all_correct' and not isinstance(idx_str, str):
                # Single-key items (e.g., 'cat', 'norm_ent')
                single_keys = set(value.split(':')[0].strip(" '") for value in feedback.values() if len(value.split(':')) == 2)

                # Triple-key items (e.g., 'tmp: nchg: stable')
                triple_keys = set(value.split(':')[1].strip(" '") for value in feedback.values() if len(value.split(':')) == 3)

                for key, value in feedback.items():
                    prefix = key.split('_')[0]
                                        
                    if prefix in feedback_columns:
                        if prefix == 'opinion':
                            modified_annotation['opinion'] = value
                        else:
                            key_value_pair = [item.strip() for item in value.split(": ")]                            
                            new_dict1, new_dict2 = extract_key_values(modified_annotation)
                            dic1_key = find_and_map_values_by_index(key_value_pair[0], new_dict1, new_dict2)
                            
                            ### 4 key_value_pair ["attr'", "{'appr'", "'mor|nodular', 'tmp'", "'improved|improved'}"]
                            if len(key_value_pair) == 1:
                                print(f"Invalid feedback. Expected key-value pair for prefix {prefix}, got {key_value_pair}")
                                st.error(f"Invalid feedback. Expected key-value pair for prefix {prefix}, got {key_value_pair}", icon="🚨")
                            
                            if len(key_value_pair) == 2:
                                
                                k, v = key_value_pair
                                k = remove_quotes_with_re(k)
                                v = remove_quotes_with_re(v)
                                                                
                                k_list = adjust_key(k, new_dict1)
                                
                                if prefix == 'include':
                                    if len(k_list) == 2:
                                        if k_list[0] in modified_annotation:
                                            if isinstance(modified_annotation[k_list[0]], dict):                                             
                                                modified_annotation[k_list[0]][k_list[1]] = [modified_annotation[k_list[0]][k_list[1]], v]
                                            else:
                                                modified_annotation[k_list[0]][k_list[1]] = [modified_annotation[k_list[0]][k_list[1]], v]
                                        else:
                                            modified_annotation[k_list[0]] = {k_list[1]: v}
                                    else:
                                        if k_list[0] in modified_annotation:
                                            if isinstance(modified_annotation[k_list[0]], list):
                                                modified_annotation[k_list[0]].append(v)
                                            else:
                                                modified_annotation[k_list[0]] = [modified_annotation[k_list[0]], v]
                                        else:
                                            modified_annotation[k_list[0]] = v

                                        
                                elif prefix == 'modify':
                                    if len(k_list) == 2:
                                        if k_list[0] in modified_annotation:
                                            modified_annotation[k_list[0]] = {k_list[1]: v}
                                    else:
                                        if k_list[0] in modified_annotation:
                                            modified_annotation[k_list[0]] = v
                                            
                                elif prefix == 'delete':
                                    if len(k_list) == 2:
                                        if k_list[0] in modified_annotation and modified_annotation[k_list[0]][k_list[1]] == v:
                                            del modified_annotation[k_list[0]][k_list[1]]
                                    else:
                                        if k_list[0] in modified_annotation and modified_annotation[k_list[0]] == v:
                                            del modified_annotation[k_list[0]]                                                                        
            new_annotate_list.append(modified_annotation)

    # print(f"annotations_list {len(annotations_list)} vs new_annotate_list {len(new_annotate_list)}")
    new_json['annotations'] = annotations_list#json.dumps(annotations_list, indent=4)
    new_json['feedback'] = new_annotate_list#json.dumps(annotations_list, indent=4)
    
    # print("new_annotate_list", new_annotate_list)
    # Create directories if they don't exist
    reviewer_name = st.session_state.reviewer_name
    
    ######## When I use local server ######
    # os.makedirs(f"./feedback/{reviewer_name}/{patient_id}", exist_ok=True)
    
    # # Save the new JSON
    # with open(f"./feedback/{reviewer_name}/{patient_id}/{display_names}.json", "w") as f:
    #     json.dump(new_json, f, indent=4)
    
    ######## When I use external driver ######
    
    reviewer_folder_id = create_folder(reviewer_name)
    patient_folder_id = create_folder(patient_id, reviewer_folder_id)

    # Serialize JSON to a string
    new_json_str = json.dumps(new_json, indent=4)

    # Create a temporary file and write the JSON string to it
    with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as tmp:
        tmp.write(new_json_str)
        temp_name = tmp.name

    # Upload the file
    upload_to_drive(f"{display_names}.json", temp_name, 'application/json', patient_folder_id)
    
    print("file uploaded to google drive!")
    # Remove the temporary file
    os.unlink(temp_name)

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
    
# when Gdrive.
def load_feedback(patient_id, display_names, service, folder_id):
    if folder_id is not None:
        results = service.files().list(
            q=f"'{folder_id}' in parents and name='{patient_id}'",
            pageSize=10,
            fields="files(id, name, mimeType)"
        ).execute()

        items = results.get('files', [])
        for item in items:
            if item['mimeType'] == 'application/vnd.google-apps.folder':
                subfolder_id = item['id']
                subfolder_results = service.files().list(
                    q=f"'{subfolder_id}' in parents and name='{display_names}.json'",
                    pageSize=10,
                    fields="files(id, name)"
                ).execute()
                
                subfolder_items = subfolder_results.get('files', [])
                if subfolder_items:
                    json_file_id = subfolder_items[0]['id']
                    feedback_data = load_json_from_drive(service, json_file_id)
                    return feedback_data

        return None  # or whatever you want to return when the file doesn't exist


def load_json_from_drive(service, file_id):
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    
    file_content = fh.getvalue().decode()
    return json.loads(file_content)


def find_top_folder(service):
    results = service.files().list(
        q=f"name='{st.session_state.reviewer_name}' and mimeType='application/vnd.google-apps.folder'",
        pageSize=10,
        fields="files(id, name)"
    ).execute()
    items = results.get('files', [])
    
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

def count_json_files_in_subfolders(service, top_folder_id):
    subfolder_results = service.files().list(
        q=f"'{top_folder_id}' in parents and mimeType='application/vnd.google-apps.folder'",
        pageSize=1000,
        fields="files(id, name)"
    ).execute()
    
    subfolders = subfolder_results.get('files', [])
    
    count_dict = {}  # 각 서브디렉터리에 있는 JSON 파일의 개수를 저장할 딕셔너리
    
    print("subfolders", subfolders)
    
    # 각 서브디렉터리에서 JSON 파일 찾기
    for folder in subfolders:
        folder_id = folder['id']
        folder_name = folder['name']
        
        json_file_results = service.files().list(
            q=f"'{folder_id}' in parents and mimeType='application/json'",
            pageSize=1000,
            fields="files(id, name)"
        ).execute()
        
        json_files = json_file_results.get('files', [])
        
        count_dict[folder_name] = len(json_files)
    
    return count_dict


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
        else:                
            if len(section_sents) != 0 and section_sents[0] != '':
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


def display_data(data):
    sections = {
        "HIST": data.get("History", ""),
        "FIND": data.get("Findings", ""),
        "IMPR": data.get("Impression", "")
    }
    
    annotations = data.get('annotations', [])

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

    return sections, dfs, annotations


# if 'reviewer_name' not in st.session_state or not st.session_state.reviewer_name:
#     st.session_state.reviewer_name = st.text_input("Please enter your name for feedback:")

# Check if 'reviewer_name' is already in the session state
if 'reviewer_name' not in st.session_state:
    st.session_state.reviewer_name = ''

# If reviewer_name is empty, prompt the user to enter their name
# instruction_placeholder = st.empty()

if not st.session_state.reviewer_name:
    col1, col2 = st.columns(2)

    st.session_state.reviewer_name = st.text_input("Please enter your name to start feedback!! :muscle:")
    with col1:
        with st.expander("한국어 안내", expanded=False):
            st.write("""
            ## 소개
            이 앱은 GPT-4를 통한 entity-relation-attribute 추출 결과에 대한 피드백을 위한 도구입니다. 
            리뷰어가 피드백을 제공할 총 데이터는 평균 10.07개의 study sequence를 갖는 293명의 환자로부터 얻어진 3,269개의 리포트입니다. 최종 완료된 리뷰는 테스트 세트로 사용될 예정입니다.
            
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
            This app serves as a tool for providing feedback on the entity-relation-attribute extraction results via GPT-4. 
            Reviewers will work with a total of 3,269 reports from 293 patients, each with an average of 10.07 study sequences. The finalized reviews are intended for use in test set.

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

    # Initialize session_state if it doesn't exist
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
        
    else:
        # 이전에 저장한 피드백이 있다면 불러옴
        previous_feedback = {}#load_feedback(selected_patient, selected_display_name, drive_service, find_top_folder(drive_service))
        # print("previous_feedback", previous_feedback)

    # Update last_selected_file in session_state
    st.session_state.last_selected_file = selected_file

    # Load and display selected JSON data
    data = load_json(selected_file)
    sections, dfs, annotations = display_data(data)

    # Get statistics    
    present_sections, sent_stats, cat_stats, norm_ent_stats, missing_sents = get_statistics(data, dfs)

    # 파일 통계 섹션 시작
    # 전체 개수를 계산 (선택 사항)
    total_missing = sum(len(value) for value in missing_sents.values())

    with st.expander(f"**Show File Statistics: {total_missing} Missing Sents**"):
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
        count_per_key = {key: len(value) for key, value in missing_sents.items()}
        st.write(f"{total_missing} Missing Sents")
        for sec, sents in missing_sents.items():
            st.write(f"  - {sec} ({count_per_key[sec]}): {', '.join(sents)}")
    
    feedback_data = {}
    correct_rows = {}
    # additional_feedback_count = {}  # Commented this out
    feedback_columns = ['include', 'delete', 'modify', 'opinion']
    desired_order = ['ent', 'cat', 'exist', 'rel', 'attr', 'sent']

    example_text = """For example: {ent: endotracheal tube|tube,
            cat: DEV,
            exist: DP|is,
            loc: upper margin of the clavicles,
            carina,
            appr: size|45 mm
            }
            """
    for sec, content in sections.items():
        feedback_data[sec] = {}
        correct_rows[sec] = {}
        st.write("")
        # st.write(f"**{sec}:** {content}")
        st.markdown(f" <span style='font-size: 2em;'> :clipboard: {sec}: </span> <span style='font-size: 1.2em;'> {content}</span>", unsafe_allow_html=True)

        current_df = dfs[sec]
        columns_to_drop = ["sec", "sent_idx"]
        columns_to_drop = [col for col in columns_to_drop if col in current_df.columns]
                
        # if columns_to_drop:
        filtered_df = current_df.drop(columns=columns_to_drop)
                
        if len(filtered_df) == 0:            
            st.write(f"No annotations.")
            # sec에 해당하는 키를 동적으로 초기화
            st.session_state.row_count_state.setdefault(sec, 0)

            # 'Add Row'와 'Remove Row' 버튼을 위한 컬럼
            col_add_remove_submit = st.columns([1, 1, 2])  # 가중치를 사용하여 'Submit Feedback' 버튼을 가장 오른쪽에 크게 만듭니다.

            # "Add Row" 버튼
            if col_add_remove_submit[0].button(f"Add for {sec} section", key=f"{sec}_add_row"):
                st.session_state.row_count_state[sec] += 1
                
            # "Remove Row" 버튼
            if col_add_remove_submit[1].button(f"Remove", key=f"{sec}_remove_row"):
                if st.session_state.row_count_state[sec] > 0:  # 행 수가 1 이상일 경우만 제거
                    st.session_state.row_count_state[sec] -= 1
           
            # 텍스트 박스를 동적으로 생성
            for i in range(st.session_state.row_count_state[sec]):
                feedback_data[sec][str(i)] = st.text_area(f"Additional feedback.", 
                                                           value=example_text,  # 기본 텍스트를 설정
                                                          key=f"{sec}_feedback_for_row_{i+1}")

            # print("11 feedback_data", feedback_data)
            # input("STOP!")  

            if previous_feedback:
                annotations_list = previous_feedback.get('feedback', [])
                # print("annotations_list", annotations_list)
                # input("SOTP!!")                
                
                prev_sec_list = [item for item in annotations_list if item['sec'] == sec]
                reordered_annotations = []
                
                print("prev_sec_list", prev_sec_list)
                
                if len(prev_sec_list) != 0:    
                    for prev_annot in prev_sec_list:
                        reordered_dict = {k: prev_annot[k] for k in desired_order if k in prev_annot}
                        reordered_annotations.append(reordered_dict)
                    
                    st.write(":sunglasses: Previous Results:")
                    for a in reordered_annotations:
                        st.write(f"  - {a}")

            
        else:
            with st.expander(f"**{sec} DataFrame**"):
                st.write(filtered_df)                       
            
            # additional_feedback_count[sec] = {}  # Commented this out
            sec_list = [item for item in annotations if item['sec'] == sec]
            
            if previous_feedback:
                annotations_list = previous_feedback.get('feedback', [])
                prev_sec_list = [item for item in annotations_list if item['sec'] == sec]
                reordered_annotations = []
                
                if len(prev_sec_list) != 0:    
                    for prev_annot in prev_sec_list:
                        reordered_dict = {k: prev_annot[k] for k in desired_order if k in prev_annot}
                        reordered_annotations.append(reordered_dict)
                    
                    for a in reordered_annotations:
                        st.write(":sunglasses: Previous Results:")
                        st.write(f"  - {a}")
                else:
                    error_message = f"No feedback found for this section."
                    st.error(error_message, icon="🚨")


            with st.expander(f"**Review {sec}**"):
                for index, row in current_df.iterrows():
                    # print("current_dfcurrent_df", current_df)
                    # print(f"{index}index and {current_df[index]}")
                    reordered_annotations = []
                    sent_only = []
                    for annotation in sec_list:
                        reordered_dict = {k: annotation[k] for k in ['ent', 'cat', 'exist', 'rel', 'attr'] if k in annotation}
                        _, new_dict2 = extract_key_values(reordered_dict)
                        reordered_annotations.append(new_dict2)
                        sent_dict = annotation['sent']
                        sent_only.append(sent_dict)
                    
                    line_show = str(reordered_annotations[index])
                    line_show = line_show.replace("'", "")                    
                    
                    st.write(f"  - Row {index}: {sent_only[index]}")
                    st.write(line_show)
                    
                    feedback_data[sec][index] = {}
                    correct_rows[sec][index] = {}

                    # Initialize session_state for the section and index
                    if sec not in st.session_state.additional_feedback_count:
                        st.session_state.additional_feedback_count[sec] = {}
                    st.session_state.additional_feedback_count[sec].setdefault(index, {col: 1 for col in feedback_columns})

                    col_list = st.columns(len(feedback_columns) + 1)
                    correct_key = f"{sec}_correct_{index}"
                    overall_correct = col_list[0].checkbox(f":thumbsup:", 
                                                            value=st.session_state.checkbox_states.get(correct_key, False),  # 상태 가져오기
                                                            key=correct_key)
                    st.session_state.checkbox_states[correct_key] = overall_correct


                    if overall_correct:
                        feedback_data[sec][index] = 'all_correct'
                    else:
                        for col_num, col_name in enumerate(feedback_columns):
                            nested_col_list = col_list[col_num + 1].columns(3)
                            correct = nested_col_list[0].text(f"{col_name}")
                            button_col1, button_col2 = nested_col_list[1], nested_col_list[2]

                            if button_col1.button(f":heavy_plus_sign:", key=f"{sec}_add_more_{index}_{col_name}"):
                                st.session_state.additional_feedback_count[sec][index][col_name] += 1

                            if button_col2.button(f":heavy_minus_sign:", key=f"{sec}_remove_{index}_{col_name}"):
                                if st.session_state.additional_feedback_count[sec][index][col_name] > 1:
                                    st.session_state.additional_feedback_count[sec][index][col_name] -= 1

                            # Dynamically generate additional feedback text boxes
                            for i in range(2, st.session_state.additional_feedback_count[sec][index][col_name] + 1):
                                additional_feedback_key = f"{sec}_feedback_{index}_{col_name}_{i-1}"
                                additional_feedback = col_list[col_num + 1].text_input(f"{col_name} {i-1}", key=additional_feedback_key)
                                feedback_data[sec][index][f"{col_name}_{i-1}"] = additional_feedback

                # # 'Submit Feedback' 버튼
                if st.button('Submit Feedback', key=f"unique_key_for_submit_button_{sec}"):
                    save_feedback(selected_patient, selected_display_name, feedback_data, feedback_columns)
                    # st.experimental_rerun()
                    now_feedback = load_feedback(selected_patient, selected_display_name, drive_service, find_top_folder(drive_service))

                    st.write(":point_right: Updated Results:")
                    
                    # If now_feedback is already a Python dict, no need for json.loads
                    feedback_list = now_feedback.get('feedback', [])                   
                    reordered_annotations = []

                    sec_list = [a for a in feedback_list if a['sec'] == sec]
                    
                    for annotation in sec_list:
                        reordered_dict = {k: annotation[k] for k in desired_order if k in annotation}
                        reordered_annotations.append(reordered_dict)
                    
                    for annotation in reordered_annotations:
                        st.write(f"  - {annotation}")                    
                else:
                    st.write("No feedback found for this section.")

            # sec에 해당하는 키를 동적으로 초기화
            st.session_state.row_count_state.setdefault(sec, 0)

            # 'Add Row'와 'Remove Row' 버튼을 위한 컬럼
            col_add_remove_submit = st.columns([1, 1, 2])  # 가중치를 사용하여 'Submit Feedback' 버튼을 가장 오른쪽에 크게 만듭니다.

            # "Add Row" 버튼
            if col_add_remove_submit[0].button(f"Add for {sec} section", key=f"{sec}_add_row"):
                st.session_state.row_count_state[sec] += 1

            # "Remove Row" 버튼
            if col_add_remove_submit[1].button(f"Remove", key=f"{sec}_remove_row"):
                if st.session_state.row_count_state[sec] > 0:  # 행 수가 1 이상일 경우만 제거
                    st.session_state.row_count_state[sec] -= 1

            # 텍스트 박스를 동적으로 생성
            for i in range(st.session_state.row_count_state[sec]):
                st.text_area(f"Additional feedback.", 
                 value=example_text,  # 기본 텍스트를 설정
                 key=f"{sec}_feedback_for_row_{i+1}")

        
        # {ent: endotracheal tube|tube, cat: DEV, exist: DP|is, loc: upper margin of the clavicles, carina, appr: size|45 mm}
        
        
        # # 'Submit Feedback for whole' 버튼
        if col_add_remove_submit[2].button('Submit', key=f"additional_submit_button_{sec}"):
            save_feedback(selected_patient, selected_display_name, feedback_data, feedback_columns)
            # st.experimental_rerun()
            now_feedback = load_feedback(selected_patient, selected_display_name, drive_service, find_top_folder(drive_service))

            st.write(":pushpin: Newely added Results:")
            
            # If now_feedback is already a Python dict, no need for json.loads
            feedback_list = now_feedback.get('feedback', [])
            reordered_annotations = []

            sec_list = [a for a in feedback_list if a['sec'] == sec]           
            
            for annotation in sec_list:
                st.write(f":heavy_plus_sign: {annotation}")
            

        else:
            st.write("No feedback found for this section.")