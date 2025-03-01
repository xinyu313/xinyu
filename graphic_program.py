import matplotlib
matplotlib.use('TkAgg')  # 强制使用Tkinter后端
import networkx as nx
import matplotlib.pyplot as plt

# 判断给定的度序列是否可图化的函数
def is_graphic(degrees):
    # 如果度序列的总和不是偶数，则该度序列不可图化，返回False和None
    if sum(degrees) % 2 != 0:
        return False, None
    # 如果度序列中存在负数，则该度序列不可图化，返回False和None
    if any(d < 0 for d in degrees):
        return False, None
    # 获取度序列的长度，即顶点的数量
    n = len(degrees)
    # 将每个顶点的度数和其索引组成一个列表，如[[度1, 索引1], [度2, 索引2], ...]
    vertices = [[d, i] for i, d in enumerate(degrees)]
    # 初始化边的列表
    edges = []
    # 循环处理度序列，直到满足条件或确定不可图化
    while True:
        # 根据顶点的度数从大到小排序，如果度数相同则按索引从小到大排序
        vertices.sort(key=lambda x: (-x[0], x[1]))
        # 如果所有顶点的度数都为0，则说明度序列可图化，返回True和边的列表
        if all(v[0] == 0 for v in vertices):
            return True, edges
        # 取出度数最大的顶点及其索引
        v = vertices[0]
        current_degree, v_idx = v
        # 如果度数最大的顶点度数为0，说明度序列不可图化，返回False和None
        if current_degree == 0:
            return False, None
        # 如果度数最大的顶点度数大于剩余顶点的数量减1，说明度序列不可图化，返回False和None
        if current_degree > len(vertices) - 1:
            return False, None
        # 取出度数最大的顶点的邻居顶点（即度数次大的前current_degree个顶点）
        neighbors = vertices[1:current_degree + 1]
        # 遍历邻居顶点，减少它们的度数，并记录边
        for u in neighbors:
            u[0] -= 1
            # 如果邻居顶点的度数变为负数，说明度序列不可图化，返回False和None
            if u[0] < 0:
                return False, None
            # 将边添加到边的列表中
            edges.append((v_idx, u[1]))
        # 将度数最大的顶点的度数设为0
        v[0] = 0


def main():
    # 提示用户输入度序列，以逗号分隔
    input_str = input("请输入度序列（用逗号分隔）: ")
    # 将用户输入的字符串转换为整数列表，即度序列
    degrees = list(map(int, input_str.strip().split(',')))
    # 如果度序列中存在负数，直接输出"no"并返回
    if any(d < 0 for d in degrees):
        print("no")
        return
    # 调用is_graphic函数判断度序列是否可图化，并获取返回的结果（是否可图化和边的列表）
    valid, edges = is_graphic(degrees)
    # 如果度序列可图化
    if valid:
        print("yes")
        # 对每条边进行排序（确保边的两个顶点顺序一致），并将边的列表排序
        edges = [tuple(sorted(e)) for e in edges]
        edges.sort()
        print("边列表:", edges)

        # 生成邻接矩阵
        n = len(degrees)
        # 初始化邻接矩阵，所有元素为0
        adj_matrix = [[0] * n for _ in range(n)]
        # 根据边的列表填充邻接矩阵，有边的位置设为1
        for edge in edges:
            u, v = edge
            adj_matrix[u][v] = 1
            adj_matrix[v][u] = 1

        print("邻接矩阵:")
        # 打印邻接矩阵
        for row in adj_matrix:
            print(row)

        # 绘制简单图
        G = nx.Graph()
        # 将边的列表添加到图中
        G.add_edges_from(edges)
        # 使用spring_layout算法计算图中顶点的位置
        pos = nx.spring_layout(G)
        # 绘制图，设置节点标签、节点大小、节点颜色、字体大小、字体粗细等属性
        nx.draw(G, pos, with_labels=True, node_size=500, node_color='skyblue', font_size=10, font_weight='bold',
                arrows=False)
        # 设置图的标题
        plt.title("Simple Graph")
        # 显示绘制的图
        plt.show()
    else:
        print("no")


if __name__ == "__main__":
    main()


