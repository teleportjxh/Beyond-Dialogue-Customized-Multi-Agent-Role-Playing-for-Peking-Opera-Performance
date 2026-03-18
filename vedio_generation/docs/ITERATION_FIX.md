# 视频迭代机制修复说明

## 问题描述

在原有的检查迭代机制中,当视频评估不通过需要重新生成时,会出现视频质量递减的问题。

### 根本原因

迭代机制采用了**"完全替换prompt"**策略,导致关键信息丢失:

1. **首次生成**: 使用完整的结构化prompt(场景设定 + 角色装扮 + 表演内容)
2. **评估不通过**: 导演Agent让大模型生成"优化后的prompt"
3. **问题所在**: 大模型生成的新prompt会丢失原始的场景和装扮细节
4. **迭代生成**: 使用简化的prompt,导致视频质量下降

### 具体表现

```
✅ 首次生成prompt (完整):
- 场景: 舞台中央布置一张方桌,两侧各置一椅...
- 装扮: 头戴凤翅紫金冠,配两根长翎子...
- 表演: 孙悟空performs...

❌ 迭代后prompt (信息丢失):
- 场景: 简化或丢失
- 装扮: 简化或丢失  
- 表演: 保留但缺少环境和视觉细节
```

---

## 解决方案

采用**"保留基础信息 + 应用改进建议"**策略:

### 核心思想

- **基础信息**(场景、装扮): 在所有迭代中保持不变
- **改进建议**: 作为Refinements追加到Performance部分
- **迭代方式**: 增量修改而非完全替换

### 修改内容

#### 1. `src/extractor/simple_prompt_extractor.py`

**修改**: `_build_complete_prompt` 函数添加 `improvements` 参数

```python
def _build_complete_prompt(
    character: str,
    emotion: str,
    content_text: str,
    scene_desc: str,
    costume_desc: str,
    improvements: Optional[List[Dict]] = None  # 新增
) -> str:
    """
    构建完整的prompt
    结构: 通用京剧描述 + 场景 + 装扮 + 具体表演 + 改进要求(可选)
    """
    # ... 保留场景和装扮部分 ...
    
    # 应用改进建议
    if improvements:
        improvement_notes = []
        for imp in improvements:
            suggestion = imp.get('suggestion', '')
            if suggestion:
                improvement_notes.append(suggestion)
        
        if improvement_notes:
            performance_parts.append("\nRefinements: " + "; ".join(improvement_notes))
```

**修改**: `extract_prompts_simple` 函数返回的数据中添加 `scene_desc` 和 `costume_desc` 字段

```python
prompt_info = {
    'scene_id': scene_id,
    'character': character,
    'prompt': prompt,
    'emotion': emotion,
    'type': content_type,
    'turn': idx,
    'raw_text': content_text,
    'scene_desc': scene_desc,      # 新增
    'costume_desc': costume_desc,  # 新增
    'content_text': content_text   # 新增
}
```

#### 2. `src/evaluator/director_agent.py`

**修改**: `generate_improved_prompt` 方法重构

```python
def generate_improved_prompt(
    self,
    original_prompt: str,
    evaluation: Dict,
    expected_content: Dict,
    scene_desc: str = "",      # 新增
    costume_desc: str = ""     # 新增
) -> str:
    """
    关键改进: 保留场景和装扮信息,仅应用改进建议到表演部分
    """
    from ..extractor.simple_prompt_extractor import _build_complete_prompt
    
    # 提取改进建议
    improvements = evaluation.get('improvement_suggestions', [])
    
    # 基于原始结构化数据重建prompt,应用改进建议
    improved_prompt = _build_complete_prompt(
        character=expected_content.get('character', ''),
        emotion=expected_content.get('emotion', ''),
        content_text=expected_content.get('content_text', ''),
        scene_desc=scene_desc,      # 保留原始场景
        costume_desc=costume_desc,  # 保留原始装扮
        improvements=improvements    # 应用改进建议
    )
    
    return improved_prompt
```

**修改**: `analyze_and_improve` 方法添加参数

