# 测试文件说明

本目录包含项目的测试文件。

## 测试文件列表

### 1. test_iteration_fix.py

**用途**: 测试迭代机制修复效果

**功能**:
- 验证场景和装扮信息在迭代中是否保持不变
- 测试改进建议是否正确追加到prompt
- 验证`_build_complete_prompt`函数的improvements参数

**运行方法**:
```bash
conda activate llm
python tests/test_iteration_fix.py
```

**测试内容**:
1. **测试1**: Prompt构建测试
   - 第1次迭代：使用完整的基础信息
   - 第2次迭代：保留基础信息 + 添加改进建议
   - 验证场景、装扮信息是否完整保留
   - 验证改进建议是否正确添加

2. **测试2**: 改进建议提取测试
   - 从评估结果中提取improvement_suggestions
   - 验证建议格式是否正确

**预期输出**:
```
✓ 所有验证通过！场景和装扮信息在迭代中成功保留。
✓✓✓ 所有测试通过！迭代机制修复成功。
```

---

### 2. test_system.py

**用途**: 系统功能测试

**功能**:
- 测试各个模块的基本功能
- 验证系统配置是否正确
- 检查依赖是否安装完整

**运行方法**:
```bash
conda activate llm
python tests/test_system.py
```

**测试模块**:
1. Prompt提取器测试
2. 导演Agent测试
3. 视频生成器测试
4. 流水线测试

**注意**: 部分测试可能需要有效的API密钥和网络连接。

---

## 运行所有测试

```bash
conda activate llm

# 运行迭代修复测试
python tests/test_iteration_fix.py

# 运行系统测试
python tests/test_system.py
```

---

## 测试最佳实践

### 1. 测试前准备

- 确保已激活conda环境：`conda activate llm`
- 确保已安装所有依赖：`pip install -r requirements.txt`
- 确保API密钥已正确配置（如需要）

### 2. 测试隔离

- 每个测试文件独立运行
- 不依赖外部状态
- 使用模拟数据避免API调用

### 3. 测试输出

- 清晰的成功/失败标记
- 详细的错误信息
- 验证点的明确说明

---

## 添加新测试

创建新测试文件时，请遵循以下规范：

1. **命名规范**: `test_<功能名>.py`
2. **文档字符串**: 在文件顶部说明测试目的
3. **函数命名**: `test_<具体功能>()`
4. **输出格式**: 使用清晰的标题和分隔符

示例：
```python
"""
测试<功能名>
"""

def test_feature_name():
    """测试具体功能"""
    print("=" * 80)
    print("测试<功能名>")
    print("=" * 80)
    
    # 测试逻辑
    result = some_function()
    
    # 验证
    assert result == expected_value
    
    print("✓ 测试通过")
    return True


if __name__ == "__main__":
    passed = test_feature_name()
    if passed:
        print("✓✓✓ 所有测试通过")
    else:
        print("✗✗✗ 测试失败")
```

---

## 已删除的测试文件

以下测试文件已被删除（过时或包含硬编码密钥）：

- `test_api_endpoint.py` - 旧的API端点测试，包含硬编码API密钥
- `test_video_api.py` - 旧的视频API测试
- `test_video_api_v2.py` - 旧的视频API测试v2

这些文件的功能已被更新的系统测试覆盖。

---

**最后更新**: 2025-11-24
