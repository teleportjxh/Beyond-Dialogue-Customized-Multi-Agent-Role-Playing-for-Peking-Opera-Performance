import sys
import re
import os
from openai import OpenAI
import PyPDF2  # 用于读取PDF
import time # 用于添加延迟

# --- PDF读取功能 (不变) ---
def get_pdf_text(pdf_path):
    """打开一个PDF文件并提取所有页面的文本。"""
    print(f"正在读取PDF文件: {pdf_path}...")
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text
            
            if not text:
                print(f"警告: 未能从 {pdf_path} 中提取到任何文本。请检查PDF是否为图片扫描版。")
                return None
            
            print("PDF文本内容读取成功。")
            return text
    except FileNotFoundError:
        print(f"错误: 找不到文件 {pdf_path}")
        return None
    except Exception as e:
        print(f"读取PDF时发生错误: {e}")
        return None

# --- 从 TXT 文件读取 durl (不变) ---
def get_durl_from_txt(txt_path):
    """从指定的 txt 文件中读取第二行作为 durl。"""
    print(f"正在从 TXT 文件读取 durl: {txt_path}...")
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) >= 2:
                durl = lines[1].strip() # 第二行，并去除首尾空白
                if durl and durl.startswith('http'): # 确保第二行是有效的 URL
                    print(f"成功读取 durl: {durl[:70]}...") # 只打印部分URL
                    return durl
                else:
                    print(f"错误: TXT 文件 '{txt_path}' 的第二行不是有效的 durl。请确保已手动添加 durl。跳过...")
                    return None
            else:
                print(f"错误: TXT 文件 '{txt_path}' 不足两行。请确保已手动添加 durl。跳过...")
                return None
    except FileNotFoundError:
        print(f"错误: 找不到对应的 TXT 文件 {txt_path}。跳过...")
        return None
    except Exception as e:
        print(f"读取 TXT 文件时发生错误: {e}。跳过...")
        return None

