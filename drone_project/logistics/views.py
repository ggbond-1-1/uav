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
    """后台线程：修复返回逻辑，增加序列号支持"""
    # 先通过ID获取无人机，缓存序列号（避免重复查询）
    try:
        drone = Drone.objects.get(pk=drone_id)
        serial_number = drone.serial_number  # 缓存序列号
        print(f"[线程初始化] 无人机 ID={drone_id} 序列号={serial_number}")
    except Drone.DoesNotExist:
        print(f"[初始化失败] 未找到ID为 {drone_id} 的无人机")
        return

    # 获取CSRF令牌
    csrf_token = get_csrf_token()
    
    # 正向路径移动（使用序列号日志）
    for x, y in path:
        try:
            headers = {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrf_token,
            }
            
            resp = requests.post(
                "http://127.0.0.1:8000/logistics/api/update_drone_position/",
                # 支持同时传递ID和序列号（兼容接口）
                json={"drone_id": drone_id, "serial_number": serial_number, "x": x, "y": y},
                headers=headers,
                allow_redirects=False
            )
            
            if resp.status_code == 200:
                print(f"[正向移动] 序列号 {serial_number}: ({x}, {y}) 更新成功")
            else:
                print(f"[正向移动] 序列号 {serial_number}: 状态码 {resp.status_code}")
                
        except Exception as e:
            print(f"[正向移动失败] 序列号 {serial_number}: {str(e)}")
        
        time.sleep(1)

    # 返回路径移动（核心修复：使用序列号）
    if return_path:
        print(f"[开始返回] 序列号 {serial_number} 开始返程，共 {len(return_path)} 步")
        for x, y in return_path:
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

    # 状态重置（使用序列号更新）
    try:
        # 重新查询最新状态（避免缓存过期）
        drone = Drone.objects.get(serial_number=serial_number)
        drone.current_status = 'in_stock'
        drone.current_load = 0
        drone.save()
        print(f"[状态更新] 序列号 {serial_number} 已设置为在库")
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
            if path and len(path) > 0:
                x0, y0 = path[0]
                print("写入初始位置点", x0, y0)
                DronePosition.objects.create(
                    drone=drone,
                    latitude=y0,
                    longitude=x0,
                )


            # 生成返回路径（保持不变）
            grid_size = (40, 40)
            abcd_points = random_abcd_points(grid_size)
            grid, polys = random_obstacles(grid_size)
            start_key = data.get('start', 'A')
            goal_key = data.get('goal', 'D')
            start = abcd_points[start_key]
            goal = abcd_points[goal_key]
            a_star_return = AStar(grid, goal, start)
            return_path, _ = a_star_return.find_path()


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
# 固定ABCD点位置
def random_abcd_points(grid_size, margin=5):
    rows, cols = grid_size
    # 固定ABCD位置
    points = {
        'A': (5, 5),      # 左上角
        'B': (13, 25),     # 右上角
        'C': (35, 5),     # 左下角
        'D': (20, 20),    # 右下角
    }
    return points


# 生成类似街区的障碍物
# 生成类似街区分布的障碍物
# 生成类似街道分布的障碍物
# 生成类似街道分布的障碍物
def random_obstacles(grid_size, num_rows=6, num_cols=6, building_width=3, building_height=3, street_width=3):
    rows, cols = grid_size
    grid = np.zeros(grid_size)
    polys = []


    # 生成规则排列的楼房
    for i in range(num_rows):
        for j in range(num_cols):
            # 计算楼房的左上角坐标
            start_x = i * (building_height + street_width) + 1
            start_y = j * (building_width + street_width) + 1


            # 确保楼房在网格范围内
            if start_x + building_height < rows and start_y + building_width < cols:
                # 创建矩形障碍物（楼房）
                poly = np.array([
                    [start_x, start_y],
                    [start_x + building_height, start_y],
                    [start_x + building_height, start_y + building_width],
                    [start_x, start_y + building_width]
                ])


                polys.append(poly)


                # 填充障碍物区域
                rr, cc = polygon(poly[:, 1], poly[:, 0], grid.shape)
                grid[rr, cc] = 1


    # 生成斜向街道
    def create_diagonal_street(grid, start_x, start_y, end_x, end_y, width):
        # 计算斜向街道的顶点
        dx = end_x - start_x
        dy = end_y - start_y
        length = int(np.sqrt(dx**2 + dy**2))
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


    # 创建两条斜向街道示例
    grid = create_diagonal_street(grid, 0, 0, rows - 1, cols - 1, street_width)
    grid = create_diagonal_street(grid, 0, cols - 1, rows - 1, 0, street_width)


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
    plt.figure(figsize=(7,7))
    plt.imshow(grid, cmap='gray_r', alpha=0.7)
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
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()
    buf.seek(0)
    return buf


@csrf_exempt
def plan_path(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        start_key = data.get('start', 'A')
        goal_key = data.get('goal', 'D')
        grid_size = (40, 40)
        abcd_points = random_abcd_points(grid_size)
        grid, polys = random_obstacles(grid_size)
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


@csrf_exempt
def get_active_drones(request):
    """获取所有正在飞行的无人机"""
    if request.method == 'GET':
        try:
            # 获取所有飞行中的无人机
            active_drones = Drone.objects.filter(current_status='in_flight')
            
            drone_data = []
            for drone in active_drones:
                # 获取最新位置
                latest_position = drone.positions.first()
                position_info = None
                if latest_position:
                    position_info = {
                        'latitude': latest_position.latitude,
                        'longitude': latest_position.longitude,
                        'altitude': latest_position.altitude,
                        'speed': latest_position.speed,
                        'heading': latest_position.heading,
                        'timestamp': latest_position.timestamp.isoformat()
                    }
                
                drone_data.append({
                    'id': drone.id,
                    'serial_number': drone.serial_number,
                    'model': drone.model,
                    'current_load': drone.current_load,
                    'max_takeoff_weight': drone.max_takeoff_weight,
                    'position': position_info
                })
            
            return JsonResponse({
                'success': True,
                'drones': drone_data,
                'count': len(drone_data)
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': '仅支持GET请求'}, status=405)




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
