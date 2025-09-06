import numpy as np
import matplotlib
matplotlib.use('Agg')  # 后端渲染
import matplotlib.pyplot as plt


# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans']  # 优先使用黑体，回退到DejaVu Sans
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题
from skimage.draw import polygon
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import get_token
import json
import heapq
import io
from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from drones.models import Drone, DronePosition
from django.shortcuts import render


import threading
import time
import requests
def auto_move(drone_id, path, return_path=None):
    try:
        drone = Drone.objects.get(pk=drone_id)
        serial_number = drone.serial_number
        # 生成唯一任务ID（如序列号+时间戳）
        task_id = f"{serial_number}_{int(time.time())}"
        print(f"[线程初始化] 任务ID: {task_id} 无人机: {serial_number}")
    except Drone.DoesNotExist:
        print(f"[初始化失败] 未找到ID为 {drone_id} 的无人机")
        return

    # 正向路径移动时，保存位置并关联task_id
    csrf_token = get_csrf_token()
    for x, y in path:
        try:
            # ... 现有请求逻辑 ...
            # 同时更新DronePosition的task_id
            DronePosition.objects.create(
                drone=drone,
                latitude=y,
                longitude=x,
                task_id=task_id  # 关联任务ID
            )
        except Exception as e:
            print(f"[正向移动失败] 序列号 {serial_number}: {str(e)}")
        time.sleep(3)

    # 返回路径移动（核心修复：使用序列号）
    if return_path:
        print(f"[开始返回] 序列号 {serial_number} 开始返程，共 {len(return_path)} 步")
        for i, (x, y) in enumerate(return_path):
            print(f"[返程进度] 序列号 {serial_number}: 第{i+1}/{len(return_path)}步 ({x}, {y})")
            try:
                headers = {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrf_token,
                }
                
                resp = requests.post(
                    "http://127.0.0.1:8000/logistics/api/update_drone_position/",
                    # 明确传递序列号
                    json={"serial_number": serial_number, "x": x, "y": y},
                    headers=headers,
                    allow_redirects=False
                )
                
                if resp.status_code == 200:
                    print(f"[返程移动] 序列号 {serial_number}: ({x}, {y}) 更新成功")
                else:
                    print(f"[返程移动] 序列号 {serial_number}: 状态码 {resp.status_code}")
                    
            except Exception as e:
                print(f"[返程移动失败] 序列号 {serial_number}: {str(e)}")
            
            time.sleep(1)
        print(f"[返回完成] 序列号 {serial_number} 已到达起点")
        print(f"[状态重置] 开始重置无人机 {serial_number} 的状态...")

    # 状态重置（使用序列号更新）
    try:
        # 重新查询最新状态（避免缓存过期）
        drone = Drone.objects.get(serial_number=serial_number)
        drone.current_status = 'in_stock'
        drone.current_load = 0
        drone.save()
        print(f"[状态更新] 序列号 {serial_number} 已设置为在库")
        
        # 更新对应的货物状态为已送达
        from goods.models import Goods
        try:
            # 查找该无人机正在运输的货物（包括所有非已送达状态的货物）
            goods = Goods.objects.filter(drone=drone).exclude(status='delivered').first()
            if goods:
                print(f"[货物状态更新] 找到货物 {goods.id}，当前状态: {goods.status}")
                goods.status = 'delivered'
                goods.save()
                print(f"[货物状态更新] 货物 {goods.id} 状态已更新为已送达")
                
                # 验证更新是否成功
                goods.refresh_from_db()
                print(f"[货物状态验证] 货物 {goods.id} 更新后状态: {goods.status}")
            else:
                # 调试：查看该无人机的所有货物
                all_goods = Goods.objects.filter(drone=drone)
                print(f"[货物状态更新] 无人机 {serial_number} 的所有货物: {[(g.id, g.status) for g in all_goods]}")
                print(f"[货物状态更新] 未找到无人机 {serial_number} 需要更新的货物")
                
                # 如果没有找到货物，尝试更新所有该无人机的货物状态
                if all_goods.exists():
                    print(f"[货物状态更新] 尝试更新所有货物的状态...")
                    for g in all_goods:
                        if g.status != 'delivered':
                            g.status = 'delivered'
                            g.save()
                            print(f"[货物状态更新] 强制更新货物 {g.id} 状态为已送达")
        except Exception as e:
            print(f"[货物状态更新异常] 序列号 {serial_number}: {str(e)}")
            import traceback
            print(f"[货物状态更新异常] 详细错误: {traceback.format_exc()}")
            
    except Drone.DoesNotExist:
        print(f"[状态更新失败] 未找到序列号 {serial_number} 的无人机")
    except Exception as e:
        print(f"[状态更新异常] 序列号 {serial_number}: {str(e)}")


