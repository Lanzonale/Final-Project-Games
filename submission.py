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
                return float('inf')
            else:
                return c.wins / c.visits + 2*( math.log(self.visits) / c.visits) ** 0.5

        return max(self.children, key=ucb)




    def expand(self, configuration):
        for c in range(configuration['columns']):
            if self.state['board'][c] == 0:
                new_board = list(self.state['board'])

                for i in range((c + 1) * configuration['rows'] - 1, c * configuration['rows'] - 1, -1):
                    if new_board[i] == 0:
                        new_board[i] = self.state['mark']


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
        return random.choice(available_columns)

    return 0  # 默认返回第0列(意外情况下）


def simulate_game(state):

    current_board = list(state['board'])
    current_mark = state['mark']
    configuration = {
        'columns': 7,
        'rows': 6,
    }



    def is_terminal(board, last_col, last_row):#节省时间 只从最后一个子的四周检查
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
            return 0

        chosen_column = random.choice(available_columns)

        last_row = -1
        for i in range((chosen_column + 1) * configuration['rows'] - 1, chosen_column * configuration['rows'] - 1, -1):
            if current_board[i] == 0:
                current_board[i] = current_mark
                last_row = i // configuration['columns']  # 计算行号
                break


        if is_terminal(current_board, chosen_column, last_row):
            if current_mark == state['mark']:
                return 1  # 胜
            else:
                return -1  # 负

        # 交换操作方
        current_mark = 3 - current_mark



def act(observation, configuration):
    num_simulations = 100
    root = Node(observation)

    for _ in range(num_simulations):
        node = root
        # 选择和扩展
        while node.children:
            node = node.select_child()
        node.expand(configuration)

        result = simulate_game(node.state)

        node.backpropagate(result)

    # 选择访问次数最多的子节点
    if root.children:
        best_child = sorted(root.children, key=lambda c: c.visits)[-1]
        best_move = get_best_move(root.state, best_child.state, configuration)
    else:
        # or选择一个可用随机列
        available_columns = [c for c in range(configuration.columns) if observation.board[c] == 0]
        best_move = random.choice(available_columns)

    return best_move