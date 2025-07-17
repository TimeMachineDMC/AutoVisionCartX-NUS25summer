#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Voice Order API using Faster Whisper
支持语音下单功能的API服务
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import tempfile
import os
import re
from faster_whisper import WhisperModel

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 初始化Whisper模型
print("Loading Whisper model...")
model = WhisperModel("base", device="cpu", compute_type="int8")
print("Whisper model loaded successfully!")

# 商品关键词字典
PRODUCT_KEYWORDS = {
    'milk': 'Fresh Milk',
    'bread': 'Whole Wheat Bread', 
    'apple': 'Red Apples',
    'apples': 'Red Apples',
    'banana': 'Fresh Bananas',
    'bananas': 'Fresh Bananas',
    'notebook': 'Notebook Set',
    'lamp': 'LED Desk Lamp',
    'light': 'LED Desk Lamp'
}

# 数字关键词字典
NUMBER_KEYWORDS = {
    'one': 1, 'a': 1, 'an': 1,
    'two': 2, 'three': 3, 'four': 4, 'five': 5,
    'six': 6, 'seven': 7, 'eight': 8, 'nine': 9, 'ten': 10,
    '1': 1, '2': 2, '3': 3, '4': 4, '5': 5,
    '6': 6, '7': 7, '8': 8, '9': 9, '10': 10
}

def extract_order_from_text(text):
    """
    从文本中提取订单信息
    """
    text = text.lower().strip()
    print(f"Processing text: {text}")
    
    # 查找商品
    found_product = None
    for keyword, product_name in PRODUCT_KEYWORDS.items():
        if keyword in text:
            found_product = product_name
            break
    
    if not found_product:
        return None, "No valid product found in speech"
    
    # 查找数量
    found_quantity = 1  # 默认数量为1
    words = text.split()
    
    for word in words:
        # 移除标点符号
        clean_word = re.sub(r'[^\w]', '', word)
        if clean_word in NUMBER_KEYWORDS:
            found_quantity = NUMBER_KEYWORDS[clean_word]
            break
    
    # 确保数量在1-10范围内
    found_quantity = max(1, min(10, found_quantity))
    
    return {
        'product': found_product,
        'quantity': found_quantity
    }, None

@app.route('/api/voice-order', methods=['POST'])
def voice_order():
    """
    处理语音下单请求
    """
    try:
        # 检查是否有音频文件
        if 'audio' not in request.files:
            return jsonify({'success': False, 'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'success': False, 'error': 'No audio file selected'}), 400
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            audio_file.save(temp_file.name)
            temp_filename = temp_file.name
        
        try:
            # 使用Whisper进行语音识别
            print(f"Transcribing audio file: {temp_filename}")
            segments, info = model.transcribe(temp_filename, language="en")
            
            # 提取转录文本
            transcribed_text = ""
            for segment in segments:
                transcribed_text += segment.text + " "
            
            transcribed_text = transcribed_text.strip()
            print(f"Transcribed text: {transcribed_text}")
            
            if not transcribed_text:
                return jsonify({
                    'success': False, 
                    'error': 'No speech detected'
                }), 400
            
            # 从文本中提取订单信息
            order_info, error = extract_order_from_text(transcribed_text)
            
            if error:
                return jsonify({
                    'success': False,
                    'error': error,
                    'transcribed_text': transcribed_text
                }), 400
            
            # 返回成功结果
            return jsonify({
                'success': True,
                'transcribed_text': transcribed_text,
                'order': order_info
            })
            
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_filename)
            except:
                pass
                
    except Exception as e:
        print(f"Error processing voice order: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Internal server error: {str(e)}'
        }), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """
    健康检查接口
    """
    return jsonify({
        'status': 'healthy',
        'message': 'Voice Order API is running',
        'model': 'faster-whisper base'
    })

if __name__ == '__main__':
    print("Starting Voice Order API...")
    print("Available products:")
    for keyword, product in PRODUCT_KEYWORDS.items():
        print(f"  - {keyword} -> {product}")
    print("\nExample usage: 'I want two apples' or 'Give me a milk'")
    print("Starting server on http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True) 