```python
def analyze_and_improve(
    self,
    video_url: str,
    original_prompt: str,
    expected_content: Dict,
    video_path: str = None,
    scene_desc: str = "",      # 新增
    costume_desc: str = ""     # 新增
) -> Tuple[bool, Dict, Optional[str]]:
    # ... 评估逻辑 ...
    
    # 生成改进的prompt(保留场景和装扮)
    improved_prompt = self.generate_improved_prompt(
        original_prompt,
        evaluation,
        expected_content,
        scene_desc,      # 传递场景
        costume_desc     # 传递装扮
    )
```

#### 3. `src/pipeline/intelligent_pipeline.py`

**修改**: `_generate_video_with_director_guidance` 方法提取并保存基础信息

```python
def _generate_video_with_director_guidance(
    self,
    prompt_data: Dict,
    script_name: str,
    video_index: int
) -> Dict:
    turn = prompt_data['turn']
    character = prompt_data['character']
    current_prompt = prompt_data['prompt']
    
    # 提取并保存基础信息(场景和装扮在迭代中保持不变)
    scene_desc = prompt_data.get('scene_desc', '')      # 新增
    costume_desc = prompt_data.get('costume_desc', '')  # 新增
    
    # ... 迭代逻辑 ...
    
    # 调用导演评估时传递场景和装扮信息
    passed, evaluation, improved_prompt = self.director.analyze_and_improve(
        video_url=video_url,
        original_prompt=current_prompt,
        expected_content=expected_content,
        video_path=video_path,
        scene_desc=scene_desc,      # 传递场景信息
        costume_desc=costume_desc   # 传递装扮信息
    )
```

---

## 效果对比

### 修复前

```
第1次迭代:
Chinese Peking Opera performance...
Scene: 舞台中央布置一张方桌,两侧各置一椅...
Character: 孙悟空 - 武生 role type. Face: 金色猴脸...
Performance: 孙悟空 performs: [筋斗翻至台中]

第2次迭代 (信息丢失):
A character performing with more emphasis on movements.
[场景和装扮信息大部分丢失]
```

### 修复后

```
第1次迭代:
Chinese Peking Opera performance...
Scene: 舞台中央布置一张方桌,两侧各置一椅...
Character: 孙悟空 - 武生 role type. Face: 金色猴脸...
Performance: 孙悟空 performs: [筋斗翻至台中]

第2次迭代 (保留所有基础信息):
Chinese Peking Opera performance...
Scene: 舞台中央布置一张方桌,两侧各置一椅...  ← 完全保留
Character: 孙悟空 - 武生 role type. Face: 金色猴脸...  ← 完全保留
Performance: 孙悟空 performs: [筋斗翻至台中]
Refinements: Emphasize the fluidity; Highlight facial details  ← 新增改进
```

---

## 测试验证

运行测试脚本:

```bash
conda activate llm
python test_iteration_fix.py
```

### 测试结果

```
✓ 场景描述包含'方桌': True
✓ 场景描述包含'山水画': True
✓ 装扮描述包含'凤翅紫金冠': True
✓ 装扮描述包含'金色猴脸': True
✓ 包含改进建议1: True
✓ 包含改进建议2: True
✓ 仍然包含原始表演内容: True
✓ 仍然包含情感描述: True

✓✓✓ 所有测试通过！迭代机制修复成功。
```

---

## 优势

1. **信息完整性**: 场景和装扮信息在所有迭代中保持完整
2. **迭代有效性**: 改进建议被正确应用,不会冲掉原有信息
3. **质量保证**: 避免了视频质量因信息丢失而递减
4. **可追溯性**: 每次迭代的prompt都包含完整上下文

---

## 注意事项

1. **向后兼容**: 如果prompt_data中没有scene_desc/costume_desc字段,会使用空字符串,不影响已有功能
2. **重新提取**: 需要重新运行prompt提取才能获得包含scene_desc/costume_desc的数据
3. **测试建议**: 使用真实场景测试完整流程,确保迭代效果符合预期

---

## 相关文件

- `src/extractor/simple_prompt_extractor.py` - Prompt构建和提取
- `src/evaluator/director_agent.py` - 导演评估和改进生成
- `src/pipeline/intelligent_pipeline.py` - 迭代流程控制
- `test_iteration_fix.py` - 测试验证脚本

---

修复日期: 2025-11-24
