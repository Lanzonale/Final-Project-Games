#3.0的启发式在原本基础上加了简单的启发式 测试可以过baseline 再优化可以从调整函数常数和扩展启发式考量下手 目前启发式只考虑了尽量往中心下棋 阻止对方连棋和鼓励己方连棋 关于己方差一赢时优先选择 己方和对方皆为2连时如何选择等并没有写，更进一步可以考虑给蒙特卡洛模拟结合剪枝
#评估分数和模拟的部分加了时间限制 这两块比较容易超时导致提交不上去
#模拟次数好像更高效果还没那么好 所以设定是5次
import random
import math
import time

def is_timeout(start_time, time_limit):#时间限制
    return time.time() - start_time > time_limit


class Node:
    def __init__(self, state, parent=None):
        self.state = state
        self.parent = parent
        self.children = []
        self.wins = 0
        self.visits = 0




    def select_child(self):
        def ucb(c):
            if c.visits == 0:
                return float('inf')  # 未访问的子节点UCB值=inf
            else:
                return c.wins / c.visits + 2*( math.log(self.visits) / c.visits) ** 0.5
                #math前面的系数2可改

        return max(self.children, key=ucb)




    def expand(self, configuration):
        for c in range(configuration['columns']):
            if self.state['board'][c] == 0:
                new_board = list(self.state['board'])  # 复制当前棋盘状态


                for i in range((c + 1) * configuration['rows'] - 1, c * configuration['rows'] - 1, -1):
                    if new_board[i] == 0:
                        new_board[i] = self.state['mark']

                        # 创建一个新的观察状态
                        new_state = {
                            'board': new_board,
                            'mark': 3 - self.state['mark']  # 交换玩家 (1 -> 2 or 2 -> 1)
                        }
                        self.children.append(Node(new_state, self))
                        break



    def backpropagate(self, result):

        self.visits += 1
        self.wins += result
        if self.parent:
            self.parent.backpropagate(result)


def get_best_move(root_state, best_child_state, configuration,start_time, time_limit):
    for c in range(configuration['columns']):
        col_top_idx = c
        if root_state['board'][col_top_idx] == 0 and best_child_state['board'][col_top_idx] != 0:
            return c

    # 随机选择一个可用列
    available_columns = [c for c in range(configuration['columns']) if root_state['board'][c] == 0]
    if available_columns:
        scores = [evaluate_column(c, root_state['board'], root_state['mark'], configuration,start_time, time_limit) for c in available_columns]
        return available_columns[scores.index(max(scores))]

    return 0  # 默认返回第0列（意外情况）



def evaluate_column(column, board, mark, configuration,start_time, time_limit):
    if is_timeout(start_time, time_limit):#超时时返回-inf（最差解） 强迫在已有的节点选择最优解
        return float('-inf')

    score = 0
    opponent_mark = 3 - mark
    center_column = configuration['columns'] // 2

    # 奖励靠近中心位置
    score += (1 / (abs(column - center_column) + 1)) * 10

    directions = [#横竖及正负对角
        (0, 1),
        (1, 1),
        (1, 0),
        (1, -1),]

    # 为每个可能位置计算得分
    for row in range(configuration['rows']):
        idx = column + row * configuration['columns']
        if board[idx] == 0:
            for dx, dy in directions:
                continuous_self = sum(1 for i in range(4)
                                      if 0 <= column + i * dx < configuration['columns']
                                      and 0 <= row + i * dy < configuration['rows']
                                      and board[(column + i * dx) + (row + i * dy) * configuration['columns']] == mark)

                continuous_opponent = sum(1 for i in range(4)
                                          if 0 <= column + i * dx < configuration['columns']
                                          and 0 <= row + i * dy < configuration['rows']
                                          and board[(column + i * dx) + (row + i * dy) * configuration['columns']] == opponent_mark)



                if continuous_opponent == 3:  # 对方差一个就能赢时优先堵住
                    return float('inf')

                score += continuous_self * 10  # 奖励形成连续棋子数

    return score

def simulate_game(state,start_time, time_limit):

    current_board = list(state['board'])
    current_mark = state['mark']
    configuration = {
        'columns': 7,
        'rows': 6,
    }



    def is_terminal(board, last_col, last_row):
        # 检查列
        if sum(1 for i in range(last_row, len(board), configuration['columns']) if board[i] == board[last_row * configuration['columns'] + last_col]) >= 4:
            return True

        # 检查行
        if sum(1 for i in range(max(last_col - 3, 0), min(last_col + 4, configuration['columns'])) if board[last_row * configuration['columns'] + i] == board[last_row * configuration['columns'] + last_col]) >= 4:
            return True

        # 检查正对角线
        if sum(1 for i in range(-3, 4) if 0 <= last_col + i < configuration['columns'] and 0 <= last_row + i < configuration['rows'] and board[(last_row + i) * configuration['columns'] + last_col + i] == board[last_row * configuration['columns'] + last_col]) >= 4:
            return True

        # 检查反对角线
        if sum(1 for i in range(-3, 4) if 0 <= last_col + i < configuration['columns'] and 0 <= last_row - i < configuration['rows'] and board[(last_row - i) * configuration['columns'] + last_col + i] == board[last_row * configuration['columns'] + last_col]) >= 4:
            return True

        return False


    def get_available_columns(board):
        return [c for c in range(configuration['columns']) if board[c] == 0]

    while True:
        if is_timeout(start_time, time_limit):
            return 0
        available_columns = get_available_columns(current_board)
        if not available_columns:
            return 0

        #chosen_column = random.choice(available_columns)未加启发式的算法 忽视
         # 使用评估函数选择列
        scores = [evaluate_column(c, current_board, current_mark, configuration,start_time, time_limit) for c in available_columns]
        chosen_column = available_columns[scores.index(max(scores))]

        last_row = -1
        for i in range((chosen_column + 1) * configuration['rows'] - 1, chosen_column * configuration['rows'] - 1, -1):
            if current_board[i] == 0:
                current_board[i] = current_mark
                last_row = i // configuration['columns']  # 计算行号
                break


        if is_terminal(current_board, chosen_column, last_row):
            if current_mark == state['mark']:
                return 1  # 己赢
            else:
                return -1  # 对方赢


        current_mark = 3 - current_mark


def my_agent(observation, configuration):
    start_time = time.time()  # 记录开始时间
    time_limit = 1.8#可改 建议不要太大
    num_simulations = 5#可改
    root = Node(observation)

    for _ in range(num_simulations):
        if time.time() - start_time > time_limit:  # 检查是否超时
            break  # 超时立即退出
        node = root
        # 选择和扩展
        while node.children:
            node = node.select_child()
        node.expand(configuration)

        # 模拟
        result = simulate_game(node.state,start_time,time_limit)
        # 反向传播
        node.backpropagate(result)

    # 选择访问次数最多的子节点
    if root.children:
        best_child = sorted(root.children, key=lambda c: c.visits)[-1]
        best_move = get_best_move(root.state, best_child.state, configuration,start_time, time_limit)
    else:

        available_columns = [c for c in range(configuration['columns']) if observation['board'][c] == 0]
        scores = [evaluate_column(c, observation['board'], observation['mark'], configuration,start_time, time_limit) for c in available_columns]
        best_move = available_columns[scores.index(max(scores))]

    return best_move
