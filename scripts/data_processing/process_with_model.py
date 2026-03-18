import sys
import re
import os
from openai import OpenAI
import PyPDF2  # 用于读取PDF

# --- PDF读取功能 (不变) ---
def get_pdf_text(pdf_path):
    """
    打开一个PDF文件并提取所有页面的文本。
    """
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

# --- [新] 从 TXT 文件读取 durl ---
def get_durl_from_txt(txt_path):
    """
    从指定的 txt 文件中读取第二行作为 durl。
    """
    print(f"正在从 TXT 文件读取 durl: {txt_path}...")
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            if len(lines) >= 2:
                durl = lines[1].strip() # 第二行，并去除首尾空白
                if durl: # 确保第二行不是空的
                    print(f"成功读取 durl: {durl[:70]}...") # 只打印部分URL
                    return durl
                else:
                    print(f"错误: TXT 文件 '{txt_path}' 的第二行为空。请确保已手动添加 durl。")
                    return None
            else:
                print(f"错误: TXT 文件 '{txt_path}' 不足两行。请确保已手动添加 durl。")
                return None
    except FileNotFoundError:
        print(f"错误: 找不到 TXT 文件 {txt_path}")
        return None
    except Exception as e:
        print(f"读取 TXT 文件时发生错误: {e}")
        return None

# --- 主函数 (不再分块) ---
def main():
    
    # --- 1. 配置参数 ---
    pdf_path = r"pdfdata/孙悟空/02006025_安天会.pdf" # 确保路径正确
    txt_dir = "txtdata\孙悟空" # 指定包含 durl 的 txt 文件所在的目录
    api_key = "sk-uNTaHplU891bjK5tF67eBf24285f4b8689F23c734dF9C9Ea" # <--- 已使用您文件中的Key
    
    # 从 PDF 路径推断 TXT 文件名
    base_name = os.path.basename(pdf_path)
    txt_filename = base_name.replace('.pdf', '.txt')
    txt_path = os.path.join(txt_dir, txt_filename)
    
    # 从 PDF 路径推断剧本名称 (用于输出文件名)
    script_name = "未知剧本"
    match = re.search(r'\d+_(.*)\.pdf', base_name)
    if match:
        script_name = match.group(1)
    # ---------------------

    print(f"配置加载: \nPDF路径: {pdf_path}\nTXT路径: {txt_path}")
    
    # 2. 提取PDF文本
    original_script_text = get_pdf_text(pdf_path)
    if not original_script_text:
        print("无法处理PDF，程序退出。")
        sys.exit(1)

    # 3. 从 TXT 文件读取 durl
    video_url = get_durl_from_txt(txt_path)
    if not video_url:
        print("无法获取 durl，程序退出。")
        sys.exit(1)

    # 4. 设置API客户端
    client = OpenAI(
      base_url="https://api.shubiaobiao.cn/v1/",
      api_key=api_key,
    )
    
    if not api_key:
         print("\n*** 错误: 请先在脚本中填入 'api_key' 变量! ***")
         sys.exit(1)

    # 5. 构建单次请求的提示 (不再分块)
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
    三.输出格式:\
    标题：明确标注剧本名称(如《XX》选段剧本)\
    剧情大纲：大致描述剧情，给出剧情发展流程\
    人物介绍：设置 “出场人物及脸谱、妆容介绍” 章节，分点清晰描述每个角色​\
    正文：按场次划分剧情，每场次包含 “场景设定”“角色动作”“唱词， / 念白”“心理情绪” 四大要素，标注清晰、逻辑连贯，在角色做出每一个动作后具体标记出来，嵌入在唱词/台词当中,所有描述均需要采用京剧中的特色表演形式进行描述\
    example:\
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
"
    user_content = [
        {
            "type": "video_url",            
            "video_url": {"url": video_url} # 使用从 TXT 读取的 durl
        },
        {
            "type": "text",
            "text": f"这是要增强的完整原版剧本：\n\n---START SCRIPT---\n{original_script_text}\n---END SCRIPT---"
        },
        {
            "type": "text",
            "text": "请你严格按照系统提示的要求，以上述“原版剧本”为基础，结合这段视频内容，生成一份包含详细动作、心理活动、专业标注的完整京剧剧本。"
        }
    ]

    print("\n正在向模型发送【完整】请求，请稍候... (这可能需要几分钟时间)")

    try:
        # 6. 执行单次 API 调用
        completion = client.chat.completions.create(
          extra_body={},
          model="gemini-2.5-pro",
          messages=[
              {"role": "system", "content": system_prompt},
              {"role": "user", "content": user_content}
          ],
          # timeout=300.0 # [可选] 延长超时时间
        )
        
        output_filename = f"{script_name}_enhanced_script_FULL.txt"
        with open(output_filename, 'w', encoding="utf-8") as file:
            file.write(completion.choices[0].message.content)
        
        print(f"处理完成！增强后的【完整】剧本已保存到 {output_filename}")

    except Exception as e:
        print(f"调用API时发生错误: {e}")


if __name__ == "__main__":
    main()