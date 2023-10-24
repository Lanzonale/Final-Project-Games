import random
import math
import time

def is_timeout(start_time, time_limit):
    return time.time() - start_time > time_limit


class Node:
    def __init__(self, state, parent=None):
        self.state = state
        self.parent = parent
        self.children = []
        self.wins = 0
        self.visits = 0






    def select_child(self, configuration):
        def ucb(c):
            if c.visits == 0:
                return float('inf')  # 未访问的子节点得到无限大的UCB值
            heuristic_value = evaluate_column(c.state['board'].index(0), c.state['board'], c.state['mark'], configuration, time.time(), 1.8)
            return c.wins / c.visits + 2* (math.log(self.visits) / c.visits) ** 0.5 + heuristic_value

        return max(self.children, key=ucb)


    def expand(self, configuration):
        urgent_moves = []
        for c in range(configuration['columns']):
            if self.state['board'][c] == 0:  # 可以在此列下棋
                heuristic_value = evaluate_column(c, self.state['board'], self.state['mark'], configuration, time.time(), 1.8)
                if heuristic_value == float('inf'):
                    urgent_moves.append(c)
                else:
                    new_board = list(self.state['board'])  # 复制当前棋盘状态

                    # 寻找该列的第一个空位置
                    for i in range((c + 1) * configuration['rows'] - 1, c * configuration['rows'] - 1, -1):
                        if new_board[i] == 0:
                            new_board[i] = self.state['mark']  # 放置棋子

                            # 创建一个新的观察状态
                            new_state = {
                                'board': new_board,
                                'mark': 3 - self.state['mark']  # 交换玩家 (1 -> 2 or 2 -> 1)
                            }
                            self.children.append(Node(new_state, self))
                            break

        # 如果有紧急的行动需要执行，只扩展这些紧急的行动
        if urgent_moves:
            self.children = [child for child in self.children if child.state['board'].index(0) in urgent_moves]

    def backpropagate(self, result):
        """ 反向传播模拟结果 """
        self.visits += 1
        self.wins += result
        if self.parent:
            self.parent.backpropagate(result)

def get_best_move(root_state, best_child_state, configuration, start_time, time_limit):
    for c in range(configuration['columns']):
        col_top_idx = c
        if root_state['board'][col_top_idx] == 0 and best_child_state['board'][col_top_idx] != 0:
            return c

    # 在检查可用列之前，检查是否有列的评分为inf
    available_columns = [c for c in range(configuration['columns']) if root_state['board'][c] == 0]
    scores = [evaluate_column(c, root_state['board'], root_state['mark'], configuration, start_time, time_limit) for c in available_columns]

    # 如果有评分为inf的列，直接返回这一列
    if float('inf') in scores:
        return available_columns[scores.index(float("inf"))]

    # 如果没有评分为inf的列，选择得分最高的列
    return available_columns[scores.index(max(scores))]


def evaluate_column(column, board, mark, configuration,start_time, time_limit):
    if is_timeout(start_time, time_limit):
        return float('-inf')

    score = 0
    opponent_mark = 3 - mark
    center_column = configuration['columns'] // 2

    # 奖励靠近中心位置
    score += (1 / (abs(column - center_column) + 1)) * 10

    directions = [
        (0, 1),  # Horizontal
        (0,-1),
        (-1,0),
        (1, 1),  # Diagonal (positive slope)
        (1, 0),  # Vertical
        (-1, 1),
        (1,-1),
        (-1,-1)# Diagonal (negative slope)

    ]

    # 为每个可能的放置位置计算得分
    for row in range(configuration['rows']):
        idx = column + row * configuration['columns']
        if board[idx] == 0:
            for dx, dy in directions:
                continuous_self = 0
                opponent_mark = 3 - mark
                opponent_count = 0

                space_count = 0
                for i in range(4):
                    new_col = column + i * dx
                    new_row = row + i * dy
                    # 确保位置在棋盘边界内
                    if 0 <= new_col < configuration['columns'] and 0 <= new_row < configuration['rows']:
                        if board[new_col + new_row * configuration['columns']] == 0:
                            space_count += 1
                        elif board[new_col + new_row * configuration['columns']] == opponent_mark:
                            opponent_count += 1
                    else:
                        # 如果超出边界，直接跳出
                        break

                if opponent_count == 3 and space_count == 1:
        # 如果在这四个位置中有三个被敌方的棋子占据，且还有一个空位置
                    return float('inf')

            forks = 0
            for dx, dy in directions:
                potential_forks = sum(1 for i in range(4)
                                      if 0 <= column + i * dx < configuration['columns']
                                      and 0 <= row + i * dy < configuration['rows']
                                      and board[(column + i * dx) + (row + i * dy) * configuration['columns']] == mark)
                if potential_forks == 2:  # 有两个连续棋子，可以产生forks
                    forks += 1
            score += forks * 5




                # 根据连续棋子数奖励得分
            score += continuous_self * 10

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
            return 0  # Game is a draw

        #chosen_column = random.choice(available_columns)
         # 使用评估函数选择列
        #scores = [evaluate_column(c, current_board, current_mark, configuration,start_time, time_limit) for c in available_columns]
        #chosen_column = available_columns[scores.index(max(scores))]

        scores = [evaluate_column(c, current_board, current_mark, configuration, start_time, time_limit) for c in available_columns]
        if float('inf') in scores:  # 如果检测到关键位置
            chosen_column = available_columns[scores.index(float('inf'))]
        else:
            chosen_column = available_columns[scores.index(max(scores))]


        # Place the piece in the chosen column
        last_row = -1
        for i in range((chosen_column + 1) * configuration['rows'] - 1, chosen_column * configuration['rows'] - 1, -1):
            if current_board[i] == 0:
                current_board[i] = current_mark
                last_row = i // configuration['columns']  # 计算行号
                break

        # 使用 last_col 和 last_row 调用 is_terminal
        if is_terminal(current_board, chosen_column, last_row):
            if current_mark == state['mark']:
                return 1  # The current player wins
            else:
                return -1  # The opponent wins

        # Switch player
        current_mark = 3 - current_mark


def my_agent(observation, configuration):
    start_time = time.time()  # 记录开始时间
    time_limit = 1.8
    num_simulations = 200
    root = Node(observation)

    for _ in range(num_simulations):
        if time.time() - start_time > time_limit:  # 检查是否超时
            break  # 如果超过时间限制，立即退出循环
        node = root
        # 选择和扩展
        while node.children:
            node = node.select_child(configuration)
        node.expand(configuration)


        # 模拟
        result = simulate_game(node.state,start_time,time_limit)
        # 反向传播
        node.backpropagate(result)

    # 如果root有子节点，选择访问次数最多的子节点
    if root.children:
        best_child = sorted(root.children, key=lambda c: c.visits)[-1]
        best_move = get_best_move(root.state, best_child.state, configuration,start_time, time_limit)
    else:
        # 使用启发式方法选择一个列
        available_columns = [c for c in range(configuration['columns']) if observation['board'][c] == 0]
        scores = [evaluate_column(c, observation['board'], observation['mark'], configuration,start_time, time_limit) for c in available_columns]
        if float("inf") in scores:
            best_move = available_columns[scores.index(float("inf"))]
        else:
            best_move = available_columns[scores.index(max(scores))]

    return best_move
