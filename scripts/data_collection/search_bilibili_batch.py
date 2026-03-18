import sys
import re
import os
from bilibili_api import search as bili_search, sync as bili_sync

def search_and_save_bili_url(pdf_filename, output_dir="txtdata"):
    """
    根据 PDF 文件名搜索 Bilibili，并将第一个结果的网页 URL 保存到 txt 文件。
    (此函数与您提供的版本相同)
    """
    try:
        # 1. 从 PDF 文件名提取剧本名称 (去除数字和下划线)
        base_name = os.path.basename(pdf_filename)
        # 改进正则，允许纯数字或不含数字的文件名开头
        match = re.search(r'([\d_]*)(.*)\.pdf', base_name) 
        if not match or not match.group(2): # 确保匹配到非数字下划线部分
            print(f"错误：无法从文件名 '{base_name}' 提取剧本名称。跳过...")
            return False
        script_name = match.group(2)
        # 如果名称以"_"开头，去掉它
        if script_name.startswith('_'): 
            script_name = script_name[1:]

        print(f"从 '{base_name}' 提取到剧本名称: '{script_name}'")

        # 2. 搜索 Bilibili
        query = f"京剧《{script_name}》 " 
        print(f"正在搜索 Bilibili: '{query}'...")
        
        search_result = bili_sync(
            bili_search.search_by_type(
                keyword=query,
                search_type=bili_search.SearchObjectType.VIDEO,
                # 可选：限制结果数量，加快速度
                # page_size=1, 
                # page=1
            )
        )
        
        if not (search_result and search_result.get('result')):
            print(f"Bilibili 未找到 '{query}' 的相关视频。跳过...")
            return False

        # 3. 获取第一个视频的网页 URL
        first_video = search_result['result'][0]
        bvid = first_video.get('bvid')
        if not bvid:
            print("Bilibili 搜索结果中未找到 bvid。跳过...")
            return False
            
        video_title = re.sub(r'<.*?>', '', first_video.get('title'))
        web_url = f"https://www.bilibili.com/video/{bvid}"
        print(f"Bilibili 搜索成功: 找到 '{video_title}' ({web_url})")

        # 4. 准备输出文件路径 (使用原始 base_name 保证对应)
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

# --- 主程序 (批量处理) ---
if __name__ == "__main__":
    # --- 配置 ---
    pdf_input_dir = "pdfdata/赵匡胤"   # <--- 指定包含 PDF 文件的文件夹路径
    txt_output_dir = "txtdata/赵匡胤" # <--- 指定输出 TXT 文件的文件夹路径
    # -----------

    print(f"开始批量处理 PDF 文件夹: {pdf_input_dir}")
    print(f"TXT 输出目录: {txt_output_dir}")

    if not os.path.isdir(pdf_input_dir):
        print(f"错误：输入目录 '{pdf_input_dir}' 不存在或不是一个文件夹。")
        sys.exit(1)

    processed_count = 0
    skipped_count = 0

    # 遍历输入目录下的所有文件
    for filename in os.listdir(pdf_input_dir):
        if filename.lower().endswith(".pdf"):
            pdf_filepath = os.path.join(pdf_input_dir, filename)
            print(f"\n--- 正在处理: {pdf_filepath} ---")
            success = search_and_save_bili_url(pdf_filepath, txt_output_dir)
            if success:
                processed_count += 1
            else:
                skipped_count += 1
        else:
            # print(f"跳过非 PDF 文件: {filename}")
            pass # 保持安静，只处理 PDF

    print(f"\n--- 批量处理完成 ---")
    print(f"成功处理 PDF 文件数: {processed_count}")
    print(f"跳过/失败 PDF 文件数: {skipped_count}")