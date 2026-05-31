#!/usr/bin/env python3
"""
PDF截图提取脚本
提取PDF关键页面或区域作为图片
"""

import fitz  # PyMuPDF
from PIL import Image
import io
import os
from pathlib import Path

def extract_page_as_image(pdf_path, page_num=0, zoom=2):
    """
    提取PDF单页为图片

    Args:
        pdf_path: PDF文件路径
        page_num: 页码（从0开始）
        zoom: 缩放比例（默认2倍，提高清晰度）

    Returns:
        PIL.Image: 图片对象
    """
    try:
        # 打开PDF
        pdf_document = fitz.open(pdf_path)

        if page_num >= len(pdf_document):
            print(f"[✗] 页码 {page_num} 超出范围，PDF共 {len(pdf_document)} 页")
            return None

        # 获取页面
        page = pdf_document[page_num]

        # 设置缩放矩阵（提高清晰度）
        mat = fitz.Matrix(zoom, zoom)

        # 渲染页面为图片
        pix = page.get_pixmap(matrix=mat)

        # 转换为PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        pdf_document.close()

        return img

    except Exception as e:
        print(f"[✗] 提取PDF页面失败: {e}")
        return None

def extract_region_as_image(pdf_path, page_num, rect, zoom=2):
    """
    提取PDF指定区域为图片

    Args:
        pdf_path: PDF文件路径
        page_num: 页码
        rect: 区域坐标 (x0, y0, x1, y1)
        zoom: 缩放比例

    Returns:
        PIL.Image: 图片对象
    """
    try:
        pdf_document = fitz.open(pdf_path)

        if page_num >= len(pdf_document):
            print(f"[✗] 页码 {page_num} 超出范围")
            return None

        page = pdf_document[page_num]

        # 创建裁剪矩形
        clip_rect = fitz.Rect(rect)

        # 设置缩放矩阵
        mat = fitz.Matrix(zoom, zoom)

        # 渲染指定区域
        pix = page.get_pixmap(matrix=mat, clip=clip_rect)

        # 转换为PIL Image
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        pdf_document.close()

        return img

    except Exception as e:
        print(f"[✗] 提取PDF区域失败: {e}")
        return None

def extract_key_pages(pdf_path, output_dir, key_pages=None):
    """
    提取PDF的关键页面

    Args:
        pdf_path: PDF文件路径
        output_dir: 输出目录
        key_pages: 关键页码列表（从1开始），如 [1, 3, 5]

    Returns:
        list: 生成的图片路径列表
    """
    if key_pages is None:
        # 默认提取前3页
        key_pages = [1, 2, 3]

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_images = []

    pdf_name = Path(pdf_path).stem

    for page_num in key_pages:
        try:
            # 页码从1开始，转换为从0开始
            page_idx = page_num - 1

            img = extract_page_as_image(pdf_path, page_idx, zoom=2)

            if img:
                output_path = output_dir / f"{pdf_name}_page_{page_num}.png"
                img.save(str(output_path), "PNG", quality=95)
                generated_images.append(str(output_path))
                print(f"[✓] 已提取: {output_path.name}")

        except Exception as e:
            print(f"[✗] 提取第 {page_num} 页失败: {e}")

    return generated_images

def extract_signature_regions(pdf_path, output_dir):
    """
    尝试提取签名/盖章区域（简化版，提取每页底部区域）

    Args:
        pdf_path: PDF文件路径
        output_dir: 输出目录

    Returns:
        list: 生成的图片路径列表
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_images = []
    pdf_name = Path(pdf_path).stem

    try:
        pdf_document = fitz.open(pdf_path)

        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]

            # 获取页面尺寸
            rect = page.rect

            # 提取底部20%区域（可能包含签名）
            x0 = 0
            y0 = rect.height * 0.8
            x1 = rect.width
            y1 = rect.height

            bottom_rect = (x0, y0, x1, y1)

            img = extract_region_as_image(pdf_path, page_num, bottom_rect, zoom=2)

            if img:
                output_path = output_dir / f"{pdf_name}_signature_region_page_{page_num + 1}.png"
                img.save(str(output_path), "PNG", quality=95)
                generated_images.append(str(output_path))
                print(f"[✓] 已提取签名区域: {output_path.name}")

        pdf_document.close()

    except Exception as e:
        print(f"[✗] 提取签名区域失败: {e}")

    return generated_images

def analyze_pdf_content(pdf_path):
    """
    分析PDF内容，返回基本信息

    Args:
        pdf_path: PDF文件路径

    Returns:
        dict: PDF信息
    """
    try:
        pdf_document = fitz.open(pdf_path)

        info = {
            'page_count': len(pdf_document),
            'file_name': Path(pdf_path).name,
            'file_size': f"{os.path.getsize(pdf_path) / 1024:.1f} KB",
            'pages': []
        }

        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            text = page.get_text()

            page_info = {
                'page_num': page_num + 1,
                'text_length': len(text),
                'has_text': len(text) > 0,
                'preview': text[:200] if text else ''
            }

            info['pages'].append(page_info)

        pdf_document.close()

        return info

    except Exception as e:
        print(f"[✗] 分析PDF失败: {e}")
        return None

def extract_screenshots_for_evidence(pdf_path, output_dir, evidence_name):
    """
    为证据材料提取截图（材料分析专用）

    Args:
        pdf_path: PDF证据文件路径
        output_dir: 输出目录
        evidence_name: 证据名称

    Returns:
        list: 生成的图片路径列表
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    generated_images = []

    try:
        pdf_document = fitz.open(pdf_path)
        total_pages = len(pdf_document)

        # 确定要提取的页面
        if total_pages <= 3:
            # 少于3页，提取所有页
            pages_to_extract = list(range(1, total_pages + 1))
        else:
            # 多于3页，提取首页、中间页、尾页
            pages_to_extract = [1, total_pages // 2 + 1, total_pages]

        for page_num in pages_to_extract:
            img = extract_page_as_image(pdf_path, page_num - 1, zoom=2)

            if img:
                safe_name = "".join([c for c in evidence_name if c.isalnum() or c in (' ', '-', '_')]).rstrip()
                output_path = output_dir / f"{safe_name}_page_{page_num}.png"
                img.save(str(output_path), "PNG", quality=95)
                generated_images.append(str(output_path))

        pdf_document.close()

    except Exception as e:
        print(f"[✗] 提取证据截图失败: {e}")

    return generated_images

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='PDF截图提取工具')
    parser.add_argument('pdf', help='PDF文件路径')
    parser.add_argument('--output', '-o', required=True, help='输出目录')
    parser.add_argument('--pages', '-p', nargs='+', type=int, help='要提取的页码（从1开始）')
    parser.add_argument('--all', action='store_true', help='提取所有页面')
    parser.add_argument('--analyze', action='store_true', help='仅分析PDF内容')

    args = parser.parse_args()

    if args.analyze:
        info = analyze_pdf_content(args.pdf)
        import json
        print(json.dumps(info, ensure_ascii=False, indent=2))
    else:
        if args.all:
            # 提取所有页面
            pdf_document = fitz.open(args.pdf)
            pages = list(range(1, len(pdf_document) + 1))
            pdf_document.close()
            images = extract_key_pages(args.pdf, args.output, pages)
        elif args.pages:
            images = extract_key_pages(args.pdf, args.output, args.pages)
        else:
            # 默认提取关键页面
            images = extract_key_pages(args.pdf, args.output)

        print(f"\n[*] 共生成 {len(images)} 张图片")
        print(f"[*] 输出目录: {args.output}")

if __name__ == '__main__':
    main()
