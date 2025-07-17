#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
订单MQTT发送程序
用于接收index.html中的订单信息并通过MQTT发送
"""

import json
import paho.mqtt.client as mqtt
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading
import time

# MQTT配置
MQTT_BROKER_HOSTNAME = "192.168.137.229"
MQTT_USERNAME = "Wang"
MQTT_PASSWORD = "Chenghao"
MQTT_ORDER_TOPIC = "Group21/message"

# Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# MQTT客户端
mqtt_client = None

def setup_mqtt_client():
    """设置MQTT客户端"""
    global mqtt_client
    client = mqtt.Client()
    client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
    
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("MQTT连接成功")
        else:
            print(f"MQTT连接失败，错误码: {rc}")
    
    def on_message(client, userdata, msg):
        print(f"收到消息: {msg.topic} - {msg.payload.decode()}")
    
    client.on_connect = on_connect
    client.on_message = on_message
    
    try:
        print(f"正在连接MQTT代理: {MQTT_BROKER_HOSTNAME}")
        client.connect(MQTT_BROKER_HOSTNAME)
        client.loop_start()
        print(f"MQTT连接请求已发送到: {MQTT_BROKER_HOSTNAME}")
        return client
    except Exception as e:
        print(f"连接MQTT代理失败: {e}")
        return None

def send_order_via_mqtt(product_name, customer_name):
    """通过MQTT发送订单信息"""
    global mqtt_client
    
    if mqtt_client is None:
        print("MQTT客户端未初始化")
        return False
    
    try:
        # 将商品名称转换为小写
        product_lower = product_name.lower()
        
        # 组合商品和客户信息
        message = f"{product_lower} {customer_name}"
        
        # 发送组合字符串
        mqtt_client.publish(MQTT_ORDER_TOPIC, message)
        print(f"MQTT消息已发送到 {MQTT_BROKER_HOSTNAME}:{MQTT_ORDER_TOPIC}")
        print(f"发送内容: {message}")
        return True
        
    except Exception as e:
        print(f"发送订单失败: {e}")
        return False

@app.route('/set_order_target', methods=['POST'])
def set_order_target():
    """接收订单目标商品"""
    try:
        data = request.get_json()
        product = data.get('product', '')
        customer = data.get('customer', '')  # 获取客户信息
        
        if not product:
            return jsonify({"status": "error", "message": "未提供商品信息"}), 400
        
        # 检查商品是否为banana或book
        if product.lower() not in ['banana', 'book']:
            return jsonify({"status": "error", "message": "只支持banana和book商品"}), 400
        
        # 发送MQTT消息（包含商品和客户信息）
        success = send_order_via_mqtt(product, customer)
        
        if success:
            return jsonify({
                "status": "success", 
                "message": f"订单已发送: {product}",
                "product": product
            })
        else:
            return jsonify({
                "status": "warning", 
                "message": "订单已记录，但MQTT发送失败",
                "product": product
            })
            
    except Exception as e:
        print(f"处理订单请求失败: {e}")
        return jsonify({"status": "error", "message": "服务器错误"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "ok",
        "mqtt_connected": mqtt_client is not None,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/test_mqtt', methods=['POST'])
def test_mqtt():
    """测试MQTT连接"""
    try:
        data = request.get_json()
        test_message = data.get('message', 'test')
        
        success = send_order_via_mqtt(test_message)
        
        if success:
            return jsonify({"status": "success", "message": "MQTT测试消息已发送"})
        else:
            return jsonify({"status": "error", "message": "MQTT发送失败"})
            
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

def main():
    """主函数"""
    global mqtt_client
    
    print("启动订单MQTT发送程序...")
    
    # 初始化MQTT客户端
    mqtt_client = setup_mqtt_client()
    
    if mqtt_client is None:
        print("警告: MQTT客户端初始化失败，程序将继续运行但无法发送MQTT消息")
    
    # 启动Flask应用
    print("启动Flask服务器...")
    print("访问 http://localhost:5001/health 检查服务状态")
    print("访问 http://localhost:5001/test_mqtt 测试MQTT连接")
    
    app.run(host='0.0.0.0', port=5001, debug=False)

if __name__ == '__main__':
    main() 