# --- [新] 单个文件处理函数 ---
def process_single_file(pdf_path, txt_path, client, output_dir="data"):
    """处理单个 PDF 和 TXT 文件对，调用 API 并保存结果。"""
    try:
        # 1. 提取PDF文本
        original_script_text = get_pdf_text(pdf_path)
        if not original_script_text:
            return False # 读取 PDF 失败

        # 2. 从 TXT 文件读取 durl
        video_url = get_durl_from_txt(txt_path)
        if not video_url:
            return False # 读取 durl 失败

        # 3. 从 PDF 路径推断剧本名称 (用于输出文件名)
        base_name = os.path.basename(pdf_path)
        script_name = "未知剧本"
        match = re.search(r'([\d_]*)(.*)\.pdf', base_name)
        if match and match.group(2):
             script_name = match.group(2)
             if script_name.startswith('_'): script_name = script_name[1:]
        
        # 4. 构建 API 请求
        system_prompt = "你是专业京剧剧本创作专家，需严格按照用户提供的视频和参考剧本理解转化剧本，确保格式规范、内容贴合京剧艺术特点,且描述均使用文字。请你基于输入的京剧视频内容和参考剧本，运用京剧艺术专业知识，完善京剧剧本，具体要求如下：\
    一.核心任务\
    1. 精准解析视频中的剧情脉络、角色设定、服饰妆容细节及动作表现\
    2. 遵循京剧剧本的传统结构（含场次划分、唱词/念白设计、动作指引等）\
    3. 角色动作标注用[]符号包裹，心理与情绪标注用()符号包裹\
    4. 明确区分唱词与念白，唱词需符合京剧唱腔韵律（如西皮、二黄）,切换角色时需要在前标注角色姓名。\
    二.剧本内容标注要求\
    1.人物介绍规范:列出视频中所有出场角色，标注每个角色的京剧行当,详细描述每个角色的脸谱特征及象征意义,根据视频内容补充妆容与服饰细节,​面部妆容的特殊处理（如老生的淡赭色额妆、旦角的贴片妆容等）​头戴盔头（如帅盔、翎子、方巾等）、身着行头（如靠、褶子、蟒袍等）及配饰（如玉带、虎头靴、马鞭等）的具体样式与象征意义\
    2.角色动作标注：根据视频内容在角色做出动作后描述角色的动作,用[]符号包裹角色的手势、肢体动作、身段\
    3.剧本台词标注:参考剧本仅用于参考人物说话顺序以及腔调\
    4.严格使用“原版剧本”中提供的台词和唱词，不要自行编撰。你的任务是补充动作和情绪，而不是改写台词。\
    三.输出格式:\
    标题：明确标注剧本名称(如《XX》选段剧本)\
    剧情大纲：大致描述剧情，给出剧情发展流程\
    人物介绍：设置 “出场人物及脸谱、妆容介绍” 章节，分点清晰描述每个角色​\
    正文：按场次划分剧情，每场次包含 “场景设定”“角色动作”“唱词， / 念白”“心理情绪” 四大要素，标注清晰、逻辑连贯，在角色做出每一个动作后具体标记出来，嵌入在唱词/台词当中,所有描述均需要采用京剧中的特色表演形式进行描述\
    example1:\
    剧目:《空城计》\
    剧情大纲:三国时期，马谡违背诸葛亮 “靠山近水扎营” 的叮嘱，执意将营寨设于山头，遭司马懿大军围困后失守街亭；司马懿随即率领四十万大军直逼西城，而此时诸葛亮驻守的西城兵力空虚，无法迎战也难以撤离，遂决定设 “空城计” 应对 他命人打开西城四门，让老军打扫街道，自己则携二名琴童登上城楼，焚香抚琴、神态自若。司马懿兵临城下，见此情景心生疑虑，又听闻诸葛亮琴声安闲有序，断定城内必有埋伏，不顾其子司马昭 “城内是空城” 的提醒，下令大军后退四十余里。诸葛亮借此机会调回赵云等将领驰援西城，待司马懿察觉西城实为空城、欲复夺时，赵云已率军赶到，司马懿见状只能领兵撤退，诸葛亮成功化解西城危机，事后也决意待马谡回营后以正军情。\
    出场人物及脸谱、妆容介绍:\
    1.诸葛亮\
    行当:老生(文官类)\
    脸谱特征:面部为传统“俊扮”——无特殊脸谱，以素净为主，象征智慧与正直\
    额头中央有一抹红晕（“额色”），代表忠义与谋略之气。\
    眉形细长上扬，眼神锐利，突出其沉稳睿智的气质。\
    妆容细节:长须垂胸，黑白相间，象征年迈而德高望重。\
    脸部施淡赭色底妆，唇色微红，鼻梁挺拔，整体轮廓清晰。\
    服饰与头饰:头戴“方巾”式乌纱帽，帽顶有绣金纹饰，象征文官身份。\
    身着紫色蟒袍，外披黑色绣云纹大袖披风，肩部饰绿色云龙纹，象征尊贵与权谋。\
    手持白色鹅毛扇，象征其智者身份。\
    腰系玉带，脚穿黑靴，整体造型庄重肃穆。\
    第一场：城楼抚琴·智定空城\
    场景设定:舞台背景为模拟古城墙，灰砖砌成，顶部有垛口。城墙中央设一木桌，桌上置古琴、茶壶、香炉等道具。天空为纯蓝色幕布，象征晴空万里。诸葛亮居中坐于桌后，两侧各立一名琴童，静候命令。\
    [开场]\
    诸葛亮（唱）:\
    我本是卧龙冈散淡的人\
    [轻摇羽扇，目光远眺，神情悠然自得]\
    (昔日隐居山林，不问世事，如今却身负重任，此情此景，不禁追忆往昔)\
    凭阴阳如反掌保定乾坤\
    [羽扇收回至胸前，双手轻握扇柄（左手辅助右手），向城外作揖，目光转向城外，眼神坚定]\
    (天机在握，运筹帷幄之中，决胜千里之外)\
    先帝爷下南阳御驾三请\
    [右手持扇指向台左方向(象征南阳方向),双手和一,向城外再三作揖后, 放下双手,轻晃羽扇,头部微微颔首]\
    (感念刘备三顾之情)\
    算就了汉家的业鼎足三分\
    [头部微微颔首,左手呈单指状轻晃] \
    (感慨天下局势已定，三分归晋，但使命未竟)\
    官封到武乡侯执掌帅印\
    [头部微微颔首,右手手持羽扇侧轻摇，头部微扬，目光平视前方，神态庄重]\
    (虽位高权重，然责任更重，不可轻忽)\
    example2: \
    **诸葛亮** （唱）**[西皮慢板]**\
    想当初在隆中排分八卦， [左手轻抚胸前长须，右手羽扇轻摇，目光远眺，神情悠然] (追忆往昔隐居南阳的闲适岁月，与当下的军旅生涯形成对比)\
    闲无事听鸟音观看山花。 [踱步至台前，羽扇轻摇，作环视状，身段舒展]\
    驾孤舟游廊院许多潇洒， [以扇为桨，作驾舟之态，脚步轻盈，面带微笑]\
    甚比那红尘中富贵荣华。 [羽扇收回胸前，微微摇头，流露出对功名富贵的淡泊]\
    先帝爷三请我才把山下， [收扇，双手合于胸前，向台左方向微一拱手，面露感念之色] (感念先帝刘备三顾茅庐的知遇之恩)\
    论阴阳如反掌扶保汉家。 [右手伸出，作翻掌之势，眼神坚定，充满自信]\
    这几日未出兵未把仗打， [转身面向台内，眉头微蹙，羽扇轻点左手手心] (思虑当前战局，心情由闲适转为凝重)\
    司马懿他笑我必然怕他。 [嘴角露出一丝不易察觉的冷笑，羽扇轻顿]\
    选一个黄道日发动人马， [目光变得锐利，羽扇向前一指，显露决断之意]\
    定中原扫北魏归复汉家。 [右手持扇有力地一挥，迈步走向帅座，气势沉稳]\
    example3:\
    **童儿** (白) 什么人？\
\
    **旗牌** (白) 烦劳通禀：献图人求见。\
\
    **童儿** (白) 候着。\
    [童儿转身向内。]\
    (白) 启禀丞相：献图人求见。\
\
    **诸葛亮** (白) 传。\
    [声音平稳，不露声色。]\
\
    **童儿** (白) 献图人，丞相传进。\
\
    **旗牌** (白) 是，是。\
    [旗牌快步入帐，至案前行礼。]\
    (白) 参见丞相。\
    "
        user_content = [
            {"type": "video_url", "video_url": {"url": video_url}},
            {"type": "text", "text": f"这是要增强的完整原版剧本：\n\n---START SCRIPT---\n{original_script_text}\n---END SCRIPT---"},
            {"type": "text", "text": "请你严格按照系统提示的要求，台词内容参照原剧本，不需要再进行修改，结合这段视频内容，生成一份包含详细动作、心理活动、专业标注的完整京剧剧本(整个剧本全部标注，不要有遗漏)。"}
        ]

        print(f"\n正在向模型发送请求 (处理 {base_name})，请稍候...")
        
        # 5. 执行 API 调用
        completion = client.chat.completions.create(
          extra_body={},
          model="gemini-2.5-pro", 
          messages=[
              {"role": "system", "content": system_prompt},
              {"role": "user", "content": user_content}
          ],
          temperature=0.1, 
        )
        
        # 6. 保存结果到 output_dir
        output_base_filename = base_name.replace('.pdf', '') 
        output_filename = f"{output_base_filename}_enhanced_script.txt"
        output_path = os.path.join(output_dir, output_filename)
        
        with open(output_path, 'w', encoding="utf-8") as file:
            file.write(completion.choices[0].message.content)
        
        print(f"处理完成！增强后的剧本已保存到 {output_path}")
        return True

    except Exception as e:
        print(f"处理文件 '{os.path.basename(pdf_path)}' 时发生错误: {e}")
        return False

