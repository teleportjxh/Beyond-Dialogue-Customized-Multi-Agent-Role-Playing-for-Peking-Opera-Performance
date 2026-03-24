"""
向量化处理器 - 多级语义切分策略
类型: plot_summary, character_profile, dialogue, performance
"""
import os
import re
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any
from langchain_openai import OpenAIEmbeddings
from ..config import Config


class VectorProcessor:
    MIN_CHUNK = 150
    MAX_CHUNK = 1200
    OVERLAP = 80

    def __init__(self):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=Config.API_KEY,
            openai_api_base=Config.BASE_URL
        )
        self.enhanced_script_path = Config.ENHANCED_SCRIPT_PATH

    def process_all(self) -> List[Dict[str, Any]]:
        """处理所有enhanced_script文件，返回文档列表"""
        all_docs = []
        base = Path(self.enhanced_script_path)
        if not base.exists():
            print(f"路径不存在: {base}")
            return all_docs
        for char_dir in sorted(base.iterdir()):
            if not char_dir.is_dir():
                continue
            char_name = char_dir.name
            for f in sorted(char_dir.glob("*_enhanced_script.txt")):
                docs = self._process_file(str(f), char_name)
                all_docs.extend(docs)
        print(f"共生成 {len(all_docs)} 个文档块")
        return all_docs

    def _process_file(self, fpath: str, char_name: str) -> List[Dict]:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                raw = f.read()
        except Exception as e:
            print(f"读取失败 {fpath}: {e}")
            return []
        content = self._clean(raw)
        fn = Path(fpath).stem.replace("_enhanced_script", "")
        parts = fn.split("_", 1)
        sid = parts[0] if parts else "unknown"
        sname = parts[1] if len(parts) > 1 else "unknown"
        base_meta = {"character_name": char_name, "script_id": sid, "script_name": sname}
        docs = []
        # 1) 剧情大纲
        summary = self._extract_summary(content)
        if summary:
            for i, chunk in enumerate(self._smart_split(summary)):
                docs.append(self._make_doc(chunk, "plot_summary", base_meta, scene_number=0, extra={"chunk_index": i}))
        # 2) 角色描述
        profiles = self._extract_profiles(content)
        for p in profiles:
            for i, chunk in enumerate(self._smart_split(p["text"])):
                docs.append(self._make_doc(chunk, "character_profile", base_meta, scene_number=0,
                                           extra={"role_name": p["name"], "chunk_index": i}))
        # 3) 场景
        scenes = self._extract_scenes(content)
        for sc in scenes:
            scene_chunks = self._split_scene(sc["text"])
            for i, chunk_text in enumerate(scene_chunks):
                doc_type = self._classify_chunk(chunk_text)
                docs.append(self._make_doc(chunk_text, doc_type, base_meta,
                                           scene_number=sc["num"], scene_name=sc["name"],
                                           extra={"chunk_index": i}))
        return docs

    def _make_doc(self, text, doc_type, base_meta, scene_number=0, scene_name="", extra=None):
        meta = dict(base_meta)
        meta["type"] = doc_type
        meta["scene_number"] = scene_number
        meta["scene_name"] = scene_name
        if extra:
            meta.update(extra)
        return {"text": text, "metadata": meta}

    def _classify_chunk(self, text: str) -> str:
        dialogue_markers = re.findall(r'\((?:白|唱|念|笑|哭|叫头)\)', text)
        stage_markers = re.findall(r'\[.*?\]', text)
        if len(dialogue_markers) >= 2:
            if any(k in text for k in ["唱", "西皮", "二黄", "摇板", "慢板", "快板", "导板"]):
                return "singing"
            return "dialogue"
        if len(stage_markers) >= 3:
            return "performance"
        return "dialogue"

    def _clean(self, content: str) -> str:
        for pat in [r'^好的[，,].*?(?=###|\*\*\*|剧目|剧情)', r'^遵照.*?(?=###|\*\*\*|剧目|剧情)',
                    r'^根据.*?(?=###|\*\*\*|剧目|剧情)', r'^按照.*?(?=###|\*\*\*|剧目|剧情)']:
            content = re.sub(pat, '', content, flags=re.DOTALL | re.MULTILINE)
        content = re.sub(r'^\s*[\*\-=]{3,}\s*$', '', content, flags=re.MULTILINE)
        for marker in [r'###\s*\*\*《', r'###\s*\*\*剧目', r'\*\*剧情大纲\*\*', r'###\s*剧目']:
            m = re.search(marker, content)
            if m and m.start() > 0:
                content = content[m.start():]
                break
        return content.strip()

    def _extract_summary(self, content: str) -> str:
        for pat in [
            r'(?:\*\*)?剧情大纲(?:\*\*)?[：:\n](.*?)(?=(?:\*\*)?出场人物|###\s*\*\*出场)',
            r'(?:\*\*)?剧情大纲(?:\*\*)?[：:\n](.*?)(?=\n#{2,})',
        ]:
            m = re.search(pat, content, re.DOTALL)
            if m:
                t = re.sub(r'[*#]+', '', m.group(1)).strip()
                if len(t) > 50:
                    return t
        return ""

    def _extract_profiles(self, content: str) -> List[Dict]:
        profiles = []
        for pat in [
            r'出场人物及脸谱.*?[：:\n](.*?)(?=###\s*(?:\*\*)?(?:正文|【第)|####\s*(?:\*\*)?第|### \*\*正文)',
            r'出场人物.*?[：:\n](.*?)(?=###\s*(?:\*\*)?(?:正文|【第)|####\s*(?:\*\*)?第)',
        ]:
            m = re.search(pat, content, re.DOTALL)
            if m:
                char_text = m.group(1)
                char_positions = [(x.start(), x.group(1).strip())
                                  for x in re.finditer(r'\d+[.．]\s*\*\*([^*]+)\*\*', char_text)]
                for i, (pos, name) in enumerate(char_positions):
                    end = char_positions[i+1][0] if i+1 < len(char_positions) else len(char_text)
                    t = re.sub(r'[*]+', '', char_text[pos:end]).strip()
                    if len(t) > 30:
                        profiles.append({"name": name, "text": t})
                break
        return profiles

    def _extract_scenes(self, content: str) -> List[Dict]:
        scenes = []
        pat = r'(【第[一二三四五六七八九十百]+[场幕]】|(?:####?\s*(?:\*\*)?)?第[一二三四五六七八九十百\d]+场)'
        splits = re.split(pat, content)
        cur_name = None
        cur_parts = []
        num = 0
        for part in splits:
            if re.match(pat, part):
                if cur_name and cur_parts:
                    t = "\n".join(cur_parts).strip()
                    if len(t) > 30:
                        scenes.append({"num": num, "name": cur_name, "text": t})
                cur_name = re.sub(r'[【】*# ]', '', part).strip()
                cur_parts = [part]
                num += 1
            elif part.strip():
                cur_parts.append(part)
        if cur_name and cur_parts:
            t = "\n".join(cur_parts).strip()
            if len(t) > 30:
                scenes.append({"num": num, "name": cur_name, "text": t})
        return scenes

    def _split_scene(self, text: str) -> List[str]:
        if len(text) <= self.MAX_CHUNK:
            return [text]
        return self._smart_split(text)

    def _smart_split(self, text: str) -> List[str]:
        if len(text) <= self.MAX_CHUNK:
            return [text]
        chunks = []
        paras = re.split(r'\n\s*\n', text)
        cur = ""
        for p in paras:
            p = p.strip()
            if not p:
                continue
            if len(p) > self.MAX_CHUNK:
                if cur and len(cur) >= self.MIN_CHUNK:
                    chunks.append(cur.strip())
                    cur = ""
                sents = re.split(r'(?<=[。！？\n])', p)
                for s in sents:
                    s = s.strip()
                    if not s:
                        continue
                    if len(cur) + len(s) > self.MAX_CHUNK:
                        if cur and len(cur) >= self.MIN_CHUNK:
                            chunks.append(cur.strip())
                            overlap = cur[-self.OVERLAP:] if len(cur) > self.OVERLAP else cur
                            cur = overlap + "\n" + s
                        else:
                            cur = (cur + "\n" + s) if cur else s
                    else:
                        cur = (cur + "\n" + s) if cur else s
            else:
                if len(cur) + len(p) + 1 > self.MAX_CHUNK:
                    if cur and len(cur) >= self.MIN_CHUNK:
                        chunks.append(cur.strip())
                        overlap = cur[-self.OVERLAP:] if len(cur) > self.OVERLAP else cur
                        cur = overlap + "\n" + p
                    else:
                        cur = (cur + "\n\n" + p) if cur else p
                else:
                    cur = (cur + "\n\n" + p) if cur else p
        if cur and len(cur) >= self.MIN_CHUNK:
            chunks.append(cur.strip())
        elif cur and chunks:
            chunks[-1] = chunks[-1] + "\n\n" + cur.strip()
        elif cur:
            chunks.append(cur.strip())
        return chunks if chunks else [text]

    def build_vector_index(self, output_dir: str = "vector_index") -> Dict[str, Any]:
        """构建向量索引"""
        os.makedirs(output_dir, exist_ok=True)
        docs = self.process_all()
        if not docs:
            print("没有文档可处理")
            return {"total": 0}
        # 分配ID
        for i, doc in enumerate(docs):
            doc["id"] = f"doc_{i}"
        # 生成embedding
        texts = [d["text"] for d in docs]
        print(f"正在为 {len(texts)} 个文档生成向量...")
        batch_size = 100
        all_embeddings = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            embs = self.embeddings.embed_documents(batch)
            all_embeddings.extend(embs)
            print(f"  已处理 {min(i+batch_size, len(texts))}/{len(texts)}")
        # 保存
        import faiss
        dim = len(all_embeddings[0])
        index = faiss.IndexFlatIP(dim)
        vectors = np.array(all_embeddings, dtype=np.float32)
        faiss.normalize_L2(vectors)
        index.add(vectors)
        faiss.write_index(index, os.path.join(output_dir, "faiss.index"))
        # 保存文档（不含向量）
        save_docs = []
        for d in docs:
            save_docs.append({
                "id": d["id"],
                "character": d["metadata"]["character_name"],
                "title": d["metadata"]["script_name"],
                "script_id": d["metadata"]["script_id"],
                "type": d["metadata"]["type"],
                "text": d["text"],
                "metadata": d["metadata"]
            })
        with open(os.path.join(output_dir, "documents.json"), "w", encoding="utf-8") as f:
            json.dump(save_docs, f, ensure_ascii=False, indent=2)
        # 统计
        type_counts = {}
        char_counts = {}
        for d in docs:
            t = d["metadata"]["type"]
            c = d["metadata"]["character_name"]
            type_counts[t] = type_counts.get(t, 0) + 1
            char_counts[c] = char_counts.get(c, 0) + 1
        stats = {
            "total": len(docs),
            "dimension": dim,
            "type_distribution": type_counts,
            "character_distribution": char_counts
        }
        with open(os.path.join(output_dir, "stats.json"), "w", encoding="utf-8") as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        print(f"\n向量索引构建完成:")
        print(f"  总文档数: {len(docs)}")
        print(f"  向量维度: {dim}")
        print(f"  类型分布: {type_counts}")
        print(f"  角色分布: {char_counts}")
        return stats


if __name__ == "__main__":
    processor = VectorProcessor()
    processor.build_vector_index()