@csrf_exempt
def assign_task(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        # 关键修改：接收serial_number而非drone_id
        serial_number = data.get('serial_number')  # 前端传序列号
        path = data.get('path')
        if not (serial_number and path):
            return JsonResponse({'success': False, 'message': '缺少参数（需序列号和路径）'})
        
        try:
            # 关键修改：通过序列号查询无人机
            drone = Drone.objects.get(serial_number=serial_number)
            drone.current_status = 'in_flight' 
            drone.save()
            
            # 调试：打印接收到的参数
            start_key = data.get('start', 'A')
            goal_key = data.get('goal', 'D')
            print(f"[任务分配] 无人机 {serial_number}: 起点={start_key}, 终点={goal_key}")
            if path and len(path) > 0:
                x0, y0 = path[0]
                print("写入初始位置点", x0, y0)
                DronePosition.objects.create(
                    drone=drone,
                    latitude=y0,
                    longitude=x0,
                )


            # 生成返回路径（使用60x60网格）
            grid_size = (60, 60)
            abcd_points = get_static_abcd_points(grid_size)
            grid, polys = get_static_obstacles(grid_size)
            # 使用之前获取的start_key和goal_key
            start = abcd_points[start_key]
            goal = abcd_points[goal_key]
            print(f"[返回路径] 从 {goal_key}({goal}) 返回到 {start_key}({start})")
            a_star_return = AStar(grid, goal, start)
            return_path, _ = a_star_return.find_path()
            print(f"[返回路径] 生成返回路径，共 {len(return_path)} 步")


            # 关键修改：线程传递无人机ID（内部仍用ID操作）
            t = threading.Thread(target=auto_move, args=(drone.id, path, return_path))
            t.start()
            return JsonResponse({'success': True, 'message': f'任务分配成功，无人机 {serial_number} 已开始移动'})
        
        except Drone.DoesNotExist:
            return JsonResponse({'error': f'未找到序列号为 {serial_number} 的无人机'}, status=404)
    else:
        return JsonResponse({'error': '仅支持POST请求'}, status=405)


    
def logistics_list(request):
    """物流跟踪列表页面"""
    return HttpResponse("This is the logistics list view.")


def logistics_detail(request):
    """物流跟踪详情页面 - 显示地图页面"""
    sender_address = request.GET.get('sender_address', '')
    receiver_address = request.GET.get('receiver_address', '')
    
    return render(request, '12地图页.html', {
        'sender_address': sender_address,
        'receiver_address': receiver_address,
    })


# 固定ABCD点位置
def get_static_abcd_points(grid_size, margin=5):
    rows, cols = grid_size
    # 修复ABCD位置坐标系统
    points = {
        'A': (8, 8),      # 左上角
        'B': (52, 8),     # 右上角 - 修复：x=52, y=8
        'C': (8, 52),     # 左下角 - 修复：x=8, y=52  
        'D': (30, 30),    # 中心点
    }
    return points


# 生成适中的静态障碍物布局
def get_static_obstacles(grid_size):
    """生成适中的静态障碍物布局，平衡清晰度和真实感"""
    rows, cols = grid_size
    grid = np.zeros(grid_size)
    polys = []

    # 适中的建筑物布局 - 增加一些障碍物但保持清晰
    buildings = [
        # 左上角区域 - 适量建筑物
        (5, 5, 4, 4), (12, 5, 4, 4), (19, 5, 4, 4), (26, 5, 4, 4),
        (5, 12, 4, 4), (12, 12, 4, 4), (19, 12, 4, 4), (26, 12, 4, 4),
        (5, 19, 4, 4), (12, 19, 4, 4), (19, 19, 4, 4), (26, 19, 4, 4),
        
        # 右上角区域 - 适量建筑物
        (35, 5, 4, 4), (42, 5, 4, 4), (49, 5, 4, 4), (56, 5, 4, 4),
        (35, 12, 4, 4), (42, 12, 4, 4), (49, 12, 4, 4), (56, 12, 4, 4),
        (35, 19, 4, 4), (42, 19, 4, 4), (49, 19, 4, 4), (56, 19, 4, 4),
        
        # 左下角区域 - 适量建筑物
        (5, 35, 4, 4), (12, 35, 4, 4), (19, 35, 4, 4), (26, 35, 4, 4),
        (5, 42, 4, 4), (12, 42, 4, 4), (19, 42, 4, 4), (26, 42, 4, 4),
        (5, 49, 4, 4), (12, 49, 4, 4), (19, 49, 4, 4), (26, 49, 4, 4),
        
        # 右下角区域 - 适量建筑物
        (35, 35, 4, 4), (42, 35, 4, 4), (49, 35, 4, 4), (56, 35, 4, 4),
        (35, 42, 4, 4), (42, 42, 4, 4), (49, 42, 4, 4), (56, 42, 4, 4),
        (35, 49, 4, 4), (42, 49, 4, 4), (49, 49, 4, 4), (56, 49, 4, 4),
        
        # 中心区域 - 一些建筑物作为参考点
        (20, 20, 6, 6), (30, 20, 6, 6), (40, 20, 6, 6),
        (20, 30, 6, 6), (30, 30, 6, 6), (40, 30, 6, 6),
        (20, 40, 6, 6), (30, 40, 6, 6), (40, 40, 6, 6),
        
        # 添加一些随机分布的建筑物增加真实感
        (15, 15, 3, 3), (45, 15, 3, 3), (15, 45, 3, 3), (45, 45, 3, 3),
        (25, 10, 3, 3), (35, 10, 3, 3), (25, 50, 3, 3), (35, 50, 3, 3),
        (10, 25, 3, 3), (50, 25, 3, 3), (10, 35, 3, 3), (50, 35, 3, 3),
    ]

    # 在网格上放置建筑物
    for start_x, start_y, width, height in buildings:
        # 确保建筑物在网格范围内
        if start_x + width < rows and start_y + height < cols:
            # 创建矩形障碍物（建筑物）
            poly = np.array([
                [start_x, start_y],
                [start_x + width, start_y],
                [start_x + width, start_y + height],
                [start_x, start_y + height]
            ])
            
            polys.append(poly)
            
            # 填充障碍物区域
            rr, cc = polygon(poly[:, 1], poly[:, 0], grid.shape)
            grid[rr, cc] = 1

    # 创建街道布局
    def create_street(grid, start_x, start_y, end_x, end_y, width):
        """创建固定宽度的街道"""
        # 计算街道的四个顶点
        dx = end_x - start_x
        dy = end_y - start_y
        angle = np.arctan2(dy, dx)
        half_width = width // 2

        # 计算街道的四个顶点
        left_top = (start_x - half_width * np.sin(angle), start_y + half_width * np.cos(angle))
        right_top = (start_x + half_width * np.sin(angle), start_y - half_width * np.cos(angle))
        left_bottom = (end_x - half_width * np.sin(angle), end_y + half_width * np.cos(angle))
        right_bottom = (end_x + half_width * np.sin(angle), end_y - half_width * np.cos(angle))

        street_poly = np.array([
            left_top, right_top, right_bottom, left_bottom
        ], dtype=int)

        # 清除街道区域的障碍物
        rr, cc = polygon(street_poly[:, 1], street_poly[:, 0], grid.shape)
        grid[rr, cc] = 0

        return grid

    # 创建街道网络
    street_width = 5
    # 主要水平街道
    grid = create_street(grid, 0, 15, cols-1, 15, street_width)  # 上部分水平街道
    grid = create_street(grid, 0, 30, cols-1, 30, street_width)  # 中心水平街道
    grid = create_street(grid, 0, 45, cols-1, 45, street_width)  # 下部分水平街道
    
    # 主要垂直街道
    grid = create_street(grid, 15, 0, 15, rows-1, street_width)  # 左部分垂直街道
    grid = create_street(grid, 30, 0, 30, rows-1, street_width)  # 中心垂直街道
    grid = create_street(grid, 45, 0, 45, rows-1, street_width)  # 右部分垂直街道
    
    # 两条对角线街道 - 连接四个角落
    grid = create_street(grid, 0, 0, rows-1, cols-1, street_width)  # 左上到右下
    grid = create_street(grid, 0, cols-1, rows-1, 0, street_width)  # 右上到左下

    return grid, polys
class Node:
    def __init__(self, x, y, g_cost=float('inf'), h_cost=float('inf'), parent=None):
        self.x = x
        self.y = y
        self.g_cost = g_cost
        self.h_cost = h_cost
        self.f_cost = g_cost + h_cost
        self.parent = parent


    def __lt__(self, other):
        return self.f_cost < other.f_cost


class AStar:
    def __init__(self, grid, start, goal):
        self.grid = grid
        self.start = start
        self.goal = goal
        self.rows, self.cols = grid.shape
        self.directions = [(-1, -1), (-1, 0), (-1, 1),
                           (0, -1), (0, 1),
                           (1, -1), (1, 0), (1, 1)]


    def heuristic(self, node):
        return abs(node.x - self.goal[0]) + abs(node.y - self.goal[1])


    def is_valid(self, x, y):
        return 0 <= x < self.rows and 0 <= y < self.cols and self.grid[x, y] == 0


    def find_path(self):
        start_node = Node(self.start[0], self.start[1], 0, self.heuristic(Node(self.start[0], self.start[1])))
        goal_node = Node(self.goal[0], self.goal[1])
        open_list = []
        closed_set = set()
        heapq.heappush(open_list, (start_node.f_cost, start_node))
        node_map = {(start_node.x, start_node.y): start_node}


        while open_list:
            _, current_node = heapq.heappop(open_list)
            if (current_node.x, current_node.y) == (goal_node.x, goal_node.y):
                path = []
                while current_node:
                    path.append((current_node.x, current_node.y))
                    current_node = current_node.parent
                return path[::-1], None
            closed_set.add((current_node.x, current_node.y))
            for dx, dy in self.directions:
                nx, ny = current_node.x + dx, current_node.y + dy
                if not self.is_valid(nx, ny) or (nx, ny) in closed_set:
                    continue
                move_cost = 1.0 if dx == 0 or dy == 0 else 1.4
                new_g_cost = current_node.g_cost + move_cost
                if (nx, ny) not in node_map or new_g_cost < node_map[(nx, ny)].g_cost:
                    neighbor = Node(nx, ny)
                    neighbor.g_cost = new_g_cost
                    neighbor.h_cost = self.heuristic(neighbor)
                    neighbor.f_cost = neighbor.g_cost + neighbor.h_cost
                    neighbor.parent = current_node
                    node_map[(nx, ny)] = neighbor
                    heapq.heappush(open_list, (neighbor.f_cost, neighbor))
        return [], None


# 可视化
# 可视化
def plot_map(grid, abcd_points, path, polys, start_key, goal_key):
    plt.figure(figsize=(10,10))
    plt.imshow(grid, cmap='gray_r', alpha=0.7, extent=[0, grid.shape[1], grid.shape[0], 0])
    # 去掉障碍物背景填充
    # for poly in polys:
    #     plt.fill(poly[:,1], poly[:,0], color='black')
    for k, (x, y) in abcd_points.items():
        plt.scatter(y, x, s=200, label=k)
        plt.text(y, x, k, fontsize=16, color='white', ha='center', va='center', weight='bold')
    if path:
        px, py = zip(*path)
        plt.plot(py, px, 'r-', linewidth=3, label='最优路径')
    sx, sy = abcd_points[start_key]
    gx, gy = abcd_points[goal_key]
    plt.scatter([sy], [sx], c='lime', s=300, marker='*', label='起点')
    plt.scatter([gy], [gx], c='red', s=300, marker='*', label='终点')
    plt.legend()
    plt.axis('off')
    # 设置图像边界，确保没有额外边距
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches=None, pad_inches=0, dpi=100)
    plt.close()
    buf.seek(0)
    return buf


