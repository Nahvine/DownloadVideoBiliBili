import json
import os
import platform
import re
import shutil

def ms_to_srt(ms_input):
    """
    Convert microseconds to SRT timestamp format: HH:mm:ss,ms
    """
    ts = int(ms_input)
    ms = (ts // 1000) % 1000
    seconds = (ts // 1000000) % 60
    minutes = (ts // (1000000 * 60)) % 60
    hours = (ts // (1000000 * 60 * 60))
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"

def extract_srt(json_path, output_path):
    """
    Parses CapCut project JSON and generates an SRT file.
    """
    try:
        if not os.path.exists(json_path):
            return False, f"File not found: {json_path}"
            
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        materials = data.get('materials', {})
        texts = materials.get('texts', [])
        tracks = data.get('tracks', [])
        
        text_info = {}
        for item in texts:
            content = item.get('content', '')
            content = re.sub(r'<.*?>', '', content)
            content = content.replace('[', '').replace(']', '')
            
            try:
                content_v3 = json.loads(item.get('content', ''))
                if isinstance(content_v3, dict) and 'text' in content_v3:
                    content = content_v3['text']
            except:
                pass
                
            text_info[item.get('id')] = content
            
        subtitles = []
        for track in tracks:
            segments = track.get('segments', [])
            for seg in segments:
                mat_id = seg.get('material_id')
                if mat_id in text_info:
                    start = seg.get('target_timerange', {}).get('start', 0)
                    duration = seg.get('target_timerange', {}).get('duration', 0)
                    content = text_info[mat_id]
                    
                    if content.strip():
                        subtitles.append({
                            'start': start,
                            'end': start + duration,
                            'content': content
                        })
        
        subtitles.sort(key=lambda x: x['start'])
        
        srt_lines = []
        for i, sub in enumerate(subtitles, 1):
            srt_lines.append(str(i))
            start_str = ms_to_srt(sub['start'])
            end_str = ms_to_srt(sub['end'])
            srt_lines.append(f"{start_str} --> {end_str}")
            srt_lines.append(sub['content'])
            srt_lines.append("")
            
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(srt_lines))
            
        return True, len(subtitles)
    except Exception as e:
        return False, str(e)

def uppercase_draft(json_path):
    """
    Converts all captions in the project to uppercase. Modifies the JSON file in-place with a backup.
    """
    try:
        if not os.path.exists(json_path):
            return False, "File not found"
            
        # Create backup
        backup_path = json_path + ".bak"
        if not os.path.exists(backup_path): # Only backup if not already done manually
            shutil.copy2(json_path, backup_path)
            
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        texts = data.get('materials', {}).get('texts', [])
        modified = 0
        for item in texts:
            original_content = item.get('content', '')
            
            # Complex content (JSON encoded)
            try:
                content_v3 = json.loads(original_content)
                if isinstance(content_v3, dict) and 'text' in content_v3:
                    content_v3['text'] = content_v3['text'].upper()
                    item['content'] = json.dumps(content_v3, ensure_ascii=False)
                    modified += 1
                    continue
            except:
                pass
            
            # Simple content (HTML/Style tags)
            # Find the text between tags or just uppercase everything if no tags
            # The JS logic: replace tags, find index, uppercase, rebuild.
            clean_text = re.sub(r'<.*?>', '', original_content).replace('[', '').replace(']', '')
            if clean_text:
                upper_text = clean_text.upper()
                # Use regex to replace only the text part, preserving tags
                # This is safer than the JS substring method
                new_content = original_content.replace(clean_text, upper_text)
                if new_content != original_content:
                    item['content'] = new_content
                    modified += 1
                    
        if modified > 0:
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            return True, modified
        return True, 0
    except Exception as e:
        return False, str(e)

def get_recent_projects():
    """
    Returns a list of recent projects sorted by modification time.
    """
    root_path = get_default_capcut_path()
    meta_path = os.path.join(root_path, "root_meta_info.json")
    
    if not os.path.exists(meta_path):
        return []
        
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
            
        drafts = meta.get('all_draft_store', [])
        # Sort by tm_draft_modified (descending)
        drafts.sort(key=lambda x: x.get('tm_draft_modified', 0), reverse=True)
        return drafts
    except:
        return []

def get_default_capcut_path():
    """
    Returns the standard CapCut draft path for the current OS.
    """
    curr_os = platform.system()
    home = os.path.expanduser("~")
    
    if curr_os == "Darwin": # macOS
        return os.path.join(home, "Movies/CapCut/User Data/Projects/com.lveditor.draft")
    elif curr_os == "Windows":
        return os.path.join(os.environ.get('LOCALAPPDATA', ''), "CapCut/User Data/Projects/com.lveditor.draft")
    else:
        return home