# --- 主程序 (批量处理，新增跳过已处理文件功能) ---
def main():
    
    # --- 1. 配置参数 ---
    character = "赵匡胤" 
    pdf_input_dir = f"./pdfdata/{character}"   # 自动变为 "./pdfdata/孙悟空"
    txt_input_dir = f"./txtdata/{character}"   # 自动变为 "./txtdata/孙悟空"
    output_dir = f"./enhanced_script/{character}"         # 自动变为 "./enhanced_script/孙悟空"
    api_key = "sk-uNTaHplU891bjK5tF67eBf24285f4b8689F23c734dF9C9Ea" # <--- 您的 API Key
    api_base_url = "https://api.shubiaobiao.cn/v1/" # <--- 您的 API Base URL
    
    # 可选：API 请求之间的延迟（秒），防止请求过于频繁
    delay_between_requests = 1 
    # ---------------------

    print(f"开始批量处理 PDF 文件夹: {pdf_input_dir}")
    print(f"TXT 输入目录: {txt_input_dir}")
    print(f"最终输出目录: {output_dir}")

    if not os.path.isdir(pdf_input_dir):
        print(f"错误：PDF 输入目录 '{pdf_input_dir}' 不存在或不是一个文件夹。")
        sys.exit(1)
    if not os.path.isdir(txt_input_dir):
        print(f"错误：TXT 输入目录 '{txt_input_dir}' 不存在或不是一个文件夹。")
        sys.exit(1)
        
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 设置API客户端
    client = OpenAI(
      base_url=api_base_url,
      api_key=api_key,
    )
    if not api_key:
         print("\n*** 错误: 请先在脚本中填入 'api_key' 变量! ***")
         sys.exit(1)

    processed_count = 0
    skipped_count = 0  # 包含“已处理跳过”和“错误跳过”
    already_processed_count = 0  # 新增：单独统计“已处理跳过”的数量

    # 遍历 PDF 输入目录下的所有文件
    pdf_files = [f for f in os.listdir(pdf_input_dir) if f.lower().endswith(".pdf")]
    total_files = len(pdf_files)
    print(f"在 '{pdf_input_dir}' 中找到 {total_files} 个 PDF 文件。")

    for i, filename in enumerate(pdf_files):
        pdf_filepath = os.path.join(pdf_input_dir, filename)
        txt_filename = filename.replace('.pdf', '.txt')
        txt_filepath = os.path.join(txt_input_dir, txt_filename)
        
        # 关键修改：检查输出文件是否已存在
        output_base_filename = filename.replace('.pdf', '')
        output_filename = f"{output_base_filename}_enhanced_script.txt"
        output_path = os.path.join(output_dir, output_filename)
        
        print(f"\n--- 正在处理 ({i+1}/{total_files}): {filename} ---")
        
        # 如果输出文件已存在，则直接跳过
        if os.path.exists(output_path):
            print(f"检测到该文件已处理（{output_path}），自动跳过...")
            already_processed_count += 1
            skipped_count += 1
            continue
        
        # 检查对应的 TXT 文件是否存在
        if not os.path.exists(txt_filepath):
            print(f"错误: 找不到对应的 TXT 文件 {txt_filepath}。跳过...")
            skipped_count += 1
            continue # 跳到下一个 PDF 文件

        # 处理单个文件
        success = process_single_file(pdf_filepath, txt_filepath, client, output_dir)
        
        if success:
            processed_count += 1
        else:
            skipped_count += 1
            
        # 在两次 API 请求之间添加延迟
        if delay_between_requests > 0 and i < total_files - 1:
            print(f"等待 {delay_between_requests} 秒...")
            time.sleep(delay_between_requests)


    print(f"\n--- 批量处理完成 ---")
    print(f"成功处理新文件数: {processed_count}")
    print(f"已处理并跳过的文件数: {already_processed_count}")  # 新增统计
    print(f"因错误跳过的文件数: {skipped_count - already_processed_count}")  # 计算错误跳过数
    print(f"总跳过文件数: {skipped_count}")

if __name__ == "__main__":
    main()