@csrf_exempt
def plan_path(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        start_key = data.get('start', 'A')
        goal_key = data.get('goal', 'D')
        grid_size = (60, 60)
        abcd_points = get_static_abcd_points(grid_size)
        grid, polys = get_static_obstacles(grid_size)
        start = abcd_points[start_key]
        goal = abcd_points[goal_key]
        a_star = AStar(grid, start, goal)
        path, _ = a_star.find_path()
        if request.headers.get('Accept') == 'application/json':
            return JsonResponse({'success': True, 'path': path})
        buf = plot_map(grid, abcd_points, path, polys, start_key, goal_key)
        return HttpResponse(buf.getvalue(), content_type='image/png')
    else:
        return HttpResponse('仅支持POST请求', status=405)@csrf_exempt
# 1. 首先确保装饰器正确应用且逻辑完整
@csrf_exempt  # 关键：必须确保这个装饰器生效
def update_drone_position(request):
    """更新无人机实时位置（修复CSRF和错误处理）"""
    if request.method == 'POST':
        try:
            # 先检查请求体是否为空
            if not request.body:
                return JsonResponse({'error': '请求体不能为空'}, status=400)
                
            # 解析JSON数据（添加异常捕获）
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError as e:
                return JsonResponse({'error': f'JSON解析错误: {str(e)}'}, status=400)
            
            # 获取无人机标识（支持ID或序列号）
            drone_identifier = data.get('drone_id') or data.get('serial_number')
            x = data.get('x')
            y = data.get('y')
            
            if not all([drone_identifier, x is not None, y is not None]):
                return JsonResponse({
                    'error': '缺少必要参数（无人机标识、x、y必须提供）'
                }, status=400)
            
            # 查询无人机（支持ID和序列号）
            try:
                # 先尝试ID查询
                drone = Drone.objects.get(pk=drone_identifier)
            except (ValueError, Drone.DoesNotExist):
                # 再尝试序列号查询
                try:
                    drone = Drone.objects.get(serial_number=drone_identifier)
                except Drone.DoesNotExist:
                    return JsonResponse({
                        'error': f'未找到无人机（标识: {drone_identifier}）'
                    }, status=404)
            
            # 创建位置记录
            position = DronePosition.objects.create(
                drone=drone,
                latitude=float(y),
                longitude=float(x),
            )
            
            return JsonResponse({
                'success': True,
                'message': f'位置更新成功',
                'timestamp': position.timestamp.isoformat()
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    # 非POST请求处理
    return JsonResponse({'error': '仅支持POST请求'}, status=405)


def get_active_drones(request):
    active_drones = Drone.objects.filter(current_status='in_flight')
    data = []
    
    # 货物状态中文映射
    goods_status_map = {
        'pending': '待发货',
        'in_transit': '运输中',
        'delivered': '已送达',
        'issue': '问题件',
        '无货物': '无货物',
        '无位置记录': '无位置记录'
    }
    
    for drone in active_drones:
        try:
            latest_pos = DronePosition.objects.filter(drone=drone).latest('id')
            
            # 获取该无人机的货物状态
            from goods.models import Goods
            goods = Goods.objects.filter(drone=drone).first()
            goods_status = goods.status if goods else '无货物'
            
            # 转换为中文状态
            goods_status_chinese = goods_status_map.get(goods_status, goods_status)
            
            data.append({
                'serial_number': drone.serial_number,
                'model': drone.model,
                'current_status': drone.current_status,
                'goods_status': goods_status_chinese,
                'task_id': latest_pos.task_id,  # 返回任务ID
                'current_position': {
                    'x': latest_pos.longitude,
                    'y': latest_pos.latitude
                }
            })
        except DronePosition.DoesNotExist:
            # 如果无人机没有位置记录，跳过该无人机或提供默认位置
            data.append({
                'serial_number': drone.serial_number,
                'model': drone.model,
                'current_status': drone.current_status,
                'goods_status': '无位置记录',
                'task_id': None,
                'current_position': {
                    'x': 0.0,
                    'y': 0.0
                },
                'note': '暂无位置信息'
            })
    return JsonResponse({'success': True, 'drones': data})

def get_all_drones_status(request):
    """获取所有无人机的状态信息（用于调试）"""
    all_drones = Drone.objects.all()
    data = []
    
    # 货物状态中文映射
    goods_status_map = {
        'pending': '待发货',
        'in_transit': '运输中',
        'delivered': '已送达',
        'issue': '问题件',
        '无货物': '无货物',
        '无位置记录': '无位置记录'
    }
    
    for drone in all_drones:
        try:
            latest_pos = DronePosition.objects.filter(drone=drone).latest('id')
            # 获取该无人机的货物状态
            from goods.models import Goods
            goods = Goods.objects.filter(drone=drone).first()
            goods_status = goods.status if goods else '无货物'
            
            # 转换为中文状态
            goods_status_chinese = goods_status_map.get(goods_status, goods_status)
            
            data.append({
                'serial_number': drone.serial_number,
                'model': drone.model,
                'current_status': drone.current_status,
                'goods_status': goods_status_chinese,
                'task_id': latest_pos.task_id,
                'current_position': {
                    'x': latest_pos.longitude,
                    'y': latest_pos.latitude
                }
            })
        except DronePosition.DoesNotExist:
            data.append({
                'serial_number': drone.serial_number,
                'model': drone.model,
                'current_status': drone.current_status,
                'goods_status': '无位置记录',
                'task_id': None,
                'current_position': None
            })
    return JsonResponse({'success': True, 'drones': data})

@csrf_exempt
def force_update_goods_status(request):
    """强制更新货物状态为已送达（用于调试）"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            serial_number = data.get('serial_number')
            
            if not serial_number:
                return JsonResponse({'error': '缺少serial_number参数'}, status=400)
            
            # 查找无人机
            try:
                drone = Drone.objects.get(serial_number=serial_number)
            except Drone.DoesNotExist:
                return JsonResponse({'error': f'未找到序列号为 {serial_number} 的无人机'}, status=404)
            
            # 更新该无人机的所有货物状态
            from goods.models import Goods
            goods_list = Goods.objects.filter(drone=drone)
            updated_count = 0
            
            for goods in goods_list:
                if goods.status != 'delivered':
                    goods.status = 'delivered'
                    goods.save()
                    updated_count += 1
                    print(f"[强制更新] 货物 {goods.id} 状态已更新为已送达")
            
            return JsonResponse({
                'success': True,
                'message': f'成功更新 {updated_count} 个货物的状态',
                'drone_status': drone.current_status,
                'updated_goods': updated_count
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': '仅支持POST请求'}, status=405)

@csrf_exempt
def clear_old_positions(request):
    """清理超过5分钟的旧位置记录"""
    if request.method == 'POST':
        try:
            five_minutes_ago = timezone.now() - timedelta(minutes=5)
            deleted_count = DronePosition.objects.filter(
                timestamp__lt=five_minutes_ago
            ).delete()[0]
            
            return JsonResponse({
                'success': True,
                'message': f'已清理 {deleted_count} 条旧位置记录'
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': '仅支持POST请求'}, status=405)
def get_csrf_token():
    """获取Django的CSRF令牌（开发环境用）"""
    try:
        # 先发送GET请求获取CSRF令牌
        resp = requests.get("http://127.0.0.1:8000/logistics/api/get_csrf/")
        return resp.cookies.get('csrftoken', '')
    except Exception as e:
        print(f"获取CSRF令牌失败: {e}")
        return ''

# 4. 添加获取CSRF令牌的接口
@csrf_exempt
def get_csrf(request):
    """提供CSRF令牌的接口"""
    return JsonResponse({'csrf_token': get_token(request)})

@csrf_exempt
def emergency_stop(request):
    """紧急停止所有无人机"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            reason = data.get('reason', 'unknown')
            timestamp = data.get('timestamp', timezone.now().isoformat())
            
            print(f"[紧急停止] 原因: {reason}, 时间: {timestamp}")
            
            # 获取所有飞行中的无人机
            flying_drones = Drone.objects.filter(current_status='in_flight')
            stopped_count = 0
            
            for drone in flying_drones:
                # 将无人机状态改为在库
                drone.current_status = 'in_stock'
                drone.save()
                stopped_count += 1
                print(f"[紧急停止] 无人机 {drone.serial_number} 已停止")
                
                # 更新相关货物的状态
                from goods.models import Goods
                goods_list = Goods.objects.filter(drone=drone, status='in_transit')
                for goods in goods_list:
                    goods.status = 'delivered'  # 或者改为其他状态
                    goods.save()
                    print(f"[紧急停止] 货物 {goods.id} 状态已更新")
            
            return JsonResponse({
                'success': True,
                'message': f'紧急停止成功，已停止 {stopped_count} 架无人机',
                'stopped_drones': stopped_count,
                'reason': reason,
                'timestamp': timestamp
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': '仅支持POST请求'}, status=405)

def real_time_tracking(request):
    """实时位置追踪页面"""
    return render(request, '13无人机实时位置.html')
