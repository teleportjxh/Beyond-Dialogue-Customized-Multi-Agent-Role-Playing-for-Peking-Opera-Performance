import sys
import re
import os
from bilibili_api import search as bili_search, sync as bili_sync

def search_and_save_bili_url(pdf_filename, output_dir="txtdata"):
    """
    根据 PDF 文件名搜索 Bilibili，并将第一个结果的网页 URL 保存到 txt 文件。
    """
    try:
        # 1. 从 PDF 文件名提取剧本名称 (去除数字和下划线)
        base_name = os.path.basename(pdf_filename)
        match = re.search(r'\d+_(.*)\.pdf', base_name)
        if not match:
            print(f"错误：无法从文件名 '{base_name}' 提取剧本名称。")
            return False
        script_name = match.group(1)
        print(f"从 '{base_name}' 提取到剧本名称: '{script_name}'")

        # 2. 搜索 Bilibili
        query = f"{script_name} 京剧" 
        print(f"正在搜索 Bilibili: '{query}'...")
        
        search_result = bili_sync(
            bili_search.search_by_type(
                keyword=query,
                search_type=bili_search.SearchObjectType.VIDEO
            )
        )
        
        if not (search_result and search_result.get('result')):
            print("Bilibili 未找到相关视频。")
            return False

        # 3. 获取第一个视频的网页 URL
        first_video = search_result['result'][0]
        bvid = first_video.get('bvid')
        if not bvid:
            print("Bilibili 搜索结果中未找到 bvid。")
            return False
            
        video_title = re.sub(r'<.*?>', '', first_video.get('title'))
        web_url = f"https://www.bilibili.com/video/{bvid}"
        print(f"Bilibili 搜索成功: 找到 '{video_title}' ({web_url})")

        # 4. 准备输出文件路径
        txt_filename = base_name.replace('.pdf', '.txt')
        output_path = os.path.join(output_dir, txt_filename)
        
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        # 5. 将网页 URL 写入 txt 文件 (覆盖写入)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(web_url + '\n') # 只写入网页 URL，并加一个换行符
            
        print(f"Bilibili 网页链接已保存到: {output_path}")
        return True

    except Exception as e:
        print(f"处理 '{pdf_filename}' 时发生错误: {e}")
        return False

# --- 主程序 ---
if __name__ == "__main__":
    # --- 配置 ---
    # 您可以修改这里来处理单个文件，或者之后改成遍历文件夹
    pdf_file_to_process = "pdfdata/01003011_斩黄袍.pdf" 
    # -----------

    search_and_save_bili_url(pdf_file_to_process)