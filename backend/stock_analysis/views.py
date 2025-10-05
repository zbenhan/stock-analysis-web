import traceback
import json
import pandas as pd
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .utils import get_stock_data, process_data, get_random_stock_codes
import os
from django.http import HttpResponse, JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import mimetypes

@csrf_exempt
def index(request):
    """首页"""
    try:
        # 方法1: 尝试直接读取模板文件
        import os
        from django.conf import settings
        
        # 可能的模板路径
        template_paths = [
            os.path.join(settings.PROJECT_ROOT, 'frontend', 'templates', 'index.html'),
            os.path.join(settings.BASE_DIR, 'frontend', 'templates', 'index.html'),
            'frontend/templates/index.html',
        ]
        
        for template_path in template_paths:
            if os.path.exists(template_path):
                print(f"找到模板文件: {template_path}")
                with open(template_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                return HttpResponse(content)
        
        # 如果找不到文件，返回错误信息
        return HttpResponse(f"模板文件未找到。搜索路径: {template_paths}")
        
    except Exception as e:
        # 方法2: 返回内置的简单页面，但提供调试信息
        debug_html = f"""
        <!DOCTYPE html>
        <html>
        <head><title>模板调试</title></head>
        <body>
            <h1>模板加载问题</h1>
            <p>错误: {str(e)}</p>
            <p>PROJECT_ROOT: {settings.PROJECT_ROOT}</p>
            <p>BASE_DIR: {settings.BASE_DIR}</p>
            <p>请检查 frontend/templates/index.html 文件是否在部署包中</p>
        </body>
        </html>
        """
        return HttpResponse(debug_html)

@csrf_exempt
def get_stock_data_api(request):
    """获取股票原始数据，供前端生成图表"""
    if request.method == 'POST':
        try:
            print("收到股票数据请求")
            data = json.loads(request.body.decode('utf-8'))
            stock_number = data.get('stock_number')
            
            if not stock_number:
                return JsonResponse({'success': False, 'error': 'empty_input'})
            
            stock_codes = [code.strip() for code in stock_number.split(';') if code.strip()]
            
            if not stock_codes:
                return JsonResponse({'success': False, 'error': '未提供有效的股票代码'})
            
            stock_data_list = []
            
            for stock_code in stock_codes:
                try:
                    print(f"处理股票代码: {stock_code}")
                    # 获取股票数据
                    result, message = get_stock_data(stock_code)
                    if result is None:
                        print(f"获取股票数据失败: {message}")
                        continue
                    
                    monthly_data = result['price_data']
                    financial_data = result['financial_data']
                    
                    if monthly_data.empty or financial_data.empty:
                        print(f"数据为空 - 月度数据: {len(monthly_data)}, 财务数据: {len(financial_data)}")
                        continue
                    
                    print("开始处理数据...")
                    # 处理数据
                    processed_monthly, processed_financial, process_msg = process_data(monthly_data, financial_data)
                    if processed_monthly is None:
                        print(f"数据处理失败: {process_msg}")
                        continue
                    
                    # 准备返回的数据
                    stock_data = {
                        'stock_code': stock_code,
                        'stock_name': result['stock_info'].security_name,
                        'market_cap_data': processed_monthly[['data_date', 'market_capitalization']].fillna(0).to_dict('records'),
                        'profit_data': processed_financial[['data_date', 'net_profit_parent_quarterly']].fillna(0).to_dict('records')
                    }
                    
                    stock_data_list.append(stock_data)
                    print(f"股票 {stock_code} 数据处理成功")
                    
                except Exception as e:
                    print(f"处理股票 {stock_code} 时发生错误: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            return JsonResponse({
                'success': True,
                'stocks_data': stock_data_list,
                'message': f'成功获取 {len(stock_data_list)} 支股票数据'
            })
            
        except Exception as e:
            print(f"API错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return JsonResponse({'success': False, 'error': f'服务器错误: {str(e)}'})
    
    else:
        return JsonResponse({'success': False, 'error': '请使用POST请求'})

@csrf_exempt
def get_random_stocks_api(request):
    """获取随机股票代码API"""
    if request.method == 'POST':
        try:
            # 获取随机股票代码
            stock_codes, message = get_random_stock_codes(10)
            
            if stock_codes is None:
                return JsonResponse({'success': False, 'error': message})
            
            # 将股票代码用分号连接
            stock_codes_str = ';'.join(stock_codes)
            
            return JsonResponse({
                'success': True,
                'stock_codes': stock_codes_str,
                'message': f'成功获取 {len(stock_codes)} 个随机股票代码'
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': f'获取随机股票代码失败: {str(e)}'})
    
    else:
        return JsonResponse({'success': False, 'error': '请使用POST请求'})

@require_http_methods(["GET"])
def download_template(request):
    """
    下载模板文件
    """
    try:
        # 模板文件路径 - 根据你的实际路径调整
        template_path = os.path.join(settings.BASE_DIR, 'data', 'template.xlsx')
        # 检查文件是否存在
        if not os.path.exists(template_path):
            return JsonResponse({
                'success': False,
                'error': '模板文件不存在'
            }, status=404)
        
        # 读取文件内容
        with open(template_path, 'rb') as f:
            file_content = f.read()
        
        # 设置响应头
        response = HttpResponse(file_content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="stock_analysis_template.xlsx"'
        response['Content-Length'] = len(file_content)
        
        return response
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'下载失败: {str(e)}'
        }, status=500)
