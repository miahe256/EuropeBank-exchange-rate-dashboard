from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import requests
from datetime import datetime, timedelta
import json
import traceback
import os

app = Flask(__name__)
CORS(app)  # 启用CORS支持跨域请求

def get_real_time_rates():
    """获取实时汇率数据"""
    try:
        # 使用 Frankfurter API 获取实时汇率
        url = "https://api.frankfurter.app/latest?from=USD&to=CNY"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("rates") and "CNY" in data["rates"]:
            rate = data["rates"]["CNY"]
            return {
                "buyPrice": round(rate - 0.001, 4),  # 买入价略低于中间价
                "sellPrice": round(rate + 0.001, 4),  # 卖出价略高于中间价
                "midPrice": round(rate, 4),
                "success": True,
                "updateTime": data.get("date", "")
            }
        else:
            print("未获取到汇率数据")
            return {"success": False, "error": "未获取到汇率数据"}
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {str(e)}")
        return {"success": False, "error": f"网络请求失败: {str(e)}"}
    except Exception as e:
        print(f"获取实时汇率出错: {str(e)}")
        print(traceback.format_exc())
        return {"success": False, "error": f"获取数据失败: {str(e)}"}

def get_historical_rates():
    """获取历史汇率数据（过去一年）"""
    try:
        # 获取过去一年的时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)  # 改为365天
        
        # 使用 Frankfurter API 获取历史汇率数据
        url = f"https://api.frankfurter.app/{start_date.strftime('%Y-%m-%d')}..{end_date.strftime('%Y-%m-%d')}?from=USD&to=CNY"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get("rates"):
            dates = []
            rates = []
            
            # 按日期排序
            sorted_dates = sorted(data["rates"].keys())
            
            for date in sorted_dates:
                # 修改日期格式为 "MM-DD"（月-日）
                formatted_date = datetime.strptime(date, "%Y-%m-%d").strftime("%m-%d")
                dates.append(formatted_date)
                rates.append(round(data["rates"][date]["CNY"], 4))
            
            # 添加数据统计信息
            stats = {
                "最高汇率": round(max(rates), 4),
                "最低汇率": round(min(rates), 4),
                "平均汇率": round(sum(rates) / len(rates), 4),
                "数据点数量": len(rates)
            }
            
            return {
                "success": True,
                "data": {
                    "labels": dates,
                    "rates": rates,
                    "statistics": stats  # 添加统计信息
                }
            }
        else:
            print("未获取到历史汇率数据")
            return {"success": False, "error": "未获取到历史汇率数据"}
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {str(e)}")
        return {"success": False, "error": f"网络请求失败: {str(e)}"}
    except Exception as e:
        print(f"获取历史汇率出错: {str(e)}")
        print(traceback.format_exc())
        return {"success": False, "error": f"获取数据失败: {str(e)}"}

@app.route('/')
def index():
    """根路由处理器"""
    return """
    <h1>汇率查询API服务</h1>
    <p>可用的API端点：</p>
    <ul>
        <li><a href="/api/real-time-rates">实时汇率</a></li>
        <li><a href="/api/historical-rates">历史汇率（过去一年）</a></li>
    </ul>
    <p>注意：历史汇率数据仅包含工作日（不含周末和节假日）</p>
    """

@app.route('/favicon.ico')
def favicon():
    """处理favicon.ico请求"""
    return '', 204  # 返回无内容状态码

@app.route('/api/real-time-rates')
def real_time_rates():
    """实时汇率API端点"""
    return jsonify(get_real_time_rates())

@app.route('/api/historical-rates')
def historical_rates():
    """历史汇率API端点"""
    return jsonify(get_historical_rates())

if __name__ == '__main__':
    try:
        print("正在启动服务器...")
        app.run(debug=True, port=5000)
    except Exception as e:
        print(f"服务器启动失败: {str(e)}")
        print(traceback.format_exc()) 