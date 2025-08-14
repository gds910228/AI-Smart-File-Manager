import os
import re
from pathlib import Path

def extract_stock_codes_from_directory(directory_path, output_file):
    """
    从指定目录中的所有文件名提取股票代码
    
    Args:
        directory_path: 要扫描的目录路径
        output_file: 输出文件路径
    """
    # 股票代码的正则表达式模式
    # 匹配6位数字的股票代码（如600031, 000001等）
    stock_code_pattern = r'[0-9]{6}'
    
    stock_codes = set()  # 使用set避免重复
    
    try:
        # 检查目录是否存在
        if not os.path.exists(directory_path):
            print(f"错误：目录 {directory_path} 不存在")
            return
        
        # 遍历目录中的所有文件
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                # 在文件名中查找股票代码
                matches = re.findall(stock_code_pattern, file)
                for match in matches:
                    stock_codes.add(match)
                    print(f"从文件 {file} 中提取到股票代码: {match}")
        
        # 将股票代码排序并写入文件
        sorted_codes = sorted(list(stock_codes))
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for code in sorted_codes:
                f.write(code + '\n')
        
        print(f"\n成功提取到 {len(sorted_codes)} 个不重复的股票代码")
        print(f"结果已保存到: {output_file}")
        print(f"提取的股票代码: {', '.join(sorted_codes)}")
        
    except Exception as e:
        print(f"处理过程中出现错误: {e}")

if __name__ == "__main__":
    # 指定目录路径
    target_directory = r"F:\doc\mine\理财相关\量化分析"
    
    # 输出文件路径（保存在当前目录）
    output_file = "stock_codes_result.txt"
    
    print(f"开始扫描目录: {target_directory}")
    extract_stock_codes_from_directory(target_directory, output_file)