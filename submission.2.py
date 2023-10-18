#加了点启发式评估分数 考虑限制MTCS中最大探索深度
import random
import math


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
                return float('inf')  # 未访问的子节点=无限大的UCB值
            else:
                return c.wins / c.visits + 2*( math.log(self.visits) / c.visits) ** 0.5#参考ucb公式 c=2 可调整

        return max(self.children, key=ucb)




    def expand(self, configuration):
        for c in range(configuration['columns']):
            if self.state['board'][c] == 0:
                new_board = list(self.state['board'])


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






    def backpropagate(self, result):

        self.visits += 1
        self.wins += result
        if self.parent:
            self.parent.backpropagate(result)


def get_best_move(root_state, best_child_state, configuration):
    for c in range(configuration['columns']):
        col_top_idx = c
        if root_state['board'][col_top_idx] == 0 and best_child_state['board'][col_top_idx] != 0:
            return c

    # 如果没有找到最佳列，随机选择一个可用列
    available_columns = [c for c in range(configuration['columns']) if root_state['board'][c] == 0]
    if available_columns:
        scores = [evaluate_column(c, root_state['board'], root_state['mark'], configuration) for c in available_columns]
        return available_columns[scores.index(max(scores))]

    return 0  # 默认返回第0列(异常情况）

def evaluate_column(column, board, mark, configuration):
    score = 0
    opponent_mark = 3 - mark
    center_column = configuration['columns'] // 2

    # 奖励靠近中心位置
    score += (1 / (abs(column - center_column) + 1)) * 10

    # 为每个可能的放置位置计算得分
    for row in range(configuration['rows']):
        idx = column + row * configuration['columns']
        if board[idx] == 0:
            # 如果此位置是当前玩家放置后形成的连续棋子数
            continuous_self = sum(1 for i in range(4)
                                  if 0 <= idx + i * configuration['columns'] < len(board)
                                  and board[idx + i * configuration['columns']] == mark)

            # 如果此位置是对方放置后形成的连续棋子数
            continuous_opponent = sum(1 for i in range(4)
                                      if 0 <= idx + i * configuration['columns'] < len(board)
                                      and board[idx + i * configuration['columns']] == opponent_mark)


            if continuous_opponent == 3:  # 对方差一个就能赢 优先堵路
                return float('inf')

            score += continuous_self * 10  # 奖励己方创造连续棋子数

    return score


def simulate_game(state):

    current_board = list(state['board'])
    current_mark = state['mark']
    configuration = {
        'columns': 7,
        'rows': 6,
    }



    def is_terminal(board, last_col, last_row):#从最后一个落子检查
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
        available_columns = get_available_columns(current_board)
        if not available_columns:
            return 0  # Game is a draw

        #chosen_column = random.choice(available_columns)初始方法 忽视
         # 使用评估函数选择
        scores = [evaluate_column(c, current_board, current_mark, configuration) for c in available_columns]
        chosen_column = available_columns[scores.index(max(scores))]

        last_row = -1
        for i in range((chosen_column + 1) * configuration['rows'] - 1, chosen_column * configuration['rows'] - 1, -1):
            if current_board[i] == 0:
                current_board[i] = current_mark
                last_row = i // configuration['columns']  # 计算行号
                break


        if is_terminal(current_board, chosen_column, last_row):
            if current_mark == state['mark']:
                return 1  # 己方赢
            else:
                return -1  # 对方赢

        # 换边
        current_mark = 3 - current_mark



def my_agent(observation, configuration):
    num_simulations = 10
    root = Node(observation)

    for _ in range(num_simulations):
        node = root
        # 选择和扩展
        while node.children:
            node = node.select_child()
        node.expand(configuration)

        # 模拟
        result = simulate_game(node.state)
        node.backpropagate(result)

    # 选择访问次数最多的子节点
    if root.children:
        best_child = sorted(root.children, key=lambda c: c.visits)[-1]
        best_move = get_best_move(root.state, best_child.state, configuration)
    else:
        # 启发式方法选择一个列
        available_columns = [c for c in range(configuration['columns']) if observation['board'][c] == 0]
        scores = [evaluate_column(c, observation['board'], observation['mark'], configuration) for c in available_columns]
        best_move = available_columns[scores.index(max(scores))]

    return best_move
