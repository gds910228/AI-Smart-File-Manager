"""
股票代码提取器模块
从指定目录的文件名中提取股票代码
"""

import os
import re
from pathlib import Path
from typing import List, Set, Tuple


class StockCodeExtractor:
    """股票代码提取器类"""
    
    def __init__(self):
        # 股票代码的正则表达式模式
        self.stock_code_pattern = r'stock_analysis_(?:sse|szse)_(\d{6})'
        # 通用6位数字模式（备用）
        self.general_pattern = r'[0-9]{6}'
    
    def extract_from_directory(self, directory_path: str, use_precise_pattern: bool = True) -> Tuple[Set[str], List[str]]:
        """
        从指定目录中的所有文件名提取股票代码
        
        Args:
            directory_path: 要扫描的目录路径
            use_precise_pattern: 是否使用精确模式（只匹配stock_analysis格式）
            
        Returns:
            Tuple[Set[str], List[str]]: (股票代码集合, 处理的文件列表)
        """
        stock_codes = set()
        processed_files = []
        
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"目录不存在: {directory_path}")
        
        pattern = self.stock_code_pattern if use_precise_pattern else self.general_pattern
        
        # 遍历目录中的所有文件
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if use_precise_pattern:
                    matches = re.findall(pattern, file)
                else:
                    matches = re.findall(pattern, file)
                    # 过滤掉明显不是股票代码的数字（如日期）
                    matches = [m for m in matches if not self._is_date_like(m)]
                
                for match in matches:
                    stock_codes.add(match)
                    processed_files.append(f"{file} -> {match}")
        
        return stock_codes, processed_files
    
    def _is_date_like(self, code: str) -> bool:
        """判断是否像日期格式的数字"""
        # 简单过滤：以20开头的可能是年份
        if code.startswith('20'):
            return True
        # 以0开头且第二位是0-3的可能是月份
        if code.startswith('0') and len(code) >= 2 and code[1] in '0123':
            return True
        return False
    
    def save_to_file(self, stock_codes: Set[str], output_file: str) -> None:
        """
        将股票代码保存到文件
        
        Args:
            stock_codes: 股票代码集合
            output_file: 输出文件路径
        """
        sorted_codes = sorted(list(stock_codes))
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for code in sorted_codes:
                f.write(code + '\n')
    
    def extract_and_save(self, directory_path: str, output_file: str = None, 
                        use_precise_pattern: bool = True) -> dict:
        """
        提取股票代码并保存到文件
        
        Args:
            directory_path: 要扫描的目录路径
            output_file: 输出文件路径，默认为stock_codes.txt
            use_precise_pattern: 是否使用精确模式
            
        Returns:
            dict: 包含提取结果的字典
        """
        if output_file is None:
            output_file = "stock_codes.txt"
        
        try:
            stock_codes, processed_files = self.extract_from_directory(
                directory_path, use_precise_pattern
            )
            
            if stock_codes:
                self.save_to_file(stock_codes, output_file)
            
            result = {
                "success": True,
                "total_codes": len(stock_codes),
                "codes": sorted(list(stock_codes)),
                "processed_files_count": len(processed_files),
                "output_file": output_file,
                "message": f"成功提取到 {len(stock_codes)} 个不重复的股票代码"
            }
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"提取过程中出现错误: {e}"
            }


def extract_stock_codes_from_path(directory_path: str, output_file: str = None) -> dict:
    """
    便捷函数：从指定路径提取股票代码
    
    Args:
        directory_path: 目录路径
        output_file: 输出文件路径
        
    Returns:
        dict: 提取结果
    """
    extractor = StockCodeExtractor()
    return extractor.extract_and_save(directory_path, output_file)


if __name__ == "__main__":
    # 测试代码
    test_directory = r"F:\doc\mine\理财相关\量化分析"
    result = extract_stock_codes_from_path(test_directory, "extracted_stock_codes.txt")
    
    if result["success"]:
        print(f"✅ {result['message']}")
        print(f"📁 输出文件: {result['output_file']}")
        print(f"📊 股票代码: {', '.join(result['codes'])}")
    else:
        print(f"❌ {result['message']}")